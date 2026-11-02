#!/usr/bin/env python3
"""QVFIL v0.6.4: read-only 1080p preflight + opt-in HUD guidance.

Layered on exact upstream 2025 and v0.6.3; does not alter the recorder,
buffer, sensor, writer, bit depth, compression, global draw or focus engine.
"""
import argparse
import subprocess
from pathlib import Path
import apply_cinema_focus_v063 as prior

UPSTREAM = prior.UPSTREAM
TARGET_FILE = prior.TARGET_FILE
replace_once = prior.replace_once


def patch(source):
    source = prior.patch(source)

    # The photos from v0.6.3 show HUD OFF / Draws:0 / Gate:1.
    # Clarify the opt-in setting; never secretly activate graphics in RAW REC.
    source = replace_once(
        source,
        '''static MENU_UPDATE_FUNC(qvfilm_hud_menu_update)
{
    MENU_SET_RINFO("QVFIL v0.6.3");
    if (qvfilm_hud_enabled >= 2 && !get_global_draw_setting())
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING, "Enable Global Draw to use Cinema Overlay.");
}''',
        '''static MENU_UPDATE_FUNC(qvfilm_hud_menu_update)
{
    MENU_SET_RINFO("QVFIL v0.6.4");
    if (qvfilm_hud_enabled == 0)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "HUD is OFF (Draws:0 / Gate:1 is normal). "
            "Select Large cinema, enable Global Draw, then Enter Cinema.");
    else if (qvfilm_hud_enabled >= 2 && !get_global_draw_setting())
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "Global Draw OFF. Enable it before using Cinema overlay.");
    else if (qvfilm_hud_enabled == 3)
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Large cinema updates in STBY. Values may freeze during RAW REC "
            "to prevent display flicker.");
}'''
    )

    # Menu-only readout. The existing v0.6.2 writer I/O rate measures active
    # write time, not guaranteed sustained CF throughput. Demand is computed
    # from current RAW size/bit depth/FPS. Never assert real card max speed.
    # Keep original stop logic and recorder untouched.
    preflight = r'''
/* QVFIL v0.6.4 Read-only preflight.
 * Uses previously measured writer data; performs NO new disk IO.
 * Relative "margin" can be misleading for a different card or changed
 * frame geometry; treat it as an advisory estimate, not certification.
 */
static MENU_UPDATE_FUNC(qvfilm_shoot_check_update)
{
    MENU_SET_NAME("QVFIL Shoot Check");
    const char *dir = get_cf_dcim_dir();
    char drive = dir ? dir[0] : '?';
    int need = qvfilm_media_demand_x10();
    int fps = (fps_get_current_x1000() + 500) / 1000;

    MENU_SET_VALUE("%dx%d %db %dfps", res_x, res_y, BPP, fps);

    if (!raw_video_enabled)
    {
        MENU_SET_RINFO("RAW OFF");
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "RAW video is OFF. Enable RAW video before testing.");
        return;
    }
    if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)
    {
        MENU_SET_RINFO("LJ BLOCKED");
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "5D3 lossless is blocked due to prior ASSERT. "
            "Use 10-bit uncompressed RAW.");
        return;
    }
    if (drive != 'A')
    {
        MENU_SET_RINFO("NOT CF");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "RAW target is not CF. Use a known-good UDMA7 CF card.");
        return;
    }
    if (need <= 0)
    {
        MENU_SET_RINFO("NO DEMAND");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "No valid RAW demand estimate for current resolution/FPS.");
        return;
    }
    if (!qvfilm_media_duration_ms || qvfilm_media_drive != drive ||
        !qvfilm_media_writer_x10)
    {
        MENU_SET_RINFO("NO SAMPLE");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "No valid CF capture sample since boot. Never infer free bandwidth.");
        return;
    }

    /* Use only integer %d (known working with Canon 5D3 menu formatter).
     * Show estimated percentage versus CURRENT mode's theoretical need.
     * This is NOT a speed benchmark or frame-loss diagnostic.
     */
    int margin = (int)((uint64_t)qvfilm_media_writer_x10 * 100 /
                        (uint64_t)need) - 100;
    MENU_SET_RINFO("CF M:%d%%", margin);

    if (qvfilm_last_stop_reason == 1)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Previous MLV stopped: BUFFER FULL. Check file and lower demand.");
    else if (qvfilm_last_stop_reason == 2)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Previous MLV stopped: FILE WRITE ERROR. Check CF and filesystem.");
    else if (qvfilm_media_duration_ms < 30000)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Last CF measurement is under 30s. Margin is preliminary only.");
    else if ((uint64_t)qvfilm_media_writer_x10 * 100 <
             (uint64_t)need * 120)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Estimated CF I/O margin is under 20%%. "
            "Keep proven settings; test MLV frame integrity.");
    else
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Margin is an estimate from LAST capture. "
            "CF sustained speed and every MLV frame are NOT guaranteed.");
}
'''
    source = replace_once(
        source,
        'static struct menu_entry qvfilm_hud_menu[] = {',
        preflight + '\nstatic struct menu_entry qvfilm_hud_menu[] = {'
    )

    source = replace_once(
        source,
        '''    {
        .name = "QVFIL Media Engine",
        .update = qvfilm_media_engine_update,''',
        '''    {
        .name = "QVFIL Shoot Check",
        .update = qvfilm_shoot_check_update,
        .help = "Read-only RAW mode and estimated CF I/O headroom check.",
        .help2 = "Last capture I/O is not CF max speed; verify .MLV integrity.",
    },
    {
        .name = "QVFIL Media Engine",
        .update = qvfilm_media_engine_update,'''
    )

    source = replace_once(
        source,
        'v0.6.3: Large LCD exposure values; native ML Focus Peak recommended.',
        'v0.6.4: HUD setup hints and read-only CF RAW preflight.'
    )
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    args = parser.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        parser.error("Expected Magic Lantern source git checkout")
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != UPSTREAM:
        parser.error("Wrong Magic Lantern source commit: " + actual)
    target = root / TARGET_FILE
    original = target.read_text(encoding="utf-8")
    updated = patch(original)
    target.write_text(updated, encoding="utf-8")
    print("QVFIL 0.6.4: read-only preflight + HUD instructions; RAW recorder unchanged.")
    print("EXPERIMENTAL: 5D3 real-camera test still required.")


if __name__ == "__main__":
    main()
