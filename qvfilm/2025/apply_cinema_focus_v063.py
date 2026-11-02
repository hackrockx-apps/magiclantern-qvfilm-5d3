#!/usr/bin/env python3
"""QVFIL 0.6.3: opt-in large exposure HUD + core Focus Peak workflow.
Extends exact 2025 source and v0.6.2 without modifying recorder function.
"""
import argparse
import subprocess
from pathlib import Path
import apply_media_engine_v062 as prior

UPSTREAM = prior.UPSTREAM
TARGET_FILE = prior.TARGET_FILE
replace_once = prior.replace_once

def patch(source):
    source = prior.patch(source)

    # Camera may currently load stock mlv_lite, or none at all. This C menu
    # only exists if the module actually boots. Never fake ML loaded state.
    source = replace_once(
        source,
        'if (qvfilm_hud_enabled != 2) { qvfilm_hud_gate_code = 1; return; }',
        'if (qvfilm_hud_enabled != 2 && qvfilm_hud_enabled != 3) '
        '{ qvfilm_hud_gate_code = 1; return; }'
    )
    source = replace_once(
        source,
        '    static int last_bits = -1;\n'
        '    static int last_refresh = INT_MIN;',
        '    static int last_bits = -1;\n'
        '    static int last_hud_style = -1;\n'
        '    static int last_focal = -1;\n'
        '    static int last_aperture = -1;\n'
        '    static int last_shutter = -1;\n'
        '    static int last_refresh = INT_MIN;'
    )
    source = replace_once(
        source,
        '    int iso = lens_info.iso;\n'
        '    int bits = BPP;',
        '    int iso = lens_info.iso ? lens_info.iso : lens_info.iso_auto;\n'
        '    int bits = BPP;\n'
        '    int focal = lens_info.focal_len; /* mm; 0 means lens has no data */\n'
        '    int aperture = lens_info.aperture; /* f-stop x10 */\n'
        '    int shutter = get_current_shutter_reciprocal_x1000();\n'
        '    int shutter_recip = shutter > 0 ? (shutter + 500) / 1000 : 0;'
    )
    source = replace_once(
        source,
        '    int changed = mode != last_mode || fps != last_fps || iso != last_iso ||\n'
        '                  res_x != last_x || res_y != last_y || bits != last_bits;',
        '    int changed = mode != last_mode || fps != last_fps || iso != last_iso ||\n'
        '                  res_x != last_x || res_y != last_y || bits != last_bits ||\n'
        '                  last_hud_style != qvfilm_hud_enabled ||\n'
        '                  (qvfilm_hud_enabled == 3 &&\n'
        '                   (last_focal != focal || last_aperture != aperture ||\n'
        '                    last_shutter != shutter_recip));'
    )
    # By design the big monitor does not touch bitmap repeatedly during RAW.
    # Native ML Focus Peak is managed by core zebra.c, not duplicated here.
    a = '''    BMP_LOCK(
        bmp_fill(COLOR_ALMOST_BLACK, 40, 85, 475, 26);
        bmp_printf(FONT(FONT_MED,
                        mode == 1 ? COLOR_RED : COLOR_WHITE,
                        COLOR_ALMOST_BLACK),
                   50, 89, "QVFIL %s   %d FPS", state, fps);

        bmp_fill(COLOR_ALMOST_BLACK, 40, 382, 570, 26);
        bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                   50, 386, "%dx%d  %db RAW   ISO %d",
                   res_x, res_y, bits, iso);
    )'''
    b = '''    if (qvfilm_hud_enabled == 3)
    {
        /* Large Cinema: one compact panel, no fresh edge detection, no
         * raw path modifications. Native ML Focus Peak can be enabled in
         * the Focus tab. Missing electronic lens info is marked "--".
         * Canon bitmap coordinates: 720x480; panel stays within frame.
         */
        BMP_LOCK(
            bmp_fill(COLOR_ALMOST_BLACK, 34, 344, 653, 44);
            if (focal)
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           42, 349, "%dmm", focal);
            else
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           42, 349, "--mm");
            if (aperture)
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           192, 349, "f/%d.%d",
                           aperture / 10, aperture % 10);
            else
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           192, 349, "f/--");
            if (shutter_recip)
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           340, 349, "1/%d", shutter_recip);
            else
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           340, 349, "1/--");
            if (iso)
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           500, 349, "ISO%d", iso);
            else
                bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           500, 349, "ISO--");

            bmp_fill(COLOR_ALMOST_BLACK, 34, 105, 330, 26);
            bmp_printf(FONT(FONT_MED,
                            mode == 1 ? COLOR_RED : COLOR_WHITE,
                            COLOR_ALMOST_BLACK),
                       42, 108, "QVFIL %s  %d FPS", state, fps);
        )
    }
    else
    {
        /* Existing v0.6.2 compact HUD remains byte-for-byte visually. */
        BMP_LOCK(
            bmp_fill(COLOR_ALMOST_BLACK, 40, 85, 475, 26);
            bmp_printf(FONT(FONT_MED,
                            mode == 1 ? COLOR_RED : COLOR_WHITE,
                            COLOR_ALMOST_BLACK),
                       50, 89, "QVFIL %s   %d FPS", state, fps);
            bmp_fill(COLOR_ALMOST_BLACK, 40, 382, 570, 26);
            bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                       50, 386, "%dx%d  %db RAW   ISO %d",
                       res_x, res_y, bits, iso);
        )
    }'''
    source = replace_once(source, a, b)
    source = replace_once(
        source,
        '    last_bits = bits;\n}',
        '    last_bits = bits;\n'
        '    last_hud_style = qvfilm_hud_enabled;\n'
        '    last_focal = focal;\n'
        '    last_aperture = aperture;\n'
        '    last_shutter = shutter_recip;\n}'
    )

    # No attempt to implement another peaking renderer. The exact 2025 core
    # already has Focus > Focus Peak with configurable color and threshold.
    source = replace_once(
        source,
        'static struct menu_entry qvfilm_hud_menu[] = {',
        '''static MENU_UPDATE_FUNC(qvfilm_focus_assist_update)
{
    MENU_SET_NAME("QVFIL Focus Assist");
    MENU_SET_RINFO("CORE FOCUS PEAK");
    if (!get_global_draw_setting())
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Global Draw OFF. Enable it before Focus > Focus Peak.");
    else
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Use ML Focus tab > Focus Peak ON; choose Red and adjust Threshold."
            " QVFIL reuses core peaking; no second focus algorithm.");
}

static struct menu_entry qvfilm_hud_menu[] = {'''
    )
    source = replace_once(
        source,
        '''        .max = 2,
        .choices = CHOICES("OFF", "Info bars", "Cinema overlay"),''',
        '''        .max = 3,
        .choices = CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema"),'''
    )
    source = replace_once(
        source,
        '''    {
        .name = "QVFIL HUD Diagnostics",''',
        '''    {
        .name = "QVFIL Focus Assist",
        .update = qvfilm_focus_assist_update,
        .help = "Read-only setup guide for original Magic Lantern Focus Peak.",
        .help2 = "Focus tab > Focus Peak ON. No extra bitmap peaking in recorder.",
    },
    {
        .name = "QVFIL HUD Diagnostics",'''
    )
    source = replace_once(
        source,
        '''    if (qvfilm_hud_enabled == 2 && !get_global_draw_setting())''',
        '''    if (qvfilm_hud_enabled >= 2 && !get_global_draw_setting())'''
    )
    source = replace_once(
        source, 'MENU_SET_RINFO("QVFIL v0.6.2");',
        'MENU_SET_RINFO("QVFIL v0.6.3");'
    )
    source = replace_once(
        source,
        'v0.6.2: Reliability hints using writer I/O; recorder unchanged.',
        'v0.6.3: Large LCD exposure values; native ML Focus Peak recommended.'
    )
    return source

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    args = parser.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        parser.error("Expected Magic Lantern source checkout.")
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if actual != UPSTREAM:
        parser.error("Wrong Magic Lantern source commit " + actual)
    target = root / TARGET_FILE
    old = target.read_text(encoding="utf-8")
    result = patch(old)
    target.write_text(result, encoding="utf-8")
    print("QVFIL v0.6.3 large cinema LCD+core focus guide; no RAW writer changes")
    print("EXPERIMENTAL: output pending on-camera acceptance.")

if __name__ == "__main__":
    main()
