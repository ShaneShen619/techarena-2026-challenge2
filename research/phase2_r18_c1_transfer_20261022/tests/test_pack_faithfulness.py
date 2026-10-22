"""The step adapter equals the submitted code on the pack's own data (needs the package data/)."""
import unittest

import numpy as np

from src import steps
from src.common import PACKAGE, mt

DATA = PACKAGE / "data"


def pack_events():
    """(seg, i, v, e, d) for every deep discharge of the pack, as ``mt._step_depths`` builds them."""
    from framework.data import load_operation
    op = load_operation(str(DATA))
    for _, seg in op.groupby("segment", sort=True):
        seg = seg.reset_index(drop=True)
        i, ah = mt._integrated_ah(seg)
        u = seg["pack_voltage_V"].to_numpy(float)
        v = seg[mt.CELLS].to_numpy(float)
        cv = (u >= mt.CV_V_MIN) & (i > 0) & (i < mt.END_I_MAX_A)
        for e in np.where(cv & ~np.r_[cv[1:], False])[0]:
            depth = ah[e] - ah[e:]
            peak = np.maximum.accumulate(depth)
            back = np.where(peak - depth > mt.STEP_RECHARGE_AH)[0]
            d = depth[:back[0]] if len(back) else depth
            if d.max() >= mt.STEP_MIN_DEPTH_AH:
                yield seg, i, v, e, d


@unittest.skipUnless((DATA / "operation").is_dir(), "package data/ not present")
class PackFaithfulness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.events = list(pack_events())

    def test_events_found(self):
        self.assertGreaterEqual(len(self.events), 40)

    def test_scaled_bands_identity_at_10A(self):
        self.assertEqual(steps.scaled_variants(10.0), tuple(
            ((b[0] * 1.0, b[1] * 1.0), u, lo, m, ir) for b, u, lo, m, ir in mt.STEP_VARIANTS))
        self.assertEqual(steps.scaled_main_band(10.0), tuple(mt.STEP_BAND_A))

    def test_robust_step_bit_identical(self):
        n_cmp = 0
        for seg, i, v, e, d in self.events:
            sub = mt._robust_step(seg, i, v, e, d)
            cur = i[e:e + len(d)]
            mine, _ = steps.robust_step(cur, v[e:e + len(d)], d, mt.STEP_VARIANTS,
                                        mt._pulse_resistance(seg, i, e))
            if np.isnan(sub):
                self.assertTrue(np.isnan(mine))
            else:
                self.assertEqual(sub, mine)
                n_cmp += 1
        self.assertGreaterEqual(n_cmp, 40)

    def test_keep_rule_identical(self):
        kept = 0
        for seg, i, v, e, d in self.events:
            cur = i[e:e + len(d)]
            vv = v[e:e + len(d)]
            band = (cur > mt.STEP_BAND_A[0]) & (cur < mt.STEP_BAND_A[1])
            sub = (band.sum() >= mt.STEP_MIN_BAND_SAMPLES
                   and np.isfinite(mt._locate_step(d[band], vv[band])).any())
            self.assertEqual(bool(sub), steps.main_detected(cur, vv, d, mt.STEP_BAND_A))
            kept += bool(sub)
        self.assertGreaterEqual(kept, 40)

    def test_interp_locator_within_one_sample(self):
        for seg, i, v, e, d in self.events:
            cur = i[e:e + len(d)]
            vv = v[e:e + len(d)]
            band = (cur > mt.STEP_BAND_A[0]) & (cur < mt.STEP_BAND_A[1])
            if band.sum() < mt.STEP_MIN_BAND_SAMPLES:
                continue
            a = np.array(mt._locate_step(d[band], vv[band]))
            b = np.array(steps.locate_step_interp(d[band], vv[band]))
            ok = np.isfinite(a)
            spacing = np.max(np.diff(d[band])) if band.sum() > 1 else 0.0
            self.assertTrue(np.all(np.isfinite(b[ok])))
            self.assertTrue(np.all(a[ok] - b[ok] >= -1e-12))
            self.assertTrue(np.all(a[ok] - b[ok] <= spacing + 1e-12))

    def test_charge_top_identical(self):
        from framework.data import load_operation
        op = load_operation(str(DATA))
        n = 0
        for _, seg in op.groupby("segment", sort=True):
            seg = seg.reset_index(drop=True)
            fc = mt._first_full_charge(seg)
            if not fc:
                continue
            i, ah = mt._integrated_ah(seg)
            pos = np.where(i > mt.CHARGE_I_MIN_A)[0]
            start = end = pos[0]
            while end + 1 < len(i) and i[end + 1] > mt.CHARGE_I_MIN_A:
                end += 1
            base = ah[max(start - 1, 0)]
            q = ah[start:end + 1] - base
            v4 = seg[mt.CELLS].to_numpy(float)[start:end + 1]
            mine = steps.charge_top(i[start:end + 1], q, v4, np.nan, cc_min_a=mt.CC_I_MIN_A)
            self.assertAlmostEqual(mine, fc["top"], places=12)
            n += 1
        self.assertGreaterEqual(n, 8)


if __name__ == "__main__":
    unittest.main()
