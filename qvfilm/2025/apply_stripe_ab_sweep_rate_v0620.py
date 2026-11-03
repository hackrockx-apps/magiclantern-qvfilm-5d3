#!/usr/bin/env python3
"""QVFIL 0.6.20 -- measured A/B: full-height, 2-band, 3-band STBY color.

Five user LCD photos (IMG_5399..IMG_5403) confirm v0.6.19, ROM SIG PASS,
full height C:138 F:138 AVG:208ms Hz:3.4, and Stripe STBY ARMED 0F followed
by a LiveView photo with NO subsequent sweep metrics. No stripe win proven.

Fix potential A/B contamination from rolling v0.6.18 mean when changing mode.
Offer 2 or 3 bands, and a separate completed-sweep rate, not LCD FPS.
Everything runs only in QVFIL_LAB_STBY, with RAW REC upstream unchanged.
"""
import argparse
import subprocess
from pathlib import Path
import apply_color_stripes_v0619 as previous

UPSTREAM=previous.UPSTREAM
TARGET_FILE=previous.TARGET_FILE
replace_once=previous.replace_once

def edit(text, old, new, n=1):
    if text.count(old) != n:
        raise ValueError("Expected exactly %d occurrence(s), found %d: %r" %
                         (n, text.count(old),old[:100]))
    return text.replace(old,new)

# Modify ONLY the opt-in STBY preview branch of v0.6.19.
PREVIEW_OLD=previous.PREVIEW_NEW
p=PREVIEW_OLD
p=edit(p,
    '    int qvfilm_lab_stripe_active_v0619 = 0;',
    '    int qvfilm_lab_stripe_active_v0619 = 0;\n'
    '    int qvfilm_lab_stripe_count_v0620 = 0;')
p=edit(p,
    '''            qvfilm_lab_last_mode_v0619 = qvfilm_preview_lab;''',
    '''            qvfilm_lab_last_mode_v0619 = qvfilm_preview_lab;
            /* Isolate benchmarks. Old v0.6.19 averages could belong to
             * previously selected full-frame or other band count. */
            qvfilm_preview_lab_draw_count = 0;
            qvfilm_preview_lab_last_draw_ms = 0;
            qvfilm_lab_avg_draw_ms_v0618 = 0;
            qvfilm_lab_avg_period_ms_v0618 = 0;
            qvfilm_lab_prev_end_ms_v0618 = 0;
            qvfilm_lab_sweep_ema_ms_v0620 = 0;
            qvfilm_lab_band_used_v0619 = 0;''')
p=edit(p,
    '''        if (qvfilm_preview_lab == 2)
        {
            int top = BM2LV_Y(os.y0);''',
    '''        if (qvfilm_preview_lab == 2 || qvfilm_preview_lab == 3)
        {
            /* 2 bands vs 3: compare partial-update latency AND full
             * sweep interval rather than single-band Hz alone. */
            qvfilm_lab_stripe_count_v0620 =
                qvfilm_preview_lab == 2 ? 2 : 3;
            int top = BM2LV_Y(os.y0);''')
p=edit(p,
    'qvfilm_lab_band_v0619 < 3)',
    'qvfilm_lab_band_v0619 < qvfilm_lab_stripe_count_v0620)')
p=edit(p,
    ' / 3;',
    ' / qvfilm_lab_stripe_count_v0620;',n=2)
PREVIEW_NEW=p

COUNT_OLD=previous.COUNT_NEW
c=COUNT_OLD
c=edit(c,
    'if (qvfilm_lab_band_v0619 == 3)',
    'if (qvfilm_lab_band_v0619 == qvfilm_lab_stripe_count_v0620)')
c=edit(c,
    '''                if (sweep_ms > 0 && sweep_ms < 10000U)
                    qvfilm_lab_sweep_ms_v0619 = (int)sweep_ms;''',
    '''                if (sweep_ms > 0 && sweep_ms < 10000U)
                {
                    qvfilm_lab_sweep_ms_v0619 = (int)sweep_ms;
                    int sample_ms = (int)sweep_ms;
                    qvfilm_lab_sweep_ema_ms_v0620 =
                        qvfilm_lab_sweep_ema_ms_v0620
                        ? (qvfilm_lab_sweep_ema_ms_v0620 * 7 +
                           sample_ms) / 8 : sample_ms;
                }''')
COUNT_NEW=c

SWEEP_OLD=previous.SWEEP_MENU
s=SWEEP_OLD
s=edit(s,
    '''    MENU_SET_NAME("QVFIL Color Sweep");''',
    '''    MENU_SET_NAME("QVFIL Color Sweep");
    int bands = qvfilm_preview_lab == 2 ? 2 : 3;''')
s=edit(s,'MENU_SET_RINFO("B:0/3");','MENU_SET_RINFO("B:0/%d", bands);')
s=edit(s,'MENU_SET_RINFO("B:%d/3", qvfilm_lab_band_v0619);',
         'MENU_SET_RINFO("B:%d/%d", qvfilm_lab_band_v0619, bands);')
