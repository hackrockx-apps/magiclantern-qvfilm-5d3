#!/usr/bin/env python3
"""QVFIL 0.6.12: verify whether Color Preview Lab actually draws frames.

This patch is intentionally diagnostic, not a YUV fullscreen conversion.
It only counts completed existing RAW preview renders in standby and makes
the menu distinguish an enabled lab from a lab that has drawn an image.
The capture/writer/compressor/queue logic stays byte-identical to 0.6.11.
"""
import argparse
import subprocess
from pathlib import Path
import apply_color_preview_lab_v0611 as previous

UPSTREAM = previous.UPSTREAM
TARGET_FILE = previous.TARGET_FILE
replace_once = previous.replace_once

def patch(source):
    source = previous.patch(source)
    # Count completed calls, not potential activation. Counter remains
    # volatile/session-only; nothing is written to disk or NVRAM.
    source = replace_once(
        source,
        'static int qvfilm_preview_lab_last_draw_ms = 0;',
        'static int qvfilm_preview_lab_last_draw_ms = 0;\n'
        'static volatile unsigned int qvfilm_preview_lab_draw_count = 0;'
    )
    source = replace_once(
        source,
        '''    if (qvfilm_lab_active)
        qvfilm_preview_lab_last_draw_ms = qvfilm_lab_draw_ms;

    give_semaphore(settings_sem);''',
        '''    if (qvfilm_lab_active)
    {
        qvfilm_preview_lab_last_draw_ms = qvfilm_lab_draw_ms;
        qvfilm_preview_lab_draw_count++;
    }

    give_semaphore(settings_sem);'''
    )
    # Reset the previous run when Lab is off. With no count a gate-valid
    # mode is ARMED, not DRAW; this avoids the prior false-positive status.
    source = replace_once(
        source,
        '''    if (!qvfilm_preview_lab)
    {
        MENU_SET_RINFO("SAFE OFF");''',
        '''    if (!qvfilm_preview_lab)
    {
        qvfilm_preview_lab_draw_count = 0;
        qvfilm_preview_lab_last_draw_ms = 0;
        MENU_SET_RINFO("SAFE OFF");'''
    )
    source = replace_once(
        source,
        '''    else if (QVFIL_LAB_STBY)
    {
        MENU_SET_RINFO("DRAW %dms", qvfilm_preview_lab_last_draw_ms);
        MENU_SET_WARNING(MENU_WARN_INFO,
            "STBY color RAW framing active with adaptive pacing. Preview FPS is not guaranteed.");
    }''',
        '''    else if (QVFIL_LAB_STBY)
    {
        if (qvfilm_preview_lab_draw_count)
        {
            MENU_SET_RINFO("F:%u %dms", qvfilm_preview_lab_draw_count,
                           qvfilm_preview_lab_last_draw_ms);
            MENU_SET_WARNING(MENU_WARN_INFO,
                "F = completed RAW color draws since enabling Lab; ms = last draw duration, NOT FPS.");
        }
        else
        {
            MENU_SET_RINFO("ARMED 0F");
            MENU_SET_WARNING(MENU_WARN_ADVICE,
                "Gates satisfied but zero RAW color draws; exit menu to LiveView then return. Do not assume Lab active.");
        }
    }'''
    )
    source = replace_once(
        source, 'MENU_SET_RINFO("QVFIL v0.6.11")',
        'MENU_SET_RINFO("QVFIL v0.6.12")'
    )
    source = replace_once(
        source,
        'v0.6.11: Preview-mode-independent STBY Lab; detailed gate diagnostics.',
        'v0.6.12: Lab frame counter and truthful STBY draw diagnostics.'
    )
    source = replace_once(
        source,
        '.help2 = "Preview choice is overridden only when Lab is ready; RAW REC stays upstream.",',
        '.help2 = "v0.6.12: F counts actual STBY RAW preview draws. Lab OFF after reboot; REC untouched.",'
    )
    return source

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    args = parser.parse_args()
    root = Path(args.checkout).resolve()
    if not (root / ".git").exists():
        parser.error("Expected pinned Magic Lantern git checkout")
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != UPSTREAM:
        parser.error("Wrong pinned Magic Lantern commit: " + actual)
    target = root / TARGET_FILE
    before = target.read_text(encoding="utf-8")
    target.write_text(patch(before), encoding="utf-8")
    print("QVFIL v0.6.12 diagnostic: counts completed STBY preview draws.")
    print("Does not enlarge Canon Real-time, optimize Bayer, or change RAW REC.")

if __name__ == "__main__":
    main()
