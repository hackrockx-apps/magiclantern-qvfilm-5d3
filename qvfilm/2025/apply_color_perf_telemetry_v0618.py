#!/usr/bin/env python3
"""QVFIL v0.6.18: fix Color Lab %u and measure STBY conversion cadence.

Field evidence: on v0.6.17 (IMG_5394), the LCD shows "F:u 209ms":
color processing completed at least once, but ML menu formatter did not
render %u. 209ms is ONE conversion duration, NOT frames per second.

This is non-optimizing telemetry, so RAW writer, compressor, display
filter and baseline color converter are unchanged. No extra work in REC.
"""
import argparse
import subprocess
from pathlib import Path
import apply_rom_verified_color_v0617 as previous

UPSTREAM=previous.UPSTREAM
TARGET_FILE=previous.TARGET_FILE
replace_once=previous.replace_once

EXTRA_VARS = '''/* STBY-only QVFIL conversion telemetry; updated after existing draw.
 * These are observable estimates of conversion cadence, NOT LCD FPS.
 * No persistent config and no allocation or polling task. */
static volatile int qvfilm_lab_avg_draw_ms_v0618 = 0;
static volatile int qvfilm_lab_avg_period_ms_v0618 = 0;
static unsigned int qvfilm_lab_prev_end_ms_v0618 = 0;
'''

OLD_COUNT = '''    if (qvfilm_lab_active)
    {
        qvfilm_preview_lab_last_draw_ms = qvfilm_lab_draw_ms;
        qvfilm_preview_lab_draw_count++;
    }

    give_semaphore(settings_sem);'''

NEW_COUNT = '''    if (qvfilm_lab_active)
    {
        /* A light 1/8 EMA; never intercept raw_preview_fast_ex().
         * End-to-end interval includes previous STBY idle sleep and
         * other processing. No new work executes during RAW REC. */
        unsigned int now = (unsigned int)get_ms_clock();
        if (qvfilm_preview_lab_draw_count)
        {
            unsigned int period = now - qvfilm_lab_prev_end_ms_v0618;
            if (period > 0 && period <= 10000U)
            {
                int p = (int)period;
                qvfilm_lab_avg_period_ms_v0618 =
                    qvfilm_lab_avg_period_ms_v0618
                    ? (qvfilm_lab_avg_period_ms_v0618 * 7 + p) / 8
                    : p;
            }
        }
        qvfilm_lab_prev_end_ms_v0618 = now;
        qvfilm_lab_avg_draw_ms_v0618 =
            qvfilm_lab_avg_draw_ms_v0618
            ? (qvfilm_lab_avg_draw_ms_v0618 * 7 + qvfilm_lab_draw_ms) / 8
            : qvfilm_lab_draw_ms;
        qvfilm_preview_lab_last_draw_ms = qvfilm_lab_draw_ms;
        qvfilm_preview_lab_draw_count++;
    }

    give_semaphore(settings_sem);'''

PERF_MENU = '''/* Diagnostic ONLY. "Hz" is completed RAW preview conversion cadence.
 * Not verified LCD presentation rate, not camera recording FPS. */
static MENU_UPDATE_FUNC(qvfilm_lab_perf_update_v0618)
{
    MENU_SET_NAME("QVFIL Color Perf");
    if (!qvfilm_preview_lab)
    {
        MENU_SET_VALUE("OFF");
        MENU_SET_RINFO("SAFE");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Lab OFF; no preview telemetry. Recorder remains original.");
    }
    else if (!qvfilm_preview_lab_draw_count)
    {
        MENU_SET_VALUE("NO DRAW");
        MENU_SET_RINFO("0F");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Color Lab has not completed a STBY conversion yet.");
    }
    else
    {
        int period = qvfilm_lab_avg_period_ms_v0618;
        MENU_SET_VALUE("AVG:%dms", qvfilm_lab_avg_draw_ms_v0618);
        if (period > 0)
        {
            int hertz10 = 10000 / period;
            MENU_SET_RINFO("Hz:%d.%d", hertz10 / 10, hertz10 % 10);
        }
        else
        {
            MENU_SET_RINFO("Hz:WAIT");
        }
        MENU_SET_WARNING(MENU_WARN_INFO,
            "AVG = rolling RAW color conversion ms; Hz = estimated completed "
            "conversion cadence. Neither is measured LCD FPS.");
    }
}

'''

