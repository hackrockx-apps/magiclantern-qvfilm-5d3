/*
 * QVFilm Cinema RAW UI for Canon EOS 5D Mark III / Canon firmware 1.2.3.
 * 4K HUD source port, v0.7 engineering integration — no sensor/RAW path changes.
 *
 * This file is included from mlv_lite.c after the normal MLV Lite
 * controls and state have been declared. It intentionally uses their
 * existing read-only values and does not patch registers, EDMAC,
 * buffers, sensor crop configuration or recording state.
 *
 * The original "Movie" menu remains available as the sole place for
 * editing RAW settings in this first milestone.
 *
 * Magic Lantern is GPL licensed; this source is redistributed under GPL-2.0-or-later.
 */

#define QVF_PAGE_COUNT 5
#define QVF_W 720
#define QVF_H 480

static int qvfilm_page = 0;

static const char *qvfilm_page_name(int page)
{
    switch (page)
    {
        case 0: return "DASH";
        case 1: return "RECORD";
        case 2: return "EXPOSURE";
        case 3: return "MONITOR";
        case 4: return "SYSTEM";
        default: return "DASH";
    }
}

static const char *qvfilm_record_state(void)
{
    if (RAW_IS_RECORDING) return "RECORDING";
    if (RAW_IS_PREPARING) return "STARTING";
    if (RAW_IS_FINISHING) return "STOPPING";
    return "STANDBY";
}

static const char *qvfilm_format(void)
{
    switch (output_format)
    {
        case OUTPUT_14BIT_NATIVE:       return "14-BIT RAW";
        case OUTPUT_12BIT_UNCOMPRESSED: return "12-BIT RAW";
        case OUTPUT_10BIT_UNCOMPRESSED: return "10-BIT RAW";
        case OUTPUT_14BIT_LOSSLESS:     return "14-BIT LOSSLESS";
        case OUTPUT_12BIT_LOSSLESS:     return "12-BIT LOSSLESS";
        case OUTPUT_AUTO_BIT_LOSSLESS:  return "AUTO LOSSLESS";
        default:                        return "UNKNOWN";
    }
}

static void qvfilm_header(void)
{
    bmp_fill(COLOR_BLACK, 0, 0, QVF_W, QVF_H);
    bmp_fill(COLOR_ALMOST_BLACK, 0, 0, QVF_W, 62);
    bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
               24, 11, "QVFILM");
    bmp_printf(FONT(FONT_MED, COLOR_YELLOW, COLOR_ALMOST_BLACK),
               267, 22, "5D3 4K CINEMA");
    bmp_fill(COLOR_YELLOW, 0, 61, QVF_W, 3);
}

static void qvfilm_footer(void)
{
    int i;
    bmp_fill(COLOR_ALMOST_BLACK, 0, 418, QVF_W, 62);
    for (i = 0; i < QVF_PAGE_COUNT; i++)
    {
        int x = 14 + i * 143;
        uint32_t font = FONT(FONT_SMALL, (i == qvfilm_page ? COLOR_YELLOW : COLOR_WHITE), COLOR_ALMOST_BLACK);
        bmp_printf(font, x, 436, "%s", qvfilm_page_name(i));
    }
    bmp_printf(FONT(FONT_SMALL, COLOR_WHITE, COLOR_ALMOST_BLACK),
               24, 461, "LEFT / RIGHT / SET: PAGE   |   MOVIE: RAW SETTINGS");
}

static void qvfilm_label(int x, int y, const char *label)
{
    bmp_printf(FONT(FONT_MED, COLOR_YELLOW, COLOR_BLACK), x, y, "%s", label);
}

static void qvfilm_dashboard(void)
{
    int fps = fps_get_current_x1000();
    qvfilm_label(24, 81, "RESOLUTION");
    if (res_x > 0 && res_y > 0)
        bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_BLACK),
                   24, 119, "%d x %d", res_x, res_y);
    else
        bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_BLACK),
                   24, 119, "NOT READY");

    qvfilm_label(397, 81, "FRAME RATE");
    if (fps > 0)
        bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_BLACK),
                   397, 119, "%d.%02d p", fps / 1000, (fps % 1000) / 10);
    else
        bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_BLACK),
                   397, 119, "N/A");

    bmp_fill(COLOR_ALMOST_BLACK, 18, 183, 684, 2);
    qvfilm_label(24, 204, "RAW FORMAT");
    bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_BLACK),
               24, 241, "%s", qvfilm_format());

    qvfilm_label(397, 204, "RECORDING");
    bmp_printf(FONT(FONT_LARGE,
                       RAW_IS_RECORDING ? COLOR_RED : COLOR_WHITE,
                       COLOR_BLACK),
               397, 241, "%s", qvfilm_record_state());

    bmp_fill(COLOR_ALMOST_BLACK, 18, 305, 684, 2);
    qvfilm_label(24, 326, "MODE");
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 358, "%s", raw_video_enabled ? "MLV RAW ENABLED" : "RAW VIDEO OFF");
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 385, "Settings: Movie > RAW video");
}

