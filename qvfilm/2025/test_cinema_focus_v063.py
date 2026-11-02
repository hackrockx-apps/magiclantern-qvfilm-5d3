#!/usr/bin/env python3
"""QVFIL 0.6.3 exact-2025 safety and presentation checks."""
import sys
import unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_media_engine_v062 as previous
import apply_cinema_focus_v063 as cinema

class CinemaFocusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = HERE / "fixture-2025-mlv_lite.c"
        if not fixture.exists():
            raise unittest.SkipTest("CI provides pinned 2025 upstream fixture")
        cls.source = fixture.read_text(encoding="utf-8")

    def test_version_and_three_existing_hud_modes(self):
        s = cinema.patch(self.source)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.3");', s)
        self.assertIn('.choices = CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema")', s)
        self.assertIn('qvfilm_hud_enabled != 2 && qvfilm_hud_enabled != 3', s)
        self.assertIn('MENU_SET_NAME("QVFIL Media Engine");', s)
        self.assertIn('MENU_SET_NAME("QVFIL Recording Report");', s)
        self.assertIn('.name = "QVFIL Focus Assist"', s)

    def test_larger_values_are_from_actual_camera_state(self):
        s = cinema.patch(self.source)
        a = s.index('static void qvfilm_draw_cinema_overlay(void)')
        b = s.index("/* Display the 'Recording...' icon and status */")
        hud = s[a:b]
        for text in ['lens_info.focal_len', 'lens_info.aperture',
                     'get_current_shutter_reciprocal_x1000()',
                     'lens_info.iso_auto', 'FONT_LARGE', '"%dmm"',
                     '"f/%d.%d"', '"1/%d"', '"ISO%d"',
                     'last_hud_style != qvfilm_hud_enabled']:
            self.assertIn(text, hud)
        self.assertIn('if (mode == 1 && last_mode == 1)', hud)
        self.assertIn('return;', hud)
        self.assertIn('bmp_fill(COLOR_ALMOST_BLACK, 34, 344, 653, 44)', hud)
        self.assertIn('bmp_fill(COLOR_ALMOST_BLACK, 40, 85, 475, 26)', hud)

    def test_peaking_reuses_core_magic_lantern(self):
        s = cinema.patch(self.source)
        p = s[s.index('static MENU_UPDATE_FUNC(qvfilm_focus_assist_update)'):
              s.index('static struct menu_entry qvfilm_hud_menu[] = {')]
        self.assertIn('Focus Peak', p)
        self.assertIn('Global Draw', p)
        self.assertNotIn('draw_zebra_and_focus', p)
        self.assertNotIn('FIO_CreateFile', p)
        self.assertNotIn('sd_overclock', p)

    def test_unchanged_2025_recorder_guard_and_storage(self):
        old = previous.patch(self.source)
        new = cinema.patch(self.source)
        def recorder(s):
            a = s.index('void raw_video_rec_task()')
            b = s.index('static REQUIRES(GuiMainTask)\nvoid raw_start_stop()', a)
            return s[a:b]
        self.assertEqual(recorder(old), recorder(new))
        self.assertIn('qvfilm_last_stop_reason = 1', new)
        self.assertIn('qvfilm_last_stop_reason = 2', new)
        self.assertIn('if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)', new)

    def test_fail_closed_when_wrong_source_or_repatch(self):
        with self.assertRaises(ValueError):
            cinema.patch("not Magic Lantern 2025")
        with self.assertRaises(ValueError):
            cinema.patch(cinema.patch(self.source))

if __name__ == "__main__":
    unittest.main(verbosity=2)
