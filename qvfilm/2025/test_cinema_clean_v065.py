#!/usr/bin/env python3
"""QVFIL v0.6.5 exact-2025, low-risk HUD and focus navigation tests."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_safe_preflight_v064 as previous
import apply_cinema_clean_v065 as current


class CleanOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = HERE / "fixture-2025-mlv_lite.c"
        if not fixture.exists():
            raise unittest.SkipTest("Requires pinned Magic Lantern 2025 fixture")
        cls.source = fixture.read_text(encoding="utf-8")
        cls.old = previous.patch(cls.source)
        cls.new = current.patch(cls.source)

    def test_byte_identical_raw_recorder(self):
        def recorder(s):
            a = s.index("void raw_video_rec_task()")
            b = s.index("static REQUIRES(GuiMainTask)\nvoid raw_start_stop()", a)
            return s[a:b]
        self.assertEqual(recorder(self.old), recorder(self.new))

    def test_all_previous_modes_preserved(self):
        s = self.new
        self.assertIn('.max = 4', s)
        self.assertIn(
            'CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema", "Cinema clean")', s
        )
        for token in (
            'if (qvfilm_hud_enabled == 4)',
            'else if (qvfilm_hud_enabled == 3)',
            '"QVFIL %s  %d FPS"',
            'if (mode == 1 && last_mode == 1)',
            '.name = "QVFIL Shoot Check"',
            '.name = "QVFIL Media Engine"',
            '.name = "QVFIL Recording Report"',
            '.name = "QVFIL Focus Assist"',
            'MENU_SET_RINFO("QVFIL v0.6.5")',
            'qvfilm_hud_enabled != 4',
        ):
            self.assertIn(token, s)

    def test_clean_panel_is_small_and_reuses_existing_state(self):
        s = self.new
        begin = s.index('    if (qvfilm_hud_enabled == 4)\n    {')
        end = s.index('    else if (qvfilm_hud_enabled == 3)', begin)
        panel = s[begin:end]
        for token in (
            'bmp_fill(COLOR_ALMOST_BLACK, 35, 312, 490, 70)',
            '44, 319, "%dmm"',
            '278, 319, "f/%d.%d"',
            '44, 351, "1/%d"',
            '278, 351, "ISO%d"',
            '"QVFIL %s  %d FPS"',
        ):
            self.assertIn(token, panel)
        for forbidden in (
            'FIO_CreateFile', 'FIO_WriteFile',
            'raw_video_rec_task', 'raw_edmac',
            'sd_overclock', 'set_iso', 'set_shutter',
            'draw_zebra_and_focus', 'focus_peaking',
        ):
            self.assertNotIn(forbidden, panel)

    def test_focus_path_is_overlay_not_focus_tab(self):
        s = self.new
        self.assertIn('"Use Overlay > Focus Peak ON; switch lens to MF; tune Threshold."', s)
        self.assertIn('.help2 = "Overlay > Focus Peak ON; set MF.', s)
        self.assertIn('"Global Draw OFF. Use Overlay > Global Draw before Focus Peak."', s)
        self.assertNotIn('Focus tab > Focus Peak', s)
        self.assertNotIn('Focus > Focus Peak', s)
        # The peaking core is intentionally unchanged, no new algorithm.
        self.assertIn('Core ML peaking is used; no QVFIL pixel processing.', s)

    def test_old_stop_guards_and_menu_telemetry_intact(self):
        for token in (
            'qvfilm_last_stop_reason = 1',
            'qvfilm_last_stop_reason = 2',
            'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
            'qvfilm_media_writer_x10',
            'MENU_SET_RINFO("CF M:%d%%", margin)',
        ):
            self.assertIn(token, self.new)
        self.assertEqual(
            self.old[self.old.index('static MENU_UPDATE_FUNC(qvfilm_shoot_check_update)'):
                     self.old.index('static struct menu_entry qvfilm_hud_menu[]')],
            self.new[self.new.index('static MENU_UPDATE_FUNC(qvfilm_shoot_check_update)'):
                     self.new.index('static struct menu_entry qvfilm_hud_menu[]')]
        )

    def test_fail_closed_on_wrong_upstream_and_reapply(self):
        with self.assertRaises(ValueError):
            current.patch("not Magic Lantern 2025")
        with self.assertRaises(ValueError):
            current.patch(self.new)


if __name__ == "__main__":
    unittest.main(verbosity=2)
