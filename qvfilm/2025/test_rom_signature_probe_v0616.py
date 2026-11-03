#!/usr/bin/env python3
"""Exact upstream source regression for v0.6.16 ROM signature probe."""
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import apply_camera_id_probe_display_v0615 as previous
import apply_rom_signature_probe_v0616 as current

class RomSignatureProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=HERE/"fixture-2025-mlv_lite.c"
        if not path.exists():
            raise unittest.SkipTest("Pinned upstream ML source fixture injected by CI")
        src=path.read_text(encoding="utf-8")
        cls.old=previous.patch(src)
        cls.new=current.patch(src)

    @staticmethod
    def extract(s,start,end):
        i=s.index(start)
        j=s.index(end,i)
        return s[i:j]

    def test_recorder_and_compressor_byte_identical(self):
        for a,b in (
            ("void raw_video_rec_task()\n{",
             "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            ("static void compress_task()\n{",
             "static REQUIRES(LiveViewTask) FAST\nvoid process_frame("),
        ):
            self.assertEqual(self.extract(self.old,a,b),
                             self.extract(self.new,a,b))

    def test_preview_renderer_byte_identical(self):
        a="unsigned int raw_rec_update_preview(unsigned int ctx)\n{"
        tail="    preview_dirty = 1;\n    return 1;\n}"
        def body(s):
            i=s.index(a)
            return s[i:s.index(tail,i)+len(tail)]
        self.assertEqual(body(self.old),body(self.new))

    def test_color_lab_gate_and_firmware_comparison_unchanged(self):
        for token in (
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
            self.assertIn(token,self.new)
        self.assertNotIn("MODULE_CONFIG(qvfilm_preview_lab)",self.new)

    def test_signature_matches_pinned_boot_fingerprint_and_is_read_only(self):
        fn=self.extract(
            self.new,
            "static MENU_UPDATE_FUNC(qvfilm_rom_sig_update_v0616)",
            "static struct menu_entry qvfilm_hud_menu[]"
        )
        for token in (
            'if (!is_camera("5D3", "*") || get_digic_version() != 5)',
            'if (!entry->selected && !qvfilm_rom_sig_done_v0616)',
            'const volatile unsigned int *p =',
            '(const volatile unsigned int *)0xFF0C0000;',
            'for (i = 0; i < 0x10000; i++)',
            'c += p[i];',
            'qvfilm_rom_sig_v0616 == 0x672EEACEU',
            'MENU_SET_VALUE("ROM:%X", qvfilm_rom_sig_v0616)',
            'MENU_SET_RINFO("SIG PASS")',
            'MENU_SET_RINFO("SIG FAIL")',
        ):
            self.assertIn(token,fn)
        self.assertEqual(fn.count("qvfilm_rom_sig_done_v0616 = 1;"),1)
        for forbidden in ("FIO_","prop_request_change", "firmware_version =",
                          "cam_5d3_123 =", "raw_video_enabled =","RAW_IS_RECORDING =",
                          "task_create(", "memcpy(", "MEM("):
            self.assertNotIn(forbidden,fn)

    def test_rom_menu_one_shot_and_version(self):
        self.assertIn('.name = "QVFIL ROM Check"',self.new)
        self.assertIn('.update = qvfilm_rom_sig_update_v0616',self.new)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.16")',self.new)
        self.assertIn('MENU_SET_VALUE("M:%s", model_text[0] ? model_text : "EMPTY")',self.new)
        self.assertIn('MENU_SET_RINFO("FW:%s", fw_text[0] ? fw_text : "EMPTY")',self.new)
        self.assertNotIn("RAW video blocked",self.new)

    def test_strict_no_double_patch(self):
        with self.assertRaises(ValueError):
            current.patch("wrong source")
        with self.assertRaises(ValueError):
            current.patch(self.new)

if __name__=="__main__":
    unittest.main(verbosity=2)
