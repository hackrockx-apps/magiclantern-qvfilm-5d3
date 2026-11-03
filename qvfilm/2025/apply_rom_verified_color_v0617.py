#!/usr/bin/env python3
"""QVFIL v0.6.17 — ROM-verified opt-in 5D3.123 STBY Color Lab.

Hardware v0.6.16 showed ROM:672EEACE / SIG PASS, M:5D3,
FW:9.0.1 A6(3... (not public Canon 1.2.3). Unlike
is_camera("5D3","1.2.3") which compares the misleading property string,
the ML2025 boot signature checks mapped firmware ROM.

Safety conditions:
- ROM check must be run manually from Movie, and PASS in this session.
- Both compiled model 5D3 and DIGIC 5 still strictly required.
- Same RAW STBY, 1x LV, <=1600x900, 10b and native 14b conditions.
- Color Lab OFF at boot; recording retains existing upstream preview.
- No scan or large memory access from the live preview callback.
"""
import argparse
import subprocess
from pathlib import Path
import apply_rom_signature_probe_v0616 as previous

UPSTREAM=previous.UPSTREAM
TARGET_FILE=previous.TARGET_FILE
replace_once=previous.replace_once

OLD_CHECK = (
    '#define QVFIL_LAB_CAMERA_OK (get_digic_version() == 5 && '
    '(cam_5d3_123 || is_camera("5D3", "1.2.3")))'
)
NEW_CHECK = (
    '/* ROM verification is cached after explicit user-selected ROM Check.\n'
    ' * Never checksum ROM from any preview/recording callback.\n'
    ' * On v0.6.15, PROP_FIRMWARE_VER returned 9.0.1 A6... even though\n'
    ' * boot-compatible 5D3.123 ROM checksum was 0x672EEACE.\n'
    ' * Do not relax the model/DIGIC or RAW standby gates.\n'
    ' */\n'
    '#define QVFIL_LAB_CAMERA_OK (is_camera("5D3", "*") && \\\n'
    '    get_digic_version() == 5 && \\\n'
    '    qvfilm_rom_sig_done_v0616 && \\\n'
    '    qvfilm_rom_sig_v0616 == 0x672EEACEU)'
)

OLD_ID_FAILURE='''    else if (!QVFIL_LAB_CAMERA_OK)
    {
        MENU_SET_RINFO("ID %d/%d D%d", cam_5d3_123,
                       is_camera("5D3", "1.2.3"), get_digic_version());
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "5D3.123 blocked: init ID/live ID/DIGIC shown. Do not bypass target guard.");
    }'''
NEW_ID_FAILURE='''    else if (!is_camera("5D3", "*") || get_digic_version() != 5)
    {
        MENU_SET_RINFO("5D3 D5 ONLY");
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "Wrong model or DIGIC. Color Preview Lab is blocked.");
    }
    else if (!qvfilm_rom_sig_done_v0616)
    {
        MENU_SET_RINFO("RUN ROM CHECK");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "First select Movie -> QVFIL ROM Check and verify SIG PASS. No implicit ROM scan.");
    }
    else if (qvfilm_rom_sig_v0616 != 0x672EEACEU)
    {
        MENU_SET_RINFO("ROM MISMATCH");
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "Camera ROM signature does not match ML 5D3.123. Color Lab blocked.");
    }'''

def patch(source):
    source=previous.patch(source)
    # Move the existing cached ROM result state ahead of the LAB guard and
    # standby preview callback. Without this, C would see undeclared names.
    declaration='''static unsigned int qvfilm_rom_sig_v0616 = 0;
static int qvfilm_rom_sig_done_v0616 = 0;

'''
    source=replace_once(source,declaration,'')
    source=replace_once(
        source,
        'static int qvfilm_preview_lab = 0;',
        declaration + 'static int qvfilm_preview_lab = 0;'
    )
    source=replace_once(source,OLD_CHECK,NEW_CHECK)
    source=replace_once(source,OLD_ID_FAILURE,NEW_ID_FAILURE)
    source=replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.16")',
        'MENU_SET_RINFO("QVFIL v0.6.17")'
    )
    source=replace_once(
        source,
        'v0.6.16: Read-only firmware ROM signature evidence.',
        'v0.6.17: ROM-verified STBY Color Lab with original RAW REC.'
    )
    source=replace_once(
        source,
        '.help2 = "v0.6.13: cached 5D3.123 ID, DIGIC 5 gate; STBY frame count. REC untouched.",',
        '.help2 = "v0.6.17: run ROM Check once, then STBY color; REC uses original preview.",'
    )
    return source

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--checkout",required=True)
    args=ap.parse_args()
    root=Path(args.checkout).resolve()
    if not (root/".git").exists():
        ap.error("Requires original ML2025 Git checkout")
    sha=subprocess.check_output(
        ["git","-C",str(root),"rev-parse","HEAD"],text=True
    ).strip()
    if sha != UPSTREAM:
        ap.error("Wrong pinned upstream commit: "+sha)
    file=root/TARGET_FILE
    file.write_text(patch(file.read_text(encoding="utf-8")),encoding="utf-8")
    print("QVFIL v0.6.17: opt-in ROM-verified STBY color only.")
    print("No ROM scan in preview path. RAW capture, compressor and card I/O unchanged.")

if __name__=="__main__":
    main()
