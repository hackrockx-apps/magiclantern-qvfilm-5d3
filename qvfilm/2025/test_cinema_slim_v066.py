#!/usr/bin/env python3
"""QVFIL 0.6.6 exact-2025 slim HUD regression tests."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_cinema_clean_v065 as previous
import apply_cinema_slim_v066 as current


class CinemaSlimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f = HERE / "fixture-2025-mlv_lite.c"
        if not f.exists():
            raise unittest.SkipTest("Pinned upstream fixture supplied by GitHub CI")
        cls.base = f.read_text(encoding="utf-8")
        cls.old = previous.patch(cls.base)
        cls.new = current.patch(cls.base)

    def test_recorder_body_is_byte_identical(self):
        def recorder(s):
            a = s.index("void raw_video_rec_task()")
            b = s.index("static REQUIRES(GuiMainTask)\nvoid raw_start_stop()", a)
            return s[a:b]
        self.assertEqual(recorder(self.old), recorder(self.new))

    def test_previous_modes_and_focus_peak_untouched(self):
        s = self.new
        self.assertIn(
            'CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema", "Cinema clean", "Cinema slim")',
            s,
        )
        for value in [
            'if (qvfilm_hud_enabled == 5)',
            'else if (qvfilm_hud_enabled == 4)',
            'else if (qvfilm_hud_enabled == 3)',
            'if (mode == 1 && last_mode == 1)',
            '"Use Overlay > Focus Peak ON; switch lens to MF; tune Threshold."',
            '.name = "QVFIL Shoot Check"',
            '.name = "QVFIL Media Engine"',
            '.name = "QVFIL Recording Report"',
            '.name = "QVFIL Focus Assist"',
            'MENU_SET_RINFO("QVFIL v0.6.6")',
            'qvfilm_hud_enabled != 5',
        ]:
            self.assertIn(value, s)

    def test_slim_panel_only_one_bitmap_background(self):
        s = self.new
        start = s.index('    if (qvfilm_hud_enabled == 5)\n    {')
        end = s.index('    else if (qvfilm_hud_enabled == 4)', start)
        slim = s[start:end]
        self.assertIn('bmp_fill(COLOR_ALMOST_BLACK, 35, 352, 526, 30)', slim)
        self.assertEqual(slim.count('bmp_fill('), 1)
        for pos in (
            '42, 356, "%dmm"',
            '179, 356, "f/%d.%d"',
            '312, 356, "1/%d"',
            '420, 356, "ISO%d"',
        ):
            self.assertIn(pos, slim)
        for forbidden in (
            '"QVFIL %s  %d FPS"', 'FIO_CreateFile',
            'FIO_WriteFile', 'raw_edmac', 'raw_video_rec_task',
            'focus_peaking', 'draw_zebra_and_focus', 'sd_overclock',
        ):
            self.assertNotIn(forbidden, slim)
        self.assertIn('FONT(FONT_MED, COLOR_WHITE, COLOR_ALMOST_BLACK)', slim)

    def test_safety_guard_unchanged(self):
        for token in (
            'qvfilm_last_stop_reason = 1',
            'qvfilm_last_stop_reason = 2',
            'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
            'MENU_SET_RINFO("CF M:%d%%", margin)',
        ):
            self.assertIn(token, self.new)
        self.assertIn('if (mode == 1 && last_mode == 1)', self.new)

    def test_strict_anchors(self):
        with self.assertRaises(ValueError):
            current.patch("not Magic Lantern 2025")
        with self.assertRaises(ValueError):
            current.patch(self.new)


if __name__ == "__main__":
    unittest.main(verbosity=2)
