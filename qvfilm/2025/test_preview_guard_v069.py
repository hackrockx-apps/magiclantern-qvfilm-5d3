#!/usr/bin/env python3
"""Pin and compare QVFIL v0.6.9 to v0.6.8; no capture/preview changes."""
from pathlib import Path
import sys
import re
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_lossless_readonly_v068 as old
import apply_preview_guard_v069 as new


class PreviewGuideV069(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f = HERE / "fixture-2025-mlv_lite.c"
        if not f.exists():
            raise unittest.SkipTest("Exact 2025 upstream fixture supplied by CI")
        source = f.read_text(encoding="utf-8")
        cls.old = old.patch(source)
        cls.new = new.patch(source)

    def assert_unchanged_region(self, begin, end):
        def get(src):
            b = src.index(end)
            # Upstream declares raw_rec_update_preview before its definition.
            # Take the LAST matching function signature before this end.
            a = src.rindex(begin, 0, b)
            return src[a:b]
        self.assertEqual(get(self.old), get(self.new))

    def test_recording_writer_and_compressor_byte_identical(self):
        self.assert_unchanged_region(
            "void raw_video_rec_task()\n{",
            "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()")
        self.assert_unchanged_region(
            "static void compress_task()\n{",
            "static REQUIRES(LiveViewTask) FAST\nvoid process_frame(")

    def test_upstream_preview_renderer_byte_identical(self):
        # QVFIL prepends menu callbacks before core info_items[]; isolate
        # only the original preview function, not the downstream menu.
        def body(src):
            start = src.index("unsigned int raw_rec_update_preview(unsigned int ctx)\\n{")
            tail = "    preview_dirty = 1;\\n    return 1;\\n}"
            stop = src.index(tail, start) + len(tail)
            return src[start:stop]
        self.assertEqual(body(self.old), body(self.new))

    def test_preview_guide_never_mutates_preview_or_raw_state(self):
        a = self.new.index("static MENU_UPDATE_FUNC(qvfilm_preview_guide_update)")
        b = self.new.index("static struct menu_entry qvfilm_hud_menu[]", a)
        s = self.new[a:b]
        for token in (
            'MENU_SET_NAME("QVFIL Preview Guide")',
            '"Auto"', '"Real-time"', '"Framing"', '"Frozen LV"',
            "preview_mode == 0", "preview_mode == 1",
            "preview_mode == 2", "preview_mode == 3",
            'MENU_SET_RINFO("CANON LV")',
            'MENU_SET_RINFO("SLOW")',
            'MENU_SET_RINFO("FREEZE")',
            "framing inaccurate",
        ):
            self.assertIn(token, s)
        self.assertIsNone(re.search(r"\bpreview_mode\s*=(?!=)", s))
        for forbidden in (
            "raw_rec_update_preview(",
            "raw_preview_fast_ex(", "raw_video_rec_task(",
            "FIO_", "BMP_LOCK(", "bmp_printf(",
            "get_free_slot", "set_raw",
            "lossless_compress_raw_rectangle(",
            "OUTPUT_COMPRESSION =", "raw_video_enabled =",
        ):
            self.assertNotIn(forbidden, s)

    def test_auto_iso_indicated_as_auto_not_mislabelled_manual(self):
        self.assertIn('if (!lens_info.raw_iso && lens_info.raw_iso_auto)', self.new)
        self.assertIn('420, 356, "ISO AUTO"', self.new)
        self.assertIn('420, 356, "ISO%d", iso', self.new)
        self.assertNotIn('420, 356, "ISO AUTO"', self.old)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.9")', self.new)

    def test_existing_modes_guards_and_diagnostics_preserved(self):
        for token in (
            'CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema", "Cinema clean", "Cinema slim")',
            '.name = "QVFIL Lossless Diag"',
            '.name = "QVFIL LJ Error Guide"',
            '.name = "QVFIL Preview Guide"',
            '.name = "QVFIL Shoot Check"',
            '.name = "QVFIL Media Engine"',
            '.name = "QVFIL Recording Report"',
            'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
            'Lossless RAW blocked on 5D3.123',
        ):
            self.assertIn(token, self.new)

    def test_strict_upstream_and_no_reapplication(self):
        with self.assertRaises(ValueError):
            new.patch("invalid upstream source")
        with self.assertRaises(ValueError):
            new.patch(self.new)


if __name__ == "__main__":
    unittest.main(verbosity=2)
