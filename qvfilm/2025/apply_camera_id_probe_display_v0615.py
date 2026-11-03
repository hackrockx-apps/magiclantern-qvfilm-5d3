#!/usr/bin/env python3
"""QVFIL v0.6.15: fix the read-only ID Probe truncated-format bug.

Camera acceptance of v0.6.14 showed "M: 6s" and "FW: 10s".
The Magic Lantern menu snprintf path does not handle field precision
(%.6s / %.10s) as expected on this target. Use explicitly bounded
NUL-terminated local strings and ordinary %s instead. No identity
guard, RAW recording or preview changes.
"""
import argparse
import subprocess
from pathlib import Path
import apply_camera_id_probe_v0614 as previous

UPSTREAM=previous.UPSTREAM
TARGET_FILE=previous.TARGET_FILE
replace_once=previous.replace_once

OLD_PROBE='''static MENU_UPDATE_FUNC(qvfilm_id_probe_update)
{
    MENU_SET_NAME("QVFIL ID Probe");
    MENU_SET_VALUE("M:%.6s",
        __camera_model_short[0] ? __camera_model_short : "EMPTY");
    MENU_SET_RINFO("FW:%.10s",
        firmware_version[0] ? firmware_version : "EMPTY");
    MENU_SET_WARNING(MENU_WARN_INFO,
        "Read-only: M=ML camera model, FW=ML firmware property. "
        "If empty/mismatch do not bypass 5D3.123 guard.");
}'''

NEW_PROBE='''static MENU_UPDATE_FUNC(qvfilm_id_probe_update)
{
    /* The camera's menu formatter does not reliably support %.Ns.
     * Use bounded NUL-terminated copies and the supported plain %s.
     * Both source buffers already exist in the ML core; read-only.
     * Never modify camera ID, PROP_FIRMWARE_VER or Color Lab gating.
     */
    char model_text[8] = {0};
    char fw_text[12] = {0};
    int i;

    for (i = 0; i < 6 && __camera_model_short[i]; i++)
        model_text[i] = __camera_model_short[i];

    for (i = 0; i < 10 && firmware_version[i]; i++)
        fw_text[i] = firmware_version[i];

    MENU_SET_NAME("QVFIL ID Probe");
    MENU_SET_VALUE("M:%s", model_text[0] ? model_text : "EMPTY");
    MENU_SET_RINFO("FW:%s", fw_text[0] ? fw_text : "EMPTY");
    MENU_SET_WARNING(MENU_WARN_INFO,
        "Read-only: M=ML camera model, FW=ML firmware property. "
        "If EMPTY/mismatch, keep Color Lab OFF and photograph these values.");
}'''

def patch(source):
    source=previous.patch(source)
    source=replace_once(source, OLD_PROBE, NEW_PROBE)
    source=replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.14")',
        'MENU_SET_RINFO("QVFIL v0.6.15")'
    )
    source=replace_once(
        source,
        'v0.6.14: Read-only model and firmware property probe.',
        'v0.6.15: ID Probe bounded string formatting fix.'
    )
    return source

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkout",required=True)
    args=p.parse_args()
    root=Path(args.checkout).resolve()
    if not (root/".git").exists():
        p.error("Requires pinned ML2025 source")
    sha=subprocess.check_output(
        ["git","-C",str(root),"rev-parse","HEAD"],text=True
    ).strip()
    if sha!=UPSTREAM:
        p.error("Wrong source SHA: "+sha)
    target=root/TARGET_FILE
    target.write_text(patch(target.read_text(encoding="utf-8")),encoding="utf-8")
    print("QVFIL v0.6.15: Model/FW local bounded strings with plain %s.")
    print("Does not unlock Color Lab, alter recorder, or write firmware properties.")

if __name__=="__main__":
    main()
