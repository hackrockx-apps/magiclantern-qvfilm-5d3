#!/usr/bin/env python3
"""QVFIL v0.6.5: opt-in Cinema clean HUD and accurate Overlay focus guide.

Strict layer over v0.6.4 and exact Magic Lantern 2025 source. Nothing in
RAW recorder, sensor, buffer management, I/O, compression, or Focus Peak core
is changed. New LCD layout is selected explicitly; v0.6.4 HUD is retained.
"""
import argparse
import subprocess
from pathlib import Path
import apply_safe_preflight_v064 as prior

UPSTREAM = prior.UPSTREAM
TARGET_FILE = prior.TARGET_FILE
replace_once = prior.replace_once


def patch(source):
    source = prior.patch(source)

    # Fourth HUD mode is separately opt-in. The other choices remain
    # in exactly the same order (existing saved value 3 stays Large cinema).
    source = replace_once(
        source,
        'if (qvfilm_hud_enabled != 2 && qvfilm_hud_enabled != 3) '
        '{ qvfilm_hud_gate_code = 1; return; }',
        'if (qvfilm_hud_enabled != 2 && qvfilm_hud_enabled != 3 && '
        'qvfilm_hud_enabled != 4) { qvfilm_hud_gate_code = 1; return; }'
    )
    source = replace_once(
        source,
        '''        .max = 3,
        .choices = CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema"),''',
        '''        .max = 4,
        .choices = CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema", "Cinema clean"),'''
    )

    # Reuse the same camera data and same draw callback. This changes only
    # the condition deciding whether to update display in STBY.
    source = replace_once(
        source,
        '''                  (qvfilm_hud_enabled == 3 &&
                   (last_focal != focal || last_aperture != aperture ||
                    last_shutter != shutter_recip));''',
        '''                  ((qvfilm_hud_enabled == 3 || qvfilm_hud_enabled == 4) &&
                   (last_focal != focal || last_aperture != aperture ||
                    last_shutter != shutter_recip));'''
    )

    # "Cinema clean" is a 2 x 2 large-text panel in the left/lower image.
    # At x=35..525 it avoids the original right-hand histogram (usually
    # x~580+) while staying clear of the core bottom info bar (y>=420).
    # Values and state are not recalculated in the RAW capture path.
    # Continue using the original one-draw-at-REC-transition / pause
    # repeated bitmap work, so peaking can run independently via ML core.
    clean = '''    if (qvfilm_hud_enabled == 4)
    {
        /* QVFIL Cinema clean. Smaller covered width to avoid histogram;
         * display-only, no extra focus detection or RAW processing.
         * 720x480 BMP geometry. User must verify on-camera positions.
         */
        BMP_LOCK(
            bmp_fill(COLOR_ALMOST_BLACK, 35, 312, 490, 70);
            if (focal)
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           44, 319, "%dmm", focal);
            else
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           44, 319, "--mm");
            if (aperture)
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           278, 319, "f/%d.%d",
                           aperture / 10, aperture % 10);
            else
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           278, 319, "f/--");
            if (shutter_recip)
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           44, 351, "1/%d", shutter_recip);
            else
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           44, 351, "1/--");
            if (iso)
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           278, 351, "ISO%d", iso);
            else
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           278, 351, "ISO--");

            bmp_fill(COLOR_ALMOST_BLACK, 34, 105, 330, 26);
            bmp_printf(FONT(FONT_MED,
                            mode == 1 ? COLOR_RED : COLOR_WHITE,
                            COLOR_ALMOST_BLACK),
                       42, 108, "QVFIL %s  %d FPS", state, fps);
        )
    }
    else if (qvfilm_hud_enabled == 3)
    {
        /* Large Cinema'''
    source = replace_once(
        source,
        '''    if (qvfilm_hud_enabled == 3)
    {
        /* Large Cinema''',
        clean
    )

    # Fix previous navigation bug: Focus Peak belongs to Overlay,
    # NOT the Focus tab. User has now verified it works natively in MF.
    source = replace_once(
        source,
        '"Global Draw OFF. Enable it before Focus > Focus Peak."',
        '"Global Draw OFF. Use Overlay > Global Draw before Focus Peak."'
    )
    source = replace_once(
        source,
        '"Use ML Focus tab > Focus Peak ON; choose Red and adjust Threshold."'
        '\n            " QVFIL reuses core peaking; no second focus algorithm."',
        '"Use Overlay > Focus Peak ON; switch lens to MF; tune Threshold."'
        '\n            " Core ML peaking is used; no QVFIL pixel processing."'
    )
    source = replace_once(
        source,
        '.help2 = "Focus tab > Focus Peak ON. No extra bitmap peaking in recorder.",',
        '.help2 = "Overlay > Focus Peak ON; set MF. No new peaking algorithm.",'
    )
    source = replace_once(
        source,
        '/* Large Cinema: one compact panel, no fresh edge detection, no\n'
        '         * raw path modifications. Native ML Focus Peak can be enabled in\n'
        '         * the Focus tab.',
        '/* Large Cinema: one compact panel, no fresh edge detection, no\n'
        '         * raw path modifications. Native ML Focus Peak can be enabled in\n'
        '         * the Overlay tab.'
    )

    # The same menu requires Global Draw for both old and new overlay modes.
    source = replace_once(
        source,
        '''    MENU_SET_RINFO("QVFIL v0.6.4");''',
        '''    MENU_SET_RINFO("QVFIL v0.6.5");'''
    )
    source = replace_once(
        source,
        '''    else if (qvfilm_hud_enabled == 3)
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Large cinema updates in STBY. Values may freeze during RAW REC "
            "to prevent display flicker.");''',
        '''    else if (qvfilm_hud_enabled == 4)
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Cinema clean: 2x2 left panel avoids right histogram. "
            "No repeated QVFIL drawing during RAW REC.");
    else if (qvfilm_hud_enabled == 3)
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Large cinema updates in STBY. Values may freeze during RAW REC "
            "to prevent display flicker.");'''
    )
    source = replace_once(
        source,
        'v0.6.4: HUD setup hints and read-only CF RAW preflight.',
        'v0.6.5: Opt-in Cinema clean panel; correct Overlay Focus Peak path.'
    )
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    args = parser.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        parser.error("Expected an exact Magic Lantern source checkout")
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != UPSTREAM:
        parser.error("Wrong source commit " + actual)
    target = root / TARGET_FILE
    original = target.read_text(encoding="utf-8")
    updated = patch(original)
    target.write_text(updated, encoding="utf-8")
    print("QVFIL 0.6.5: opt-in Cinema clean and corrected focus navigation.")
    print("Raw recorder is unchanged. Camera hardware acceptance pending.")


if __name__ == "__main__":
    main()
