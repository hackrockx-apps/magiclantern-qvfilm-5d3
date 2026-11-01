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
 * The existing ShootTask status refresh is ~1 Hz, never every VSYNC.
 */
static void qvfilm_draw_cinema_overlay(void)
{
    if (qvfilm_hud_enabled != 2 || !is_camera("5D3", "*") ||
        !raw_video_enabled || !lv || !is_movie_mode() ||
        !get_global_draw() || gui_menu_shown() || !liveview_display_idle())
        return;

    const char *state =
        RAW_IS_RECORDING ? "REC" :
        RAW_IS_PREPARING ? "ARMING" :
        RAW_IS_FINISHING ? "ENDING" : "STBY";
    int fps = fps_get_current_x1000();
    bmp_fill(COLOR_BG_DARK, 32, 35, 656, 30);
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BG_DARK),
               44, 40, "QVFIL CINEMA");
    bmp_printf(FONT(FONT_MED,
                    RAW_IS_RECORDING ? COLOR_RED : COLOR_WHITE,
                    COLOR_BG_DARK), 280, 40, "%s", state);
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BG_DARK),
               475, 40, "%d.%02d FPS", fps / 1000, (fps % 1000) / 10);

    bmp_fill(COLOR_BG_DARK, 32, 397, 656, 30);
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BG_DARK),
               44, 403, "%dx%d  %db %s    ISO %d",
               res_x, res_y, BPP,
               OUTPUT_COMPRESSION ? "LJ" : "RAW",
               lens_info.iso);
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
    source = replace_once(
        source,
        '    /* Determine if we should redraw */\n'
        '    if (!RAW_IS_IDLE && liveview_display_idle())',
        '    qvfilm_draw_cinema_overlay();\n'
        '    /* Determine if we should redraw */\n'
        '    if (!RAW_IS_IDLE && liveview_display_idle())'
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

static MENU_UPDATE_FUNC(qvfilm_hud_menu_update)
{
    MENU_SET_RINFO("QVFIL v0.5.3");
    if (qvfilm_hud_enabled == 2)
    {
        /* LiveView from inside the ML menu is NOT the recording screen:
         * the LV key toggles Transparent Menu; close the menu first. */
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Exit ML menu with DELETE/MENU before using START/STOP.");
    }
}

static struct menu_entry qvfilm_hud_menu[] = {
    {
        .name = "QVFIL HUD",
        .priv = &qvfilm_hud_enabled,
        .update = qvfilm_hud_menu_update,
        .max = 2,
        .choices = CHOICES("OFF", "Bars", "Cinema"),
        .help = "Close ML menu, then START/STOP to record in Movie LiveView.",
        .help2 = "LV in menu = transparent menu, NOT REC. Requires Global Draw ON.",
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
    print("QVFIL v0.5.3 patch: clarified menu exit, preserved RAW key handler and cinema overlay")
    print("WARNING: CPU/emulator build PASS is not camera hardware PASS. NOT FOR INSTALLATION.")


if __name__ == "__main__":
    main()
