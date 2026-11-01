import unittest
import install_readiness as readiness

def sample(card_status="NO_ML_FILES"):
    return {
        "audit_version": "0.2.2",
        "camera_model_confirmed": True,
        "mpu_evidence": "MPU 9.0.1 / A6",
        "public_firmware_candidate_from_community_mapping": "1.2.3",
        "mapping_is_independent_firmware_proof": False,
        "installation_decision": "HOLD_NOT_APPROVED",
        "card_status": {"status": card_status, "bootable_verified": False,
                        "file_fingerprints": {}, "ml_directory_present": False,
                        "module_names": []},
    }

class InstallReadinessTests(unittest.TestCase):
    def test_user_report_blocks(self):
        r = readiness.assess(sample())
        self.assertEqual(r["decision"], "DO_NOT_INSTALL")
        self.assertEqual(r["inspected_card_status"], "NO_ML_FILES")
        self.assertTrue(r["mpu_is_not_public_firmware_proof"])
        self.assertGreaterEqual(len(r["blockers"]), 3)

    def test_unchecked_card_blocks(self):
        r = readiness.assess(sample("NOT_CHECKED"))
        self.assertEqual(r["decision"], "DO_NOT_INSTALL")

    def test_files_present_dont_prove_boot(self):
        r = readiness.assess(sample("ML_FILES_SEEN_UNVERIFIED"))
        self.assertEqual(r["decision"], "DO_NOT_INSTALL")

    def test_camera_mismatch_blocks(self):
        x = sample()
        x["camera_model_confirmed"] = False
        r = readiness.assess(x)
        self.assertEqual(r["decision"], "DO_NOT_INSTALL")
        self.assertFalse(r["camera_model_confirmed_in_photo"])

    def test_false_positive_flag_not_install_authorization(self):
        x = sample("ML_FILES_SEEN_UNVERIFIED")
        x["mapping_is_independent_firmware_proof"] = True
        x["card_status"]["bootable_verified"] = True
        r = readiness.assess(x)
        self.assertEqual(r["decision"], "DO_NOT_INSTALL")

    def test_invalid_json_structure(self):
        with self.assertRaises(ValueError):
            readiness.assess(["not an audit dict"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
