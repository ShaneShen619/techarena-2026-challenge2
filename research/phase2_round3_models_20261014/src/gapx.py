"""Stage D gap-extrapolation rules on top of V2's fallback branch (stage_D/protocol.json)."""
import numpy as np
import pandas as pd

import harness as H
from v2 import anchors_by_checkup, beta_a4, theil_sen

GAP_MIN_DAYS = 10.0
EA = 37.3e3
R_GAS = 8.314
T_REF = 298.15


def last_step(ctx):
    st = ctx["steps"][ctx["step"]].dropna(subset=["step_mean"])
    return st["t_cv_end"].max() if len(st) else None


def gap_days(ctx):
    t = last_step(ctx)
    return (ctx["at_date"] - t).total_seconds() / 86400.0 if t is not None else np.nan


def _days(ts):
    return (pd.to_datetime(ts) - H.CK[0]).dt.total_seconds().to_numpy() / 86400.0 \
        if isinstance(ts, pd.Series) else (pd.Timestamp(ts) - H.CK[0]).total_seconds() / 86400.0


def _f(T_K):
    return np.exp(-EA / R_GAS * (1.0 / T_K - 1.0 / T_REF))


def d1(ctx):
    st = ctx["steps"][ctx["step"]].dropna(subset=["step_mean"])
    s45 = st[st["setpoint_C"] == 45]
    segs = [s for s, g in s45.groupby("segment") if s != 1 and len(g) >= 3]
    if segs:
        g = s45[s45["segment"] == max(segs)].sort_values("t_cv_end")
    else:
        g = s45[s45["segment"] == 1].sort_values("t_cv_end").iloc[-3:]
    if len(g) < 2:
        return 0.0
    r = theil_sen(_days(g["t_cv_end"]), g["step_mean"].to_numpy())
    beta = beta_a4(ctx["fc"], ctx["a4"][ctx["a4s"]], ctx["ck"], ctx["k"], 1.0, 1.0)
    return beta * r * gap_days(ctx)


def _clock(op):
    """Cumulative Arrhenius-weighted sqrt-time clock C and discharge counter A per row."""
    op = op.sort_values("timestamp")
    t = np.maximum(_days(op["timestamp"]), 0.0)
    T = op["temp_mean_C"].to_numpy(float) + 273.15
    dc = _f(T) * np.diff(np.sqrt(t), prepend=np.sqrt(t[0]))
    return op["timestamp"].to_numpy(), np.cumsum(dc), op["discharge_Ah_cum"].to_numpy(float), op


def _at(times, arr, t):
    i = np.searchsorted(times, np.datetime64(t), side="right") - 1
    return arr[max(i, 0)]


def _nnls2(X, y):
    best, sse = np.zeros(2), float((y ** 2).sum())
    cands = []
    try:
        cands.append(np.linalg.lstsq(X, y, rcond=None)[0])
    except np.linalg.LinAlgError:
        pass
    for j in range(2):
        xj = X[:, j]
        den = float(xj @ xj)
        if den > 0:
            c = np.zeros(2)
            c[j] = float(xj @ y) / den
            cands.append(c)
    for c in cands:
        if (c >= 0).all():
            e = float(((X @ c - y) ** 2).sum())
            if e < sse:
                best, sse = c, e
    return best


def d2_fit(ctx):
    fc, st, ck, eps = ctx["fc"], ctx["steps"][ctx["step"]].dropna(subset=["step_mean"]), ctx["ck"], ctx["eps"]
    anc = anchors_by_checkup(fc, ck)
    if 0 not in anc:
        return None
    times, C, A, op = _clock(ctx["op"])
    obs = []
    for j, a in sorted(anc.items()):
        q_a = H.Q_CK0 if j == 0 else a["Q_Ah"] + eps
        obs.append((a["t_end"], q_a))
        sel = st["t_cv_end"] >= a["t_end"]
        if j + 1 in anc:
            sel &= st["t_cv_end"] < anc[j + 1]["t_start"]
        s = st[sel].sort_values("t_cv_end")
        if len(s):
            s0 = s["step_mean"].iloc[0]
            obs += [(t, q_a + (v - s0)) for t, v in zip(s["t_cv_end"], s["step_mean"])]
    t0 = anc[0]["t_end"]
    c0, a0 = _at(times, C, t0), _at(times, A, t0)
    X = np.array([[-(_at(times, C, t) - c0), -(_at(times, A, t) - a0)] for t, _ in obs])
    y = np.array([q - H.Q_CK0 for _, q in obs])
    coef = _nnls2(X, y)
    # mean daily discharge throughput of visible 45 C rows
    o45 = op[op["chamber_temperature_C"] == 45].sort_values("timestamp")
    dt = o45["elapsed_s"].diff().to_numpy()
    dA = o45["discharge_Ah_cum"].diff().to_numpy()
    ok = (dt > 0) & (dt <= 600)
    rate45 = float(dA[ok].sum() / (dt[ok].sum() / 86400.0)) if ok.any() else 0.0
    return dict(a=float(coef[0]), b=float(coef[1]), rate45=rate45, n_obs=len(obs))


def d2(ctx):
    p = d2_fit(ctx)
    t_last = last_step(ctx)
    if p is None or t_last is None:
        return 0.0
    dC = _f(318.15) * (np.sqrt(_days(ctx["at_date"])) - np.sqrt(max(_days(t_last), 0.0)))
    dA = p["rate45"] * gap_days(ctx)
    return -p["a"] * dC - p["b"] * dA


def d3(ctx):
    fc = ctx["fc"]
    a25 = fc[fc["setpoint_C"] == 25].sort_values("t_end")
    t_last = last_step(ctx)
    if len(a25) < 2 or t_last is None:
        return np.nan
    t = np.sqrt(_days(a25["t_end"]))
    b = np.polyfit(t, a25["Q_Ah"].to_numpy(), 1)[0]
    return b * (np.sqrt(_days(ctx["at_date"])) - np.sqrt(_days(t_last)))


RULES = {"D0": lambda ctx: 0.0, "D1": d1, "D2": d2, "D3": d3}


def make(rule):
    def pred(ctx):
        q, info = H.v2_pred(ctx)
        g = gap_days(ctx)
        add = 0.0
        if info["branch"] == "fallback" and g > GAP_MIN_DAYS:
            add = RULES[rule](ctx)
        info = dict(info, gap_days=g, extrap_Ah=add)
        if add != add:  # undefined (D3 without two 25 C anchors)
            return np.nan, info
        return q + add, info
    return pred
