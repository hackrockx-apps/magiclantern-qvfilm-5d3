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


if __name__ == "__main__":
    unittest.main(verbosity=2)