static void qvfilm_record(void)
{
    qvfilm_label(24, 88, "RECORDER / CURRENT SETTINGS");
    bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_BLACK),
               24, 134, "RAW VIDEO: %s", raw_video_enabled ? "ON" : "OFF");
    if (res_x > 0 && res_y > 0)
        bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_BLACK),
                   24, 178, "IMAGE: %d x %d", res_x, res_y);
    else
        bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_BLACK),
                   24, 178, "IMAGE: NOT READY");
    bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_BLACK),
               24, 222, "%s", qvfilm_format());
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 286, "Select real crop mode in Movie > Crop mode.");
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 316, "QVFIL HUD is display-only; no RAW changes.");
    if (!RAW_IS_IDLE)
        bmp_printf(FONT(FONT_MED, COLOR_RED, COLOR_BLACK),
                   24, 370, "Recorder busy: do not change settings.");
}

static void qvfilm_exposure(void)
{
    qvfilm_label(24, 88, "CAMERA EXPOSURE");
    if (lens_info.iso_analog_raw > 0)
        bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_BLACK),
                   24, 137, "ISO %d", raw2iso(lens_info.iso_analog_raw));
    else
        bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_BLACK),
                   24, 137, "ISO N/A");
    bmp_printf(FONT(FONT_LARGE, COLOR_WHITE, COLOR_BLACK),
               24, 197, "SHUTTER %s", lens_format_shutter(lens_info.raw_shutter));
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 292, "Aperture / WB: use Canon controls.");
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 329, "Recording exposure is not altered.");
}

static void qvfilm_monitor(void)
{
    qvfilm_label(24, 88, "MONITORING TOOLS");
    bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_BLACK),
               24, 137, "Use the Magic Lantern Overlay menu");
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 191, "to configure available overlays.");
    bmp_printf(FONT(FONT_MED, COLOR_YELLOW, COLOR_BLACK),
               24, 266, "4K-WIDTH MODE NOTE");
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 302, "3840x1600 = 2.40:1, NOT 3840x2160.");
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 332, "Color REC preview / FPS need hardware test.");
}

static void qvfilm_system(void)
{
    qvfilm_label(24, 88, "SYSTEM / REAL-TIME DIAGNOSTICS");
    bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_BLACK),
               24, 134, "BODY: CANON 5D MARK III");
    bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_BLACK),
               24, 172, "TARGET: 5D3.123");
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 231, "RAW MEMORY SLOTS: %d", valid_slot_count);
    if (measured_write_speed > 0)
        bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
                   24, 270, "CARD WRITE (LAST): %d.%d MB/s",
                   measured_write_speed / 10,
                   measured_write_speed % 10);
    else
        bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
                   24, 270, "CARD WRITE: NOT MEASURED");
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 327, "Recorder state: %s", qvfilm_record_state());
    bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_BLACK),
               24, 373, "QVFIL 4K HUD / untested");
}

/*
 * menu.c only permits full-screen custom drawing when the active menu item
 * is selected and a draw pass has been requested.
 */
static MENU_UPDATE_FUNC(qvfilm_screen_update)
{
    if (!info->can_custom_draw || !entry->selected)
        return;

    info->custom_drawing = CUSTOM_DRAW_THIS_MENU;
    qvfilm_header();

    switch (qvfilm_page)
    {
        case 0: qvfilm_dashboard(); break;
        case 1: qvfilm_record(); break;
        case 2: qvfilm_exposure(); break;
        case 3: qvfilm_monitor(); break;
        case 4: qvfilm_system(); break;
        default: qvfilm_dashboard(); break;
    }
    qvfilm_footer();
}

/* Does not touch recording settings; only cycles local UI pages. */
static MENU_SELECT_FUNC(qvfilm_page_select)
{
    if (!RAW_IS_IDLE)
        return;

    if (delta == 0)
        delta = 1;
    qvfilm_page = (qvfilm_page + ((delta % QVF_PAGE_COUNT) + QVF_PAGE_COUNT))
                  % QVF_PAGE_COUNT;
    menu_redraw();
}

static struct menu_entry qvfilm_menu[] = {
    {
        .name = "Cinema RAW",
        .select = qvfilm_page_select,
        .update = qvfilm_screen_update,
        .icon_type = IT_ACTION,
        .help = "QVFilm Cinema RAW. Select to change dashboard page.",
    }
};

/* Port of the v0.6.x QVFIL LCD concept into the Danne/Arnaud 4K tree.
 * New optional cinema overlay uses only existing camera/recorder telemetry.
 * Default is OFF each boot. This never changes sensor, codec, writer,
 * raw preview engine, frame buffers or card speed constraints.
 */
