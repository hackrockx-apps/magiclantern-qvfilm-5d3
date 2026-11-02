#!/usr/bin/env python3
"""QVFIL 0.6.4 conservative patch regression tests on pinned ML 2025 source."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_cinema_focus_v063 as previous
import apply_safe_preflight_v064 as current


class SafePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = HERE / "fixture-2025-mlv_lite.c"
        if not fixture.exists():
            raise unittest.SkipTest("Requires exact upstream 2025 fixture from CI")
        cls.source = fixture.read_text(encoding="utf-8")
        cls.old = previous.patch(cls.source)
        cls.new = current.patch(cls.source)

    def test_unchanged_raw_recorder(self):
        def recorder(s):
            a = s.index("void raw_video_rec_task()")
            b = s.index("static REQUIRES(GuiMainTask)\nvoid raw_start_stop()", a)
            return s[a:b]
        self.assertEqual(recorder(self.old), recorder(self.new))

    def test_preserve_existing_hud_and_focus_menu(self):
        for token in (
            '.choices = CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema")',
            '.name = "QVFIL Focus Assist"',
            '.name = "QVFIL Media Engine"',
            '.name = "QVFIL Recording Report"',
            'qvfilm_hud_enabled != 2 && qvfilm_hud_enabled != 3',
            'if (mode == 1 && last_mode == 1)',
            'FONT_LARGE',
            'qvfilm_last_stop_reason = 1',
            'qvfilm_last_stop_reason = 2',
            'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
        ):
            self.assertIn(token, self.new)

    def test_preflight_is_menu_only_and_protects_uncertain_data(self):
        a = self.new.index("static MENU_UPDATE_FUNC(qvfilm_shoot_check_update)")
        b = self.new.index("static struct menu_entry qvfilm_hud_menu[]", a)
        section = self.new[a:b]
        for token in (
            'MENU_SET_NAME("QVFIL Shoot Check")',
            'qvfilm_media_demand_x10()',
            'qvfilm_media_writer_x10',
            'qvfilm_media_duration_ms < 30000',
            'qvfilm_last_stop_reason == 1',
            'qvfilm_last_stop_reason == 2',
            'OUTPUT_COMPRESSION',
            'MENU_SET_RINFO("CF M:%d%%", margin)',
            'estimated CF I/O margin is under 20',
        ):
            self.assertIn(token.lower(), section.lower())
        for forbidden in (
            "FIO_WriteFile", "FIO_CreateFile", "sd_overclock",
            "BMP_LOCK", "raw_video_rec_task()", "raw_edmac",
            "NotifyBox", "set_shutter", "set_iso",
        ):
            self.assertNotIn(forbidden, section)

    def test_hud_off_guidance_and_menu_formatter(self):
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.4")', self.new)
        self.assertIn('HUD is OFF (Draws:0 / Gate:1 is normal)', self.new)
        self.assertIn('Select Large cinema, enable Global Draw', self.new)
        self.assertIn('Large cinema updates in STBY', self.new)
        self.assertIn('.name = "QVFIL Shoot Check"', self.new)
        self.assertNotIn('MENU_SET_RINFO("QVFIL v0.6.3")', self.new)

    def test_strict_source_anchors(self):
        with self.assertRaises(ValueError):
            current.patch("not the exact 2025 ML source")
        with self.assertRaises(ValueError):
            current.patch(self.new)


if __name__ == "__main__":
    unittest.main(verbosity=2)
