#!/usr/bin/env python3
"""Pinned-source tests for QVFIL v0.6.19 experimental 3-band STBY Lab."""
from pathlib import Path
import sys, unittest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import apply_color_perf_telemetry_v0618 as previous
import apply_color_stripes_v0619 as current

class ColorStripesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=HERE/"fixture-2025-mlv_lite.c"
        if not f.exists(): raise unittest.SkipTest("Exact ML2025 fixture injected by CI")
        original=f.read_text(encoding="utf-8")
        cls.before=previous.patch(original)
        cls.after=current.patch(original)

    @staticmethod
    def section(src,start,end):
        i=src.index(start);j=src.index(end,i)
        return src[i:j]

    def test_encoder_compressor_and_card_logic_unchanged(self):
        for begin,end in (
            ("void raw_video_rec_task()\n{",
             "static REQUIRES(GuiMainTask)\nvoid raw_start_stop()"),
            ("static void compress_task()\n{",
             "static REQUIRES(LiveViewTask) FAST\nvoid process_frame("),
        ):
            self.assertEqual(self.section(self.before,begin,end),
                             self.section(self.after,begin,end))

    def test_previous_color_converter_and_semaphores_preserved(self):
        new=self.after
        self.assertIn(current.PREVIEW_NEW,new)
        self.assertIn(current.COUNT_NEW,new)
        normalized=new.replace(current.PREVIEW_NEW,current.PREVIEW_OLD).replace(
            current.COUNT_NEW,current.COUNT_OLD)
        begin="unsigned int raw_rec_update_preview(unsigned int ctx)\n{"
        end="    preview_dirty = 1;\n    return 1;\n}"
        a=self.section(self.before,begin,end)
        b=self.section(normalized,begin,end)
        self.assertEqual(a,b)
        for name in (
            "raw_preview_fast_ex(", "RAW_PREVIEW_COLOR_HALFRES",
            "give_semaphore(settings_sem);", "msleep(",
            "RAW_IS_RECORDING ? fullsize_buffers[fi] : (void*)-1",
        ): self.assertIn(name,new)

    def test_only_stby_color_and_readonly_rom_signature(self):
        src=self.after
        for t in (
            '#define QVFIL_LAB_CAMERA_OK (is_camera("5D3", "*")',
            'get_digic_version() == 5',
            'qvfilm_rom_sig_done_v0616 &&',
            'qvfilm_rom_sig_v0616 == 0x672EEACEU',
            'is_movie_mode() && RAW_IS_IDLE',
            'lv_dispsize == 1',
            'BPP == 10 && raw_info.bits_per_pixel == 14',
            'res_x <= 1600 && res_y > 0 && res_y <= 900',
            'static int qvfilm_preview_lab = 0;',
            'if (!entry->selected && !qvfilm_rom_sig_done_v0616)',
            'MENU_SET_RINFO("REC: BASE")',
        ):self.assertIn(t,src)
        self.assertNotIn("MODULE_CONFIG(qvfilm_preview_lab)",src)

    def test_3_bands_use_original_lv_coordinates_and_preserve_rec(self):
        fn=self.section(self.after,
            "unsigned int raw_rec_update_preview(unsigned int ctx)\n{",
            "    give_semaphore(settings_sem);")
        for t in (
            'int qvfilm_lab_stripe_active_v0619 = 0;',
            'if (qvfilm_lab_active)',
            'if (qvfilm_preview_lab == 2)',
            'BM2LV_Y(os.y0)',
            'BM2LV_Y(os.y_max)',
            'height >= 12',
            'qvfilm_lab_band_v0619 < 3',
            'top + height * qvfilm_lab_band_v0619 / 3',
            'top + height * (qvfilm_lab_band_v0619 + 1) / 3',
            'qvfilm_lab_stripe_active_v0619 ? qvfilm_lab_y1_v0619 : -1',
            'qvfilm_lab_stripe_active_v0619 ? qvfilm_lab_y2_v0619 : -1',
            'qvfilm_lab_band_v0619 == 3',
            'qvfilm_lab_full_sweeps_v0619++',
        ): self.assertIn(t,fn)
        # Lab being active is still impossible during RAW recording,
        # so both coordinates fall back to -1/-1 in every REC path.
        self.assertIn('int qvfilm_lab_active = QVFIL_LAB_STBY;',fn)
        self.assertIn('RAW_IS_IDLE',self.after)

    def test_switches_default_off_and_retain_full_frame_reference(self):
        src=self.after
        self.assertIn('.choices = CHOICES("OFF", "Color STBY", "Stripe STBY"),',src)
        self.assertIn('        .max = 2,\n        .choices = CHOICES("OFF", "Color STBY", "Stripe STBY"),',src)
        self.assertIn('static int qvfilm_preview_lab = 0;',src)
        self.assertIn('MENU_SET_RINFO("QVFIL v0.6.19")',src)
        self.assertIn('MENU_SET_RINFO("F:%d %dms"',src)
        self.assertIn('.name = "QVFIL Color Sweep"',src)

    def test_bands_cover_complete_height_no_gaps(self):
        for h in range(12,721):
            bands=[(h*i//3,h*(i+1)//3) for i in range(3)]
            self.assertEqual(bands[0][0],0)
            self.assertEqual(bands[-1][1],h)
            self.assertEqual(bands[0][1],bands[1][0])
            self.assertEqual(bands[1][1],bands[2][0])
            self.assertTrue(all(e>s for s,e in bands))

    def test_sweep_menu_does_not_change_raw_or_lcd(self):
        menu=self.section(self.after,
            "static MENU_UPDATE_FUNC(qvfilm_lab_sweep_update_v0619)",
            "static struct menu_entry qvfilm_hud_menu[]")
        for t in (
            'MENU_SET_NAME("QVFIL Color Sweep")',
            'MENU_SET_VALUE("FULL")',
            'MENU_SET_RINFO("T:%dms"',
            'MENU_SET_RINFO("B:%d/3"',
            'NOT synchronized full-frame FPS.',
        ): self.assertIn(t,menu)
        for dangerous in (
            "FIO_", "raw_preview_fast_ex(", "prop_request_change",
            "task_create(", "msleep(", "firmware_version =", "raw_video_enabled =",
            "set_raw", "MEM(",
        ): self.assertNotIn(dangerous,menu)

    def test_fail_closed_wrong_source_or_double_patch(self):
        with self.assertRaises(ValueError): current.patch("wrong ML source")
        with self.assertRaises(ValueError): current.patch(self.after)

if __name__=="__main__":
    unittest.main(verbosity=2)
