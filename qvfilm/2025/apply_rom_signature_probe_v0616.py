#!/usr/bin/env python3
"""QVFIL v0.6.16 — read-only ROM signature evidence, NOT a gate bypass.

On v0.6.15 hardware, M:5D3 but PROP_FIRMWARE_VER starts "9.0.1 A6(3".
The ML cstart() for the 5D3.123 platform checks a 0x10000-word
additive ROM signature from 0xFF0C0000 against 0x672EEACE. Reproduce
that check in a *menu-only*, one-time, read-only diagnostic, leaving
all RAW, preview, capture and Color Lab gate code unchanged.
"""
import argparse
import subprocess
from pathlib import Path
import apply_camera_id_probe_display_v0615 as previous

UPSTREAM=previous.UPSTREAM
TARGET_FILE=previous.TARGET_FILE
replace_once=previous.replace_once

INSERT='''/* QVFIL v0.6.16: 5D3.123 ROM identity diagnostic, READ-ONLY.
 * The native boot cstart() uses exactly this start/length and expected
 * additive checksum (src/fw-signature.h). Only scan when the existing
 * camera model + DIGIC 5 tests pass, and do so once in this session.
 * This diagnostic does NOT unlock Color Lab or modify any firmware.
 */
static unsigned int qvfilm_rom_sig_v0616 = 0;
static int qvfilm_rom_sig_done_v0616 = 0;

static MENU_UPDATE_FUNC(qvfilm_rom_sig_update_v0616)
{
    MENU_SET_NAME("QVFIL ROM Check");

    if (!is_camera("5D3", "*") || get_digic_version() != 5)
    {
        MENU_SET_VALUE("TARGET FAIL");
        MENU_SET_RINFO("NO SCAN");
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "Read-only ROM probe allowed only on model 5D3, DIGIC 5.");
        return;
    }

    /* Avoid scanning while merely scrolling through Movie options.
     * The probe runs only when this exact menu entry is highlighted. */
    if (!entry->selected && !qvfilm_rom_sig_done_v0616)
    {
        MENU_SET_VALUE("SELECT ME");
        MENU_SET_RINFO("NO SCAN");
        return;
    }

    if (!qvfilm_rom_sig_done_v0616)
    {
        const volatile unsigned int *p =
            (const volatile unsigned int *)0xFF0C0000;
        unsigned int c = 0;
        int i;
        /* Boot's SIG_LEN=0x10000 is a word count, i.e. 256 KiB. */
        for (i = 0; i < 0x10000; i++)
            c += p[i];
        qvfilm_rom_sig_v0616 = c;
        qvfilm_rom_sig_done_v0616 = 1;
    }

    MENU_SET_VALUE("ROM:%X", qvfilm_rom_sig_v0616);
    if (qvfilm_rom_sig_v0616 == 0x672EEACEU)
    {
        MENU_SET_RINFO("SIG PASS");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Read-only ROM matches ML 5D3.123 boot signature. "
            "Color Lab remains locked pending separate review.");
    }
    else
    {
        MENU_SET_RINFO("SIG FAIL");
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "ROM signature differs from ML 5D3.123. Keep Color Lab OFF. "
            "Do not use this module to enable Preview Lab.");
    }
}

'''

def patch(source):
    source=previous.patch(source)
    source=replace_once(
        source,
        'static struct menu_entry qvfilm_hud_menu[] = {',
        INSERT+'static struct menu_entry qvfilm_hud_menu[] = {'
    )
    source=replace_once(
        source,
        '''    {
        .name = "QVFIL ID Probe",
        .update = qvfilm_id_probe_update,''',
        '''    {
        .name = "QVFIL ROM Check",
        .update = qvfilm_rom_sig_update_v0616,
        .help = "Read-only ROM signature match for the 5D3.123 platform.",
        .help2 = "Scans 256 KiB of ROM only once. Does NOT unlock Color Lab.",
    },
    {
        .name = "QVFIL ID Probe",
        .update = qvfilm_id_probe_update,'''
    )
    source=replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.15")',
        'MENU_SET_RINFO("QVFIL v0.6.16")'
    )
    source=replace_once(
        source,
        'v0.6.15: ID Probe bounded string formatting fix.',
        'v0.6.16: Read-only firmware ROM signature evidence.'
    )
    return source

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--checkout",required=True)
    args=parser.parse_args()
    root=Path(args.checkout).resolve()
    if not (root/".git").exists():
        parser.error("Expected pinned Magic Lantern git checkout")
    sha=subprocess.check_output(
        ["git","-C",str(root),"rev-parse","HEAD"],text=True
    ).strip()
    if sha != UPSTREAM:
        parser.error("Wrong pinned upstream commit: "+sha)
    file=root/TARGET_FILE
    old=file.read_text(encoding="utf-8")
    file.write_text(patch(old),encoding="utf-8")
    print("QVFIL v0.6.16 ROM signature probe: read-only; no Color Lab gate changes.")
    print("RAW recorder, compressor, preview filter, capture and card I/O unchanged.")

if __name__=="__main__":
    main()