def patch(source):
    source=previous.patch(source)
    source=replace_once(
        source,
        'static volatile unsigned int qvfilm_preview_lab_draw_count = 0;',
        'static volatile unsigned int qvfilm_preview_lab_draw_count = 0;\n'+EXTRA_VARS.rstrip()
    )
    source=replace_once(source, OLD_COUNT, NEW_COUNT)
    source=replace_once(
        source,
        '''        qvfilm_preview_lab_last_draw_ms = 0;
        MENU_SET_RINFO("SAFE OFF");''',
        '''        qvfilm_preview_lab_last_draw_ms = 0;
        qvfilm_lab_avg_draw_ms_v0618 = 0;
        qvfilm_lab_avg_period_ms_v0618 = 0;
        qvfilm_lab_prev_end_ms_v0618 = 0;
        MENU_SET_RINFO("SAFE OFF");'''
    )
    # Magic Lantern compact snprintf on this camera renders %u as literal 'u'.
    # Plain %d is demonstrated working in existing HUD 'Draws:12' values.
    # Clamp the display to INT_MAX while keeping the underlying unsigned counter.
    source=replace_once(
        source,
        '''MENU_SET_RINFO("F:%u %dms", qvfilm_preview_lab_draw_count,
                           qvfilm_preview_lab_last_draw_ms);''',
        '''MENU_SET_RINFO("F:%d %dms",
                           qvfilm_preview_lab_draw_count > 2147483647U
                               ? 2147483647 : (int)qvfilm_preview_lab_draw_count,
                           qvfilm_preview_lab_last_draw_ms);'''
    )
    source=replace_once(
        source,
        'static struct menu_entry qvfilm_hud_menu[] = {',
        PERF_MENU+'static struct menu_entry qvfilm_hud_menu[] = {'
    )
    source=replace_once(
        source,
        '''    {
        .name = "QVFIL Color Lab",
        .priv = &qvfilm_preview_lab,''',
        '''    {
        .name = "QVFIL Color Perf",
        .update = qvfilm_lab_perf_update_v0618,
        .help = "Read-only RAW color conversion timing (STBY only).",
        .help2 = "AVG:ms per draw, Hz: completed conversion cadence, not LCD FPS.",
    },
    {
        .name = "QVFIL Color Lab",
        .priv = &qvfilm_preview_lab,'''
    )
    source=replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.17")',
        'MENU_SET_RINFO("QVFIL v0.6.18")'
    )
    source=replace_once(
        source,
        'v0.6.17: ROM-verified STBY Color Lab with original RAW REC.',
        'v0.6.18: fixed frame count and bounded color timing telemetry.'
    )
    return source

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkout",required=True)
    args=p.parse_args()
    root=Path(args.checkout).resolve()
    if not (root/".git").exists():
        p.error("Requires pinned Magic Lantern 2025 Git checkout")
    sha=subprocess.check_output(
        ["git","-C",str(root),"rev-parse","HEAD"],text=True
    ).strip()
    if sha != UPSTREAM:
        p.error("Wrong pinned upstream: "+sha)
    file=root/TARGET_FILE
    file.write_text(patch(file.read_text(encoding="utf-8")),encoding="utf-8")
    print("QVFIL v0.6.18: corrected %d frame count + STBY timing telemetry.")
    print("Original RAW recorder, compressor and color converter unchanged.")

if __name__=="__main__":
    main()
