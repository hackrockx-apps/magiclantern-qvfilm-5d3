#!/usr/bin/env python3
"""Structural tests against the actual 2025 source, not the unrelated 2018 fork."""
import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_qvfilm_patch as qv


class PatchSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = HERE / "fixture-2025-mlv_lite.c"
        if not src.is_file():
            raise unittest.SkipTest("Fixture not provided; run via source-checkout CI")
        cls.source = src.read_text(encoding="utf-8")

    def test_known_release_patches_exactly(self):
        result = qv.patch(self.source)
        self.assertIn('if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)', result)
        self.assertIn('NotifyBox(6000, "QVFIL: Lossless blocked.', result)
        self.assertIn('MENU_SET_WARNING(MENU_WARN_NOT_WORKING,', result)
        self.assertIn('Lossless disabled on 5D3.123', result)
        self.assertIn('if (is_camera("5D3", "*"))', result)
        self.assertIn('menu_add("Movie", raw_video_menu, COUNT(raw_video_menu));', result)
        self.assertIn('menu_add("Movie", qvfilm_hud_menu, COUNT(qvfilm_hud_menu));', result)
        self.assertLess(result.index('menu_add("Movie", qvfilm_hud_menu'),
                        result.index('menu_add("Movie", raw_video_menu'))
        self.assertIn('MENU_SET_RINFO("QVFIL v0.5.4")', result)
        self.assertIn('qvfilm_top_info', result)
        self.assertIn('qvfilm_bottom_info', result)
        self.assertIn('MODULE_CONFIG(qvfilm_hud_enabled)', result)
        self.assertIn('ASSERT(0);', result)  # not silently hiding other memory/encoder failures

    def test_cinema_overlay_uses_actual_raw_bit_depth(self):
        result = qv.patch(self.source)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.5.4")', result)
        self.assertIn('CHOICES("OFF", "Info bars", "Cinema overlay")', result)
        self.assertIn('static void qvfilm_draw_cinema_overlay(void)', result)
        self.assertIn('qvfilm_draw_cinema_overlay();', result)
        self.assertIn('res_x, res_y, BPP,', result)
        self.assertNotIn('res_x, res_y, BPP_D,', result)
        self.assertIn('RAW_IS_RECORDING ? "REC"', result)
        self.assertIn('!liveview_display_idle()', result)
        self.assertIn('START/STOP for RAW.', result)

    def test_cinema_overlay_renders_on_canon_liveview(self):
        result = qv.patch(self.source)
        fn = result[result.index('static void qvfilm_draw_cinema_overlay(void)'):
                    result.index("/* Display the 'Recording...' icon and status */")]
        self.assertIn('get_global_draw_setting()', fn)
        self.assertNotIn('!get_global_draw()', fn)
        self.assertIn('!DISPLAY_IS_ON', fn)
        self.assertIn('!bmp_is_on()', fn)
        self.assertIn('gui_menu_shown()', fn)
        self.assertIn('liveview_display_idle()', fn)
        self.assertIn('BMP_LOCK(', fn)
        self.assertIn('COLOR_ALMOST_BLACK', fn)
        self.assertIn('should_run_polling_action(250', fn)
        self.assertIn('QVFIL CINEMA v0.5.4', fn)
        update = result[result.index('unsigned int raw_rec_polling_cbr('):
                        result.index('static void unhack_liveview_vsync')]
        self.assertLess(update.index('show_recording_status();'),
                        update.index('qvfilm_draw_cinema_overlay();'))
        status = result[result.index('void show_recording_status()'):
                        result.index('unsigned int raw_rec_polling_cbr(')]
        self.assertNotIn('qvfilm_draw_cinema_overlay();', status)

    def test_explicit_cinema_entry_closes_menu_without_fake_recording(self):
        result = qv.patch(self.source)
        self.assertIn('static MENU_SELECT_FUNC(qvfilm_enter_cinema)', result)
        self.assertIn('gui_stop_menu();', result)
        self.assertIn('lens_display_set_dirty();', result)
        self.assertIn('.name = "QVFIL Enter Cinema"', result)
        self.assertIn('MENU_SET_RINFO("SET / LIVEVIEW")', result)
        self.assertLess(result.index('.name = "QVFIL Enter Cinema"'),
                        result.index('.name = "QVFIL Cinema HUD"'))
        self.assertIn('START/STOP for RAW.', result)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.5.4")', result)
        self.assertNotIn('fake_simple_button(BGMT_REC)', result)

    def test_patching_twice_fails_closed(self):
        first = qv.patch(self.source)
        with self.assertRaises(ValueError):
            qv.patch(first)

    def test_other_source_tree_fails_closed(self):
        with self.assertRaises(ValueError):
            qv.patch("unrelated Magic Lantern source")


if __name__ == "__main__":
    unittest.main(verbosity=2)
