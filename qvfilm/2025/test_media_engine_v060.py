#!/usr/bin/env python3
"""Structural and safety tests for v0.6.0 on exact Magic Lantern 2025 source."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_media_engine_v060 as media


class MediaEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = HERE / "fixture-2025-mlv_lite.c"
        if not p.exists():
            raise unittest.SkipTest("Exact-source fixture provided only by CI")
        cls.source = p.read_text(encoding="utf-8")

    def test_source_lock_and_version(self):
        result = media.patch(self.source)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.0")', result)
        self.assertIn('if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)', result)
        self.assertIn('MODULE_CONFIG(qvfilm_hud_enabled)', result)
        self.assertIn('menu_add("Movie", raw_video_menu', result)
        self.assertIn('.name = "QVFIL Media Engine"', result)
        self.assertIn('.name = "QVFIL Recording Report"', result)

    def test_no_unsafe_overclock_or_dummy_benchmark(self):
        result = media.patch(self.source)
        delta = result[result.index('/* v0.6.0 Passive Media Engine.'):]
        self.assertNotIn('FIO_CreateFile(', delta)
        self.assertNotIn('FIO_RemoveFile(', delta)
        self.assertNotIn('sd_overclock', delta)
        self.assertNotIn('SD_ReConfiguration', delta)
        self.assertNotIn('MEM(0xC040', delta)
        self.assertNotIn('raw_recording_state = RAW_IDLE;', delta)

    def test_capture_derived_throughput_measurement(self):
        result = media.patch(self.source)
        self.assertIn('uint32_t qvfilm_media_start_ms = 0;', result)
        self.assertIn('qvfilm_media_start_ms = get_ms_clock();', result)
        self.assertIn('qvfilm_media_drive = raw_movie_filename', result)
        self.assertIn('qvfilm_media_stream_x10 =', result)
        self.assertIn('qvfilm_media_writer_x10 =', result)
        self.assertIn('qvfilm_media_end_queue =', result)
        self.assertIn('written_total * 10000ULL', result)
        self.assertIn('elapsed * 1048576ULL', result)
        self.assertIn('writing_time * 1048576ULL', result)
        self.assertIn('before queued frames are flushed.', result)

    def test_safety_stop_unchanged(self):
        result = media.patch(self.source)
        self.assertIn('qvfilm_last_stop_reason = 1;', result)
        self.assertIn('qvfilm_last_stop_reason = 2;', result)
        self.assertIn('goto abort_and_check_early_stop;', result)
        self.assertIn('goto abort;', result)
        self.assertIn('Flushing buffers...', result)
        self.assertIn('Movie recording stopped automagically', result)

    def test_headroom_uses_consistent_mib_units(self):
        result = media.patch(self.source)
        self.assertIn('qvfilm_media_demand_x10(void)', result)
        self.assertIn('bytes_per_second * 10 / 1048576ULL', result)
        self.assertIn('qvfilm_media_drive != drive', result)
        self.assertIn('qvfilm_media_stream_x10 * 100', result)
        self.assertIn('needed * 120', result)
        self.assertIn('Short capture only; no long-duration pass implied.', result)

    def test_tightening_is_one_shot(self):
        patched = media.patch(self.source)
        with self.assertRaises(ValueError):
            media.patch(patched)
        with self.assertRaises(ValueError):
            media.patch("invalid old tree")


if __name__ == "__main__":
    unittest.main(verbosity=2)
