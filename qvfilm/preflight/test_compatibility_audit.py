#!/usr/bin/env python3
"""Synthetic tests for read-only QVFilm v0.2.2 compatibility assessment."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import compatibility_audit as audit


class CompatibilityAuditTests(unittest.TestCase):
    def setUp(self):
        self.preflight = {
            "report_version": "0.2.1", "camera_platform": "5D3.123",
            "status": "REVIEW_REQUIRED", "photo_name": "_C2A8994.JPG",
            "photo_sha256": "a" * 64,
            "camera_metadata": {
                "IFD0:Model": "Canon EOS 5D Mark III",
                "Canon:CanonFirmwareVersion": "Firmware Version 9.0.1",
                "Canon:FirmwareVersion": "9.0.1 ",
                "Canon:FirmwareInfo": "9.0.1 A6(34) at offset 0x242",
            }
        }

    def test_exact_user_case_remains_hold(self):
        result = audit.review(self.preflight)
        self.assertEqual(result["installation_decision"], "HOLD_NOT_APPROVED")
        self.assertEqual(result["public_firmware_candidate_from_community_mapping"], "1.2.3")
        self.assertFalse(result["mapping_is_independent_firmware_proof"])
        self.assertEqual(result["card_status"]["status"], "NOT_CHECKED")

    def test_wrong_camera_will_not_infer(self):
        self.preflight["camera_metadata"]["IFD0:Model"] = "Canon EOS 5D Mark II"
        self.assertIsNone(audit.review(self.preflight)["public_firmware_candidate_from_community_mapping"])

    def test_firmware_conflict_blocks_inference(self):
        self.preflight["status"] = "BLOCK_MISMATCH"
        self.assertIsNone(audit.review(self.preflight)["public_firmware_candidate_from_community_mapping"])

    def test_mpu_136_mapping_stays_hold(self):
        self.preflight["camera_metadata"]["Canon:FirmwareInfo"] = "9.3.9 AB"
        self.preflight["camera_metadata"]["Canon:FirmwareVersion"] = "9.3.9"
        self.preflight["camera_metadata"]["Canon:CanonFirmwareVersion"] = "9.3.9"
        result = audit.review(self.preflight)
        self.assertEqual(result["public_firmware_candidate_from_community_mapping"], "1.3.6")
        self.assertEqual(result["installation_decision"], "HOLD_NOT_APPROVED")

    def test_read_only_card_inventory_and_no_photo_read(self):
        with tempfile.TemporaryDirectory() as temp:
            card = Path(temp) / "CARD"
            (card / "ML" / "MODULES").mkdir(parents=True)
            (card / "DCIM").mkdir()
            (card / "DCIM" / "IMG_9999.CR2").write_bytes(b"DO_NOT_READ")
            (card / "autoexec.bin").write_bytes(b"SYNTHETIC_TEST_BOOT")
            (card / "ML" / "MODULES" / "mlv_lite.mo").write_bytes(b"TEST")
            before = (card / "autoexec.bin").read_bytes()
            result = audit.review(self.preflight, str(card))
            inv = result["card_status"]
            self.assertEqual(inv["status"], "ML_FILES_SEEN_UNVERIFIED")
            self.assertFalse(inv["bootable_verified"])
            self.assertIn("autoexec.bin", inv["file_fingerprints"])
            self.assertIn("mlv_lite.mo", inv["module_names"])
            self.assertEqual(before, (card / "autoexec.bin").read_bytes())
            self.assertNotIn("DCIM", json.dumps(inv))

    def test_unavailable_card_never_passes(self):
        inv = audit.review(self.preflight, "X:\\non_existing_test_card")["card_status"]
        self.assertEqual(inv["status"], "CARD_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
