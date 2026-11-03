#!/usr/bin/env python3
"""Pinned-source regression for QVFIL v0.6.12 preview telemetry."""
import unittest
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import apply_color_preview_lab_v0611 as previous
import apply_preview_telemetry_v0612 as current

class PreviewTelemetryV0612(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=HERE/"fixture-2025-mlv_lite.c"
        if not f.exists():
            raise unittest.SkipTest("Fixture supplied by exact-source CI workflow")
        src=f.read_text(encoding="utf-8")
        cls.before=previous.patch(src)
        cls.after=current.patch(src)

    @staticmethod
    def block(src,start,stop):
        i=src.index(start)
        j=src.index(stop,i)
        return src[i:j]

    def test_raw_recorder_and_compressor_unchanged(self):
        for start,end in (
            ("void raw_video_rec_task()\n{",
             "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            ("static void compress_task()\n{",
             "static REQUIRES(LiveViewTask) FAST\nvoid process_frame("),
        ):
            self.assertEqual(self.block(self.before,start,end),
                             self.block(self.after,start,end))

    def test_draw_count_only_after_existing_color_render(self):
        render="raw_preview_fast_ex(\n"
        src=self.after
        a=src.index(render)
        b=src.index("    give_semaphore(settings_sem);",a)
        span=src[a:b]
        self.assertIn("qvfilm_preview_lab_draw_count++;",span)
        self.assertIn("if (qvfilm_lab_active)",span)
        self.assertLess(span.index("raw_preview_fast_ex("),
                        span.index("qvfilm_preview_lab_draw_count++;"))
        # Only the counter block is new within the display callback.
        old=self.block(self.before,
              "    int qvfilm_lab_start_ms = qvfilm_lab_active ? get_ms_clock() : 0;",
              "    give_semaphore(settings_sem);")
        new=self.block(self.after,
              "    int qvfilm_lab_start_ms = qvfilm_lab_active ? get_ms_clock() : 0;",
              "    give_semaphore(settings_sem);")
        injection_before="""    if (qvfilm_lab_active)
        qvfilm_preview_lab_last_draw_ms = qvfilm_lab_draw_ms;"""
        injection_after="""    if (qvfilm_lab_active)
    {
        qvfilm_preview_lab_last_draw_ms = qvfilm_lab_draw_ms;
        qvfilm_preview_lab_draw_count++;
    }"""
        self.assertEqual(old,new.replace(injection_after,injection_before))

    def test_truthful_status_has_armed_and_frame_count(self):
        src=self.after
        status=self.block(src,
            "static MENU_UPDATE_FUNC(qvfilm_preview_lab_update)",
            "static struct menu_entry qvfilm_hud_menu[]")
        self.assertIn('MENU_SET_RINFO("ARMED 0F")',status)
        self.assertIn('MENU_SET_RINFO("F:%u %dms"',status)
        self.assertIn("qvfilm_preview_lab_draw_count = 0;",status)
        self.assertIn('MENU_SET_RINFO("SAFE OFF")',status)
        self.assertIn('MENU_SET_RINFO("REC: BASE")',status)
        self.assertNotIn('MENU_SET_RINFO("DRAW %dms"',status)
        self.assertNotIn('MENU_SET_RINFO("STBY: N/A")',status)

    def test_gates_and_default_off(self):
        src=self.after
        self.assertIn("static int qvfilm_preview_lab = 0;",src)
        self.assertIn("static volatile unsigned int qvfilm_preview_lab_draw_count = 0;",src)
        self.assertNotIn("MODULE_CONFIG(qvfilm_preview_lab)",src)
        for item in ('is_camera("5D3", "1.2.3")','RAW_IS_IDLE',
                     'lv_dispsize == 1','BPP == 10',
                     'raw_info.bits_per_pixel == 14',
                     'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
                     '.name = "QVFIL Color Preview Lab"',
                     '.name = "QVFIL Preview Guide"',
                     '.name = "QVFIL Lossless Diag"',
                     'MENU_SET_RINFO("QVFIL v0.6.12")'):
            self.assertIn(item,src)

    def test_strict_patch_wrong_source_and_double_apply_fail(self):
        with self.assertRaises(ValueError):
            current.patch("bad source")
        with self.assertRaises(ValueError):
            current.patch(self.after)

if __name__=="__main__":
    unittest.main(verbosity=2)
