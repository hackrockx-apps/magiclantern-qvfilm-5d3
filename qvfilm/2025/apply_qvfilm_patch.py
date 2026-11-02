#!/usr/bin/env python3
"""Apply QVFilm's conservative 2025-specific recorder/UI patch.
Not a camera firmware flasher. Inputs: an exact checkout of commit ed3e7c0df.
No rebase to unrelated (2018/2020) Magic Lantern module ABI.
"""
import argparse
import subprocess
from pathlib import Path

UPSTREAM = "ed3e7c0dfacfdeaf3349dee73edf9e3621217462"
TARGET_FILE = "modules/raw_video/mlv_lite/mlv_lite.c"


def replace_once(text, original, replacement):
    count = text.count(original)
    if count != 1:
        raise ValueError("Source anchor mismatch (expected exactly once, found %d): %r" %
                         (count, original[:90]))
    return text.replace(original, replacement, 1)


def patch(source):
    # Guard ONLY the reported path. Fail closed instead of deliberately entering
    # a compression task that ASSERTs at line 2742 on this camera/build.
    source = replace_once(
        source,
        'static CONFIG_INT("raw.output_format", output_format, 3);',
        'static CONFIG_INT("raw.output_format", output_format, 3);\n'
        'static CONFIG_INT("qvfilm.hud.enabled", qvfilm_hud_enabled, 0);\n'
    )

    # Real observed 5D3.123 bug: 14-bit lossless compressor returned negative;
    # existing code calls ASSERT(0). Simply swallowing an error in compress_task
    # would let invalid frame slots reach the MLV writer, so we do not do that.
    source = replace_once(
        source,
        'void raw_video_rec_task()\n{\n    //~ console_show();',
        'void raw_video_rec_task()\n{\n'
        '    /* QVFilm guard: do not feed known-failing lossless to the encoder.\n'
        '     * This is a CONTAINMENT measure, not a repair of lossless compression.\n'
        '     * 14-bit uncompressed remains available for a fast enough card.\n'
        '     * Restrict to verified 5D3.123, leave other cameras unchanged. */\n'
        '    if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)\n'
        '    {\n'
        '        printf("QVFIL: Lossless RAW blocked on 5D3.123 (known mlv_lite ASSERT).\\n");\n'
        '        NotifyBox(6000, "QVFIL: Lossless blocked. Use RAW uncompressed.");\n'
        '        return;\n'
        '    }\n'
        '    //~ console_show();'
    )

    # Draw only in Canon's *idle* LiveView status path, at 1s cadence.
    # Keeps the original Canon/Magic Lantern shutter/AF/record handlers.
    overlay = r"""
/* QVFIL Cinema Overlay: opt-in, non-invasive bitmap HUD (not RAW pixels).
 * Do not draw in menus or Canon GUI states; half-shutter/AF can switch preview.
 * Drawn during ShootTask polling after Canon's shooting status UI updates,
 * bounded to <=4 Hz, never during VSYNC or RAW/EDMAC capture.
 */
/* Observable run-time gate; counters visible in Movie > QVFIL HUD Diagnostics.
 * 0=drawn, 1=disabled, 2=not Movie LiveView/RAW, 3=GD setting OFF,
 * 4=bitmap palette disabled, 6=Canon UI not idle.
 * No card writes, no log dumps, no polling in the frame capture path.
 */
static volatile unsigned int qvfilm_hud_draws = 0;
static volatile int qvfilm_hud_gate_code = 1;

static void qvfilm_draw_cinema_overlay(void)
{
    if (qvfilm_hud_enabled != 2) { qvfilm_hud_gate_code = 1; return; }
    if (!is_camera("5D3", "*") || !raw_video_enabled || !lv || !is_movie_mode())
    { qvfilm_hud_gate_code = 2; return; }
    if (!get_global_draw_setting()) { qvfilm_hud_gate_code = 3; return; }
    if (!bmp_is_on()) { qvfilm_hud_gate_code = 4; return; }
    /* Preserve the most recent LiveView gate when the operator reopens Movie. */
    if (gui_menu_shown()) return;
    if (!liveview_display_idle()) { qvfilm_hud_gate_code = 6; return; }
    qvfilm_hud_gate_code = 0;

    /* Canon may use a standard LV display mode where get_global_draw() is
     * false despite Global Draw setting being ON. Since this mode is explicitly
     * user selected, use the setting and guard actual bitmap/display state.
     * Never re-enable LCD or change Canon UI display modes ourselves. */
    static int last_overlay_draw = INT_MIN;
    if (!should_run_polling_action(250, &last_overlay_draw)) return;

    const char *state =
        RAW_IS_RECORDING ? "REC" :
        RAW_IS_PREPARING ? "ARMING" :
        RAW_IS_FINISHING ? "ENDING" : "STBY";
    int fps = fps_get_current_x1000();
    BMP_LOCK(
        bmp_fill(COLOR_ALMOST_BLACK, 24, 24, 672, 30);
        bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                   36, 29, "QVFIL CINEMA v0.5.4");
        bmp_printf(FONT(FONT_MED,
                        RAW_IS_RECORDING ? COLOR_RED : COLOR_WHITE,
                        COLOR_ALMOST_BLACK), 328, 29, "%s", state);
        bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                   504, 29, "%d.%02d FPS", fps / 1000, (fps % 1000) / 10);

        bmp_fill(COLOR_ALMOST_BLACK, 24, 422, 672, 30);
        bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                   36, 427, "%dx%d  %db %s  ISO %d",
                   res_x, res_y, BPP,
                   OUTPUT_COMPRESSION ? "LJ" : "RAW",
                   lens_info.iso);
    )
    qvfilm_hud_draws++;
}
"""
    source = replace_once(
        source,
        "/* Display the 'Recording...' icon and status */\n"
        'static REQUIRES(ShootTask)\n'
        'void show_recording_status()',
        overlay + "\n/* Display the 'Recording...' icon and status */\n"
        'static REQUIRES(ShootTask)\n'
        'void show_recording_status()'
    )
    # The old v0.5.3 call ran inside show_recording_status() only after the
    # ~1-second early-return, and its pixels could be cleared by Canon's UI.
    # Draw after core status from the main ShootTask callback instead.
    source = replace_once(
        source,
        '    /* update status messages */\n'
        '    show_recording_status();\n\n'
        '    return 0;',
        '    /* update status messages */\n'
        '    show_recording_status();\n'
        '    /* QVFIL opt-in bitmap overlay goes last, outside the 1s gate. */\n'
        '    qvfilm_draw_cinema_overlay();\n\n'
        '    return 0;'
    )

    # Explain the guard in the Data format submenu before REC is pressed.
    source = replace_once(
        source,
        'static MENU_UPDATE_FUNC(output_format_update)\n{\n    refresh_raw_settings(0);',
        'static MENU_UPDATE_FUNC(output_format_update)\n{\n    refresh_raw_settings(0);\n'
        '    if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)\n'
        '        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,\n'
        '            "QVFIL: Lossless disabled on 5D3.123; choose RAW uncompressed.");'
    )

    # Blackmagic-inspired status info uses the existing LiveView bars, so
    # Canon Movie menu, exposure controls and record button remain untouched.
    # Disabled by default; no per-frame rendering, polling, or hot path writes.
    ui = r"""
/* QVFilm Cinema Monitor: readable cinema status in the existing LV info bars.
 * Visually inspired by dedicated cinema-camera HUDs, not a Blackmagic UI copy.
 * Opt in via first Movie item -> QVFIL Cinema HUD. Draw via core LVInfo.
 */
static LVINFO_UPDATE_FUNC(qvfilm_top_info)
{
    LVINFO_BUFFER(48);
    if (qvfilm_hud_enabled != 1 || !is_camera("5D3", "*") || !lv || !is_movie_mode()) return;
    int fps = fps_get_current_x1000();
    snprintf(buffer, sizeof(buffer), "QVFIL %s %d.%02d",
             RAW_IS_RECORDING ? "REC" : "STBY",
             fps / 1000, (fps % 1000) / 10);
    item->color_fg = RAW_IS_RECORDING ? COLOR_RED : COLOR_WHITE;
    item->color_bg = COLOR_BG_DARK;
}

static LVINFO_UPDATE_FUNC(qvfilm_bottom_info)
{
    LVINFO_BUFFER(64);
    if (qvfilm_hud_enabled != 1 || !is_camera("5D3", "*") || !lv || !is_movie_mode()) return;
    /* The resolution and bit depth come from the actual MLV recorder state,
     * never fake 3K or advertise lossless as operational. */
    snprintf(buffer, sizeof(buffer), "%dx%d  %db %s  ISO%u",
             res_x, res_y, BPP,
             OUTPUT_COMPRESSION ? "LJ" : "RAW",
             lens_info.iso);
    item->color_fg = COLOR_WHITE;
    item->color_bg = COLOR_BG_DARK;
}

/* Explicit one-tap exit from the Magic Lantern menu. When ML is still
 * in transparent-menu mode (a menu item, e.g. Gradual Exposure, remains
 * visible above the live image), START/STOP may be consumed by menu.c.
 * Do not manufacture fake REC key events or auto-enable recording.
 */
static MENU_SELECT_FUNC(qvfilm_enter_cinema)
{
    if (!lv || !is_movie_mode())
    {
        NotifyBox(3000, "QVFIL: Switch to Movie LiveView first.");
        return;
    }
    if (!raw_video_enabled)
    {
        NotifyBox(3000, "QVFIL: Enable RAW video in Movie first.");
        return;
    }
    gui_stop_menu();
    lens_display_set_dirty();
}

static MENU_UPDATE_FUNC(qvfilm_enter_cinema_update)
{
    MENU_SET_RINFO("SET / LIVEVIEW");
    if (!lv || !is_movie_mode())
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING, "Requires Movie LiveView.");
    else if (!raw_video_enabled)
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING, "Turn RAW video ON first.");
}

static MENU_UPDATE_FUNC(qvfilm_hud_menu_update)
{
    MENU_SET_RINFO("QVFIL v0.5.4");
    if (qvfilm_hud_enabled == 2 && !get_global_draw_setting())
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING, "Enable Global Draw to use Cinema Overlay.");
}

static MENU_UPDATE_FUNC(qvfilm_hud_diagnostics_update)
{
    MENU_SET_VALUE("Draws:%u", qvfilm_hud_draws);
    MENU_SET_RINFO("Gate:%d", qvfilm_hud_gate_code);
    MENU_SET_HELP("After closing menu: 0 drawn, 1 OFF, 2 not LV/RAW, 3 GD OFF, 4 LCD OFF, 6 UI busy.");
}

static struct menu_entry qvfilm_hud_menu[] = {
    {
        .name = "QVFIL Enter Cinema",
        .select = qvfilm_enter_cinema,
        .update = qvfilm_enter_cinema_update,
        .icon_type = IT_ACTION,
        .help = "Close ML menu fully before pressing START/STOP for RAW.",
        .help2 = "Transparent LiveView still handles keys as a Magic Lantern menu.",
    },
    {
        .name = "QVFIL Cinema HUD",
        .priv = &qvfilm_hud_enabled,
        .update = qvfilm_hud_menu_update,
        .max = 2,
        .choices = CHOICES("OFF", "Info bars", "Cinema overlay"),
        .help = "Select HUD style, then use QVFIL Enter Cinema to close ML menu.",
        .help2 = "v0.5.4: Compatible with Canon LiveView UI; rear START/STOP records.",
    },
    {
        .name = "QVFIL HUD Diagnostics",
        .update = qvfilm_hud_diagnostics_update,
        .help = "Read Draws and Gate after entering Cinema and returning to Movie.",
        .help2 = "After LiveView, Gate 0=drawn, 1=OFF, 2=not LV/RAW, 3=GD, 4=LCD, 6=busy.",
    },
};
"""
    source = replace_once(
        source,
        'static struct lvinfo_item info_items[] = {',
        ui + '\nstatic struct lvinfo_item info_items[] = {'
    )
    source = replace_once(
        source,
        '        .priority = 10,\n    }\n};\n\nstatic unsigned int raw_rec_init()',
        '        .priority = 10,\n'
        '    },\n'
        '    {\n'
        '        .name = "QVFIL Cinema Top",\n'
        '        .which_bar = LV_PREFER_TOP_BAR,\n'
        '        .update = qvfilm_top_info,\n'
        '        .preferred_position = -40,\n'
        '        .priority = 15,\n'
        '    },\n'
        '    {\n'
        '        .name = "QVFIL Cinema Bottom",\n'
        '        .which_bar = LV_PREFER_BOTTOM_BAR,\n'
        '        .update = qvfilm_bottom_info,\n'
        '        .preferred_position = 40,\n'
        '        .priority = 15,\n'
        '    }\n'
        '};\n\nstatic unsigned int raw_rec_init()'
    )
    source = replace_once(
        source,
        '    menu_add("Movie", raw_video_menu, COUNT(raw_video_menu));',
        '    /* QVFIL first so it is not lost below the Movie menu page fold. */\n'
        '    if (is_camera("5D3", "*"))\n'
        '        menu_add("Movie", qvfilm_hud_menu, COUNT(qvfilm_hud_menu));\n'
        '    menu_add("Movie", raw_video_menu, COUNT(raw_video_menu));'
    )
    source = replace_once(
        source,
        '    MODULE_CONFIG(output_format)\n',
        '    MODULE_CONFIG(output_format)\n'
        '    MODULE_CONFIG(qvfilm_hud_enabled)\n'
    )
    return source


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", required=True, help="Path to exact upstream checkout")
    p.add_argument("--allow-unverified-tree", action="store_true",
                   help="Unit tests only: DO NOT use for actual distribution")
    args = p.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not args.allow_unverified_tree:
        if not (root / ".git").exists():
            p.error("Expected an exact Git checkout of the original 2025 source.")
        actual = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        if actual != UPSTREAM:
            p.error("Wrong Magic Lantern source commit %s; expected %s" % (actual, UPSTREAM))
    file = root / TARGET_FILE
    if not file.is_file():
        p.error("No 2025 mlv_lite source at " + str(file))
    original = file.read_text(encoding="utf-8")
    updated = patch(original)  # all anchors validated before writing
    file.write_text(updated, encoding="utf-8")
    print("QVFIL v0.5.4 patch: shoot-task OLED-style LCD overlay + Canon LV compatibility")
    print("WARNING: CPU/emulator build PASS is not camera hardware PASS. NOT FOR INSTALLATION.")


if __name__ == "__main__":
    main()
