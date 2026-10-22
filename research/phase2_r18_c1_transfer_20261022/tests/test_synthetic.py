"""End-to-end checks on synthetic cells with planted physics (no real data needed)."""
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd

from src import baselines, c1io, metrics, model_adapter, synth, view
from src.common import PROTOCOL

INFO = PROTOCOL["information_structure"]


def predictions(vw, **kw):
    return {k: model_adapter.predict(vw, k, **kw) for k in range(1, len(vw.boundaries))
            if k in vw.truth}


class Synthetic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="r18_synth_")
        cls.planted = {
            "match": synth.make_cell(cls.tmp, "match", days=210, b_dis=0.75, b_chg=0.75, seed=1),
            "mismatch": synth.make_cell(cls.tmp, "mismatch", days=210, b_dis=0.60, b_chg=1.00, seed=2),
            "onec": synth.make_cell(cls.tmp, "onec", c_rate=1.0, b_dis=0.75, b_chg=0.75, seed=3),
        }
        cls.raw = {c: c1io.read_cell(cls.tmp, c) for c in cls.planted}
        cls.views = {c: view.build_view(cls.raw[c], c, with_full=True) for c in cls.planted}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ---- information structure ------------------------------------------------------
    def test_structure(self):
        vw = self.views["match"]
        self.assertGreaterEqual(len(vw.boundaries), 5)
        self.assertEqual([a["m"] for a in vw.anchors], list(range(len(vw.boundaries))))
        per_window = pd.Series([p["m"] for p in vw.programs]).value_counts()
        self.assertTrue((per_window <= 6).all() and (per_window >= 4).all())
        anchor_cycles = {a["cycle"] for a in vw.anchors}
        self.assertFalse(anchor_cycles & {p["cycle"] for p in vw.programs})
        for p in vw.programs:
            self.assertTrue(p["detected"])

    def test_truncation_irrelevant_for_step(self):
        for c in ("match", "onec"):
            d = [abs(p["robust"] - p["robust_full"]) for p in self.views[c].programs]
            self.assertLessEqual(np.median(d), 0.05)

    def test_planted_step_recovered(self):
        for c, tol in (("match", 0.15), ("onec", 0.30)):
            tr = self.planted[c].set_index("cycle_number")
            off = np.array([p["robust_interp"] - tr.loc[p["cycle"], "s_dis"]
                            for p in self.views[c].programs])
            self.assertLess(np.std(off), tol, c)

    # ---- causality and leakage ------------------------------------------------------
    def test_future_rows_replaced_by_noise(self):
        vw = self.views["match"]
        rng = np.random.default_rng(0)
        for k in (2, 3):
            raw = self.raw["match"].copy()
            fut = raw["absolute_time"] > vw.boundaries[k]
            for col in ("voltage_V", "current_A", "step_capacity_Ah", "temperature_C"):
                raw.loc[fut, col] = rng.uniform(-5, 120, int(fut.sum()))
            cut_view = view.build_view(raw, "match")
            self.assertTrue((cut_view.boundaries[:k + 1] == vw.boundaries[:k + 1]).all())
            self.assertEqual(model_adapter.predict(cut_view, k)["q"], model_adapter.predict(vw, k)["q"])
            self.assertEqual(baselines.e4_baseline(cut_view, k), baselines.e4_baseline(vw, k))
            self.assertEqual(baselines.e5_trend(cut_view, k), baselines.e5_trend(vw, k))

    def test_hidden_rows_never_used(self):
        """Voltages below the visible depth and the anchors' discharges carry no input."""
        vw = self.views["match"]
        raw = self.raw["match"].copy()
        dis = raw["step_type"] == c1io.STEP["discharge"]
        anchor_cycles = raw["cycle_number"].isin({a["cycle"] for a in vw.anchors})
        hide = dis & ((raw["step_capacity_Ah"] > INFO["visible_depth_ah"]) | anchor_cycles)
        raw.loc[hide, "voltage_V"] = np.random.default_rng(1).uniform(2.0, 3.6, int(hide.sum()))
        noisy = view.build_view(raw, "match")
        for k in range(1, len(vw.boundaries)):
            if k in vw.truth:
                self.assertEqual(model_adapter.predict(noisy, k)["q"], model_adapter.predict(vw, k)["q"])

    def test_dataset_carries_only_label0(self):
        ds = view.make_dataset(self.views["match"], 3)
        self.assertEqual(len(ds.checkups_released), 1)
        self.assertEqual(float(ds.checkups_released["capacity_Ah"].iloc[0]), self.views["match"].label0)
        self.assertTrue(all(s[3] <= ds.until for s in ds.steps))
        self.assertTrue(all(c["t_end"] <= ds.until for c in ds.charges))

    # ---- the submitted logic on planted physics ------------------------------------
    def test_branches(self):
        p = predictions(self.views["match"])
        self.assertEqual(p[1]["branch"], "fallback")
        self.assertTrue(all(p[k]["branch"] == "phase" for k in p if k >= 2))
        g = predictions(self.views["match"], scenario="gap")
        self.assertTrue(all(g[k]["branch"] == "sqrt_gap" for k in g if k >= 2))
        a = predictions(self.views["match"], scenario="no_steps")
        self.assertTrue(all(a[k]["branch"] == "anchor" for k in a))

    def test_step_update_beats_anchor_only(self):
        vw = self.views["match"]
        p, a = predictions(vw), predictions(vw, scenario="no_steps")
        ks = [k for k in p if k >= 2]
        e2 = np.mean([abs(p[k]["q"] - vw.truth[k]) for k in ks])
        e0 = np.mean([abs(a[k]["q"] - vw.truth[k]) for k in ks])
        self.assertLess(e2, 0.5 * e0)

    def test_beta_matched_and_mismatched(self):
        """V2's charge-side beta follows the planted charge side; the oracle sees the discharge side."""
        for cell, b_chg, b_dis in (("match", 0.75, 0.75), ("mismatch", 1.00, 0.60)):
            vw = self.views[cell]
            p = predictions(vw, key="robust_interp")
            last = max(p)
            xs = {k: p[k]["x"] for k in p}
            self.assertLess(abs(p[last]["beta"] - 1 / b_chg), 0.25, cell)
            self.assertLess(abs(model_adapter.oracle_beta(vw, last, xs) - 1 / b_dis), 0.25, cell)
        p = predictions(self.views["mismatch"], key="robust_interp")
        last = max(p)
        gap = model_adapter.oracle_beta(self.views["mismatch"], last, {k: p[k]["x"] for k in p}) - p[last]["beta"]
        self.assertGreater(gap, 0.30)

    # ---- decision rules -------------------------------------------------------------
    def test_decision_rules(self):
        s = {"n_cells": 6, "macro_ratio": 0.5, "cells_better": 6, "loco_ratio_max": 0.6,
             "macro_gain": 0.5, "cells_worse": 0}
        self.assertEqual(metrics.decide_c1(s, 6, 0.05), "supported")
        self.assertEqual(metrics.decide_c1(s, 4, 0.05), "inconclusive")
        self.assertEqual(metrics.decide_c1({**s, "macro_ratio": 1.1}, 6, 0.05), "not_supported")
        self.assertEqual(metrics.decide_c1({**s, "cells_better": 3}, 6, 0.05), "not_supported")
        self.assertEqual(metrics.decide_gain(s, 0.05), "supported")
        self.assertEqual(metrics.decide_gain({**s, "macro_gain": -0.1}, 0.05), "not_supported")
        self.assertEqual(metrics.decide_gain({**s, "macro_gain": 0.01, "cells_better": 4}, 0.05),
                         "inconclusive")
        self.assertEqual(metrics.decide_gain({**s, "macro_gain": 0.01, "cells_better": 2,
                                              "cells_worse": 4}, 0.05, worse_rule=True,
                                             better_rule_on_fail=False), "not_supported")
        self.assertEqual(metrics.decide_c5(0.30, {"a": 0.29, "b": 0.35, "c": 0.40}, 0.05), "supported")
        self.assertEqual(metrics.decide_c5(0.50, {"a": 0.29, "b": 0.35, "c": 0.40}, 0.05), "not_supported")
        self.assertEqual(metrics.decide_c8({"a": 0.1, "b": 0.2, "c": 0.25}), "supported")
        self.assertEqual(metrics.decide_c8({"a": 0.1, "b": 1.2, "c": 0.25}), "not_supported")
        self.assertEqual(metrics.decide_c1({"n_cells": 2}, 2, 0.05), "insufficient")


if __name__ == "__main__":
    unittest.main()
