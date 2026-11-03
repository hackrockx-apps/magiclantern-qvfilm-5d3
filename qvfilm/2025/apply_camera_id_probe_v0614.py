#!/usr/bin/env python3
"""QVFIL v0.6.14: read actual ML model/firmware property; do not bypass guard.

After v0.6.13 hardware photo: Color STBY selected but ID 0/0 D5.
Both cached and live strict 5D3.123 checks failed; DIGIC5 succeeded.
Identify which string is not populated before modifying the target guard.
"""
import argparse
import subprocess
from pathlib import Path
import apply_camera_id_gate_v0613 as previous

UPSTREAM=previous.UPSTREAM
TARGET_FILE=previous.TARGET_FILE
replace_once=previous.replace_once

def patch(source):
    source=previous.patch(source)
    source=replace_once(
        source,
        '#include <property.h>\n#include <bmp.h>',
        '#include <property.h>\n#include <propvalues.h>\n#include <bmp.h>'
    )
    source=replace_once(
        source,
        'static struct menu_entry qvfilm_hud_menu[] = {',
        '''/* Identity probe displays only the *existing* ML model and
 * firmware property strings. It does not attempt to repair them,
 * authorize Color Lab or change any capture/preview/RAW setting.
 * Short field widths preserve 5D3 LCD menu readability.
 */
static MENU_UPDATE_FUNC(qvfilm_id_probe_update)
{
    MENU_SET_NAME("QVFIL ID Probe");
    MENU_SET_VALUE("M:%.6s",
        __camera_model_short[0] ? __camera_model_short : "EMPTY");
    MENU_SET_RINFO("FW:%.10s",
        firmware_version[0] ? firmware_version : "EMPTY");
    MENU_SET_WARNING(MENU_WARN_INFO,
        "Read-only: M=ML camera model, FW=ML firmware property. "
        "If empty/mismatch do not bypass 5D3.123 guard.");
}

static struct menu_entry qvfilm_hud_menu[] = {'''
    )
    source=replace_once(
        source,
        '''    {
        .name = "QVFIL Color Lab",
        .priv = &qvfilm_preview_lab,''',
        '''    {
        .name = "QVFIL ID Probe",
        .update = qvfilm_id_probe_update,
        .help = "Read the actual Magic Lantern model/firmware values.",
        .help2 = "Display-only. Camera model and PROP_FIRMWARE_VER; no writes.",
    },
    {
        .name = "QVFIL Color Lab",
        .priv = &qvfilm_preview_lab,'''
    )
    source=replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.13")',
        'MENU_SET_RINFO("QVFIL v0.6.14")'
    )
    source=replace_once(
        source,
        'v0.6.13: Cached 5D3.123 model gate + live identity diagnostics.',
        'v0.6.14: Read-only model and firmware property probe.'
    )
    return source

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkout",required=True)
    args=p.parse_args()
    root=Path(args.checkout).resolve()
    if not (root/".git").exists():
        p.error("Requires pinned ML2025 source git checkout")
    sha=subprocess.check_output(
        ["git","-C",str(root),"rev-parse","HEAD"],text=True
    ).strip()
    if sha!=UPSTREAM:
        p.error("Wrong pinned upstream: "+sha)
    file=root/TARGET_FILE
    before=file.read_text(encoding="utf-8")
    file.write_text(patch(before),encoding="utf-8")
    print("QVFIL v0.6.14: read-only camera model/firmware identity.")
    print("Existing 5D3.123 Color Lab guard is NOT relaxed.")
    print("RAW writer, compressor, preview renderer and card I/O unchanged.")

if __name__=="__main__":
    main()
