#!/usr/bin/env python3
"""Exact-source regression tests for 5D3 ROM-verified Color Lab v0.6.17."""
from pathlib import Path
import unittest
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import apply_rom_signature_probe_v0616 as previous
import apply_rom_verified_color_v0617 as current

class RomVerifiedColorV0617(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=HERE/"fixture-2025-mlv_lite.c"
        if not f.exists():
            raise unittest.SkipTest("Exact pinned upstream fixture injected by CI")
        src=f.read_text(encoding="utf-8")
        cls.before=previous.patch(src)
        cls.after=current.patch(src)

    @staticmethod
    def section(src,start,end):
        i=src.index(start);j=src.index(end,i)
        return src[i:j]

    def test_recorder_compressor_byte_identical(self):
        for a,b in (
            ("void raw_video_rec_task()\n{",
             "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            ("static void compress_task()\n{",
             "static REQUIRES(LiveViewTask) FAST\nvoid process_frame(")
        ):
            self.assertEqual(self.section(self.before,a,b),self.section(self.after,a,b))

    def test_frame_renderer_and_existing_color_path_byte_identical(self):
        begin="unsigned int raw_rec_update_preview(unsigned int ctx)\n{"
        tail="    preview_dirty = 1;\n    return 1;\n}"
        def renderer(src):
            i=src.index(begin);return src[i:src.index(tail,i)+len(tail)]
        self.assertEqual(renderer(self.before),renderer(self.after))

    def test_no_rom_read_in_preview_and_strict_gate(self):
        src=self.after
        a=src.index("static unsigned int qvfilm_rom_sig_v0616 = 0;")
        macro=src.index("#define QVFIL_LAB_CAMERA_OK")
        update=src.index("unsigned int raw_rec_update_preview(unsigned int ctx)")
        self.assertLess(a,macro)
        self.assertLess(macro,update)
        self.assertEqual(src.count("static unsigned int qvfilm_rom_sig_v0616 = 0;"),1)
        self.assertEqual(src.count("static int qvfilm_rom_sig_done_v0616 = 0;"),1)
        guard=self.section(src,"#define QVFIL_LAB_CAMERA_OK","#define QVFIL_LAB_STBY")
        for token in (
            'is_camera("5D3", "*")',
            'get_digic_version() == 5',
            'qvfilm_rom_sig_done_v0616',
            'qvfilm_rom_sig_v0616 == 0x672EEACEU'
        ): self.assertIn(token,guard)
        self.assertNotIn('is_camera("5D3", "1.2.3")',guard)
        self.assertIn('QVFIL_LAB_CAMERA_OK && raw_video_enabled && lv',src)
        for term in ("is_movie_mode() && RAW_IS_IDLE", "lv_dispsize == 1",
                     "res_x <= 1600", "res_y <= 900",
                     "BPP == 10", "raw_info.bits_per_pixel == 14"):
            self.assertIn(term,src)
        self.assertNotIn("MODULE_CONFIG(qvfilm_preview_lab)",src)
        self.assertIn("static int qvfilm_preview_lab = 0;",src)

    def test_menu_guides_manual_rom_check_then_standby(self):
        src=self.after
        menu=self.section(src,
            "static MENU_UPDATE_FUNC(qvfilm_preview_lab_update)",
            "static MENU_UPDATE_FUNC(qvfilm_id_probe_update)")
        for token in (
            'MENU_SET_RINFO("SAFE OFF")',
            'MENU_SET_RINFO("REC: BASE")',
            'MENU_SET_RINFO("5D3 D5 ONLY")',
            'MENU_SET_RINFO("RUN ROM CHECK")',
            'MENU_SET_RINFO("ROM MISMATCH")',
            'MENU_SET_RINFO("ARMED 0F")',
            'MENU_SET_RINFO("F:%u %dms"',
            'RAW_IS_IDLE',
        ):
            self.assertIn(token,menu)
        self.assertNotIn('MENU_SET_RINFO("ID %d/%d D%d"',menu)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.17")',src)
        self.assertIn('.name = "QVFIL ROM Check"',src)
        self.assertIn('.name = "QVFIL Color Lab"',src)
        self.assertIn('.choices = CHOICES("OFF", "Color STBY")',src)

    def test_rom_signature_calculation_still_selected_only(self):
        sig=self.section(self.after,
            "static MENU_UPDATE_FUNC(qvfilm_rom_sig_update_v0616)",
            "static struct menu_entry qvfilm_hud_menu[]")
        for token in (
            'if (!entry->selected && !qvfilm_rom_sig_done_v0616)',
            'if (!qvfilm_rom_sig_done_v0616)',
            '(const volatile unsigned int *)0xFF0C0000',
            'for (i = 0; i < 0x10000; i++)',
            'qvfilm_rom_sig_done_v0616 = 1;',
            'MENU_SET_RINFO("SIG PASS")',
            'MENU_SET_RINFO("SIG FAIL")',
        ): self.assertIn(token,sig)
        self.assertEqual(self.section(self.before,
            "static MENU_UPDATE_FUNC(qvfilm_rom_sig_update_v0616)",
            "static struct menu_entry qvfilm_hud_menu[]"),
            sig)

    def test_non_camera_sources_rejected(self):
        with self.assertRaises(ValueError):
            current.patch("invalid code")
        with self.assertRaises(ValueError):
            current.patch(self.after)

if __name__=="__main__":
    unittest.main(verbosity=2)
