#!/usr/bin/env python3
"""Regression: QVFIL v0.6.20 full vs 2 vs 3 stripe STBY diagnostics."""
import sys
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import apply_color_stripes_v0619 as previous
import apply_stripe_ab_sweep_rate_v0620 as current

class ColorStripeABTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=HERE/"fixture-2025-mlv_lite.c"
        if not f.exists():raise unittest.SkipTest("Pinned ML2025 fixture injected by GitHub CI")
        orig=f.read_text(encoding="utf-8")
        cls.before=previous.patch(orig)
        cls.after=current.patch(orig)

    @staticmethod
    def section(src,a,b):
        first=src.index(a)
        last=src.index(b,first)
        return src[first:last]

    def test_original_raw_rec_compress_and_card_io_unchanged(self):
        for a,b in (
            ("void raw_video_rec_task()\n{",
             "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            ("static void compress_task()\n{",
             "static REQUIRES(LiveViewTask) FAST\nvoid process_frame("),
        ):
            self.assertEqual(self.section(self.before,a,b),
                             self.section(self.after,a,b))

    def test_existing_preview_unchanged_but_safe_optin_segment(self):
        self.assertIn(current.PREVIEW_NEW,self.after)
        self.assertIn(current.COUNT_NEW,self.after)
        reverted=self.after.replace(
            current.PREVIEW_NEW,current.PREVIEW_OLD).replace(
            current.COUNT_NEW,current.COUNT_OLD)
        a="unsigned int raw_rec_update_preview(unsigned int ctx)\n{"
        b="    preview_dirty = 1;\n    return 1;\n}"
        self.assertEqual(self.section(self.before,a,b),
                         self.section(reverted,a,b))
        self.assertIn("int qvfilm_lab_active = QVFIL_LAB_STBY;",self.after)
        self.assertIn("RAW_IS_IDLE",self.after)
        self.assertIn("RAW_PREVIEW_COLOR_HALFRES",self.after)
        self.assertIn('raw_preview_fast_ex(',self.after)
        self.assertIn('qvfilm_lab_stripe_active_v0619 ? qvfilm_lab_y1_v0619 : -1',self.after)
        self.assertIn('qvfilm_lab_stripe_active_v0619 ? qvfilm_lab_y2_v0619 : -1',self.after)

    def test_qvfilm_safe_model_rom_and_raw_gates(self):
        for t in (
            '#define QVFIL_LAB_CAMERA_OK (is_camera("5D3", "*")',
            'get_digic_version() == 5',
            'qvfilm_rom_sig_done_v0616 &&',
            'qvfilm_rom_sig_v0616 == 0x672EEACEU',
            'is_movie_mode() && RAW_IS_IDLE',
            'lv_dispsize == 1',
            'BPP == 10 && raw_info.bits_per_pixel == 14',
            'res_x <= 1600 && res_y > 0 && res_y <= 900',
            'static int qvfilm_preview_lab = 0;',
            'MENU_SET_RINFO("REC: BASE")',
        ):self.assertIn(t,self.after)
        self.assertNotIn("MODULE_CONFIG(qvfilm_preview_lab)",self.after)

    def test_modes_and_reset_on_switch(self):
        s=self.after
        self.assertIn('CHOICES("OFF", "Color STBY", "Stripe 2", "Stripe 3")',s)
        self.assertIn('        .max = 3,\n        .choices = CHOICES',s)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.20")',s)
        self.assertIn('qvfilm_preview_lab == 2 ? 2 : 3',s)
        for t in (
            'qvfilm_preview_lab_draw_count = 0;',
            'qvfilm_preview_lab_last_draw_ms = 0;',
            'qvfilm_lab_avg_draw_ms_v0618 = 0;',
            'qvfilm_lab_avg_period_ms_v0618 = 0;',
            'qvfilm_lab_prev_end_ms_v0618 = 0;',
            'qvfilm_lab_sweep_ema_ms_v0620 = 0;',
            'qvfilm_lab_full_sweeps_v0619 = 0;',
        ):self.assertIn(t,current.PREVIEW_NEW)

    def test_2_and_3_bands_tile_without_gap_or_overlap(self):
        for stripes in (2,3):
            for height in range(12,721):
                bands=[(height*i//stripes,height*(i+1)//stripes)
                       for i in range(stripes)]
                self.assertEqual(bands[0][0],0)
                self.assertEqual(bands[-1][1],height)
                self.assertTrue(all(bands[i][1]==bands[i+1][0]
                                    for i in range(len(bands)-1)))
                self.assertTrue(all(lo<hi for lo,hi in bands))
        for t in (
            'qvfilm_lab_band_v0619 < qvfilm_lab_stripe_count_v0620',
            'height * qvfilm_lab_band_v0619 / qvfilm_lab_stripe_count_v0620',
            'height * (qvfilm_lab_band_v0619 + 1) / qvfilm_lab_stripe_count_v0620',
            'qvfilm_lab_band_v0619 == qvfilm_lab_stripe_count_v0620',
        ):self.assertIn(t,self.after)

    def test_read_only_completion_rate_separate_from_partial_stripe(self):
        s=self.after
        menu=self.section(s,
            "static MENU_UPDATE_FUNC(qvfilm_lab_sweep_rate_update_v0620)",
            "static struct menu_entry qvfilm_hud_menu[]")
        for t in (
            'MENU_SET_NAME("QVFIL Sweep Rate")',
            'MENU_SET_VALUE("AVG:%dms", ms)',
            'MENU_SET_RINFO("Hz:%d.%d"',
            'MENU_SET_VALUE("NO RATE")',
            'NOT synchronized video',
            'static MENU_UPDATE_FUNC(qvfilm_lab_sweep_update_v0619)',
        ):self.assertIn(t,menu)
        for bad in (
            "FIO_","raw_preview_fast_ex(","prop_request_change",
            "task_create(","msleep(","MEM(","firmware_version =",
            "raw_video_enabled =",
        ):self.assertNotIn(bad,menu)
        self.assertIn('.name = "QVFIL Sweep Rate"',s)
        self.assertIn('qvfilm_lab_sweep_ema_ms_v0620',current.COUNT_NEW)

    def test_fails_closed_on_wrong_source_and_double_patch(self):
        with self.assertRaises(ValueError):current.patch("wrong camera code")
        with self.assertRaises(ValueError):current.patch(self.after)

if __name__=="__main__":
    unittest.main(verbosity=2)
