# -*- coding: utf-8 -*-
"""Time-scale collapse model for the 102 Ah LFP cell.

    SOH(n) = s0 - a*t^p - b*hinge_n(t; w),          t = n / tau
    ln tau = lnA + Ea/(R*T_eff) + gamma*ln(C)
    T_eff  = T_nominal + dT(T_nominal, C)

Every operating condition enters through ONE number, tau.  The curve shape
(a, p, b, w) is global.  dT is the gap between the nominal set-point and the
temperature the cell actually runs at - it is large (up to +12 K) and has to
be reconstructed at prediction time, because the evaluation interface only
ever passes the nominal set-point.  It is reconstructed from a physical law
(chamber cooling floor + C^2 self-heating, see t_eff_phys), not from a
lookup over the released conditions, so it extrapolates to the unseen ones.

The fit runs in ABSOLUTE SOH, not in per-cell relative units.  Normalising
each cell by its own initial capacity was tried and measurably hurts: the
cells' initial spread (102.0-102.9%) behaves like formation noise, so
dividing it out injects noise instead of removing it, and it silently
shifts the SOH>=90 head threshold to 91.8 for some cells (collapsed CV at
70% SOH: 2.9% absolute vs 13.3% relative).

"""
import json
import os

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from .collapse import fit_master, fit_tau, master, s0_from_early

R_GAS = 8.314
N_CYCLES = 12000
HERE = os.path.dirname(os.path.abspath(__file__))
PRETRAINED = os.path.join(HERE, "pretrained.json")

SMOOTH_W = 21
SOH_HI, SOH_LO = 106.0, 50.0
MIN_CYCLE = 3
DEEP_LEVEL = 85.0
HEAD_LEVEL = 90.0
DT_BOUNDS = ((20.0, 0.0, 0.05), (50.0, 20.0, 6.0))


def t_eff_phys(theta, T_nom, c_rate):
    """Smooth physical temperature surface.

    T_eff = smoothmax(T_nom + k*C^2, floor)

    The parameters are fitted only from temperature measurements belonging to
    the cells supplied to fit().
    """
    floor, k, smooth = theta
    u = np.asarray(T_nom, float) + k * np.asarray(c_rate, float) ** 2
    return 0.5 * (u + floor + np.sqrt((u - floor) ** 2 + smooth ** 2))


