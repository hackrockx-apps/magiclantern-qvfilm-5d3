#!/usr/bin/env python3
"""Pinned Magic Lantern 2025 regression tests for v0.6.15 ID Probe."""
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import apply_camera_id_probe_v0614 as oldpatch
import apply_camera_id_probe_display_v0615 as newpatch

class ProbeDisplayV0615(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=HERE/"fixture-2025-mlv_lite.c"
        if not fixture.exists():
            raise unittest.SkipTest("CI injects the exact upstream fixture")
        original=fixture.read_text(encoding="utf-8")
        cls.before=oldpatch.patch(original)
        cls.after=newpatch.patch(original)

    def segment(self,s,a,b):
        p=s.index(a);return s[p:s.index(b,p)]

    def test_raw_recorder_compressor_unchanged(self):
        for a,b in (
            ("void raw_video_rec_task()\n{",
             "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            ("static void compress_task()\n{",
             "static REQUIRES(LiveViewTask) FAST\nvoid process_frame("),
        ):
            self.assertEqual(self.segment(self.before,a,b),
                             self.segment(self.after,a,b))

    def test_preview_path_unchanged(self):
        a="unsigned int raw_rec_update_preview(unsigned int ctx)\n{"
        b="    preview_dirty = 1;\n    return 1;\n}"
        def segment(s):
            i=s.index(a);return s[i:s.index(b,i)+len(b)]
        self.assertEqual(segment(self.before),segment(self.after))

    def test_camera_gate_unchanged(self):
        for needle in (
            '#define QVFIL_LAB_CAMERA_OK (get_digic_version() == 5 && (cam_5d3_123 || is_camera("5D3", "1.2.3")))',
            'static int qvfilm_preview_lab = 0;',
            '.name = "QVFIL Color Lab"',
            '.choices = CHOICES("OFF", "Color STBY")',
            'MENU_SET_RINFO("ID %d/%d D%d"',
            'MENU_SET_RINFO("ARMED 0F")',
            'MENU_SET_RINFO("F:%u %dms"',
            'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
            'Lossless RAW blocked on 5D3.123',
        ):
            self.assertIn(needle,self.after)
        self.assertNotIn("MODULE_CONFIG(qvfilm_preview_lab)",self.after)

    def test_formatting_is_plain_percent_s_and_bounds_are_explicit(self):
        probe=self.segment(
            self.after,
            "static MENU_UPDATE_FUNC(qvfilm_id_probe_update)",
            "static struct menu_entry qvfilm_hud_menu[]"
        )
        for needle in (
            'char model_text[8] = {0};',
            'char fw_text[12] = {0};',
            'i < 6 && __camera_model_short[i]',
            'model_text[i] = __camera_model_short[i];',
            'i < 10 && firmware_version[i]',
            'fw_text[i] = firmware_version[i];',
            'MENU_SET_VALUE("M:%s", model_text[0] ? model_text : "EMPTY");',
            'MENU_SET_RINFO("FW:%s", fw_text[0] ? fw_text : "EMPTY");',
            'MENU_SET_NAME("QVFIL ID Probe")',
        ):
            self.assertIn(needle,probe)
        self.assertNotIn('MENU_SET_VALUE("M:%.6s"',probe)
        self.assertNotIn('MENU_SET_RINFO("FW:%.10s"',probe)
        for forbidden in (
            "FIO_", "firmware_version =", "__camera_model_short =",
            "raw_rec_update_preview(", "task_create(", "raw_video_enabled =",
        ):
            self.assertNotIn(forbidden,probe)

    def test_expected_version_and_unchanged_module_controls(self):
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.15")',self.after)
        self.assertIn('.name = "QVFIL ID Probe"',self.after)
        self.assertIn("#include <propvalues.h>",self.after)
        for needle in ('.name = "QVFIL Lossless Diag"',
                       '.name = "QVFIL LJ Error Guide"',
                       '.name = "QVFIL Preview Guide"'):
            self.assertIn(needle,self.after)

    def test_wrong_source_or_repeat_patch_rejected(self):
        with self.assertRaises(ValueError):
            newpatch.patch("incompatible")
        with self.assertRaises(ValueError):
            newpatch.patch(self.after)

if __name__=="__main__":
    unittest.main(verbosity=2)
