#!/usr/bin/env python3
"""QVFIL v0.6.11 — remove the redundant Preview-mode gate and expose blockers.

Layered on the exact v0.6.10 patch and pinned Magic Lantern 2025 source.
The renderer, RAW writer, compressor, queues, EDMAC and card I/O are untouched.
"""
import argparse
import subprocess
from pathlib import Path

import apply_color_preview_lab_v0610 as previous

UPSTREAM = previous.UPSTREAM
TARGET_FILE = previous.TARGET_FILE
replace_once = previous.replace_once

OLD_MACRO = """#define QVFIL_LAB_STBY (qvfilm_preview_lab &&     is_camera("5D3", "1.2.3") && RAW_IS_IDLE && lv_dispsize == 1 &&     (PREVIEW_AUTO || PREVIEW_CANON) &&     res_x > 0 && res_x <= 1600 && res_y > 0 && res_y <= 900 &&     BPP == 10 && raw_info.bits_per_pixel == 14)"""

NEW_MACRO = """#define QVFIL_LAB_STBY (qvfilm_preview_lab && is_camera("5D3", "1.2.3") && raw_video_enabled && lv && is_movie_mode() && RAW_IS_IDLE && lv_dispsize == 1 && res_x > 0 && res_x <= 1600 && res_y > 0 && res_y <= 900 && BPP == 10 && raw_info.bits_per_pixel == 14)"""

OLD_STATUS = """/* QVFIL v0.6.10: read-only status of experimental STBY preview.
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
}"""

NEW_STATUS = """/* QVFIL v0.6.11: explain each remaining Preview Lab safety gate.
 * Lab OFF at boot; no setting is persisted to camera configuration.
 */
static MENU_UPDATE_FUNC(qvfilm_preview_lab_update)
{
    MENU_SET_NAME("QVFIL Color Preview Lab");
    if (!qvfilm_preview_lab)
    {
        MENU_SET_RINFO("SAFE OFF");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Optional STBY color RAW framing. Default OFF; enable per session.");
    }
    else if (!is_camera("5D3", "1.2.3"))
    {
        MENU_SET_RINFO("5D3.123 ONLY");
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "Camera/firmware target mismatch. Keep the 5D3.123 guard; do not bypass it.");
    }
    else if (RAW_IS_RECORDING)
    {
        MENU_SET_RINFO("REC: BASE");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Lab is bypassed during RAW recording. Original RAW preview remains active.");
    }
    else if (!RAW_IS_IDLE)
    {
        MENU_SET_RINFO("RAW BUSY");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Wait until RAW recorder returns to IDLE before using Color Preview Lab.");
    }
    else if (!raw_video_enabled)
    {
        MENU_SET_RINFO("RAW OFF");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Enable RAW video in Movie before using Color Preview Lab.");
    }
    else if (!lv || !is_movie_mode())
    {
        MENU_SET_RINFO("MOVIE LV");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Enter Movie mode and start LiveView before using Color Preview Lab.");
    }
    else if (lv_dispsize != 1)
    {
        MENU_SET_RINFO("SET 1X LV");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Set LiveView magnification to 1x. Zoomed LiveView is excluded for safe framing.");
    }
    else if (res_x <= 0 || res_y <= 0)
    {
        MENU_SET_RINFO("NO RAW SIZE");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "RAW frame size is not initialized. Re-enter Movie LiveView and check RAW settings.");
    }
    else if (res_x > 1600 || res_y > 900)
    {
        MENU_SET_RINFO("LOWER RES");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Color Preview Lab is limited to 1600x900 or smaller in this build.");
    }
    else if (BPP != 10)
    {
        MENU_SET_RINFO("SET 10-BIT");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Select 10-bit uncompressed in RAW Data Format. Lossless remains blocked.");
    }
    else if (raw_info.bits_per_pixel != 14)
    {
        MENU_SET_RINFO("RAW INFO WAIT");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Native sensor RAW information is not ready. Re-enter Movie LiveView; do not bypass this check.");
    }
    else if (QVFIL_LAB_STBY)
    {
        MENU_SET_RINFO("DRAW %dms", qvfilm_preview_lab_last_draw_ms);
        MENU_SET_WARNING(MENU_WARN_INFO,
            "STBY color RAW framing active with adaptive pacing. Preview FPS is not guaranteed.");
    }
    else
    {
        MENU_SET_RINFO("CHECK GATE");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "An unexpected preview gate is closed. Keep Lab OFF and report this status with camera settings.");
    }
}"""


def patch(source):
    source = previous.patch(source)

    source = replace_once(source, OLD_MACRO, NEW_MACRO)
    source = replace_once(source, OLD_STATUS, NEW_STATUS)

    source = replace_once(
        source,
        "/* QVFIL Preview Lab (0.6.10): volatile session-only test switch.",
        "/* QVFIL Preview Lab (0.6.11): volatile session-only test switch."
    )
    source = replace_once(
        source,
        "* OFF on every boot, even if the camera previously opted in.",
        "* Preview mode is not a gate; QVFIL takes priority only when STBY gates pass.\n * OFF on every boot, even if the camera previously opted in."
    )
    source = replace_once(
        source,
        '.help2 = "OFF on reboot. REC always uses upstream preview mode.",',
        '.help2 = "Preview choice is overridden only when Lab is ready; RAW REC stays upstream.",'
    )
    source = replace_once(
        source,
        'MENU_SET_RINFO("QVFIL v0.6.10")',
        'MENU_SET_RINFO("QVFIL v0.6.11")'
    )
    source = replace_once(
        source,
        "v0.6.10: Opt-in STBY Color Preview Lab; original RAW REC.",
        "v0.6.11: Preview-mode-independent STBY Lab; detailed gate diagnostics."
    )
    return source


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", required=True)
    args = p.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        p.error("Requires exact Magic Lantern source git checkout")
    sha = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if sha != UPSTREAM:
        p.error("Wrong upstream commit " + sha)
    path = root / TARGET_FILE
    original = path.read_text(encoding="utf-8")
    path.write_text(patch(original), encoding="utf-8")
    print("QVFIL v0.6.11: Preview-mode-independent STBY Color Preview Lab.")
    print("RAW recorder, compressor, queues, EDMAC and card I/O unchanged.")
    print("No camera binary is authorized by this source patch alone.")


if __name__ == "__main__":
    main()
