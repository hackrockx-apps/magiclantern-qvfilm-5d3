#!/usr/bin/env python3
"""Regression suite for experimental QVFIL v0.6.10 STBY preview lab."""
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_preview_guard_v069 as prior
import apply_color_preview_lab_v0610 as current


class PreviewLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = HERE / "fixture-2025-mlv_lite.c"
        if not path.exists():
            raise unittest.SkipTest("Pinned upstream fixture injected by CI")
        original = path.read_text(encoding="utf-8")
        cls.prior = prior.patch(original)
        cls.new = current.patch(original)

    def segment(self, s, begin, end):
        a = s.index(begin)
        b = s.index(end, a)
        return s[a:b]

    def test_recorder_and_compressor_exactly_unchanged(self):
        self.assertEqual(
            self.segment(self.prior, "void raw_video_rec_task()\n{",
                         "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            self.segment(self.new, "void raw_video_rec_task()\n{",
                         "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()")
        )
        self.assertEqual(
            self.segment(self.prior, "static void compress_task()\n{",
                         "static REQUIRES(LiveViewTask) FAST\nvoid process_frame("),
            self.segment(self.new, "static void compress_task()\n{",
                         "static REQUIRES(LiveViewTask) FAST\nvoid process_frame(")
        )

    def test_5d3_only_disabled_default_not_persisted(self):
        s = self.new
        self.assertIn('static int qvfilm_preview_lab = 0;', s)
        self.assertNotIn('MODULE_CONFIG(qvfilm_preview_lab)', s)
        self.assertIn('is_camera("5D3", "1.2.3") && RAW_IS_IDLE && lv_dispsize == 1', s)
        self.assertIn('(PREVIEW_AUTO || PREVIEW_CANON)', s)
        self.assertIn('res_x > 0 && res_x <= 1600 && res_y > 0 && res_y <= 900', s)
        self.assertIn('BPP == 10 && raw_info.bits_per_pixel == 14', s)

    def test_focus_and_original_preview_modes_retained(self):
        src = self.new
        a = src.index("static int raw_rec_should_preview(void)")
        b = src.index("unsigned int raw_rec_update_preview(unsigned int ctx)", a)
        code = src[a:b]
        self.assertLess(code.index("if (lv_dispsize == 10)"), code.index("if (QVFIL_LAB_STBY)"))
        self.assertLess(code.index("if (autofocusing)"), code.index("if (QVFIL_LAB_STBY)"))
        self.assertIn("if (PREVIEW_AUTO)", code)
        self.assertIn("else if (PREVIEW_CANON)", code)
        self.assertIn("else if (PREVIEW_ML)", code)
        self.assertIn("else if (PREVIEW_HACKED)", code)

    def test_color_and_layout_expansion_only_in_stby(self):
        s = self.new
        a = s.index("unsigned int raw_rec_update_preview(unsigned int ctx)")
        b = s.index("static struct lvinfo_item info_items[]", a)
        new = s[a:b]
        for phrase in (
            "int qvfilm_lab_active = QVFIL_LAB_STBY;",
            "qvfilm_lab_active ? 0 : 1",
            "RAW_PREVIEW_COLOR_HALFRES",
            "RAW_PREVIEW_GRAY_ULTRA_FAST",
            "qvfilm_lab_draw_ms < 40) ? 20",
            "qvfilm_lab_draw_ms < 80) ? 35",
            ": 50",
            "(need_for_speed)",
            "? ((queued_frames > valid_slot_count / 2) ? 1000 : 500)",
            "qvfilm_preview_lab_last_draw_ms = qvfilm_lab_draw_ms",
        ):
            self.assertIn(phrase, new)
        for forbidden in (
            "OUTPUT_COMPRESSION =", "buffer_full =", "raw_recording_state =",
            "FIO_CreateFile", "FIO_WriteFile", "frame_fake_edmac_check",
            "shrink_slot", "TTL_Start(", "EngDrvOut(", "raw_lv_redirect_edmac",
        ):
            self.assertNotIn(forbidden, new)

    def test_known_good_fallback_restored_when_off_or_recording(self):
        s = self.new
        self.assertIn('static int qvfilm_preview_lab = 0;', s)
        self.assertIn('RAW_IS_IDLE', s)
        self.assertIn('raw_set_preview_rect(skip_x, skip_y, res_x, res_y,\n                         qvfilm_lab_active ? 0 : 1)', s)
        self.assertIn('int qvfilm_lab_start_ms = qvfilm_lab_active ? get_ms_clock() : 0;', s)
        self.assertIn('qvfilm_lab_active && qvfilm_lab_draw_ms < 40', s)
        self.assertIn('qvfilm_lab_active && qvfilm_lab_draw_ms < 80', s)

    def test_menu_and_prior_protections_retained(self):
        s = self.new
        for phrase in (
            '.name = "QVFIL Color Preview Lab"',
            '.priv = &qvfilm_preview_lab',
            '.choices = CHOICES("OFF", "Color large STBY")',
            'MENU_SET_RINFO("SAFE OFF")',
            'MENU_SET_RINFO("REC: BASE")',
            'MENU_SET_RINFO("QVFIL v0.6.10")',
            '.name = "QVFIL Preview Guide"',
            '.name = "QVFIL Lossless Diag"',
            '.name = "QVFIL LJ Error Guide"',
            '.name = "QVFIL Focus Assist"',
            '.name = "QVFIL Media Engine"',
            '.name = "QVFIL Recording Report"',
            'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
        ):
            self.assertIn(phrase, s)

    def test_wrong_upstream_or_double_patch_fails_closed(self):
        with self.assertRaises(ValueError):
            current.patch("not the pinned upstream")
        with self.assertRaises(ValueError):
            current.patch(self.new)


if __name__ == "__main__":
    unittest.main(verbosity=2)
