#!/usr/bin/env python3
"""QVFIL v0.6.7 one-shot Lossless diagnostic patch tests."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_cinema_slim_v066 as v066
import apply_lossless_diagnostic_v067 as v067


class LosslessDiagnosticV067Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = HERE / "fixture-2025-mlv_lite.c"
        if not fixture.exists():
            raise unittest.SkipTest("Pinned upstream fixture is supplied by GitHub CI")
        cls.upstream = fixture.read_text(encoding="utf-8")
        cls.v066 = v066.patch(cls.upstream)
        cls.v067 = v067.patch(cls.upstream)

    def test_default_stays_blocked_and_arm_is_session_only(self):
        s = self.v067
        self.assertIn("static volatile int qvfilm_lossless_diag_armed = 0;", s)
        self.assertNotIn('CONFIG_INT("qvfilm.lossless_diag', s)
        self.assertIn('if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)', s)
        self.assertIn("!qvfilm_lossless_diag_armed || reason", s)
        self.assertIn("qvfilm_lossless_diag_preflight()", s)
        self.assertIn("output_format != OUTPUT_14BIT_LOSSLESS", s)

    def test_preflight_limits_probe_to_low_load_cf_only(self):
        s = self.v067
        for token in (
            'is_camera("5D3", "1.2.3")',
            "pre_record || rec_trigger || h264_proxy_menu",
            "dir[0] != 'A'",
            "res_x > 1280 || res_y > 720",
            "fps1000 > 25000",
            "qvfilm_lossless_diag_reboot_required",
        ):
            self.assertIn(token, s)

    def test_error_is_captured_before_slot_can_become_full(self):
        s = self.v067
        fail = s.index("qvfilm_lossless_diag_mark_failure(compressed_size, frame_count-1, slot_index, 0);")
        continue_pos = s.index("                continue;", fail)
        full = s.index("slots[slot_index].status = SLOT_FULL;", continue_pos)
        self.assertLess(fail, continue_pos)
        self.assertLess(continue_pos, full)
        branch = s[s.index("if (compressed_size < 0 && qvfilm_lossless_diag_active)"):
                   s.index("if (compressed_size < 0 && !RAW_IS_IDLE)")]
        self.assertNotIn("ASSERT(0)", branch)
        self.assertIn("DeleteMemorySuite(outSuite);", branch)

    def test_bad_sizes_are_stopped_before_resize_or_fake_edmac_check(self):
        s = self.v067
        start = s.index("if (qvfilm_lossless_diag_active && compressed_size <= 0)")
        end = s.index("if (1)\n            {", start)
        guard = s[start:end]
        self.assertIn("qvfilm_lossless_diag_mark_failure(-6", guard)
        self.assertIn("qvfilm_lossless_diag_mark_failure(-4", guard)
        self.assertIn("qvfilm_lossless_diag_mark_failure(-5", guard)
        self.assertEqual(guard.count("continue;"), 3)
        self.assertNotIn("shrink_slot(", guard)
        self.assertNotIn("frame_fake_edmac_check(", guard)

    def test_fault_drains_queue_and_truncates_before_failed_slot(self):
        s = self.v067
        self.assertIn("if (qvfilm_lossless_diag_fault)", s)
        self.assertIn("qvfilm_lossless_diag_drain_ack = 1;", s)
        self.assertIn("qvfilm_lossless_diag_failed_slot", s)
        self.assertIn("writing_queue_tail = qvfilm_failed_pos;", s)
        self.assertIn("qvfilm_lossless_diag_drain_timeout = 1;", s)
        self.assertIn("if (!qvfilm_lossless_diag_drain_timeout)\n        free_buffers();", s)
        self.assertIn("if (qvfilm_lossless_diag_drain_timeout)\n        writing_queue_head = writing_queue_tail;", s)

    def test_probe_is_one_shot_and_stops_after_25_successful_frames(self):
        s = self.v067
        self.assertIn("#define QVFIL_LD_MAX_FRAMES 25", s)
        self.assertIn("qvfilm_lossless_diag_ok_frames >= QVFIL_LD_MAX_FRAMES", s)
        self.assertIn("qvfilm_lossless_diag_stop_requested = 1;", s)
        self.assertIn("buffer_full = 1;", s)
        self.assertIn("qvfilm_lossless_diag_armed = 0;", s)

    def test_uncompressed_edmac_path_and_v066_hud_modes_remain(self):
        s = self.v067
        self.assertIn("edmac_copy_rectangle_cbr_start(", s)
        self.assertIn(
            'CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema", "Cinema clean", "Cinema slim")',
            s,
        )
        self.assertIn('"Use Overlay > Focus Peak ON; switch lens to MF; tune Threshold."', s)
        self.assertIn('.name = "QVFIL Media Engine"', s)
        self.assertIn('.name = "QVFIL Recording Report"', s)
        self.assertIn('.name = "QVFIL Lossless Diagnostic"', s)

    def test_failure_helper_frees_slot_and_latches_buffer_stop(self):
        s = self.v067
        a = s.index("static void qvfilm_lossless_diag_mark_failure")
        b = s.index("static void compress_task()", a)
        helper = s[a:b]
        self.assertIn("free_slot(slot);", helper)
        self.assertIn("qvfilm_lossless_diag_fault = 1;", helper)
        self.assertIn("buffer_full = 1;", helper)
        self.assertNotIn("slots[slot].status = SLOT_FULL", helper)

    def test_only_expected_recorder_regions_change_from_v066(self):
        # The diagnostic is deliberately localized to the lossless guard,
        # compression task, stop/drain path and diagnostic menu/report.
        self.assertIn("raw_video_rec_task()", self.v067)
        self.assertIn("qvfilm_lossless_diag_preflight", self.v067)
        self.assertIn("lossless_compress_raw_rectangle(", self.v067)
        self.assertIn("QVFIL Lossless Diagnostic", self.v067)
        self.assertNotIn("EngDrvOut(0xC0F", self.v067)
        self.assertNotIn("OUTPUT_COMPRESSION = 0", self.v067)

    def test_strict_anchors_reject_wrong_or_already_patched_source(self):
        with self.assertRaises(ValueError):
            v067.patch("not Magic Lantern 2025")
        with self.assertRaises(ValueError):
            v067.patch(self.v067)


if __name__ == "__main__":
    unittest.main(verbosity=2)
