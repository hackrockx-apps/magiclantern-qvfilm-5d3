import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import baseline_stager as st


class BaselineStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name) / "5D Mark III Upgrade"
        self.base.mkdir(parents=True, exist_ok=True)

    def make_zip(self, filename="magiclantern-5D3.123.zip", contents=None):
        out = self.base / filename
        if contents is None:
            contents = {
                "autoexec.bin": b"fake baseline test file",
                "ML-SETUP.FIR": b"fake setup test file",
                "ML/FONTS/test.fnt": b"font",
                "ML/MODULES/test.mo": b"module",
            }
        with zipfile.ZipFile(out, "w") as zip:
            for name, data in contents.items():
                zip.writestr(name, data)
        return out

    def test_expected_structure_is_not_install_authorization(self):
        result = st.analyze_archive(self.make_zip())
        self.assertEqual(result["decision"], "STRUCTURE_PASS_INSTALL_HOLD")
        self.assertTrue(result["archive_readable"])
        self.assertTrue(result["structure"]["setup_fir_present"])
        self.assertEqual(len(result["source_sha256"]), 64)

    def test_5d2_firmware_name_rejected(self):
        result = st.analyze_archive(self.make_zip(filename="magiclantern-5D2.212.zip"))
        self.assertEqual(result["decision"], "BLOCK")

    def test_5d3_113_name_rejected(self):
        result = st.analyze_archive(self.make_zip(filename="magiclantern-5D3.113.zip"))
        self.assertEqual(result["decision"], "BLOCK")

    def test_wrong_body_5d4_name_rejected(self):
        result = st.analyze_archive(self.make_zip(filename="magiclantern-5D4.133.zip"))
        self.assertEqual(result["decision"], "BLOCK")

    def test_unknown_zip_name_requires_review(self):
        result = st.analyze_archive(self.make_zip(filename="magiclantern-unknown.zip"))
        self.assertEqual(result["decision"], "REVIEW_NAME")

    def test_missing_setup_fir_rejected(self):
        result = st.analyze_archive(self.make_zip(contents={
            "autoexec.bin": b"x", "ML/x": b"x"
        }))
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("ML-SETUP.FIR", result["structure"]["missing_required"])

    def test_path_traversal_rejected(self):
        result = st.analyze_archive(self.make_zip(contents={
            "autoexec.bin": b"x", "ML-SETUP.FIR": b"x",
            "ML/x": b"x", "../malicious": b"x"
        }))
        self.assertEqual(result["decision"], "BLOCK")

    def test_windows_executable_rejected(self):
        result = st.analyze_archive(self.make_zip(contents={
            "autoexec.bin": b"x", "ML-SETUP.FIR": b"x",
            "ML/x": b"x", "CLICKME.exe": b"x"
        }))
        self.assertEqual(result["decision"], "BLOCK")

    def test_extra_fir_rejected(self):
        result = st.analyze_archive(self.make_zip(contents={
            "autoexec.bin": b"x", "ML-SETUP.FIR": b"x",
            "ML/x": b"x", "UPGRADE.FIR": b"x"
        }))
        self.assertEqual(result["decision"], "BLOCK")

    def test_stage_writes_only_report_on_pc(self):
        archive = self.make_zip()
        report = self.base / "reports" / "stage.json"
        self.assertEqual(st.stage(archive, report), 0)
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(data["decision"], "STRUCTURE_PASS_INSTALL_HOLD")
        self.assertTrue(archive.is_file())

    def test_zip_has_no_setup_and_no_ml(self):
        result = st.analyze_archive(self.make_zip(contents={"random.bin": b"x"}))
        self.assertEqual(result["decision"], "BLOCK")

    def test_corrupt_zip_not_accepted(self):
        f = self.base / "magiclantern-5D3.123.zip"
        f.write_bytes(b"NOT A ZIP")
        result = st.analyze_archive(f)
        self.assertEqual(result["decision"], "BLOCK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
