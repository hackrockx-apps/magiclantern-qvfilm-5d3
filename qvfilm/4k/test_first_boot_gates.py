#!/usr/bin/env python3
"""Static fail-closed first-boot gates for the 5D3.123 4K engineering pilot.

These checks do not run a camera, validate its ROM, or approve installation.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CROP = (ROOT / "modules/crop_rec/crop_rec.c").read_text(encoding="utf-8")
RAW = (ROOT / "modules/mlv_lite/mlv_lite.c").read_text(encoding="utf-8")
PACK = (ROOT / "qvfilm/4k/package_test_card.py").read_text(encoding="utf-8")

class FirstBootSafetyGates(unittest.TestCase):
    def test_crop_is_off_by_default(self):
        self.assertIn('CONFIG_INT("crop.preset", crop_preset_index, 0);', CROP)

    def test_recorder_and_aggressive_features_off(self):
        for anchor in (
            'CONFIG_INT("raw.video.enabled", raw_video_enabled, 0);',
            'CONFIG_INT("raw.card_spanning", card_spanning, 0);',
            'CONFIG_INT("raw.CropRecPreview", prevmode, 0);',
            'CONFIG_INT("raw.use.srm.memory", use_srm_memory, 0);',
            'CONFIG_INT("raw.small.hacks", small_hacks, 0);',
            'CONFIG_INT("raw.more.hacks", more_hacks, 0);',
            'CONFIG_INT("raw.one.more.hack", one_more_hack, 0);',
            'CONFIG_INT("raw.output_format", output_format, 2);',
        ):
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, RAW)

    def test_no_legacy_binaries_in_packaging(self):
        self.assertIn('"camera_installation_approved":False', PACK)
        self.assertIn('"CARD_ROOT/autoexec.bin"', PACK)
        self.assertIn('"modules/mlv_lite/mlv_lite.mo"', PACK)
        self.assertIn('"modules/crop_rec/crop_rec.mo"', PACK)
        self.assertNotIn('"QVFILL_2025_MLV_LITE.MO": "CARD_ROOT/', PACK)

    def test_testcard_has_no_firmware_fir_deployment(self):
        self.assertIn('if "autoexec.bin" in names or "ML-SETUP.FIR" in names:', PACK)

if __name__ == "__main__":
    unittest.main(verbosity=2)
