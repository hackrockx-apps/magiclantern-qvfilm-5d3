#!/usr/bin/env python3
"""QVFIL v0.6.8: camera-side READ-ONLY lossless preflight.

Exact Magic Lantern 2025, layered over known-good QVFIL v0.6.6.
This module C patch adds ONLY two menu update callbacks (called by ML menu)
and menu entries. Does NOT change the compression task, raw recorder, queues,
sensor, buffer, FIO, lens focus or any input/boot settings. The negative
lossless compressor result is NOT measurable while the 5D3 guard is active.
"""
import argparse
import subprocess
from pathlib import Path

import apply_cinema_slim_v066 as previous

UPSTREAM = previous.UPSTREAM
TARGET_FILE = previous.TARGET_FILE
replace_once = previous.replace_once


def patch(source):
    source = previous.patch(source)

    # Important: do not make a "silent fix" to the compress task. A failed
    # slot is already in the writer queue as SLOT_CAPTURING. The host model
    # in v0.6.7 has no authority to prove the embedded queue-safe abort path.
    source = replace_once(
        source,
        'static struct menu_entry qvfilm_hud_menu[] = {',
        '''/* QVFIL v0.6.8: menu callbacks ONLY; no compressor or writer hooks.
 * Historical lossless error code is UNKNOWN. Never claim to read it.
 * This is a risk preflight, not an actual hardware encoder probe.
 */
static MENU_UPDATE_FUNC(qvfilm_lossless_diag_update)
{
    MENU_SET_NAME("QVFIL Lossless Diag");
    MENU_SET_VALUE("%db %dx%d", BPP, res_x, res_y);
    if (!is_camera("5D3", "*"))
    {
        MENU_SET_RINFO("5D3 ONLY");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "This diagnostic applies only to EOS 5D Mark III 1.2.3.");
        return;
    }
    if (OUTPUT_COMPRESSION)
    {
        MENU_SET_RINFO("LJ BLOCKED");
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "Lossless remains BLOCKED by the 5D3 RAW recorder guard. "
            "No encoder probe or code capture is performed.");
    }
    else if (!raw_video_enabled)
    {
        MENU_SET_RINFO("RAW OFF");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "RAW is disabled. No lossless test runs. "
            "Previous compressor error code remains unknown.");
    }
    else
    {
        MENU_SET_RINFO("LJ OFF");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "RAW uncompressed. Historical lossless code UNKNOWN; "
            "no new 14-bit test and no unsafe codec changes.");
    }
}

static MENU_UPDATE_FUNC(qvfilm_lossless_codes_update)
{
    MENU_SET_NAME("QVFIL LJ Error Guide");
    MENU_SET_VALUE("-1 -2 -3");
    MENU_SET_RINFO("HIST: ?");
    MENU_SET_WARNING(MENU_WARN_INFO,
        "Guide only: -1 encoder init, -2 1000ms timeout, "
        "-3 invalid JPEG marker. NO live error code captured.");
}

static struct menu_entry qvfilm_hud_menu[] = {'''
    )

    source = replace_once(
        source,
        '''    {
        .name = "QVFIL Shoot Check",
        .update = qvfilm_shoot_check_update,''',
        '''    {
        .name = "QVFIL Lossless Diag",
        .update = qvfilm_lossless_diag_update,
        .help = "Read-only: shows blocked lossless status; no codec probe.",
        .help2 = "5D3 1.2.3 lossless guard remains ON. Historical code unknown.",
    },
    {
        .name = "QVFIL LJ Error Guide",
        .update = qvfilm_lossless_codes_update,
        .help = "Historical error codes GUIDE only, not live measurements.",
        .help2 = "-1 init; -2 timeout; -3 invalid JPEG. Never enable LJ to test.",
    },
    {
        .name = "QVFIL Shoot Check",
        .update = qvfilm_shoot_check_update,'''
    )
    source = replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.6")',
        'MENU_SET_RINFO("QVFIL v0.6.8")'
    )
    source = replace_once(
        source,
        'v0.6.6: Optional one-row slim monitor, no duplicate top badge.',
        'v0.6.8: Read-only lossless status and historical error guide.'
    )

    return source


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", required=True)
    args = p.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        p.error("Require Magic Lantern source git checkout")
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != UPSTREAM:
        p.error("Wrong upstream source commit " + actual)
    target = root / TARGET_FILE
    before = target.read_text(encoding="utf-8")
    after = patch(before)
    target.write_text(after, encoding="utf-8")
    print("QVFIL v0.6.8: read-only Lossless Diag menu; no 14-bit capture.")
    print("RAW recorder and compression task unchanged; hardware test pending.")


if __name__ == "__main__":
    main()
