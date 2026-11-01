import tempfile
import unittest
from pathlib import Path
import triage_ml_logs as t


class TriageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name) / "5D Mark III Upgrade"
        self.p.mkdir()

    def write(self, text):
        file = self.p / "ASSERT00.LOG"
        file.write_text(text, encoding="utf-8")
        return file

    def test_negative_code_minus_two(self):
        d = t.triage_file(self.write("Compression error -2 at frame 15\nASSERT: mlv_lite.c:2742\n"))
        self.assertEqual(d["findings"][0]["compression_error"], -2)
        self.assertEqual(d["findings"][0]["frame"], 15)
        self.assertIn("timed out", d["findings"][0]["interpretation"])
        self.assertEqual(len(d["file_sha256"]), 64)

    def test_minus_one(self):
        d = t.triage_file(self.write("Compression error -1 at frame 0"))
        self.assertIn("not initialized", d["findings"][0]["interpretation"])

    def test_minus_three(self):
        d = t.triage_file(self.write("Compression error -3 at frame 2"))
        self.assertIn("JPEG signature", d["findings"][0]["interpretation"])

    def test_without_negative_code_is_not_attributed(self):
        d = t.triage_file(self.write("ASSERT 0 at mlv_lite.c:2742 (compress_task)"))
        self.assertFalse(d["contains_compression_return_code"])
        self.assertTrue(d["findings"])

    def test_no_finding_is_unknown(self):
        d = t.triage_file(self.write("Booted normally"))
        self.assertFalse(d["contains_compression_return_code"])
        self.assertEqual(d["findings"], [])

    def test_not_a_log_rejected(self):
        p = self.p / "ROM0.BIN"
        p.write_bytes(b"ROM PRIVATE")
        with self.assertRaises(ValueError):
            t.triage_file(p)

    def test_seven_logs_two_unique_and_no_code(self):
        same = b"ML ASSERT:\n0\nat mlv_lite.c:2742 (compress_task), task compress_task\nFree Memory : 234K + 3897K"
        other = same.replace(b"3897K", b"3900K")
        entries = []
        for i in range(7):
            p = self.p / f"ASSERT{i:02d}.LOG"
            p.write_bytes(other if i == 2 else same)
            entries.append(t.triage_file(p))
        report = t.summarize_logs(entries)
        self.assertEqual(report["log_files"], 7)
        self.assertEqual(report["unique_file_contents"], 2)
        self.assertEqual(report["files_with_mlv_lite_2742_assert"], 7)
        self.assertEqual(report["root_cause_decision"], "ERROR_CODE_NOT_CAPTURED")
        self.assertEqual(sorted(group["file_count"] for group in report["duplicate_groups"]), [1, 6])


if __name__ == "__main__":
    unittest.main(verbosity=2)
