"""Round-17 two-term law with per-term clocks (WP2 designs B0, S, C, O1, O2, D).

``LawFit17(cfg)`` equals ``smodel5c.LawFit(cfg)`` when every round-17 key is at its default
(checked in WP0). Round-17 keys:

  switch_fix   B0: chamber-switch rows at the bounding-row temperature
  cal_Ea_kJ    calendar-term clock Ea applied to time (default = Ea_kJ, 37.3)
  cal_soc      None | "tum2" | "tum1" | "naumann2": calendar clock weight k_SOC(SOC)^2 (or ^1), normalised
               to a time-weighted mean of 1 over the visible observed rows (kappa)
  ck_soc       "half" | "entry" | "zero": SOC rule for true-checkup rows
  breakin      "exp" (A_b (1 - exp(-tau/tau_b))) | "overhang" (A_oh X_oh(t))
  tau_b_days   override of the fixed break-in time constant (O1 grid); None = prior2 mean
  oh           overhang settings: soc0, ea_tau_kJ, t_full_ref_d, T_full_ref_C, x0 ("zero" | "eq")
  use_cyc      False drops the cycle term and its prior row (D)
"""
import json
import os

import numpy as np
import pandas as pd

from smodel import Q_CK0, _lm, anchors
from smodel5c import BASE, LawFit, beta_a4_safe, restarts, select_steps
from stress import horizon_lag_days
from stress17 import NOM, clock, overhang_state, soc_series, stress_table17

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
EXT = os.path.join(STUDY, "wp1", "outputs", "external_params.json")

R17 = dict(switch_fix=False, cal_Ea_kJ=None, cal_soc=None, ck_soc="half", breakin="exp", tau_b_days=None,
           oh=None, use_cyc=True)


def _ext():
    return json.load(open(EXT))


def ksoc_fun(name):
    """k_SOC normalised to 1 at SOC = 50 %, from the frozen WP1 parameters."""
    p = _ext()["P2_k_SOC"]
    if name.startswith("tum"):
        s = np.array(sorted(float(k) for k in p["tum_table"]))
        v = np.array([p["tum_table"][f"{x:g}"] for x in s])
        base = lambda x: np.interp(np.clip(x, 0, 1), s, v)
    elif name.startswith("naumann"):
        c, d = p["naumann"]["c"], p["naumann"]["d"]
        base = lambda x: (c * (np.clip(x, 0, 1) - 0.5) ** 3 + d) / d
    else:
        raise ValueError(name)
    power = 2 if name.endswith("2") else 1
    return lambda x: base(np.asarray(x, float)) ** power


def oh_defaults():
    p = _ext()["P3_overhang"]
    return dict(soc0=0.30, ea_tau_kJ=p["Ea_tau_kJ_main"], t_full_ref_d=p["t_full_ref"]["days"],
                T_full_ref_C=p["t_full_ref"]["T_C"], x0="zero", f_oh=p["f_oh_sony"]["value"], line="stated")


_SOC = {}


