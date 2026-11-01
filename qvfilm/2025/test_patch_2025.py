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
        self.assertIn('if (cam_5d3_123 && OUTPUT_COMPRESSION)', result)
        self.assertIn('NotifyBox(6000, "QVFIL: Lossless blocked.', result)
        self.assertIn('if (cam_5d3_123)', result)
        self.assertIn('menu_add("Movie", raw_video_menu, COUNT(raw_video_menu));', result)
        self.assertIn('menu_add("Movie", qvfilm_hud_menu, COUNT(qvfilm_hud_menu));', result)
        self.assertIn('qvfilm_top_info', result)
        self.assertIn('qvfilm_bottom_info', result)
        self.assertIn('MODULE_CONFIG(qvfilm_hud_enabled)', result)
        self.assertIn('ASSERT(0);', result)  # not silently hiding other memory/encoder failures

    def test_patching_twice_fails_closed(self):
        first = qv.patch(self.source)
        with self.assertRaises(ValueError):
            qv.patch(first)

    def test_other_source_tree_fails_closed(self):
        with self.assertRaises(ValueError):
            qv.patch("unrelated Magic Lantern source")


if __name__ == "__main__":
    unittest.main(verbosity=2)
