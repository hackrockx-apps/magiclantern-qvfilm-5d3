#!/usr/bin/env python3
# Unit tests use synthetic metadata; they do NOT access any camera, card or real firmware.
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import preflight


class FirmwareGateTests(unittest.TestCase):
    def test_exact_supported_firmware(self):
        self.assertEqual(preflight.classify_metadata({
            "EXIF:Model": "Canon EOS 5D Mark III",
            "Canon:CanonFirmwareVersion": "Firmware Version 1.2.3"
        })[0], "PASS_METADATA")

    def test_internal_mpu_only_requires_review(self):
        status, _ = preflight.classify_metadata({
            "EXIF:Model": "Canon EOS 5D Mark III",
            "Canon:FirmwareVersion": "9.0.1 A6(34)"
        })
        self.assertEqual(status, "REVIEW_REQUIRED")

    def test_missing_metadata_requires_review(self):
        self.assertEqual(preflight.classify_metadata({})[0], "REVIEW_REQUIRED")

    def test_wrong_camera_blocks(self):
        self.assertEqual(preflight.classify_metadata({
            "EXIF:Model": "Canon EOS 5D Mark II",
            "Canon:FirmwareVersion": "1.2.3"
        })[0], "BLOCK_MISMATCH")

    def test_other_firmware_blocks(self):
        self.assertEqual(preflight.classify_metadata({
            "EXIF:Model": "Canon EOS 5D Mark III",
            "Canon:FirmwareVersion": "1.3.6"
        })[0], "BLOCK_MISMATCH")

    def test_conflicting_firmware_tags_block(self):
        self.assertEqual(preflight.classify_metadata({
            "EXIF:Model": "Canon EOS 5D Mark III",
            "Canon:CanonFirmwareVersion": "1.2.3",
            "MakerNotes:FirmwareVersion": "1.3.6"
        })[0], "BLOCK_MISMATCH")

    def test_duplicate_different_models_block(self):
        self.assertEqual(preflight.classify_metadata({
            "EXIF:Model": "Canon EOS 5D Mark III",
            "MakerNotes:CameraModelName": "EOS 5D Mark II",
            "Canon:CanonFirmwareVersion": "1.2.3"
        })[0], "BLOCK_MISMATCH")


class ReadOnlyBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.card = self.root / "card"
        (self.card / "ML" / "MODULES").mkdir(parents=True)
        (self.card / "autoexec.bin").write_bytes(b"KNOWN_GOOD_TEST_BOOT")
        (self.card / "ML" / "MODULES" / "mlv_lite.mo").write_bytes(b"ORIGINAL_MODULE")
        (self.card / "DCIM").mkdir()
        (self.card / "DCIM" / "IMG_0001.JPG").write_bytes(b"DO_NOT_BACKUP_FOOTAGE")

    def test_backup_and_verify(self):
        dest = self.root / "saved"
        self.assertEqual(preflight.backup(SimpleNamespace(
            card=str(self.card), dest=str(dest), max_gb=1)), 0)
        self.assertEqual(preflight.verify_backup(SimpleNamespace(dir=str(dest))), 0)
        self.assertFalse((dest / "DCIM").exists())
        self.assertEqual((self.card / "autoexec.bin").read_bytes(), b"KNOWN_GOOD_TEST_BOOT")
        manifest = json.loads((dest / "BACKUP_MANIFEST.json").read_text())
        self.assertEqual(len(manifest["files"]), 2)

    def test_detect_tampered_backup(self):
        dest = self.root / "saved"
        preflight.backup(SimpleNamespace(card=str(self.card), dest=str(dest), max_gb=1))
        (dest / "autoexec.bin").write_bytes(b"CHANGED")
        with self.assertRaises(ValueError):
            preflight.verify_backup(SimpleNamespace(dir=str(dest)))

    def test_never_overwrite_backup(self):
        dest = self.root / "saved"
        dest.mkdir()
        with self.assertRaises(ValueError):
            preflight.backup(SimpleNamespace(card=str(self.card), dest=str(dest), max_gb=1))

    def test_never_backup_to_card_itself(self):
        with self.assertRaises(ValueError):
            preflight.backup(SimpleNamespace(card=str(self.card),
                                             dest=str(self.card / "NEWBACKUP"), max_gb=1))

    def test_no_magic_lantern_files(self):
        empty = self.root / "empty"
        empty.mkdir()
        with self.assertRaises(ValueError):
            preflight.backup(SimpleNamespace(card=str(empty),
                                             dest=str(self.root / "saved"), max_gb=1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
