#!/usr/bin/env python3
"""QVFIL v0.6.10: opt-in, standby-only Color Preview Lab on Canon 5D3.123.

Experiments with existing Magic Lantern RAW color framing: margin fill and
adaptive bounded refresh pacing in STBY. Does NOT create a new color decoder
or upscale Canon LiveView; cannot promise real-time full-size image.
Restores upstream preview path in RAW REC and whenever the option is OFF.
"""
import argparse
import subprocess
from pathlib import Path

import apply_preview_guard_v069 as previous

UPSTREAM = previous.UPSTREAM
TARGET_FILE = previous.TARGET_FILE
replace_once = previous.replace_once


def patch(source):
    source = previous.patch(source)

    # Boot-time OFF on purpose. No MODULE_CONFIG: the test switch cannot
    # remain enabled accidentally after a power cycle.
    source = replace_once(
        source,
        '''static CONFIG_INT("raw.preview", preview_mode, 0);''',
        '''static CONFIG_INT("raw.preview", preview_mode, 0);

/* QVFIL Preview Lab (0.6.10): volatile session-only test switch.
 * OFF on every boot, even if the camera previously opted in.
 */
static int qvfilm_preview_lab = 0;
static int qvfilm_preview_lab_last_draw_ms = 0;
#define QVFIL_LAB_STBY (qvfilm_preview_lab && \
    is_camera("5D3", "1.2.3") && RAW_IS_IDLE && lv_dispsize == 1 && \
    (PREVIEW_AUTO || PREVIEW_CANON) && \
    res_x > 0 && res_x <= 1600 && res_y > 0 && res_y <= 900 && \
    BPP == 10 && raw_info.bits_per_pixel == 14)'''
    )

    # Entirely bypass user-selected Canon Real-time only when opt-in STBY
    # test is valid. Existing AF and x10 focus guards already ran.
    source = replace_once(
        source,
        '''    if (autofocusing)
    {
        /* disable our preview during autofocus */
        return 0;
    }

    if (PREVIEW_AUTO)''',
        '''    if (autofocusing)
    {
        /* disable our preview during autofocus */
        return 0;
    }

    /* Opt-in 5D3 Preview Lab: use existing COLOR_HALFRES RAW framing only
     * in standby. No effect on recording, live x10, AF or other cameras.
     * Returning 1 here routes to the standard ML display filter.
     */
    if (QVFIL_LAB_STBY)
        return 1;

    if (PREVIEW_AUTO)'''
    )

    # Fill more of the LCD (do not reserve 38px top/bottom info margins)
    # only in STBY. Aspect ratio remains constrained by the original core.
    source = replace_once(
        source,
        '''    raw_set_preview_rect(skip_x, skip_y, res_x, res_y, 1);
    raw_force_aspect_ratio(0, 0);

    /* when recording, preview both full-size buffers,''',
        '''    int qvfilm_lab_active = QVFIL_LAB_STBY;
    raw_set_preview_rect(skip_x, skip_y, res_x, res_y,
                         qvfilm_lab_active ? 0 : 1);
    raw_force_aspect_ratio(0, 0);

    /* when recording, preview both full-size buffers,'''
    )

    # The existing full-res YUV display filter's color half-res converter
    # is still called exactly once per update. We NEVER force heavy color
    # frames during REC and retain the original 500/1000ms queue safety
    # throttle. Adapt only the STBY pause when color draw itself is fast.
    source = replace_once(
        source,
        '''    raw_preview_fast_ex(
        RAW_IS_RECORDING ? fullsize_buffers[fi] : (void*)-1,
        PREVIEW_HACKED && RAW_IS_RECORDING ? (void*)-1 : buffers->dst_buf,
        -1,
        -1,
        (need_for_speed && !get_halfshutter_pressed())
            ? RAW_PREVIEW_GRAY_ULTRA_FAST
            : RAW_PREVIEW_COLOR_HALFRES
    );

    give_semaphore(settings_sem);

    /* be gentle with the CPU, save it for recording (especially if the buffer is almost full) */
    msleep(
        (need_for_speed)
            ? ((queued_frames > valid_slot_count / 2) ? 1000 : 500)
            : 50
    );''',
        '''    int qvfilm_lab_start_ms = qvfilm_lab_active ? get_ms_clock() : 0;
    raw_preview_fast_ex(
        RAW_IS_RECORDING ? fullsize_buffers[fi] : (void*)-1,
        PREVIEW_HACKED && RAW_IS_RECORDING ? (void*)-1 : buffers->dst_buf,
        -1,
        -1,
        (need_for_speed && !get_halfshutter_pressed())
            ? RAW_PREVIEW_GRAY_ULTRA_FAST
            : RAW_PREVIEW_COLOR_HALFRES
    );
    int qvfilm_lab_draw_ms = qvfilm_lab_active
        ? get_ms_clock() - qvfilm_lab_start_ms : 0;
    if (qvfilm_lab_active)
        qvfilm_preview_lab_last_draw_ms = qvfilm_lab_draw_ms;

    give_semaphore(settings_sem);

    /* Existing recording-time queue throttling stays unmodified.
     * In STBY lab mode, never reduce the idle sleep below 20 ms;
     * fall back to the original 50 ms if color conversion is slow.
     * This caps polling, not guaranteed preview frames per second.
     */
    msleep(
        (need_for_speed)
            ? ((queued_frames > valid_slot_count / 2) ? 1000 : 500)
            : (qvfilm_lab_active && qvfilm_lab_draw_ms < 40) ? 20
            : (qvfilm_lab_active && qvfilm_lab_draw_ms < 80) ? 35
            : 50
    );'''
    )

    # Menu is near existing Preview Guide. Does not mutate Preview
    # selection or any RAW engine state, only the opt-in scratch flag.
    source = replace_once(
        source,
        '''static struct menu_entry qvfilm_hud_menu[] = {''',
        '''/* QVFIL v0.6.10: read-only status of experimental STBY preview.
 * Lab OFF at boot, manual opt-in, no option saved to camera settings.
 */
static MENU_UPDATE_FUNC(qvfilm_preview_lab_update)
{
    MENU_SET_NAME("QVFIL Color Preview Lab");
    if (!qvfilm_preview_lab)
    {
        MENU_SET_RINFO("SAFE OFF");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Optional large color RAW framing in STBY only. Default OFF.");
    }
    else if (RAW_IS_RECORDING)
    {
        MENU_SET_RINFO("REC: BASE");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Lab OFF automatically while recording. Original RAW preview.");
    }
    else if (QVFIL_LAB_STBY)
    {
        MENU_SET_RINFO("DRAW %dms", qvfilm_preview_lab_last_draw_ms);
        MENU_SET_WARNING(MENU_WARN_INFO,
            "STBY: expanded RAW color framing; adaptive pacing. "
            "May still be slow. Focus and frame only; never assume 25fps.");
    }
    else
    {
        MENU_SET_RINFO("STBY: N/A");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Needs 5D3.123, RAW 10-bit <=1600x900, 1x LV, "
            "Auto/Real-time Preview. Other modes use core preview.");
    }
}

static struct menu_entry qvfilm_hud_menu[] = {'''
    )
    source = replace_once(
        source,
        '''    {
        .name = "QVFIL Preview Guide",
        .update = qvfilm_preview_guide_update,''',
        '''    {
        .name = "QVFIL Color Preview Lab",
        .priv = &qvfilm_preview_lab,
        .min = 0,
        .max = 1,
        .choices = CHOICES("OFF", "Color large STBY"),
        .update = qvfilm_preview_lab_update,
        .help = "Experimental expanded COLOR framing, STBY only.",
        .help2 = "OFF on reboot. REC always uses upstream preview mode.",
    },
    {
        .name = "QVFIL Preview Guide",
        .update = qvfilm_preview_guide_update,'''
    )
    source = replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.9")',
        'MENU_SET_RINFO("QVFIL v0.6.10")'
    )
    source = replace_once(
        source,
        'v0.6.9: Preview mode guide and honest Cinema Slim Auto ISO label.',
        'v0.6.10: Opt-in STBY Color Preview Lab; original RAW REC.'
    )
    return source


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", required=True)
    args = p.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        p.error("Requires exact Magic Lantern source checkout")
    sha = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if sha != UPSTREAM:
        p.error("Wrong upstream commit " + sha)
    path = root / TARGET_FILE
    original = path.read_text(encoding="utf-8")
    path.write_text(patch(original), encoding="utf-8")
    print("QVFIL v0.6.10: optional larger color RAW framing in STBY only.")
    print("No RAW REC changes. Lab OFF on every reboot. Camera test pending.")


if __name__ == "__main__":
    main()
