import tempfile
import unittest
from pathlib import Path
import inspect_mlv


class MLVTinyInspectorTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name) / "5D Mark III Upgrade"
        self.root.mkdir()

    def test_minimal_mlv_signature(self):
        p = self.root / "M26-0001.MLV"
        p.write_bytes(b"MLVI" + b"\x00" * 128)
        d = inspect_mlv.inspect(p)
        self.assertEqual(d["status"], "BASIC_FILE_CHECK_PASS")
        self.assertEqual(len(d["file_sha256"]), 64)
        self.assertIn("do not verify", d["note"])

    def test_invalid_magic(self):
        p = self.root / "M26-0002.MLV"
        p.write_bytes(b"BAD!" + b"\x00" * 128)
        d = inspect_mlv.inspect(p)
        self.assertEqual(d["status"], "REJECT")

    def test_tiny_truncated_file(self):
        p = self.root / "M26-0003.MLV"
        p.write_bytes(b"MLVI")
        d = inspect_mlv.inspect(p)
        self.assertEqual(d["status"], "REJECT")

    def test_missing_file(self):
        d = inspect_mlv.inspect(self.root / "missing.MLV")
        self.assertEqual(d["status"], "REJECT")

    def test_wrong_extension(self):
        p = self.root / "REC.M00"
        p.write_bytes(b"MLVI" + b"\x00" * 128)
        self.assertEqual(inspect_mlv.inspect(p)["status"], "REJECT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
