#!/usr/bin/env python3
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
import package_test_card as p

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/"source"
        self.root.mkdir()
        self.out=Path(self.tmp.name)/"review"
        for src in p.REQUIRED:
            q=self.root/src
            q.parent.mkdir(parents=True,exist_ok=True)
            q.write_bytes(b"dummy same revision build output, not real ARM executable")
        for srcdir,prefix,num,ext in (
            ("data/fonts","f",5,".rbf"),
            ("data/vram","v",5,".lut"),
            ("data/cropmks","c",1,".bmp"),
        ):
            for k in range(num):
                q=self.root/srcdir/f"{prefix}{k}{ext}"
                q.parent.mkdir(parents=True,exist_ok=True)
                q.write_bytes(bytes([65+k])*23)

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_and_not_directly_installable(self):
        x=p.stage(self.root,self.out,"a"*40,allow_synthetic=True)
        self.assertFalse(x["camera_installable_approval"])
        self.assertGreater(x["files"],10)
        zfile=Path(x["archive"])
        self.assertEqual(x["archive_sha256"],p.sha256(zfile))
        with zipfile.ZipFile(zfile) as z:
            self.assertIsNone(z.testzip())
            self.assertIn("CARD_ROOT/ML/MODULES/CROP_REC.MO",z.namelist())
            self.assertIn("CARD_ROOT/ML/MODULES/MLV_LITE.MO",z.namelist())
            self.assertIn("CARD_ROOT/ML/MODULES/5D3_123.SYM",z.namelist())
            self.assertNotIn("autoexec.bin",z.namelist())
            self.assertNotIn("ML-SETUP.FIR",z.namelist())
            self.assertIn(b"NOT APPROVED",z.read("READ_ME_FIRST.txt"))
        with self.assertRaises(RuntimeError):
            p.stage(self.root,self.out,"b"*40,allow_synthetic=True)

    def test_missing_core_fails_closed(self):
        (self.root/"platform/5D3.123/autoexec.bin").unlink()
        with self.assertRaisesRegex(RuntimeError,"missing/empty"):
            p.stage(self.root,self.out,"c"*40,allow_synthetic=True)
        self.assertFalse(self.out.exists())

    def test_missing_support_files_fails_closed(self):
        for f in list((self.root/"data/vram").glob("*.lut"))[:3]:f.unlink()
        with self.assertRaisesRegex(RuntimeError,"expected >= 4"):
            p.stage(self.root,self.out,"d"*40,allow_synthetic=True)

if __name__=="__main__":
    unittest.main(verbosity=2)