s=edit(s,'"C = 3-band sweeps; T = last complete sweep interval. "',
         '"C = full 2/3-band sweeps; T = last interval. "')
SWEEP_NEW=s

EXTRA_STATE = '''/* A/B is test-only; completed-sweep EMA is independent of per-band Hz.
 * Reset together with all other benchmark counters on mode transition. */
static int qvfilm_lab_sweep_ema_ms_v0620 = 0;
'''

SWEEP_RATE_MENU = '''/* Read-only time to finish a full pass across ALL selected bands.
 * A 2/3-band sweep is a mosaic of different moments, NOT LCD FPS.
 * Distinct from v0.6.18 "Color Perf" (single color draw / partial stripe).
 */
static MENU_UPDATE_FUNC(qvfilm_lab_sweep_rate_update_v0620)
{
    MENU_SET_NAME("QVFIL Sweep Rate");
    if (!qvfilm_preview_lab)
    {
        MENU_SET_VALUE("OFF");
        MENU_SET_RINFO("SAFE");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Lab OFF. Default every boot; original recorder unchanged.");
    }
    else if (qvfilm_lab_sweep_ema_ms_v0620 <= 0)
    {
        MENU_SET_VALUE("NO RATE");
        MENU_SET_RINFO("WAIT");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Need at least 2 completed sweeps in this mode for a rate.");
    }
    else
    {
        int ms = qvfilm_lab_sweep_ema_ms_v0620;
        int hz10 = 10000 / ms;
        MENU_SET_VALUE("AVG:%dms", ms);
        MENU_SET_RINFO("Hz:%d.%d", hz10 / 10, hz10 % 10);
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Completed full-height sweep cadence, NOT synchronized video "
            "or measured LCD FPS. Band seams are possible.");
    }
}

'''

def patch(source):
    source=previous.patch(source)
    source=replace_once(
        source,
        'static unsigned int qvfilm_lab_last_sweep_clock_v0619 = 0;',
        'static unsigned int qvfilm_lab_last_sweep_clock_v0619 = 0;\n'
        +EXTRA_STATE.rstrip())
    source=replace_once(source, PREVIEW_OLD, PREVIEW_NEW)
    source=replace_once(source, COUNT_OLD, COUNT_NEW)
    source=replace_once(source, SWEEP_OLD, SWEEP_NEW+SWEEP_RATE_MENU)
    source=replace_once(
        source,
        '''        qvfilm_lab_last_sweep_clock_v0619 = 0;
        MENU_SET_RINFO("SAFE OFF");''',
        '''        qvfilm_lab_last_sweep_clock_v0619 = 0;
        qvfilm_lab_sweep_ema_ms_v0620 = 0;
        MENU_SET_RINFO("SAFE OFF");'''
    )
    source=replace_once(
        source,
        '''        .name = "QVFIL Color Perf",
        .update = qvfilm_lab_perf_update_v0618,''',
        '''        .name = "QVFIL Sweep Rate",
        .update = qvfilm_lab_sweep_rate_update_v0620,
        .help = "Read-only completed full-height sweep average and rate.",
        .help2 = "Not real LCD FPS. A sweep may contain different-age bands.",
    },
    {
        .name = "QVFIL Color Perf",
        .update = qvfilm_lab_perf_update_v0618,'''
    )
    source=replace_once(
        source,
        '.choices = CHOICES("OFF", "Color STBY", "Stripe STBY"),',
        '.choices = CHOICES("OFF", "Color STBY", "Stripe 2", "Stripe 3"),'
    )
    source=replace_once(
        source,
        '''        .max = 2,
        .choices = CHOICES("OFF", "Color STBY", "Stripe 2", "Stripe 3"),''',
        '''        .max = 3,
        .choices = CHOICES("OFF", "Color STBY", "Stripe 2", "Stripe 3"),'''
    )
    source=replace_once(
        source, 'MENU_SET_RINFO("QVFIL v0.6.19")',
        'MENU_SET_RINFO("QVFIL v0.6.20")')
    source=replace_once(
        source,
        'v0.6.19: optional 3-band STBY color preview vs full-frame.',
        'v0.6.20: isolated full/2/3-band STBY sweep comparison.')
    return source

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--checkout",required=True)
    args=parser.parse_args()
    root=Path(args.checkout).resolve()
    if not (root/".git").exists():
        parser.error("Expected exact pinned ML2025 checkout")
    sha=subprocess.check_output(
        ["git","-C",str(root),"rev-parse","HEAD"],text=True
    ).strip()
    if sha != UPSTREAM:
        parser.error("Unexpected upstream commit: "+sha)
    target=root/TARGET_FILE
    target.write_text(patch(target.read_text(encoding="utf-8")),
                      encoding="utf-8")
    print("QVFIL v0.6.20: STBY full vs 2-/3-band, reset benchmark on switch.")
    print("Unmodified RAW recorder, compressor, camera firmware and autoexec.")

if __name__=="__main__":
    main()
