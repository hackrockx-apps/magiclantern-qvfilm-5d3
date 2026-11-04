#!/usr/bin/env python3
"""Synthetic structural tests: not an actual video decode."""
import struct
import tempfile
import unittest
from pathlib import Path
import mlv_audit

def mlvi(guid=1,flags=0,count=3):
    result=struct.pack("<4sI8sQHHIHHIIII",
        b"MLVI",52,b"v2.0\x00\x00\x00\x00",guid,0,1,flags,
        1,0,count,0,24000,1000)
    assert len(result)==52
    return result

def rawi(w=3840,h=1600):
    return struct.pack("<4sIQHH",b"RAWI",20,0,w,h)

def vidf(num,stamp=0):
    result=struct.pack("<4sIQIHHHHI",
        b"VIDF",32,stamp,num,0,0,0,0,0)
    assert len(result)==32
    return result

class MlvAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"MVI_0001.MLV"

    def tearDown(self):
        self.tmp.cleanup()

    def make(self,*blocks):
        self.path.write_bytes(b"".join(blocks))
        return mlv_audit.inspect([self.path])

    def test_valid_4k_width_is_not_uhd(self):
        info=self.make(mlvi(),rawi(),vidf(0),vidf(1),vidf(2))
        self.assertEqual(info["result"],"STRUCTURE_PASS")
        self.assertTrue(info["is_true_4k_width"])
        self.assertFalse(info["is_true_uhd_3840x2160"])
        self.assertEqual(info["declared_fps"],[24.0])
        self.assertEqual(info["observed_vidf_frames"],3)

    def test_true_uhd_and_frame_gap(self):
        info=self.make(mlvi(),rawi(3840,2160),vidf(0),vidf(1),vidf(3))
        self.assertEqual(info["result"],"STRUCTURE_FAIL")
        self.assertTrue(info["is_true_uhd_3840x2160"])
        self.assertEqual(info["missing_frame_numbers"],1)

    def test_error_flag_and_short_block(self):
        info=self.make(mlvi(flags=10),rawi(),vidf(0),b"VIDF\x00")
        self.assertEqual(info["result"],"STRUCTURE_FAIL")
        self.assertTrue(any("recording error" in e for e in info["errors"]))
        self.assertTrue(any("Trailing short" in e for e in info["errors"]))

    def test_invalid_vidf_header(self):
        info=self.make(mlvi(),rawi(),struct.pack("<4sIQ",b"VIDF",16,0))
        self.assertEqual(info["result"],"STRUCTURE_FAIL")
        self.assertTrue(any("Short VIDF" in e for e in info["errors"]))

    def test_non_video_can_never_pass(self):
        info=self.make(mlvi())
        self.assertEqual(info["result"],"STRUCTURE_FAIL")
        self.assertFalse(info["is_true_4k_width"])
        self.assertEqual(info["observed_vidf_frames"],0)

if __name__=="__main__":
    unittest.main(verbosity=2)
