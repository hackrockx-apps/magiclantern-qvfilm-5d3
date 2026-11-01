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
        '    if (cam_5d3_123 && OUTPUT_COMPRESSION)\n'
        '    {\n'
        '        printf("QVFIL: Lossless RAW blocked on 5D3.123 (known mlv_lite ASSERT).\\n");\n'
        '        NotifyBox(6000, "QVFIL: Lossless blocked. Use RAW uncompressed.");\n'
        '        return;\n'
        '    }\n'
        '    //~ console_show();'
    )

    # Explain the guard in the Data format submenu before REC is pressed.
    source = replace_once(
        source,
        'static MENU_UPDATE_FUNC(output_format_update)\n{\n    refresh_raw_settings(0);',
        'static MENU_UPDATE_FUNC(output_format_update)\n{\n    refresh_raw_settings(0);\n'
        '    if (cam_5d3_123 && OUTPUT_COMPRESSION)\n'
        '        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,\n'
        '            "QVFIL: Lossless disabled on 5D3.123; choose RAW uncompressed.");'
    )

    # Blackmagic-inspired status info uses the existing LiveView bars, so
    # Canon Movie menu, exposure controls and record button remain untouched.
    # Disabled by default; no per-frame rendering, polling, or hot path writes.
    ui = r"""
/* QVFilm Cinema Monitor: readable cinema status in the existing LV info bars.
 * Visually inspired by dedicated cinema-camera HUDs, not a Blackmagic UI copy.
 * Opt in via Movie -> QVFIL Cinema HUD. Draw is handled by core LVInfo.
 */
static LVINFO_UPDATE_FUNC(qvfilm_top_info)
{
    LVINFO_BUFFER(48);
    if (!qvfilm_hud_enabled || !cam_5d3_123 || !lv || !is_movie_mode()) return;
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
    if (!qvfilm_hud_enabled || !cam_5d3_123 || !lv || !is_movie_mode()) return;
    /* The resolution and bit depth come from the actual MLV recorder state,
     * never fake 3K or advertise lossless as operational. */
    snprintf(buffer, sizeof(buffer), "%dx%d  %db %s  ISO%u",
             res_x, res_y, BPP_D,
             OUTPUT_COMPRESSION ? "LJ" : "RAW",
             lens_info.iso);
    item->color_fg = COLOR_WHITE;
    item->color_bg = COLOR_BG_DARK;
}

static struct menu_entry qvfilm_hud_menu[] = {
    {
        .name = "QVFIL Cinema HUD",
        .priv = &qvfilm_hud_enabled,
        .max = 1,
        .help = "Cinema camera-style status strips in Movie LiveView.",
        .help2 = "Only changes display. Does not alter recording settings.",
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
        '    menu_add("Movie", raw_video_menu, COUNT(raw_video_menu));\n'
        '    /* Preserve existing Movie tab; add one optional QVFIL toggle. */\n'
        '    if (cam_5d3_123)\n'
        '        menu_add("Movie", qvfilm_hud_menu, COUNT(qvfilm_hud_menu));'
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
    print("QVFIL v0.5.0 source patch applied: 5D3 lossless fail-closed guard + opt-in LVInfo HUD")
    print("WARNING: CPU/emulator build PASS is not camera hardware PASS. NOT FOR INSTALLATION.")


if __name__ == "__main__":
    main()