class LawFit17(LawFit):
    def __init__(self, cfg=None):
        cfg = dict(cfg or {})
        r17 = {k: cfg.pop(k) for k in list(cfg) if k in R17}
        super().__init__(cfg)
        self.r17 = dict(R17, **r17)
        if self.r17["breakin"] == "overhang":
            self.r17["oh"] = dict(oh_defaults(), **(self.r17["oh"] or {}))

    # ------------------------------------------------------------ params
    def _names(self, months_off):
        names = super()._names(months_off)
        r = self.r17
        if r["breakin"] == "overhang":
            names = ["logA_oh" if n == "logA_b" else n for n in names]
        if not r["use_cyc"]:
            names = [n for n in names if n != "logA_cyc"]
        return names

    def _prior(self, names):
        mu, sd = super()._prior([("logA_b" if n == "logA_oh" else n) for n in names])
        if "logA_oh" in names:
            i = names.index("logA_oh")
            mu[i], sd[i] = self._oh_prior
        return mu, sd

    def _tau_b(self):
        if self.r17["tau_b_days"] is not None:
            return float(self.r17["tau_b_days"])
        return float(np.exp(self.cfg["prior2"]["logtau_b"][0]))

    def _M17(self, p, cl):
        r = self.r17
        if r["breakin"] == "overhang":
            brk = np.exp(p["logA_oh"]) * cl["X"]
        else:
            brk = np.exp(p["logA_b"]) * (1 - np.exp(-np.clip(cl["tau_b"], 0, None) / self._tau_b()))
        M = brk + np.exp(p["logA_cal"]) * np.sqrt(np.clip(cl["tau_cal"], 0, None))
        if r["use_cyc"]:
            M = M + np.exp(p["logA_cyc"]) * cl["ah"]
        return M

    def terms(self, p, cl):
        """Per-term loss (Ah) at the evaluation times, for WP0 F3."""
        r = self.r17
        brk = (np.exp(p["logA_oh"]) * cl["X"] if r["breakin"] == "overhang"
               else np.exp(p["logA_b"]) * (1 - np.exp(-np.clip(cl["tau_b"], 0, None) / self._tau_b())))
        cal = np.exp(p["logA_cal"]) * np.sqrt(np.clip(cl["tau_cal"], 0, None))
        cyc = np.exp(p["logA_cyc"]) * cl["ah"] if r["use_cyc"] else np.zeros_like(cal)
        return brk, cal, cyc

    # ------------------------------------------------------------ table and clocks
    def table(self, op, fc, ck, k, hz, key=None, tab_cache=None):
        r = self.r17
        need_soc = r["cal_soc"] is not None or r["breakin"] == "overhang"
        wname = r["cal_soc"] if r["cal_soc"] is not None else ("tum2" if need_soc else None)
        tkey = (key, self.cfg["checkup_Ah"], str(hz), r["switch_fix"], wname, r["ck_soc"])
        if tab_cache is not None and key is not None and tkey in tab_cache:
            return tab_cache[tkey]
        op2 = op
        if need_soc:
            skey = ("soc", key)
            if key is not None and skey in _SOC:
                s = _SOC[skey]
            else:
                s = soc_series(op, fc, ck)
                if key is not None:
                    _SOC[skey] = s
            op2 = op.copy()
            op2["soc"] = s
        tab = stress_table17(op2, ck[k], ck, horizon=hz, checkup_Ah=self.cfg["checkup_Ah"],
                             switch_fix=r["switch_fix"], wfun=ksoc_fun(wname) if wname else None, ck_soc=r["ck_soc"])
        if tab_cache is not None and key is not None:
            tab_cache[tkey] = tab
        return tab

    def clocks(self, tab, times):
        c, r = self.cfg, self.r17
        out = {}
        out["tau_b"] = clock(tab, c["Ea_kJ"] * 1e3, times)
        ea_cal = (r["cal_Ea_kJ"] if r["cal_Ea_kJ"] is not None else c["Ea_kJ"]) * 1e3
        w = None
        if r["cal_soc"] is not None:
            obs = tab["kind"].to_numpy() == "observed"
            ww = tab["w"].to_numpy(float)
            dd = tab["days"].to_numpy(float)
            ok = obs & np.isfinite(ww)
            kappa = float((ww[ok] * dd[ok]).sum() / max(dd[ok].sum(), 1e-12))
            w = np.where(np.isfinite(ww), ww, kappa) / kappa
            self.kappa = kappa
        out["tau_cal"] = clock(tab, ea_cal, times, weight=w)
        ah_tab = tab["thr_Ah"].to_numpy(float)
        aT = np.exp(-c["Ea_kJ"] * 1e3 / 8.314462618 * (1.0 / (tab["T_thr"].to_numpy(float) + 273.15) - 1 / 298.15))
        dah = np.where(ah_tab > 0, ah_tab * np.nan_to_num(aT, nan=1.0), 0.0)
        from stress17 import _interp_cum
        out["ah"] = _interp_cum(tab, dah, times)
        if r["breakin"] == "overhang":
            o = r["oh"]
            obs = tab["kind"].to_numpy() == "observed"
            s = tab["soc"].to_numpy(float)
            dd = tab["days"].to_numpy(float)
            ok = obs & np.isfinite(s)
            soc_op = float((s[ok] * dd[ok]).sum() / max(dd[ok].sum(), 1e-12))
            self.soc_op = soc_op
            if o["line"] == "fitted":
                p3 = _ext()["P3_overhang"]
                ea_tau = p3["Ea_tau_kJ_sens"] * 1e3
                fl = p3["t_full_fit_line"]
                t_ref = float(np.exp(fl["intercept"] + fl["slope_K"] / (o["T_full_ref_C"] + 273.15)))
            else:
                ea_tau, t_ref = o["ea_tau_kJ"] * 1e3, o["t_full_ref_d"]
            x0 = 0.0 if o["x0"] == "zero" else 1.0
            out["X"] = overhang_state(tab, times, o["soc0"], soc_op, ea_tau, t_ref, o["T_full_ref_C"], x0=x0)
            self._oh_prior = (float(np.log(o["f_oh"] * max(soc_op - o["soc0"], 1e-3) * NOM)), float(np.log(2.0)))
        return out

    # ------------------------------------------------------------ run (LawFit.run with per-term clocks)
    def run(self, op, fc, ck, at_date, eps, tab_cache=None, key=None, steps=None, a4=None, return_fit=False):
        c = self.cfg
        ck = pd.DatetimeIndex(ck)
        k = int((ck <= pd.Timestamp(at_date)).sum()) - 1
        anc = anchors(fc, ck)
        vis = sorted(j for j in anc if j <= k - 1)
        L = horizon_lag_days(fc, ck, pd.Timestamp(at_date))
        hz = ck[k] + pd.Timedelta(days=L)
        tab = self.table(op, fc, ck, k, hz, key=key, tab_cache=tab_cache)
        pairs = [(i - 1, i) for i in range(1, len(vis)) if vis[i] == vis[i - 1] + 1]
        ref = restarts(op, ck) if c["transient_ref"] == "restart" else None
        st = (select_steps(steps, ck, c["include_25C"], c["transient_days"], ref) if c["steps"]
              else select_steps(None, ck, False, 0))
        spairs = []
        if c["steps"] and c["steps_mode"] == "gap_endpoint":
            m0 = vis[-1] if vis else 0
            for m in sorted(set(st["m"])):
                if m < m0:
                    continue
                ii = np.where((st["m"] == m).to_numpy())[0]
                if len(ii) >= 2:
                    spairs.append((int(ii[0]), int(ii[-1]), False, int(m)))
        for i in (range(1, len(st)) if c["steps_mode"] == "all_pairs" else []):
            if st["m"].iloc[i] == st["m"].iloc[i - 1]:
                cross = bool(st["sp"].iloc[i - 1] == 25 and st["sp"].iloc[i] == 45)
                if c["include_25C"] or (st["sp"].iloc[i] == 45 and st["sp"].iloc[i - 1] == 45):
                    spairs.append((i - 1, i, cross, int(st["m"].iloc[i])))
        months_off = sorted({m for _, _, cr, m in spairs if cr}) if c["include_25C"] else []
        n_anc = len(vis)
        times = [anc[j][0] for j in vis] + list(st["t"]) + [hz]
        cl = self.clocks(tab, times)
        names = self._names(months_off)
        mu, sd = self._prior(names)
        beta_fixed = beta_a4_safe(fc, a4, ck, k) if (c["steps"] and c["beta_mode"] == "a4" and a4 is not None) else 1.0
        if c["beta_mode"] == "one":
            beta_fixed = 1.0
        idx = {n: i for i, n in enumerate(names)}

        def P(x):
            return {n: x[i] for n, i in idx.items()}

        def resid(x):
            p = P(x)
            M = self._M17(p, cl)
            res = []
            for a, b in pairs:
                dq_obs = anc[vis[b]][1] - anc[vis[a]][1]
                dq_mod = -(M[b] - M[a]) - (p["o45"] if vis[a] == 0 else 0.0)
                res.append((dq_obs - dq_mod) / c["sigma_pair"])
            beta = p["beta"] if "beta" in p else beta_fixed
            for i, j, cross, m in spairs:
                ds = st["s"].iloc[j] - st["s"].iloc[i] - (p[f"off_{m}"] if cross else 0.0)
                res.append((beta * ds + (M[n_anc + j] - M[n_anc + i])) / c["sigma_s"])
            return np.r_[np.array(res, float), (x - mu) / sd]

        if pairs or spairs:
            x, _ = _lm(resid, mu)
        else:
            x = mu.copy()
        p = P(x)
        M = self._M17(p, cl)
        last = vis[-1] if vis else None
        if last is None:
            base, ml = Q_CK0, 0.0
        elif last == 0:
            base, ml = Q_CK0, M[vis.index(0)]
        else:
            base, ml = anc[last][1] + eps, M[len(vis) - 1]
        q = base - (M[-1] - ml)
        info = dict(n_pairs=len(pairs), n_step_pairs=len(spairs), beta_used=float(p.get("beta", beta_fixed)),
                    horizon_lag_d=L, last_anchor=-1 if last is None else int(last), month_loss=float(M[-1] - ml),
                    **{n: float(v) for n, v in p.items() if not n.startswith("off_")})
        if return_fit:
            r0 = resid(x)
            J = np.empty((len(r0), len(x)))
            for i in range(len(x)):
                h = 1e-6 * max(1.0, abs(x[i]))
                xp = x.copy()
                xp[i] += h
                J[:, i] = (resid(xp) - r0) / h
            sign, logdet = np.linalg.slogdet(J.T @ J)
            info["logZ"] = float(-0.5 * r0 @ r0 - 0.5 * logdet)
            info["_fit"] = dict(x=x, names=names, cl=cl, times=times, n_anc=n_anc, vis=vis, tab=tab)
        return float(q), info
