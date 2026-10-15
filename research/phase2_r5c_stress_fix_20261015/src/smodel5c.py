"""Round-5C law fits (stage_1/protocol.json): power or two-term law, optional in-month step terms.

numpy/pandas only (the candidate class reuses it). MAP with smodel._lm.
"""
import json
import os

import numpy as np
import pandas as pd

from smodel import MAIN, Q_CK0, _lm, anchors
from stress import cumulative, horizon_lag_days, stress_table

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)


def load_prior2():
    p = json.load(open(os.path.join(STUDY, "stage_1", "prior2.json")))
    return {k: (p[k]["mean"], p[k]["sd"]) for k in ("logA_b", "logtau_b", "logA_cal", "logA_cyc")}


BASE = dict(law="power", steps=False, sigma_pair=0.20, o45_sd=0.3, sigma_s=0.05, beta_mode="a4",
            beta_prior=(1.3, 0.2), include_25C=False, offset_prior=(0.0, 0.5), tau_b_free=False,
            transient_days=5.0, Ea_kJ=37.3, checkup_Ah=0.0, prior2=None, steps_mode="all_pairs")


def beta_a4_safe(fc, a4, ck, k):
    from v2 import beta_a4
    try:
        return float(beta_a4(fc, a4, ck, k, 1.0, 1.0))
    except Exception:
        return 1.0


def select_steps(steps, ck, include_25C, transient_days):
    if steps is None or len(steps) == 0:
        return pd.DataFrame(columns=["t", "s", "sp", "m"])
    s = steps.dropna(subset=["step_mean"]).sort_values("t_cv_end")
    if not include_25C:
        s = s[s["setpoint_C"] == 45]
    t = pd.DatetimeIndex(s["t_cv_end"])
    m = np.array([int((ck <= x).sum()) - 1 for x in t])
    keep = np.array([x >= ck[mm] + pd.Timedelta(days=transient_days) for x, mm in zip(t, m)], bool) if len(t) else []
    out = pd.DataFrame({"t": t, "s": s["step_mean"].to_numpy(float), "sp": s["setpoint_C"].to_numpy(int), "m": m})
    return out[keep].reset_index(drop=True) if len(out) else out


class LawFit:
    def __init__(self, cfg=None):
        self.cfg = dict(BASE, **(cfg or {}))
        if self.cfg["law"] == "two" and self.cfg["prior2"] is None:
            self.cfg["prior2"] = load_prior2()

    # ---------------------------------------------------------------- law
    def _names(self, months_off):
        c = self.cfg
        if c["law"] == "power":
            names = ["logA_cal", "logA_cyc"]
        else:
            names = ["logA_b", "logA_cal", "logA_cyc"] + (["logtau_b"] if c["tau_b_free"] else [])
        names += ["o45"]
        if c["steps"] and c["beta_mode"] == "free":
            names += ["beta"]
        names += [f"off_{m}" for m in months_off]
        return names

    def _prior(self, names):
        c = self.cfg
        mu, sd = [], []
        for n in names:
            if c["law"] == "power" and n == "logA_cal":
                mu.append(MAIN["logA_cal_mu"]); sd.append(MAIN["logA_sd"])
            elif c["law"] == "power" and n == "logA_cyc":
                mu.append(MAIN["logA_cyc_mu"]); sd.append(MAIN["logA_sd"])
            elif n in ("logA_b", "logA_cal", "logA_cyc", "logtau_b"):
                m, s = c["prior2"][n]; mu.append(m); sd.append(s)
            elif n == "o45":
                mu.append(0.0); sd.append(c["o45_sd"])
            elif n == "beta":
                mu.append(c["beta_prior"][0]); sd.append(c["beta_prior"][1])
            else:
                mu.append(c["offset_prior"][0]); sd.append(c["offset_prior"][1])
        return np.array(mu), np.array(sd)

    def _M(self, p, tau, ah):
        c = self.cfg
        if c["law"] == "power":
            return np.exp(p["logA_cal"]) * np.power(np.clip(tau, 0, None), MAIN["z"]) + np.exp(p["logA_cyc"]) * ah
        tb = np.exp(p["logtau_b"]) if c["tau_b_free"] else np.exp(c["prior2"]["logtau_b"][0])
        return (np.exp(p["logA_b"]) * (1 - np.exp(-np.clip(tau, 0, None) / tb))
                + np.exp(p["logA_cal"]) * np.sqrt(np.clip(tau, 0, None)) + np.exp(p["logA_cyc"]) * ah)

    # ---------------------------------------------------------------- run
    def run(self, op, fc, ck, at_date, eps, tab_cache=None, key=None, steps=None, a4=None):
        c = self.cfg
        ck = pd.DatetimeIndex(ck)
        k = int((ck <= pd.Timestamp(at_date)).sum()) - 1
        anc = anchors(fc, ck)
        vis = sorted(j for j in anc if j <= k - 1)
        L = horizon_lag_days(fc, ck, pd.Timestamp(at_date))
        hz = ck[k] + pd.Timedelta(days=L)
        ckey = (key, c["checkup_Ah"], str(hz))
        if tab_cache is not None and key is not None and ckey in tab_cache:
            tab = tab_cache[ckey]
        else:
            tab = stress_table(op, ck[k], ck, horizon=hz, checkup_Ah=c["checkup_Ah"])
            if tab_cache is not None and key is not None:
                tab_cache[ckey] = tab
        pairs = [(i - 1, i) for i in range(1, len(vis)) if vis[i] == vis[i - 1] + 1]
        st = select_steps(steps, ck, c["include_25C"], c["transient_days"]) if c["steps"] else select_steps(None, ck, False, 0)
        spairs = []
        if c["steps"] and c["steps_mode"] == "gap_endpoint":
            # round 2: one endpoint pair per month not covered by an anchor pair (month >= latest anchor)
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
        names = self._names(months_off)
        mu, sd = self._prior(names)
        beta_fixed = beta_a4_safe(fc, a4, ck, k) if (c["steps"] and c["beta_mode"] == "a4" and a4 is not None) else 1.0
        if c["beta_mode"] == "one":
            beta_fixed = 1.0
        n_anc = len(vis)
        times = [anc[j][0] for j in vis] + list(st["t"]) + [hz]
        tau, ah = cumulative(tab, c["Ea_kJ"] * 1e3, t_eval=times)
        idx = {n: i for i, n in enumerate(names)}

        def P(x):
            return {n: x[i] for n, i in idx.items()}

        def resid(x):
            p = P(x)
            M = self._M(p, tau, ah)
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
        M = self._M(p, tau, ah)
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
        return float(q), info
