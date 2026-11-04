#!/usr/bin/env python3
import unittest
import feasibility as f

class BandwidthModel(unittest.TestCase):
    def test_known_reference_4k_widescreen(self):
        m=f.MODES[0]
        self.assertEqual((m.width,m.height,m.fps,m.bitdepth),(3840,1600,24,10))
        self.assertAlmostEqual(f.rate_mb_s(m),184.32,places=3)
        self.assertAlmostEqual(f.rate_mb_s(m,2),92.16,places=3)

    def test_full_uhd_25p_storage(self):
        m=next(x for x in f.MODES if x.label=="UHD 16:9 research")
        self.assertAlmostEqual(f.rate_mb_s(m),259.2,places=4)
        self.assertAlmostEqual(f.required_ratio(m,100,.20),3.24,places=4)
        self.assertFalse(f.evaluate(m,100,.20,2)["within_modeled_storage_budget"])

    def test_full_uhd_14b_24p_storage(self):
        m=next(x for x in f.MODES if x.label=="UHD 16:9 research 14b")
        self.assertAlmostEqual(f.rate_mb_s(m),348.3648,places=3)

    def test_4k_width_requires_compression_at_100mb(self):
        m=f.MODES[0]
        self.assertAlmostEqual(f.required_ratio(m,100,.20),2.304,places=3)
        self.assertFalse(f.evaluate(m,100,.20,2)["within_modeled_storage_budget"])
        self.assertTrue(f.evaluate(m,100,.20,2.5)["within_modeled_storage_budget"])

    def test_validation_and_assumptions(self):
        with self.assertRaises(ValueError):f.required_ratio(f.MODES[0],0)
        with self.assertRaises(ValueError):f.required_ratio(f.MODES[0],100,1)
        with self.assertRaises(ValueError):f.rate_mb_s(f.MODES[0],.9)
        for m in f.MODES:
            self.assertIn("NOT_A_CAMERA_VALIDATION",f.evaluate(m,100,.2,1))
            self.assertIn("caveat",f.evaluate(m,100,.2,1))

if __name__=="__main__":
    unittest.main(verbosity=2)