static int qvfilm_4k_hud_mode = 0;
static unsigned int qvfilm_4k_hud_draws = 0;
static unsigned int qvfilm_4k_hud_skips = 0;
static int qvfilm_4k_hud_last_gate = 0;

static void qvfilm_4k_draw_hud(void)
{
    static unsigned int last_tick = 0;
    static int last_record_state = -1;
    static int last_style = -1;
    int state = RAW_IS_RECORDING ? 2 : (RAW_IS_IDLE ? 0 : 1);
    unsigned int now = (unsigned int)get_ms_clock();

    /* No fast display callback; only called from existing ShootTask polling.
     * Paint at most every 500ms in standby. During REC paint only on the
     * transition or on style change to avoid competing with RAW capture. */
    if (!qvfilm_4k_hud_mode) { qvfilm_4k_hud_last_gate = 1; return; }
    if (!lv || !is_movie_mode() || !raw_video_enabled || gui_menu_shown())
        { qvfilm_4k_hud_last_gate = 2; return; }
    if (!get_global_draw_setting() || !bmp_is_on())
        { qvfilm_4k_hud_last_gate = 3; return; }
    if (!RAW_IS_IDLE && !RAW_IS_RECORDING)
        { qvfilm_4k_hud_last_gate = 4; return; }
    if (state == last_record_state && qvfilm_4k_hud_mode == last_style &&
        ((RAW_IS_RECORDING) || (unsigned int)(now - last_tick) < 500))
        { qvfilm_4k_hud_skips++; return; }

    const char *st = RAW_IS_RECORDING ? "REC" : "STBY";
    int fps = fps_get_current_x1000();
    int iso = lens_info.iso ? lens_info.iso : lens_info.iso_auto;
    int focal = lens_info.focal_len;
    int aperture = lens_info.aperture;
    int shutter = get_current_shutter_reciprocal_x1000();
    int shutter_d = shutter > 0 ? (shutter + 500) / 1000 : 0;

    BMP_LOCK(
        /* Opaque small bars. Painting stays in bitmap plane, not raw LV. */
        bmp_fill(COLOR_ALMOST_BLACK, 28, 84, 440, 30);
        bmp_printf(FONT(FONT_MED, RAW_IS_RECORDING ? COLOR_RED : COLOR_WHITE,
                        COLOR_ALMOST_BLACK),
                   36, 89, "QVFIL 4K %s  %d.%02d p", st,
                   fps / 1000, (fps % 1000) / 10);
        bmp_fill(COLOR_ALMOST_BLACK, 28, 381, 665, 30);
        bmp_printf(FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK),
                   36, 386, "%dx%d   %s", res_x, res_y, qvfilm_format());
        if (qvfilm_4k_hud_mode == 2)
        {
            bmp_fill(COLOR_ALMOST_BLACK, 28, 340, 665, 38);
            if (focal > 0)
                bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           35, 347, "%dmm", focal);
            else
                bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           35, 347, "--mm");
            if (aperture > 0)
                bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           175, 347, "f/%d.%d", aperture / 10, aperture % 10);
            else
                bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           175, 347, "f/--");
            if (shutter_d > 0)
                bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           323, 347, "1/%d", shutter_d);
            else
                bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           323, 347, "1/--");
            if (iso > 0)
                bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           490, 347, "ISO%d", iso);
            else
                bmp_printf(FONT(FONT_MED_LARGE, COLOR_WHITE, COLOR_ALMOST_BLACK),
                           490, 347, "ISO--");
        }
    )

    last_tick = now;
    last_record_state = state;
    last_style = qvfilm_4k_hud_mode;
    qvfilm_4k_hud_draws++;
    qvfilm_4k_hud_last_gate = 0;
}

static MENU_UPDATE_FUNC(qvfilm_4k_hud_update)
{
    MENU_SET_NAME("QVFIL Cinema HUD");
    MENU_SET_RINFO("D:%u G:%d", qvfilm_4k_hud_draws, qvfilm_4k_hud_last_gate);
    MENU_SET_WARNING(MENU_WARN_INFO,
        "Opt-in read-only STBY/REC overlay. Core Focus Peak is separate.");
}

static struct menu_entry qvfilm_4k_hud_menu[] = {
    {
        .name = "QVFIL Cinema HUD",
        .priv = &qvfilm_4k_hud_mode,
        .max = 2,
        .choices = CHOICES("OFF", "Info bars", "Large cinema"),
        .update = qvfilm_4k_hud_update,
        .help = "Display-only; starts OFF each boot.",
        .help2 = "No new 4K sensor mode or preview acceleration is implied.",
    },
};

static void qvfilm_register_menu(void)
{
    /* Restrict this experimental UI to the intended camera/firmware. */
    if (cam_5d3_123)
        {
            menu_add("QVFIL", qvfilm_menu, COUNT(qvfilm_menu));
            menu_add("Movie", qvfilm_4k_hud_menu, COUNT(qvfilm_4k_hud_menu));
        }
}
