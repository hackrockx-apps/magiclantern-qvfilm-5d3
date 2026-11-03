#!/usr/bin/env python3
"""QVFIL 0.6.13: guard Color STBY with validated cached MLV Lite camera ID.

On physical 5D3.123, the v0.6.12 Movie menu showed "5D3.123 ONLY"
because a *runtime* is_camera("5D3","1.2.3") check returned false.
MLV Lite already captures this exact identity during raw_rec_init() as
cam_5d3_123. Prefer the cached identity, with the existing runtime check
as a fallback. Never authorize an unknown model or firmware version.
"""
import argparse
import subprocess
from pathlib import Path

import apply_preview_telemetry_v0612 as previous

UPSTREAM = previous.UPSTREAM
TARGET_FILE = previous.TARGET_FILE
replace_once = previous.replace_once

OLD_GUARD = (
    '#define QVFIL_LAB_STBY (qvfilm_preview_lab && '
    'is_camera("5D3", "1.2.3") && raw_video_enabled && lv && '
    'is_movie_mode() && RAW_IS_IDLE && lv_dispsize == 1 && '
    'res_x > 0 && res_x <= 1600 && res_y > 0 && res_y <= 900 && '
    'BPP == 10 && raw_info.bits_per_pixel == 14)'
)

NEW_GUARD = (
    '/* The recorder caches the firmware identity at module init. An\n'
    ' * on-camera report showed the later property-based is_camera()\n'
    ' * could disagree with that cached identity. Neither branch\n'
    ' * permits firmware other than 5D3.123; DIGIC 5 is also required.\n'
    ' * No global bypass, no change to RAW/REC or Canon firmware.\n'
    ' */\n'
    '#define QVFIL_LAB_CAMERA_OK (get_digic_version() == 5 && '
    '(cam_5d3_123 || is_camera("5D3", "1.2.3")))\n'
    '#define QVFIL_LAB_STBY (qvfilm_preview_lab && '
    'QVFIL_LAB_CAMERA_OK && raw_video_enabled && lv && '
    'is_movie_mode() && RAW_IS_IDLE && lv_dispsize == 1 && '
    'res_x > 0 && res_x <= 1600 && res_y > 0 && res_y <= 900 && '
    'BPP == 10 && raw_info.bits_per_pixel == 14)'
)

def patch(source):
    source = previous.patch(source)
    source = replace_once(source, OLD_GUARD, NEW_GUARD)
    source = replace_once(
        source,
        'else if (!is_camera("5D3", "1.2.3"))\n'
        '    {\n'
        '        MENU_SET_RINFO("5D3.123 ONLY");\n'
        '        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,\n'
        '            "Camera/firmware target mismatch. Keep the 5D3.123 guard; do not bypass it.");\n'
        '    }',
        'else if (!QVFIL_LAB_CAMERA_OK)\n'
        '    {\n'
        '        MENU_SET_RINFO("ID %d/%d D%d", cam_5d3_123,\n'
        '                       is_camera("5D3", "1.2.3"), get_digic_version());\n'
        '        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,\n'
        '            "5D3.123 blocked: init ID/live ID/DIGIC shown. Do not bypass target guard.");\n'
        '    }'
    )
    source = replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.12")',
        'MENU_SET_RINFO("QVFIL v0.6.13")'
    )
    source = replace_once(
        source,
        'v0.6.12: Lab frame counter and truthful STBY draw diagnostics.',
        'v0.6.13: Cached 5D3.123 model gate + live identity diagnostics.'
    )
    source = replace_once(
        source,
        '.help2 = "v0.6.12: F counts actual STBY RAW preview draws. Lab OFF after reboot; REC untouched.",',
        '.help2 = "v0.6.13: cached 5D3.123 ID, DIGIC 5 gate; STBY frame count. REC untouched.",'
    )
    return source

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", required=True)
    args = p.parse_args()
    root = Path(args.checkout).resolve()
    if not (root / ".git").exists():
        p.error("Requires pinned ML2025 source checkout")
    sha = subprocess.check_output(
        ["git","-C",str(root),"rev-parse","HEAD"],text=True
    ).strip()
    if sha != UPSTREAM:
        p.error("Wrong pinned upstream: " + sha)
    file = root / TARGET_FILE
    before = file.read_text(encoding="utf-8")
    file.write_text(patch(before), encoding="utf-8")
    print("QVFIL v0.6.13: prefer proven recorder init 5D3.123 target ID.")
    print("Guard never allows unknown 5D3 firmware, or non-DIGIC 5.")
    print("RAW recorder, compressor, writer, DMA and preview frame renderer unchanged.")

if __name__ == "__main__":
    main()
