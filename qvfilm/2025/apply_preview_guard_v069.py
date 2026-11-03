#!/usr/bin/env python3
"""QVFIL v0.6.9 — preview diagnostics and honest auto-ISO in Cinema Slim.

Pinned 2025 ML source; all recorder / compression / Preview implementation
bytes unchanged from v0.6.8. Does NOT repair or change Canon framing,
RAW data, camera clocks, BMP preview scaling or card writing.
"""
import argparse
import subprocess
from pathlib import Path

import apply_lossless_readonly_v068 as previous

UPSTREAM = previous.UPSTREAM
TARGET_FILE = previous.TARGET_FILE
replace_once = previous.replace_once


def patch(source):
    source = previous.patch(source)

    # Show the actual user-selected RAW Preview mode. "Auto" is a policy,
    # not a single fixed preview path. No calls that change preview_mode.
    source = replace_once(
        source,
        '''static struct menu_entry qvfilm_hud_menu[] = {''',
        '''/* QVFIL 0.6.9: read-only Preview guide. No preview setters, no
 * RAW-preview rendering hooks and no assumptions about sensor framing.
 */
static MENU_UPDATE_FUNC(qvfilm_preview_guide_update)
{
    MENU_SET_NAME("QVFIL Preview Guide");
    const char * mode = "Unknown";
    if (preview_mode == 0) mode = "Auto";
    else if (preview_mode == 1) mode = "Real-time";
    else if (preview_mode == 2) mode = "Framing";
    else if (preview_mode == 3) mode = "Frozen LV";
    MENU_SET_VALUE("%s", mode);

    if (!is_camera("5D3", "1.2.3"))
    {
        MENU_SET_RINFO("5D3.123");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Guide intended for Canon EOS 5D Mark III firmware 1.2.3.");
    }
    else if (preview_mode == 0)
    {
        MENU_SET_RINFO("AUTO");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Auto may use slow RAW Framing for smaller modes. "
            "Compare Real-time in STBY; its Canon frame may be smaller.");
    }
    else if (preview_mode == 1)
    {
        MENU_SET_RINFO("CANON LV");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Color and fast Canon LiveView. Image may be smaller or "
            "framing inaccurate versus recorded RAW crop.");
    }
    else if (preview_mode == 2)
    {
        MENU_SET_RINFO("SLOW");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Correct RAW framing, lower-res and slow. This is preview "
            "only, not recorded image quality.");
    }
    else if (preview_mode == 3)
    {
        MENU_SET_RINFO("FREEZE");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Frozen LV may be used for recording speed, not composition.");
    }
    else
    {
        MENU_SET_RINFO("UNKNOWN");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Unknown Preview setting. Keep accepted working configuration.");
    }
}

static struct menu_entry qvfilm_hud_menu[] = {'''
    )

    source = replace_once(
        source,
        '''    {
        .name = "QVFIL Shoot Check",
        .update = qvfilm_shoot_check_update,''',
        '''    {
        .name = "QVFIL Preview Guide",
        .update = qvfilm_preview_guide_update,
        .help = "Shows RAW video Preview selection; does NOT change it.",
        .help2 = "RAW video > Preview: Auto/Real-time/Framing/Frozen LV.",
    },
    {
        .name = "QVFIL Shoot Check",
        .update = qvfilm_shoot_check_update,'''
    )

    # Stock Magic Lantern shows Auto ISO with an "A" designation. Earlier
    # QVFIL versions printed its approximate frame value as manual ISO.
    # Do not guess Canon's effective/digital-gain ISO; label AUTO instead.
    # Only Cinema Slim text changes; the numerical RAW ISO and file remain.
    source = replace_once(
        source,
        '''            if (iso)
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           420, 356, "ISO%d", iso);
            else
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           420, 356, "ISO--");''',
        '''            if (!lens_info.raw_iso && lens_info.raw_iso_auto)
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           420, 356, "ISO AUTO");
            else if (iso)
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           420, 356, "ISO%d", iso);
            else
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           420, 356, "ISO--");'''
    )

    source = replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.8")',
        'MENU_SET_RINFO("QVFIL v0.6.9")'
    )
    source = replace_once(
        source,
        'v0.6.8: Read-only lossless status and historical error guide.',
        'v0.6.9: Preview mode guide and honest Cinema Slim Auto ISO label.'
    )
    return source


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", required=True)
    args = p.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        p.error("Requires pinned Magic Lantern source checkout")
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != UPSTREAM:
        p.error("Wrong upstream commit: " + actual)
    path = root / TARGET_FILE
    before = path.read_text(encoding="utf-8")
    path.write_text(patch(before), encoding="utf-8")
    print("QVFIL v0.6.9: read-only Preview Guide / Cinema Slim Auto ISO.")
    print("Original preview, compressor, RAW writer unchanged.")
    print("Color/full-frame preview NOT repaired: camera validation pending.")


if __name__ == "__main__":
    main()
