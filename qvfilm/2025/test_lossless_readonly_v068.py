#!/usr/bin/env python3
"""QVFIL 0.6.8 read-only diagnostic tests on pinned Magic Lantern 2025."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_cinema_slim_v066 as previous
import apply_lossless_readonly_v068 as current


class LosslessReadonlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = HERE / "fixture-2025-mlv_lite.c"
        if not src.exists():
            raise unittest.SkipTest("Requires exact upstream fixture copied by CI")
        cls.base = src.read_text(encoding="utf-8")
        cls.old = previous.patch(cls.base)
        cls.new = current.patch(cls.base)

    @staticmethod
    def between(source, start, end):
        a = source.index(start)
        b = source.index(end, a)
        return source[a:b]

    def test_raw_recorder_byte_identical(self):
        start = "void raw_video_rec_task()\n{"
        end = "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"
        self.assertEqual(self.between(self.old, start, end),
                         self.between(self.new, start, end))

    def test_compress_task_byte_identical(self):
        start = "static void compress_task()\n{"
        end = "static REQUIRES(LiveViewTask) FAST\nvoid process_frame("
        self.assertEqual(self.between(self.old, start, end),
                         self.between(self.new, start, end))

    def test_status_menu_is_explicitly_readonly(self):
        start = "static MENU_UPDATE_FUNC(qvfilm_lossless_diag_update)"
        end = "static struct menu_entry qvfilm_hud_menu[]"
        callbacks = self.between(self.new, start, end)
        for needed in (
            'MENU_SET_NAME("QVFIL Lossless Diag")',
            'MENU_SET_RINFO("LJ BLOCKED")',
            'MENU_SET_RINFO("LJ OFF")',
            'MENU_SET_RINFO("RAW OFF")',
            'MENU_SET_RINFO("HIST: ?")',
            'NO live error code captured',
            'OUTPUT_COMPRESSION',
        ):
            self.assertIn(needed, callbacks)
        for banned in (
            "FIO_WriteFile(", "FIO_CreateFile(", "CreateMemorySuite(",
            "lossless_compress_raw_rectangle(", "raw_video_rec_task(",
            "shrink_slot(", "frame_fake_edmac_check(", "ASSERT(0)",
            "msg_queue_post(", "raw_recording_state =",
            "buffer_full =", "set_recording_custom(",
            "bmp_fill(", "bmp_printf(", "EngDrvOut(", "TTL_Start(",
        ):
            self.assertNotIn(banned, callbacks)

    def test_old_modes_and_lossless_block_preserved(self):
        for token in (
            'CHOICES("OFF", "Info bars", "Cinema overlay", "Large cinema", "Cinema clean", "Cinema slim")',
            'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
            'Lossless RAW blocked on 5D3.123',
            '.name = "QVFIL Shoot Check"',
            '.name = "QVFIL Media Engine"',
            '.name = "QVFIL Recording Report"',
            '.name = "QVFIL Focus Assist"',
            '.name = "QVFIL Lossless Diag"',
            '.name = "QVFIL LJ Error Guide"',
            'MENU_SET_RINFO("QVFIL v0.6.8")',
        ):
            self.assertIn(token, self.new)
        self.assertNotIn('MENU_SET_RINFO("QVFIL v0.6.6")', self.new)

    def test_guard_not_weakened_and_source_strict(self):
        for token in (
            '    if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)\n',
            '        NotifyBox(6000, "QVFIL: Lossless blocked. Use RAW uncompressed.");',
            '        return;\n    }\n',
        ):
            self.assertIn(token, self.new)
        with self.assertRaises(ValueError):
            current.patch("incorrect source")
        with self.assertRaises(ValueError):
            current.patch(self.new)


if __name__ == "__main__":
    unittest.main(verbosity=2)
