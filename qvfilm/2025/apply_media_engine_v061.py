#!/usr/bin/env python3
"""QVFIL v0.6.1: isolate Canon/ML menu snprintf compatibility bug.
This is an additional, narrowly scoped source patch layered over v0.6.0.
Never touches RAW recorder, buffers, output bit-depth or SD clock.
"""
import argparse
import subprocess
from pathlib import Path
import apply_media_engine_v060 as prior

UPSTREAM = prior.UPSTREAM
TARGET_FILE = prior.TARGET_FILE
replace_once = prior.replace_once

def patch(source):
    source = prior.patch(source)

    # The on-camera screenshot of v0.6.0 shows "Draws:u", "Obs:u.u", and
    # names filled with A characters. Canon's 5D3 vsnprintf does not behave
    # like the host runtime. Keep ONLY %d and %s in QVFIL menu renderers.
    source = replace_once(
        source,
        '    MENU_SET_VALUE("Draws:%u", qvfilm_hud_draws);',
        '    MENU_SET_NAME("QVFIL HUD Diagnostics");\n'
        '    MENU_SET_VALUE("Draws:%d", (int)qvfilm_hud_draws);'
    )
    source = replace_once(
        source,
        '    MENU_SET_VALUE("%c: %d.%dMB/s", drive,\n'
        '                   demand_tenths / 10, demand_tenths % 10);',
        '    MENU_SET_NAME("QVFIL Storage Check");\n'
        '    MENU_SET_VALUE("%s: %d.%d MB/s",\n'
        '                   drive == \'A\' ? "CF" : drive == \'B\' ? "SD" : "?",\n'
        '                   demand_tenths / 10, demand_tenths % 10);'
    )
    source = replace_once(
        source,
        '    MENU_SET_VALUE("%c: %d.%d MiB/s", drive, needed / 10, needed % 10);',
        '    MENU_SET_NAME("QVFIL Media Engine");\n'
        '    MENU_SET_VALUE("%s: %d.%d MiB/s",\n'
        '        drive == \'A\' ? "CF" : drive == \'B\' ? "SD" : "?",\n'
        '        needed / 10, needed % 10);'
    )
    source = replace_once(
        source,
        '    MENU_SET_RINFO("Obs:%u.%u", qvfilm_media_stream_x10 / 10,\n'
        '                   qvfilm_media_stream_x10 % 10);',
        '    MENU_SET_RINFO("Obs:%d.%d", (int)(qvfilm_media_stream_x10 / 10),\n'
        '                   (int)(qvfilm_media_stream_x10 % 10));'
    )
    source = replace_once(
        source,
        '            "Observed %u.%u MiB/s < 120%% of demand. Buffer-stop risk. "',
        '            "Observed %d.%d MiB/s < 120%% demand. Buffer risk. "'
    )
    source = replace_once(
        source,
        '            qvfilm_media_stream_x10 / 10,\n'
        '            qvfilm_media_stream_x10 % 10);',
        '            (int)(qvfilm_media_stream_x10 / 10),\n'
        '            (int)(qvfilm_media_stream_x10 % 10));'
    )
    source = replace_once(
        source,
        '    MENU_SET_VALUE("Flow:%u.%u", qvfilm_media_stream_x10 / 10,\n'
        '                   qvfilm_media_stream_x10 % 10);\n'
        '    MENU_SET_RINFO("I/O:%u.%u", qvfilm_media_writer_x10 / 10,\n'
        '                   qvfilm_media_writer_x10 % 10);',
        '    MENU_SET_NAME("QVFIL Recording Report");\n'
        '    MENU_SET_VALUE("Flow:%d.%d", (int)(qvfilm_media_stream_x10 / 10),\n'
        '                   (int)(qvfilm_media_stream_x10 % 10));\n'
        '    MENU_SET_RINFO("I/O:%d.%d", (int)(qvfilm_media_writer_x10 / 10),\n'
        '                   (int)(qvfilm_media_writer_x10 % 10));'
    )
    source = replace_once(
        source,
        '        "Last MLV %c: capture %us, pending %u queue entries, stop %s. "',
        '        "Last MLV %s: capture %ds, pending %d queue entries, stop %s. "'
    )
    source = replace_once(
        source,
        '        qvfilm_media_drive, qvfilm_media_duration_ms / 1000,\n'
        '        qvfilm_media_end_queue, stop);',
        '        qvfilm_media_drive == \'A\' ? "CF" :\n'
        '            qvfilm_media_drive == \'B\' ? "SD" : "?",\n'
        '        (int)(qvfilm_media_duration_ms / 1000),\n'
        '        (int)qvfilm_media_end_queue, stop);'
    )
    source = replace_once(
        source, 'MENU_SET_RINFO("QVFIL v0.6.0");',
        'MENU_SET_RINFO("QVFIL v0.6.1");'
    )
    source = replace_once(
        source, 'v0.6.0: Passive CF/SD media profile; recorder safety preserved.',
        'v0.6.1: Canon menu formatter hotfix; recorder unchanged.'
    )
    return source

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", required=True)
    args = p.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        p.error("Expected exact source checkout")
    actual = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if actual != UPSTREAM:
        p.error("Wrong ML commit: " + actual)
    file = root / TARGET_FILE
    original = file.read_text(encoding="utf-8")
    patched = patch(original)
    file.write_text(patched, encoding="utf-8")
    print("QVFIL v0.6.1 menu formatter compatibility patch applied. RAW recorder unchanged.")
    print("EXPERIMENTAL: ARM build is not hardware validation.")

if __name__ == "__main__":
    main()
