#!/usr/bin/env python3
"""Static regression gates for QVFIL Cinema HUD port to the Danne/Arnaud 4K source."""
import unittest
from pathlib import Path
R = Path(__file__).resolve().parents[2]
HUD = (R / "modules/mlv_lite/qvfilm_4k_ui.inc").read_text(encoding="utf-8")
RAW = (R / "modules/mlv_lite/mlv_lite.c").read_text(encoding="utf-8")
CROP = (R / "modules/crop_rec/crop_rec.c").read_text(encoding="utf-8")
CORE = (R / "src/module.c").read_text(encoding="utf-8")

class HUDPortTests(unittest.TestCase):
    def test_consolidated_build_and_ui_are_present(self):
        self.assertIn('#include "qvfilm_4k_ui.inc"', RAW)
        self.assertIn('qvfilm_register_menu();', RAW)
        self.assertIn('qvfilm_4k_draw_hud();', RAW)
        self.assertIn('menu_add("QVFIL", qvfilm_menu, COUNT(qvfilm_menu))', HUD)
        self.assertIn('menu_add("Movie", qvfilm_4k_hud_menu', HUD)

    def test_opt_in_hud_and_5d3_gate(self):
        self.assertIn('static int qvfilm_4k_hud_mode = 0;', HUD)
        self.assertIn('if (cam_5d3_123)', HUD)
        self.assertIn('get_global_draw_setting()', HUD)
        self.assertIn('BMP_LOCK(', HUD)
        self.assertIn('RAW_IS_RECORDING', HUD)
        self.assertIn('500', HUD)
        self.assertIn('"Large cinema"', HUD)

    def test_no_hud_sensor_or_writer_modification(self):
        banned = ('edmac_', 'shamem_write', 'crop_preset_index =',
                  'raw_video_enabled =', 'card_spanning =', 'output_format =',
                  'FIO_WriteFile', 'raw_preview_fast_ex2(', 'bmp_vram')
        for token in banned:
            with self.subTest(token=token):
                self.assertNotIn(token, HUD)
        self.assertIn('CROP_PRESET_UHD', CROP)
        self.assertIn('raw_preview_fast_ex2(', RAW)
        self.assertIn('CONFIG_INT("raw.video.enabled", raw_video_enabled, 0);', RAW)

    def test_capture_modules_remain_opt_in(self):
        self.assertIn('char *core_modules[] = {"mlv_play", "mlv_snd"', CORE)
        self.assertNotIn('char *core_modules[] = {"mlv_lite", "crop_rec"', CORE)

if __name__ == "__main__":
    unittest.main(verbosity=2)
