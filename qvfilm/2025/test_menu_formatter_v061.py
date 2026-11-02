#!/usr/bin/env python3
"""Canon 5D3 menu formatter regression tests on pinned 2025 upstream."""
import unittest
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_media_engine_v061 as hotfix

class MenuFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = HERE / "fixture-2025-mlv_lite.c"
        if not p.exists():
            raise unittest.SkipTest("Exact upstream source fixture is provided by CI")
        cls.source = p.read_text(encoding="utf8")

    def test_labels_and_media_formats(self):
        code = hotfix.patch(self.source)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.1");', code)
        self.assertIn('MENU_SET_NAME("QVFIL Storage Check");', code)
        self.assertIn('MENU_SET_NAME("QVFIL Media Engine");', code)
        self.assertIn('MENU_SET_NAME("QVFIL Recording Report");', code)
        self.assertIn('MENU_SET_NAME("QVFIL HUD Diagnostics");', code)
        self.assertIn('MENU_SET_VALUE("Flow:%d.%d"', code)
        self.assertIn('MENU_SET_VALUE("%s: %d.%d MiB/s"', code)
        self.assertIn('MENU_SET_RINFO("Obs:%d.%d"', code)
        self.assertIn('MENU_SET_RINFO("I/O:%d.%d"', code)
        self.assertIn('MENU_SET_VALUE("Draws:%d"', code)

    def test_no_unsupported_unsigned_or_character_tokens_in_qvfilm_menu(self):
        code = hotfix.patch(self.source)
        block = code[code.index('static MENU_UPDATE_FUNC(qvfilm_hud_diagnostics_update)'):
                     code.index('static struct lvinfo_item info_items[] = {')]
        self.assertNotIn('%u', block)
        self.assertNotIn('%c', block)
        self.assertIn('drive == \'A\' ? "CF"', block)
        self.assertIn('(int)qvfilm_media_end_queue', block)
        self.assertNotIn('FIO_WriteFile(', block)
        self.assertNotIn('FIO_CreateFile(', block)

    def test_recording_safety_is_unchanged_from_v060(self):
        import apply_media_engine_v060 as base
        old = base.patch(self.source)
        new = hotfix.patch(self.source)
        self.assertIn('goto abort_and_check_early_stop;', new)
        self.assertIn('qvfilm_last_stop_reason = 1;', new)
        self.assertIn('qvfilm_last_stop_reason = 2;', new)
        self.assertIn('OUTPUT_COMPRESSION', new)
        self.assertIn('Flushing buffers...', new)
        self.assertEqual(old[old.index('void raw_video_rec_task()'):old.index('static REQUIRES(GuiMainTask)\nvoid raw_start_stop()')],
                         new[new.index('void raw_video_rec_task()'):new.index('static REQUIRES(GuiMainTask)\nvoid raw_start_stop()')])

    def test_idempotency_guard(self):
        once = hotfix.patch(self.source)
        with self.assertRaises(ValueError):
            hotfix.patch(once)

if __name__ == "__main__":
    unittest.main(verbosity=2)
