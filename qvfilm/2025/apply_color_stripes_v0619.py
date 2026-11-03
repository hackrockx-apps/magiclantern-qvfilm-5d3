#!/usr/bin/env python3
"""QVFIL 0.6.19 - opt-in THREE STRIPE RAW COLOR STBY experiment.

IMG_5398.JPG on 5D3 QVFIL v0.6.18: F:2 211ms; AVG:207ms, Hz:3.4.
This means RAW color conversion is too slow for fluid full-frame preview.
Our next *test* uses the existing upstream raw_preview_fast_ex quality 0
color converter with bounded vertical line ranges (one-third each draw).

This can reduce the time to the FIRST PARTIAL UPDATE, but cannot promise
better completed full-frame FPS. Each stripe reconstructs color and gamma
LUT independently; composite full-frame throughput could get worse.
No new frame buffers, tasks, DMA, firmware writes, capture changes.
Lab session default OFF; mode1 full-frame reference retained; mode2 stripes.
On recording QVFIL_LAB_STBY is false, and y1/y2 remain upstream -1/-1.
"""
import argparse
import subprocess
from pathlib import Path
import apply_color_perf_telemetry_v0618 as previous

UPSTREAM=previous.UPSTREAM
TARGET_FILE=previous.TARGET_FILE
replace_once=previous.replace_once

EXTRA_STATE = '''/* Color Stripe STBY: no DMA or task, one of three LV-Y bands per update.
 * Full sweep means all 3 bands displayed; NOT a synchronized video frame. */
static int qvfilm_lab_band_v0619 = 0;
static int qvfilm_lab_last_mode_v0619 = -1;
static int qvfilm_lab_band_used_v0619 = 0;
static volatile unsigned int qvfilm_lab_full_sweeps_v0619 = 0;
static int qvfilm_lab_sweep_ms_v0619 = 0;
static unsigned int qvfilm_lab_last_sweep_clock_v0619 = 0;
'''

PREVIEW_OLD = '''    int qvfilm_lab_start_ms = qvfilm_lab_active ? get_ms_clock() : 0;
    raw_preview_fast_ex(
        RAW_IS_RECORDING ? fullsize_buffers[fi] : (void*)-1,
        PREVIEW_HACKED && RAW_IS_RECORDING ? (void*)-1 : buffers->dst_buf,
        -1,
        -1,
        (need_for_speed && !get_halfshutter_pressed())
            ? RAW_PREVIEW_GRAY_ULTRA_FAST
            : RAW_PREVIEW_COLOR_HALFRES
    );'''

PREVIEW_NEW = '''    /* QVFIL v0.6.19: only split existing color LV processing in opt-in
     * STBY stripe mode. No change to the original recorder path or buffers.
     * The original core raw_preview_fast_ex accepts [start_line,end_line)
     * in LV coordinates, measured using the SAME default boundary macros.
     */
    int qvfilm_lab_y1_v0619 = -1;
    int qvfilm_lab_y2_v0619 = -1;
    int qvfilm_lab_stripe_active_v0619 = 0;
    if (qvfilm_lab_active)
    {
        if (qvfilm_lab_last_mode_v0619 != qvfilm_preview_lab)
        {
            qvfilm_lab_band_v0619 = 0;
            qvfilm_lab_full_sweeps_v0619 = 0;
            qvfilm_lab_last_sweep_clock_v0619 = 0;
            qvfilm_lab_sweep_ms_v0619 = 0;
            qvfilm_lab_last_mode_v0619 = qvfilm_preview_lab;
        }
        if (qvfilm_preview_lab == 2)
        {
            int top = BM2LV_Y(os.y0);
            int bottom = BM2LV_Y(os.y_max);
            int height = bottom - top;
            if (height >= 12 && qvfilm_lab_band_v0619 >= 0 &&
                qvfilm_lab_band_v0619 < 3)
            {
                qvfilm_lab_y1_v0619 =
                    top + height * qvfilm_lab_band_v0619 / 3;
                qvfilm_lab_y2_v0619 =
                    top + height * (qvfilm_lab_band_v0619 + 1) / 3;
                if (qvfilm_lab_y2_v0619 > qvfilm_lab_y1_v0619)
                    qvfilm_lab_stripe_active_v0619 = 1;
            }
        }
        qvfilm_lab_band_used_v0619 = qvfilm_lab_stripe_active_v0619;
    }
    int qvfilm_lab_start_ms = qvfilm_lab_active ? get_ms_clock() : 0;
    raw_preview_fast_ex(
        RAW_IS_RECORDING ? fullsize_buffers[fi] : (void*)-1,
        PREVIEW_HACKED && RAW_IS_RECORDING ? (void*)-1 : buffers->dst_buf,
        qvfilm_lab_stripe_active_v0619 ? qvfilm_lab_y1_v0619 : -1,
        qvfilm_lab_stripe_active_v0619 ? qvfilm_lab_y2_v0619 : -1,
        (need_for_speed && !get_halfshutter_pressed())
            ? RAW_PREVIEW_GRAY_ULTRA_FAST
            : RAW_PREVIEW_COLOR_HALFRES
    );'''

