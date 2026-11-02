#!/usr/bin/env python3
"""QVFIL 0.6.2: no recorder changes, accurate warnings for source-limited Flow."""
import sys
import unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_media_engine_v061 as previous
import apply_media_engine_v062 as candidate


class ReliabilityMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f = HERE / "fixture-2025-mlv_lite.c"
        if not f.exists():
            raise unittest.SkipTest("Exact-source fixture provided by CI")
        cls.source = f.read_text(encoding="utf-8")

    def test_compatible_and_present(self):
        out = candidate.patch(self.source)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.2")', out)
        self.assertIn('.name = "QVFIL Media Engine"', out)
        self.assertIn('.name = "QVFIL Recording Report"', out)
        self.assertIn('MENU_SET_VALUE("%s Need:%d.%d"', out)
        self.assertIn('MENU_SET_RINFO("I/O:%d.%d"', out)
        self.assertIn('qvfilm_last_stop_reason == 1', out)
        self.assertIn('qvfilm_last_stop_reason == 2', out)
        self.assertIn('qvfilm_media_duration_ms < 30000', out)

    def test_flow_not_used_to_infer_card_capacity(self):
        out = candidate.patch(self.source)
        fn = out[out.index('static MENU_UPDATE_FUNC(qvfilm_media_engine_update)'):
                 out.index('static MENU_UPDATE_FUNC(qvfilm_media_report_update)')]
        self.assertIn('(uint64_t)qvfilm_media_writer_x10 * 100', fn)
        self.assertNotIn('(uint64_t)qvfilm_media_stream_x10 * 100', fn)
        self.assertIn('qvfilm_media_duration_ms < 30000', fn)
        self.assertIn('qvfilm_media_drive != drive', fn)
        self.assertIn('Estimated headroom only', fn)
        self.assertIn('BUFFER FULL on last capture', fn)
        self.assertIn('FILE WRITE failed on last capture', fn)
        self.assertNotIn('MENU_SET_RINFO("Obs:', fn)
        self.assertNotIn('MENU_SET_VALUE("Flow:', fn)

    def test_recorder_byte_identical_to_hardware_menu_pass(self):
        prev = previous.patch(self.source)
        next = candidate.patch(self.source)
        def recorder(x):
            a = x.index('void raw_video_rec_task()')
            b = x.index('static REQUIRES(GuiMainTask)\nvoid raw_start_stop()', a)
            return x[a:b]
        self.assertEqual(recorder(prev), recorder(next))
        self.assertIn('goto abort_and_check_early_stop;', next)
        self.assertIn('if (buffer_full)', next)
        self.assertIn('qvfilm_last_stop_reason = 1;', next)
        self.assertIn('qvfilm_last_stop_reason = 2;', next)

    def test_no_new_io_or_overclock_in_update_menu(self):
        out = candidate.patch(self.source)
        menu = out[out.index('static MENU_UPDATE_FUNC(qvfilm_media_engine_update)'):
                   out.index('static struct menu_entry qvfilm_hud_menu[] = {')]
        self.assertNotIn('FIO_WriteFile(', menu)
        self.assertNotIn('FIO_CreateFile(', menu)
        self.assertNotIn('sd_uhs', menu)
        self.assertNotIn('SD_ReConfiguration(', menu)
        self.assertNotIn('%u', menu)
        self.assertNotIn('%c', menu)

    def test_repeat_patching_fails_closed(self):
        out = candidate.patch(self.source)
        with self.assertRaises(ValueError):
            candidate.patch(out)

if __name__ == "__main__":
    unittest.main(verbosity=2)