class MyModel:
    def __init__(
        self,
        lam=1.0,
        seed=0,
        shape_prior_strength=3.0,
        extra_dT_anchors=None,
        ea_prior_strength=0.1,
    ):
        self.lam = float(lam)
        self.seed = int(seed)
        self.shape_prior_strength = float(shape_prior_strength)
        self.ea_prior_strength = float(ea_prior_strength)
        # Optional extra (T_nom, c_rate, T_eff) points for the effective-temperature
        # surface, used only by the validation harness to simulate a condition whose
        # thermal anchor is available even though its cell is held out.
        # run_model.py never passes this; the default keeps _fit_dT purely data-driven.
        self.extra_dT_anchors = list(extra_dT_anchors or [])
        

        with open(PRETRAINED, encoding="utf-8") as fh:
            self.pre_ = json.load(fh)

        if "d3_prior" not in self.pre_:
            raise RuntimeError(
                "pretrained.json is missing d3_prior. Regenerate it with "
                "analysis/build_pretrained.py."
            )
        if "ea_prior" not in self.pre_:
            raise RuntimeError(
                "pretrained.json is missing ea_prior. Supply an independently "
                "sourced Ea value when running analysis/build_pretrained.py."
            )

    @staticmethod
    def _clean(cell):
        d = cell.soh.dropna()
        x = d["cycle_number"].to_numpy(float)
        y = d["soh_percent"].to_numpy(float)

        keep = (y <= SOH_HI) & (y >= SOH_LO)
        x, y = x[keep], y[keep]
        if len(x) < 8:
            return None

        s0c = s0_from_early(x, y)
        ys = (
            pd.Series(y)
            .rolling(SMOOTH_W, center=True, min_periods=3)
            .median()
            .to_numpy()
        )
        ok = np.isfinite(ys) & (x >= MIN_CYCLE)
        if ok.sum() < 8 or not np.isfinite(s0c) or s0c <= 0:
            return None
        return x[ok], ys[ok], float(s0c)

    @staticmethod
    def _initial_dT_theta(P, T_eff_obs):
        """Create a data-driven starting point; no target-wide shipped prior."""
        P = np.asarray(P, float)
        T_eff_obs = np.asarray(T_eff_obs, float)

        floor0 = float(np.clip(np.percentile(T_eff_obs, 25), 20.0, 50.0))
        denom = np.maximum(P[:, 1] ** 2, 1e-6)
        k_candidates = (T_eff_obs - P[:, 0]) / denom
        k_candidates = k_candidates[np.isfinite(k_candidates)]
        if len(k_candidates):
            k0 = float(np.clip(np.median(np.maximum(k_candidates, 0.0)), 0.0, 20.0))
        else:
            k0 = 2.0
        return np.array([floor0, k0, 2.0], float)

    def _fit_dT(self, observed):
        """Fit T_eff only from currently available training-cell temperatures.

        No missing condition is backfilled from a full-target lookup table.
        """
        rows = list(observed) + list(self.extra_dT_anchors)
        if not rows:
            self.dT_theta_ = None
            self.dT_points_ = np.empty((0, 2), float)
            self.dT_rmse_ = np.nan
            return

        P = np.asarray([[r["T_nom"], r["c_rate"]] for r in rows], float)
        T_eff_obs = np.asarray([r["T_eff"] for r in rows], float)
        theta0 = self._initial_dT_theta(P, T_eff_obs)

        # With fewer than three independent points the 3-parameter surface is
        # underdetermined. Keep the data-driven initial surface instead of
        # importing information from unavailable target conditions.
        if len(P) < 3:
            theta = theta0
        else:
            def resid(theta):
                return t_eff_phys(theta, P[:, 0], P[:, 1]) - T_eff_obs

            theta = theta0
            try:
                res = least_squares(
                    resid,
                    theta0,
                    bounds=DT_BOUNDS,
                    max_nfev=20000,
                )
                if np.all(np.isfinite(res.x)):
                    theta = res.x
            except Exception:
            # Fall back to the data-driven initial surface if optimization fails.
                pass

        self.dT_theta_ = np.asarray(theta, float)
        self.dT_points_ = P
        pred = t_eff_phys(self.dT_theta_, P[:, 0], P[:, 1])
        self.dT_rmse_ = float(np.sqrt(np.mean((pred - T_eff_obs) ** 2)))

    def _dT(self, T_nom, c_rate):
        if self.dT_theta_ is None:
            return 0.0
        return float(t_eff_phys(self.dT_theta_, T_nom, c_rate)) - float(T_nom)

    def fit(self, cells):
        np.random.seed(self.seed)

        recs = []
        for cell in cells:
            got = self._clean(cell)
            if got is None:
                continue
            x, y, s0c = got
            recs.append(
                dict(
                    cell_id=getattr(cell, "cell_id", "?"),
                    T_nom=float(cell.temperature_degC),
                    c_rate=float(cell.c_rate),
                    x=x,
                    y=y,
                    s0=s0c,
                    cell=cell,
                )
            )

        if not recs:
            raise RuntimeError("no usable training cells")
        self.n_cells_ = len(recs)
        self.s0_meas_ = float(np.mean([r["s0"] for r in recs]))

        # ------------------------- public Dataset 3 soft prior
        d3 = self.pre_["d3_prior"]
        d3_prior = {
            "a": float(d3["a_rel"]) * self.s0_meas_ / 100.0,
            "p": float(d3["p"]),
        }

        # ------------------------- temperature observations from CURRENT fit cells
        observed = []
        for r in recs:
            try:
                ts = r["cell"].time_series()
                t = ts["temperature_C"].astype(float)
                if t.notna().mean() >= 0.2:
                    observed.append(
                        dict(
                            T_nom=r["T_nom"],
                            c_rate=r["c_rate"],
                            T_eff=float(t.mean()),
                        )
                    )
            except Exception:
                pass
        # One thermal anchor per unique (T_nom, c_rate). Extra sibling cells at
        # a condition should sharpen that anchor, not add coordinates to the
        # surface fit. With one cell per condition this is a no-op.
        by_cond = {}
        for o in observed:
            by_cond.setdefault((o["T_nom"], o["c_rate"]), []).append(o["T_eff"])
        observed = [
            dict(T_nom=T, c_rate=C, T_eff=float(np.median(v)))
            for (T, C), v in sorted(by_cond.items())
        ]

        self._fit_dT(observed)
        self.n_dT_observed_ = len(observed)

        # ------------------------- shared degradation shape
        curves = [(r["x"], r["y"]) for r in recs]
        n_deep = sum(1 for r in recs if r["y"].min() <= DEEP_LEVEL)

        if n_deep >= 2:
            # Normal/full training: learn the knee from the CURRENT training
            # cells. D3 only regularizes a,p softly.
            fix = {}
            self.shape_mode_ = "target fit + D3 a/p soft prior"
        else:
            # Honest shallow-data fallback: early data cannot identify a knee.
            # Do not import b,w from full target data or from rejected public
            # knee-transfer experiments.
            fix = {"b": 0.0, "w": 1.0}
            self.shape_mode_ = "D3 a/p soft prior; no identifiable knee"

        shape, _tau_joint, rmse, _r2, _eps = fit_master(
            curves,
            s0_init=self.s0_meas_ + 1.0,
            s0_bounds=(98.0, 108.0),
            fix=fix,
            soft_prior=d3_prior,
            prior_strength=self.shape_prior_strength,
        )
        self.shape_ = np.asarray(shape, float)
        self.fit_rmse_ = float(rmse)

        # ------------------------- per-cell early timescale
        taus, Tn, Cr, Te = [], [], [], []
        for r in recs:
            m = r["y"] >= HEAD_LEVEL
            if m.sum() < 8:
                m = np.ones(len(r["y"]), bool)

            tau = fit_tau(self.shape_, r["x"][m], r["y"][m])
            if not np.isfinite(tau):
                continue

            taus.append(tau)
            Tn.append(r["T_nom"])
            Cr.append(r["c_rate"])
            Te.append(r["T_nom"] + self._dT(r["T_nom"], r["c_rate"]))

        # One Arrhenius observation per unique (T_nom, c_rate). Four siblings at
        # 25 degC/1C say more about that condition, not more about the
        # temperature dependence, so they must not get four times the leverage.
        # Te is a function of (T_nom, c_rate) alone, so it is constant per group.
        agg = {}
        for tau, T, C, te in zip(taus, Tn, Cr, Te):
            agg.setdefault((T, C), {"tau": [], "Te": te})["tau"].append(tau)

        self.n_tau_cells_ = len(taus)
        keys = sorted(agg)
        taus = [float(np.median(agg[k]["tau"])) for k in keys]
        Tn = [k[0] for k in keys]
        Cr = [k[1] for k in keys]
        Te = [agg[k]["Te"] for k in keys]

        self.tau_fit_ = np.asarray(taus, float)
        if len(taus) < 2:
            raise RuntimeError("need >=2 conditions with an estimable tau")

        # ------------------------- condition -> tau
        Ea0 = float(self.pre_["ea_prior"]["value_kJ_per_mol"]) * 1000.0
        ln_tau = np.log(self.tau_fit_)
        self.ax_ = {}
        for name, Tk in (
            ("eff", np.asarray(Te) + 273.15),
            ("nom", np.asarray(Tn) + 273.15),
        ):
            self.ax_[name] = self._arrhenius(
                Tk,
                np.asarray(Cr),
                ln_tau,
                Ea0,
            )

    def _arrhenius(self, Tk, C, ln_tau, Ea0):
        """Regularized Arrhenius/C-rate regression.

        ln tau = lnA + Ea/(R*T) + gamma*ln(C)

        Ea is softly pulled toward an independently sourced external value.
        """
        n = len(ln_tau)
        use_c = len(np.unique(C)) > 1 and n >= 4

        cols = [np.ones(n), 1.0 / (R_GAS * Tk)]
        if use_c:
            cols.append(np.log(C))
        X = np.column_stack(cols)

        k = X.shape[1]
        nrm = np.linalg.norm(X, axis=0)
        nrm[nrm == 0] = 1.0
        rows, rhs = [X], [ln_tau]

        # Stronger Ea regularization when fewer independent cells are available.
        base_ea_ridge = nrm[1] * (0.05 + max(0.0, 6.0 - n) / 3.0)
        s_ea = self.ea_prior_strength * base_ea_ridge
        row = np.zeros(k)
        row[1] = s_ea
        rows.append(row[None, :])
        rhs.append([s_ea * Ea0])

        if use_c:
            s_gamma = 0.3 * nrm[2]
            row = np.zeros(k)
            row[2] = s_gamma
            rows.append(row[None, :])
            rhs.append([0.0])

        A = np.vstack(rows)
        co, *_ = np.linalg.lstsq(A, np.concatenate(rhs), rcond=None)
        return dict(
            lnA=float(co[0]),
            Ea=float(co[1]),
            gamma=float(co[2]) if use_c else 0.0,
        )

    def _ln_tau(self, axis, T_value_degC, c_rate):
        par = self.ax_[axis]
        return (
            par["lnA"]
            + par["Ea"] / (R_GAS * (T_value_degC + 273.15))
            + par["gamma"] * np.log(max(c_rate, 1e-6))
        )

    def predict_soh(self, temperature_degC, c_rate):
        T = float(temperature_degC)
        C = float(c_rate)
        T_eff = T + self._dT(T, C)

        ln_tau = (
            self.lam * self._ln_tau("eff", T_eff, C)
            + (1.0 - self.lam) * self._ln_tau("nom", T, C)
        )
        tau = float(np.exp(np.clip(ln_tau, np.log(50.0), np.log(1e6))))

        n = np.arange(1, N_CYCLES + 1, dtype=float)
        soh = master(self.shape_, n / tau)
        soh = np.minimum.accumulate(soh)
        return np.clip(soh, 1.0, 119.9)
