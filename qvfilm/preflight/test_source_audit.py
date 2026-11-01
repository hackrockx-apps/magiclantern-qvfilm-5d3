import unittest

import source_audit as source


def make_report():
    return {
        "version": "0.3.0",
        "target": "5D3.123",
        "source_filename": "magiclantern.2025-06-20.5D3.123.zip",
        "source_sha256": "63ca9e56405573ce58f9fca2680d17bb87ce57a5b946f66afc2cbb16ccf00d77",
        "archive_readable": True,
        "structure": {
            "file_count": 53,
            "total_uncompressed_bytes": 3392655,
            "autoexec_present": True,
            "setup_fir_present": True,
            "setup_fir_names": ["ML-SETUP.FIR"],
            "ml_file_count": 51,
            "missing_required": [],
            "unexpected_root_firmware_bins": [],
        },
        "decision": "STRUCTURE_PASS_INSTALL_HOLD",
    }


class SourceAuditTests(unittest.TestCase):
    def test_real_report_fingerprint_matches(self):
        out = source.verify(make_report())
        self.assertEqual(out["baseline_zip_decision"], "CHECKSUM_AND_STRUCTURE_MATCH")
        self.assertEqual(out["installation_decision"], "DO_NOT_INSTALL")
        self.assertFalse(out["canon_public_firmware_1_2_3_independently_verified"])

    def test_wrong_checksum_fails(self):
        data = make_report()
        data["source_sha256"] = "0" * 64
        self.assertEqual(source.verify(data)["baseline_zip_decision"],
                         "CHECKSUM_OR_STRUCTURE_MISMATCH")

    def test_wrong_filename_fails(self):
        data = make_report()
        data["source_filename"] = "magiclantern.2025-06-20.5D3.113.zip"
        self.assertEqual(source.verify(data)["baseline_zip_decision"],
                         "CHECKSUM_OR_STRUCTURE_MISMATCH")

    def test_missing_fir_fails(self):
        data = make_report()
        data["structure"]["setup_fir_present"] = False
        self.assertEqual(source.verify(data)["baseline_zip_decision"],
                         "CHECKSUM_OR_STRUCTURE_MISMATCH")

    def test_bad_structure_fails(self):
        data = make_report()
        data["decision"] = "BLOCK"
        self.assertEqual(source.verify(data)["baseline_zip_decision"],
                         "CHECKSUM_OR_STRUCTURE_MISMATCH")

    def test_no_positive_install_decision_even_if_everything_matches(self):
        data = make_report()
        data["camera_firmware"] = "1.2.3"
        data["user_approved_install"] = True
        self.assertEqual(source.verify(data)["installation_decision"], "DO_NOT_INSTALL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
