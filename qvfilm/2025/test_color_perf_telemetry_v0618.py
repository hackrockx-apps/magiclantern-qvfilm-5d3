#!/usr/bin/env python3
"""Pinned ML2025 regression for QVFIL v0.6.18 Color Lab telemetry."""
from pathlib import Path
import sys
import unittest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import apply_rom_verified_color_v0617 as previous
import apply_color_perf_telemetry_v0618 as current

class ColorPerfV0618(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=HERE/"fixture-2025-mlv_lite.c"
        if not fixture.exists():
            raise unittest.SkipTest("Pinned upstream fixture injected by CI")
        original=fixture.read_text(encoding="utf-8")
        cls.before=previous.patch(original)
        cls.after=current.patch(original)

    @staticmethod
    def section(s,a,b):
        start=s.index(a)
        end=s.index(b,start)
        return s[start:end]

    def test_recorder_and_compressor_unchanged(self):
        for a,b in (
            ("void raw_video_rec_task()\n{",
             "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            ("static void compress_task()\n{",
             "static REQUIRES(LiveViewTask) FAST\nvoid process_frame("),
        ):
            self.assertEqual(self.section(self.before,a,b),
                             self.section(self.after,a,b))

    def test_raw_display_filter_unmodified(self):
        start="unsigned int raw_rec_update_preview(unsigned int ctx)\n{"
        finish="    preview_dirty = 1;\n    return 1;\n}"
        def body(src):
            a=src.index(start)
            b=src.index(finish,a)+len(finish)
            return src[a:b]
        self.assertEqual(body(self.before),body(self.after))

    def test_rom_and_stby_guards_strict(self):
        for t in (
            '#define QVFIL_LAB_CAMERA_OK (is_camera("5D3", "*")',
            'get_digic_version() == 5',
            'qvfilm_rom_sig_done_v0616 &&',
            'qvfilm_rom_sig_v0616 == 0x672EEACEU',
            'QVFIL_LAB_CAMERA_OK && raw_video_enabled && lv',
            'is_movie_mode() && RAW_IS_IDLE',
            'lv_dispsize == 1',
            'res_x <= 1600 && res_y > 0 && res_y <= 900',
            'BPP == 10 && raw_info.bits_per_pixel == 14',
            'static int qvfilm_preview_lab = 0;',
            'if (RAW_IS_RECORDING)',
            'MENU_SET_RINFO("REC: BASE")',
            'if (!entry->selected && !qvfilm_rom_sig_done_v0616)',
        ):
            self.assertIn(t,self.after)
        self.assertNotIn('MODULE_CONFIG(qvfilm_preview_lab)',self.after)

    def test_f_counter_format_fixed_and_clamped(self):
        src=self.after
        self.assertNotIn('MENU_SET_RINFO("F:%u',src)
        self.assertIn('MENU_SET_RINFO("F:%d %dms"',src)
        self.assertIn('qvfilm_preview_lab_draw_count > 2147483647U',src)
        self.assertIn('qvfilm_preview_lab_last_draw_ms);',src)

    def test_perf_telemetry_is_only_after_stby_draw(self):
        src=self.after
        func=self.section(src,
            "unsigned int raw_rec_update_preview(unsigned int ctx)\n{",
            "    give_semaphore(settings_sem);")
        self.assertIn("raw_preview_fast_ex(",func)
        self.assertIn("if (qvfilm_lab_active)",func)
        self.assertIn("qvfilm_lab_avg_draw_ms_v0618",func)
        self.assertIn("qvfilm_lab_avg_period_ms_v0618",func)
        self.assertIn("qvfilm_preview_lab_draw_count++",func)
        self.assertLess(func.index("raw_preview_fast_ex("),
                        func.index("qvfilm_lab_avg_period_ms_v0618"))
        # Original conversion algorithm still used and selected in the same branch.
        self.assertEqual(src.count('RAW_PREVIEW_COLOR_HALFRES'),
                         self.before.count('RAW_PREVIEW_COLOR_HALFRES'))
        self.assertIn('static unsigned int qvfilm_lab_prev_end_ms_v0618 = 0;',src)
        self.assertIn('static volatile int qvfilm_lab_avg_draw_ms_v0618 = 0;',src)

    def test_perf_menu_is_read_only_and_reports_not_lcd_fps(self):
        src=self.after
        menu=self.section(src,
            "static MENU_UPDATE_FUNC(qvfilm_lab_perf_update_v0618)",
            "static struct menu_entry qvfilm_hud_menu[]")
        for token in (
            'MENU_SET_NAME("QVFIL Color Perf")',
            'MENU_SET_VALUE("AVG:%dms"',
            'MENU_SET_RINFO("Hz:%d.%d"',
            'MENU_SET_RINFO("Hz:WAIT")',
            'MENU_SET_VALUE("NO DRAW")',
            'MENU_SET_VALUE("OFF")',
            'Neither is measured LCD FPS.',
        ):self.assertIn(token,menu)
        for term in ("FIO_","prop_request_change","task_create(", "msleep(",
                     "raw_preview_fast_ex(", "firmware_version =",
                     "raw_video_enabled =","raw_rec_start"):
            self.assertNotIn(term,menu)
        self.assertIn('.name = "QVFIL Color Perf"',src)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.18")',src)

    def test_safe_refuse_mismatched_patch(self):
        with self.assertRaises(ValueError):
            current.patch("not pinned ML source")
        with self.assertRaises(ValueError):
            current.patch(self.after)

if __name__=="__main__":
    unittest.main(verbosity=2)
