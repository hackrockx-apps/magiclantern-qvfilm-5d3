#!/usr/bin/env python3
"""Strict exact-source tests for v0.6.14 read-only identity probe."""
import sys
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import apply_camera_id_gate_v0613 as before_patch
import apply_camera_id_probe_v0614 as now_patch

class IdentityProbeV0614(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=HERE/"fixture-2025-mlv_lite.c"
        if not fixture.exists():
            raise unittest.SkipTest("Upstream 2025 source fixture supplied by CI")
        original=fixture.read_text(encoding="utf-8")
        cls.old=before_patch.patch(original)
        cls.new=now_patch.patch(original)

    @staticmethod
    def cut(s,start,end):
        a=s.index(start)
        b=s.index(end,a)
        return s[a:b]

    def test_raw_capture_and_compressor_byte_identical(self):
        for begin,end in (
            ("void raw_video_rec_task()\n{",
             "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            ("static void compress_task()\n{",
             "static REQUIRES(LiveViewTask) FAST\nvoid process_frame("),
        ):
            self.assertEqual(self.cut(self.old,begin,end),
                             self.cut(self.new,begin,end))

    def test_preview_display_filter_byte_identical(self):
        a="unsigned int raw_rec_update_preview(unsigned int ctx)\n{"
        b="    preview_dirty = 1;\n    return 1;\n}"
        def body(s):
            i=s.index(a)
            return s[i:s.index(b,i)+len(b)]
        self.assertEqual(body(self.old),body(self.new))

    def test_identity_guard_and_menu_preserved(self):
        for t in (
            '#define QVFIL_LAB_CAMERA_OK (get_digic_version() == 5 && (cam_5d3_123 || is_camera("5D3", "1.2.3")))',
            '#define QVFIL_LAB_STBY (qvfilm_preview_lab && QVFIL_LAB_CAMERA_OK',
            'static int qvfilm_preview_lab = 0;',
            '.name = "QVFIL Color Lab"',
            '.choices = CHOICES("OFF", "Color STBY")',
            'MENU_SET_RINFO("ID %d/%d D%d"',
            'MENU_SET_RINFO("ARMED 0F")',
            'MENU_SET_RINFO("F:%u %dms"',
            'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
            'Lossless RAW blocked on 5D3.123',
        ):
            self.assertIn(t,self.new)
        self.assertNotIn("MODULE_CONFIG(qvfilm_preview_lab)",self.new)

    def test_model_and_version_read_only(self):
        self.assertIn("#include <propvalues.h>",self.new)
        a=self.new.index("static MENU_UPDATE_FUNC(qvfilm_id_probe_update)")
        b=self.new.index("static struct menu_entry qvfilm_hud_menu[]",a)
        p=self.new[a:b]
        for t in (
            'MENU_SET_NAME("QVFIL ID Probe")',
            'MENU_SET_VALUE("M:%.6s"',
            '__camera_model_short[0] ? __camera_model_short : "EMPTY"',
            'MENU_SET_RINFO("FW:%.10s"',
            'firmware_version[0] ? firmware_version : "EMPTY"',
            'MENU_WARN_INFO',
        ):
            self.assertIn(t,p)
        for t in ("firmware_version =", "__camera_model_short =",
                  "raw_rec_update_preview(", "FIO_", "module_config",
                  "task_create(", "raw_video_enabled ="):
            self.assertNotIn(t,p)
        self.assertIn('.name = "QVFIL ID Probe"',self.new)
        self.assertIn("MENU_SET_RINFO(\"QVFIL v0.6.14\")",self.new)

    def test_no_other_change_except_expected_ui_probe(self):
        self.assertIn("#include <propvalues.h>",self.new)
        self.assertNotIn("#include <propvalues.h>",self.old)
        self.assertEqual(self.old.count("QVFIL Color Lab"),
                         self.new.count("QVFIL Color Lab"))
        self.assertEqual(self.old.count("QVFIL Lossless Diag"),
                         self.new.count("QVFIL Lossless Diag"))

    def test_unknown_source_rejected(self):
        with self.assertRaises(ValueError):
            now_patch.patch("different source")
        with self.assertRaises(ValueError):
            now_patch.patch(self.new)

if __name__=="__main__":
    unittest.main(verbosity=2)