COUNT_OLD = '''        qvfilm_preview_lab_last_draw_ms = qvfilm_lab_draw_ms;
        qvfilm_preview_lab_draw_count++;
    }

    give_semaphore(settings_sem);'''
COUNT_NEW = '''        qvfilm_preview_lab_last_draw_ms = qvfilm_lab_draw_ms;
        qvfilm_preview_lab_draw_count++;
        /* A sweep is one complete pass through the 3 disjoint bands.
         * No additional rendering call is made here. If a caller switches
         * preview mode or begins REC, these counters are not updated. */
        int qvfilm_lab_sweep_done_v0619 = 0;
        if (qvfilm_lab_stripe_active_v0619)
        {
            qvfilm_lab_band_v0619++;
            if (qvfilm_lab_band_v0619 == 3)
            {
                qvfilm_lab_band_v0619 = 0;
                qvfilm_lab_sweep_done_v0619 = 1;
            }
        }
        else if (qvfilm_preview_lab == 1)
        {
            qvfilm_lab_band_v0619 = 0;
            qvfilm_lab_sweep_done_v0619 = 1;
        }
        if (qvfilm_lab_sweep_done_v0619)
        {
            if (qvfilm_lab_last_sweep_clock_v0619)
            {
                unsigned int sweep_ms = now -
                    qvfilm_lab_last_sweep_clock_v0619;
                if (sweep_ms > 0 && sweep_ms < 10000U)
                    qvfilm_lab_sweep_ms_v0619 = (int)sweep_ms;
            }
            qvfilm_lab_last_sweep_clock_v0619 = now;
            qvfilm_lab_full_sweeps_v0619++;
        }
    }

    give_semaphore(settings_sem);'''

SWEEP_MENU = '''/* Read-only. "C" is completed color *sweeps*, NOT LCD frames.
 * "B" is next band index. The live image may contain mixed-age strips. */
static MENU_UPDATE_FUNC(qvfilm_lab_sweep_update_v0619)
{
    MENU_SET_NAME("QVFIL Color Sweep");
    if (qvfilm_preview_lab == 0)
    {
        MENU_SET_VALUE("OFF");
        MENU_SET_RINFO("SAFE");
        MENU_SET_WARNING(MENU_WARN_INFO, "Lab disabled; default after boot.");
    }
    else if (qvfilm_preview_lab == 1)
    {
        MENU_SET_VALUE("FULL");
        MENU_SET_RINFO("C:%d",
            qvfilm_lab_full_sweeps_v0619 > 2147483647U
                ? 2147483647 : (int)qvfilm_lab_full_sweeps_v0619);
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Legacy whole-frame Color STBY reference. C = completed draws.");
    }
    else if (!qvfilm_lab_band_used_v0619)
    {
        MENU_SET_VALUE("WAIT LV");
        MENU_SET_RINFO("B:0/3");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Enter Movie LiveView 1x with Color Lab Stripe STBY. No bands yet.");
    }
    else
    {
        MENU_SET_VALUE("C:%d",
            qvfilm_lab_full_sweeps_v0619 > 2147483647U
                ? 2147483647 : (int)qvfilm_lab_full_sweeps_v0619);
        if (qvfilm_lab_sweep_ms_v0619 > 0)
            MENU_SET_RINFO("T:%dms", qvfilm_lab_sweep_ms_v0619);
        else
            MENU_SET_RINFO("B:%d/3", qvfilm_lab_band_v0619);
        MENU_SET_WARNING(MENU_WARN_INFO,
            "C = 3-band sweeps; T = last complete sweep interval. "
            "May tear/mix ages, NOT synchronized full-frame FPS.");
    }
}

'''

