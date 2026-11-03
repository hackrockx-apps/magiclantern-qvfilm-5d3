#!/usr/bin/env python3
"""QVFIL 0.6.13 pinned-source tests for target identity and recorder safety."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_preview_telemetry_v0612 as oldpatch
import apply_camera_id_gate_v0613 as newpatch

class CameraIDGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = HERE / "fixture-2025-mlv_lite.c"
        if not fixture.exists():
            raise unittest.SkipTest("Exact Magic Lantern pinned source injected by CI")
        source = fixture.read_text(encoding="utf-8")
        cls.old = oldpatch.patch(source)
        cls.new = newpatch.patch(source)

    @staticmethod
    def between(s,start,end):
        a=s.index(start)
        b=s.index(end,a)
        return s[a:b]

    def test_recorder_and_codec_not_modified(self):
        for begin,end in [
            ("void raw_video_rec_task()\n{", "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            ("static void compress_task()\n{","static REQUIRES(LiveViewTask) FAST\nvoid process_frame(")
        ]:
            self.assertEqual(self.between(self.old,begin,end),
                             self.between(self.new,begin,end))

    def test_preview_update_renderer_byte_identical(self):
        begin="unsigned int raw_rec_update_preview(unsigned int ctx)\n{"
        tail="    preview_dirty = 1;\n    return 1;\n}"
        def body(s):
            a=s.index(begin)
            b=s.index(tail,a)+len(tail)
            return s[a:b]
        self.assertEqual(body(self.old),body(self.new))

    def test_camera_guard_accepts_only_verified_init_or_live_5d3_123(self):
        s=self.new
        self.assertIn(
            '#define QVFIL_LAB_CAMERA_OK (get_digic_version() == 5 && '
            '(cam_5d3_123 || is_camera("5D3", "1.2.3")))',
            s)
        self.assertIn("#define QVFIL_LAB_STBY (qvfilm_preview_lab && QVFIL_LAB_CAMERA_OK",s)
        self.assertIn('cam_5d3_123 = is_camera("5D3",  "1.2.3");',s)
        self.assertNotIn('is_camera("5D3", "*"))',s)
        for expected in ('raw_video_enabled && lv','is_movie_mode() && RAW_IS_IDLE',
                         'lv_dispsize == 1', 'res_x <= 1600', 'res_y <= 900',
                         'BPP == 10', 'raw_info.bits_per_pixel == 14'):
            self.assertIn(expected,s)

    def test_status_shows_identity_values_if_both_checks_fail(self):
        s=self.new
        menu=self.between(s,
            "static MENU_UPDATE_FUNC(qvfilm_preview_lab_update)",
            "static struct menu_entry qvfilm_hud_menu[]")
        self.assertIn('else if (!QVFIL_LAB_CAMERA_OK)',menu)
        self.assertIn('MENU_SET_RINFO("ID %d/%d D%d", cam_5d3_123,',menu)
        self.assertIn('is_camera("5D3", "1.2.3"), get_digic_version())',menu)
        self.assertNotIn('MENU_SET_RINFO("5D3.123 ONLY")',menu)
        self.assertIn('MENU_SET_RINFO("ARMED 0F")',menu)
        self.assertIn('MENU_SET_RINFO("F:%u %dms"',menu)

    def test_existing_controls_and_release_id(self):
        s=self.new
        for token in (
            'static int qvfilm_preview_lab = 0;',
            'MENU_SET_RINFO("QVFIL v0.6.13")',
            '.name = "QVFIL Color Lab"',
            '.choices = CHOICES("OFF", "Color STBY")',
            '.name = "QVFIL Preview Guide"',
            '.name = "QVFIL Lossless Diag"',
            '.name = "QVFIL LJ Error Guide"',
            'if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)',
            'Lossless RAW blocked on 5D3.123',
        ):
            self.assertIn(token,s)
        self.assertNotIn('MODULE_CONFIG(qvfilm_preview_lab)',s)

    def test_wrong_source_and_repeat_patch_fail_closed(self):
        with self.assertRaises(ValueError):
            newpatch.patch("not the exact upstream source")
        with self.assertRaises(ValueError):
            newpatch.patch(self.new)

if __name__ == "__main__":
    unittest.main(verbosity=2)
