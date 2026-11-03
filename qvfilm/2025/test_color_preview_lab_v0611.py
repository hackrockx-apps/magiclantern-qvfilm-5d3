#!/usr/bin/env python3
"""Regression tests for QVFIL v0.6.11 STBY Color Preview gate fix."""
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import apply_color_preview_lab_v0610 as v0610
import apply_color_preview_lab_v0611 as v0611


class PreviewLabV0611Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = HERE / "fixture-2025-mlv_lite.c"
        if not fixture.exists():
            raise unittest.SkipTest("Pinned upstream fixture injected by CI")
        source = fixture.read_text(encoding="utf-8")
        cls.old = v0610.patch(source)
        cls.new = v0611.patch(source)

    @staticmethod
    def segment(source, begin, end):
        a = source.index(begin)
        b = source.index(end, a)
        return source[a:b]

    def test_recorder_and_compressor_are_byte_identical(self):
        for begin, end in (
            ("void raw_video_rec_task()\n{",
             "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            ("static void compress_task()\n{",
             "static REQUIRES(LiveViewTask) FAST\nvoid process_frame("),
        ):
            self.assertEqual(
                self.segment(self.old, begin, end),
                self.segment(self.new, begin, end)
            )

    def test_preview_renderer_and_update_pacing_are_byte_identical(self):
        begin = "unsigned int raw_rec_update_preview(unsigned int ctx)\n{"
        tail = "    preview_dirty = 1;\n    return 1;\n}"

        def preview_body(source):
            a = source.index(begin)
            b = source.index(tail, a) + len(tail)
            return source[a:b]

        self.assertEqual(preview_body(self.old), preview_body(self.new))

    def test_preview_mode_is_not_a_false_blocker(self):
        macro = next(
            line for line in self.new.splitlines()
            if line.startswith("#define QVFIL_LAB_STBY ")
        )
        self.assertIn('is_camera("5D3", "1.2.3")', macro)
        self.assertIn("raw_video_enabled && lv && is_movie_mode()", macro)
        self.assertIn("RAW_IS_IDLE && lv_dispsize == 1", macro)
        self.assertIn("BPP == 10 && raw_info.bits_per_pixel == 14", macro)
        self.assertNotIn("PREVIEW_AUTO", macro)
        self.assertNotIn("PREVIEW_CANON", macro)

        a = self.new.index("static int raw_rec_should_preview(void)")
        b = self.new.index("unsigned int raw_rec_update_preview(unsigned int ctx)", a)
        body = self.new[a:b]
        self.assertLess(body.index("if (autofocusing)"), body.index("if (QVFIL_LAB_STBY)"))
        self.assertLess(body.index("if (QVFIL_LAB_STBY)"), body.index("if (PREVIEW_AUTO)"))
        self.assertIn("if (QVFIL_LAB_STBY)\n        return 1;", body)

    def test_menu_reports_specific_remaining_blockers(self):
        a = self.new.index("static MENU_UPDATE_FUNC(qvfilm_preview_lab_update)")
        b = self.new.index("static struct menu_entry qvfilm_hud_menu[]", a)
        status = self.new[a:b]
        for token in (
            'MENU_SET_RINFO("SAFE OFF")',
            'MENU_SET_RINFO("5D3.123 ONLY")',
            'MENU_SET_RINFO("REC: BASE")',
            'MENU_SET_RINFO("RAW BUSY")',
            'MENU_SET_RINFO("RAW OFF")',
            'MENU_SET_RINFO("MOVIE LV")',
            'MENU_SET_RINFO("SET 1X LV")',
            'MENU_SET_RINFO("NO RAW SIZE")',
            'MENU_SET_RINFO("LOWER RES")',
            'MENU_SET_RINFO("SET 10-BIT")',
            'MENU_SET_RINFO("RAW INFO WAIT")',
            'MENU_SET_RINFO("DRAW %dms"',
            'MENU_SET_RINFO("CHECK GATE")',
        ):
            self.assertIn(token, status)
        self.assertNotIn("STBY: N/A", status)

    def test_lab_stays_opt_in_and_does_not_persist(self):
        self.assertIn("static int qvfilm_preview_lab = 0;", self.new)
        self.assertNotIn("MODULE_CONFIG(qvfilm_preview_lab)", self.new)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.11")', self.new)
        self.assertIn(
            '.help2 = "Preview choice is overridden only when Lab is ready; RAW REC stays upstream."',
            self.new
        )

    def test_prior_protections_remain(self):
        for token in (
            'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
            'Lossless RAW blocked on 5D3.123',
            '.name = "QVFIL Lossless Diag"',
            '.name = "QVFIL LJ Error Guide"',
            '.name = "QVFIL Focus Assist"',
            '.name = "QVFIL Media Engine"',
            '.name = "QVFIL Recording Report"',
        ):
            self.assertIn(token, self.new)

    def test_wrong_upstream_and_double_patch_fail_closed(self):
        with self.assertRaises(ValueError):
            v0611.patch("not the pinned upstream source")
        with self.assertRaises(ValueError):
            v0611.patch(self.new)


if __name__ == "__main__":
    unittest.main(verbosity=2)