def patch(source):
    source=previous.patch(source)
    source=replace_once(
        source,
        'static unsigned int qvfilm_lab_prev_end_ms_v0618 = 0;',
        'static unsigned int qvfilm_lab_prev_end_ms_v0618 = 0;\n'+EXTRA_STATE.rstrip()
    )
    source=replace_once(source,PREVIEW_OLD,PREVIEW_NEW)
    source=replace_once(source,COUNT_OLD,COUNT_NEW)
    source=replace_once(
        source,
        '''        qvfilm_lab_prev_end_ms_v0618 = 0;
        MENU_SET_RINFO("SAFE OFF");''',
        '''        qvfilm_lab_prev_end_ms_v0618 = 0;
        qvfilm_lab_band_v0619 = 0;
        qvfilm_lab_last_mode_v0619 = -1;
        qvfilm_lab_band_used_v0619 = 0;
        qvfilm_lab_full_sweeps_v0619 = 0;
        qvfilm_lab_sweep_ms_v0619 = 0;
        qvfilm_lab_last_sweep_clock_v0619 = 0;
        MENU_SET_RINFO("SAFE OFF");'''
    )
    source=replace_once(
        source,
        'static struct menu_entry qvfilm_hud_menu[] = {',
        SWEEP_MENU+'static struct menu_entry qvfilm_hud_menu[] = {'
    )
    source=replace_once(
        source,
        '''    {
        .name = "QVFIL Color Perf",
        .update = qvfilm_lab_perf_update_v0618,''',
        '''    {
        .name = "QVFIL Color Sweep",
        .update = qvfilm_lab_sweep_update_v0619,
        .help = "3-band Color STBY sweeps (read-only); NOT LCD frame rate.",
        .help2 = "C: 3-band sweeps; B: next band; T: completed sweep interval.",
    },
    {
        .name = "QVFIL Color Perf",
        .update = qvfilm_lab_perf_update_v0618,'''
    )
    source=replace_once(
        source,
        '.choices = CHOICES("OFF", "Color STBY"),',
        '.choices = CHOICES("OFF", "Color STBY", "Stripe STBY"),'
    )
    # Strict min/max toggle; no persistent config, boot OFF.
    source=replace_once(
        source,
        '''        .max = 1,
        .choices = CHOICES("OFF", "Color STBY", "Stripe STBY"),''',
        '''        .max = 2,
        .choices = CHOICES("OFF", "Color STBY", "Stripe STBY"),'''
    )
    source=replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.18")',
        'MENU_SET_RINFO("QVFIL v0.6.19")'
    )
    source=replace_once(
        source,
        'v0.6.18: fixed frame count and bounded color timing telemetry.',
        'v0.6.19: optional 3-band STBY color preview vs full-frame.'
    )
    return source

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkout",required=True)
    args=p.parse_args()
    root=Path(args.checkout).resolve()
    if not (root/".git").exists():
        p.error("Need the pinned Magic Lantern 2025 git checkout")
    sha=subprocess.check_output(
        ["git","-C",str(root),"rev-parse","HEAD"],text=True
    ).strip()
    if sha != UPSTREAM:
        p.error("Wrong upstream commit: "+sha)
    path=root/TARGET_FILE
    path.write_text(patch(path.read_text(encoding="utf-8")),encoding="utf-8")
    print("QVFIL v0.6.19: opt-in 3-band RAW color STBY, no REC changes.")
    print("May improve partial update latency but not whole-frame FPS.")

if __name__=="__main__":
    main()
