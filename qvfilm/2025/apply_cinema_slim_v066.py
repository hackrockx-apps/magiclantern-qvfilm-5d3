#!/usr/bin/env python3
"""QVFIL v0.6.6: optional low-coverage Cinema slim HUD.

Strictly layered on 0.6.5, pinned 2025 MLV Lite. No changes to RAW recording
task, sensor, storage, buffer management, codec, focus rendering or core
Magic Lantern overlays. Existing saved HUD modes 0..4 keep their semantics.
"""
import argparse
import subprocess
from pathlib import Path
import apply_cinema_clean_v065 as prior

UPSTREAM = prior.UPSTREAM
TARGET_FILE = prior.TARGET_FILE
replace_once = prior.replace_once


def patch(source):
    source = prior.patch(source)

    # Preserve 0:OFF, 1:Info bars, 2:Cinema overlay, 3:Large cinema,
    # 4:Cinema clean. New 5:Cinema slim is opt-in, OFF by default.
    source = replace_once(
        source,
        '''if (qvfilm_hud_enabled != 2 && qvfilm_hud_enabled != 3 && qvfilm_hud_enabled != 4) { qvfilm_hud_gate_code = 1; return; }''',
        '''if (qvfilm_hud_enabled != 2 && qvfilm_hud_enabled != 3 &&
        qvfilm_hud_enabled != 4 && qvfilm_hud_enabled != 5)
    { qvfilm_hud_gate_code = 1; return; }'''
    )
    source = replace_once(
        source,
        '''        .max = 4,
        .choices = CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema", "Cinema clean"),''',
        '''        .max = 5,
        .choices = CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema", "Cinema clean", "Cinema slim"),'''
    )
    source = replace_once(
        source,
        '''                  ((qvfilm_hud_enabled == 3 || qvfilm_hud_enabled == 4) &&
                   (last_focal != focal || last_aperture != aperture ||
                    last_shutter != shutter_recip));''',
        '''                  ((qvfilm_hud_enabled == 3 || qvfilm_hud_enabled == 4 ||
                    qvfilm_hud_enabled == 5) &&
                   (last_focal != focal || last_aperture != aperture ||
                    last_shutter != shutter_recip));'''
    )

    # Existing v0.6.5 Cinema clean draws 490x70 near the lower left PLUS
    # a 330x26 status panel up top. This mode uses ONE 526x30 stripe only.
    # Magic Lantern already displays RAW/FPS/REC state at the top, so we
    # intentionally do not duplicate "QVFIL STBY 25 FPS" on this mode.
    # Keep right histogram and native bottom Canon/ML status bars clear.
    # 720x480 canonical bitmap coordinates; x=35..561, y=352..382.
    # FONT_MED is deliberately smaller than the old large type in exchange
    # for less image occlusion; users can stay on Cinema clean for big text.
    slim = '''    if (qvfilm_hud_enabled == 5)
    {
        /* Cinema slim: single read-only row, no redundant upper badge.
         * No new high-frequency bitmap calls during sustained RAW REC.
         * Physical placement requires real 5D3 validation.
         */
        BMP_LOCK(
            bmp_fill(COLOR_ALMOST_BLACK, 35, 352, 526, 30);
            if (focal)
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           42, 356, "%dmm", focal);
            else
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           42, 356, "--mm");
            if (aperture)
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           179, 356, "f/%d.%d",
                           aperture / 10, aperture % 10);
            else
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           179, 356, "f/--");
            if (shutter_recip)
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           312, 356, "1/%d", shutter_recip);
            else
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           312, 356, "1/--");
            if (iso)
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           420, 356, "ISO%d", iso);
            else
                bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           420, 356, "ISO--");
        )
    }
    else if (qvfilm_hud_enabled == 4)
    {
        /* QVFIL Cinema clean.'''
    source = replace_once(
        source,
        '''    if (qvfilm_hud_enabled == 4)
    {
        /* QVFIL Cinema clean.''',
        slim
    )

    # Make opt-in tradeoff explicit in the 5D3 menu. Never claim RAW FPS
    # or peaking performance improvements from a display-only change.
    source = replace_once(
        source,
        '''    MENU_SET_RINFO("QVFIL v0.6.5");''',
        '''    MENU_SET_RINFO("QVFIL v0.6.6");'''
    )
    source = replace_once(
        source,
        '''    else if (qvfilm_hud_enabled == 4)
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Cinema clean: 2x2 left panel avoids right histogram. "
            "No repeated QVFIL drawing during RAW REC.");''',
        '''    else if (qvfilm_hud_enabled == 5)
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Cinema slim: smaller type, one low strip, no upper QVFIL badge. "
            "Core RAW/REC/FPS indicators remain. No repeated REC drawing.");
    else if (qvfilm_hud_enabled == 4)
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Cinema clean: 2x2 left panel avoids right histogram. "
            "No repeated QVFIL drawing during RAW REC.");'''
    )
    source = replace_once(
        source,
        'v0.6.5: Opt-in Cinema clean panel; correct Overlay Focus Peak path.',
        'v0.6.6: Optional one-row slim monitor, no duplicate top badge.'
    )
    return source


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", required=True)
    args = p.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        p.error("Require pinned Magic Lantern source Git checkout")
    sha = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if sha != UPSTREAM:
        p.error("Incorrect upstream commit: " + sha)
    target = root / TARGET_FILE
    source = target.read_text(encoding="utf-8")
    result = patch(source)
    target.write_text(result, encoding="utf-8")
    print("QVFIL v0.6.6: opt-in Cinema slim HUD; recorder unchanged.")
    print("EXPERIMENTAL: requires real 5D3 on-camera validation.")


if __name__ == "__main__":
    main()
