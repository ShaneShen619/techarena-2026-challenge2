"""Stage C: linear-Gaussian MAP fusion of anchors and step depths (stage_C/protocol.json)."""
import numpy as np
import pandas as pd

import harness as H
from v2 import anchors_by_checkup, beta_a4

SD_ANCHOR, SD_STEP = 0.05, 0.15


def _d(t, t0):
    return (pd.Timestamp(t) - pd.Timestamp(t0)).total_seconds() / 86400.0


def months(op, fc, ck):
    """Regime boundaries per visible month m: (t_anchor_end, t45_start or None, t_month_end or None)."""
    anc = anchors_by_checkup(fc, ck)
    out = {}
    ms = sorted(anc)
    for m in ms:
        t0 = anc[m]["t_end"]
        t1 = anc[m + 1]["t_start"] if m + 1 in anc else None
        if m == 0:
            t45 = t0
        else:
            sel = (op["timestamp"] > t0) & (op["chamber_temperature_C"] == 45)
            if t1 is not None:
                sel &= op["timestamp"] < t1
            t45 = op.loc[sel, "timestamp"].min() if sel.any() else None
        out[m] = (t0, t45, t1)
    return anc, out


def regime_days(mon, t):
    """Vectors (d25 per month m>=1, d45 per month m>=0) of days spent up to time t."""
    K = len(mon)
    d25, d45 = np.zeros(K), np.zeros(K)
    for m, (t0, t45, t1) in mon.items():
        if pd.Timestamp(t) <= t0:
            continue
        end = t if t1 is None else min(pd.Timestamp(t), t1)
        if t45 is None:
            d25[m] = max(_d(end, t0), 0.0)
        else:
            d25[m] = max(_d(min(pd.Timestamp(end), t45), t0), 0.0)
            d45[m] = max(_d(end, t45), 0.0)
    return d25, d45


def fit_predict(ctx, tau=5.0, beta=None, rw=0.02):
    fc, ck, k, eps = ctx["fc"], ctx["ck"], ctx["k"], ctx["eps"]
    st = ctx["steps"][ctx["step"]].dropna(subset=["step_mean"]).sort_values("t_cv_end")
    anc, mon = months(ctx["op"], fc, ck)
    if 0 not in mon:
        return H.Q_CK0, {}
    K = max(mon) + 1
    if beta is None:
        beta = beta_a4(fc, ctx["a4"][2.0], ck, k, 1.0, 1.0)
    # parameter layout: s0, delta, r25[1..K-1], r45[0..K-1], A[0..K-1]
    i_s0, i_dl = 0, 1
    i25 = {m: 2 + (m - 1) for m in range(1, K)}
    i45 = {m: 2 + (K - 1) + m for m in range(K)}
    iA = {m: 2 + (K - 1) + K + m for m in range(K)}
    P = 2 + (K - 1) + 2 * K
    rows, ys, ws = [], [], []

    def qrow(t):
        d25, d45 = regime_days(mon, t)
        r = np.zeros(P)
        for m in range(1, K):
            r[i25[m]] = d25[m]
        for m in range(K):
            r[i45[m]] = d45[m]
        return r

    for m in range(1, K):
        if m in anc:
            rows.append(qrow(anc[m]["t_end"]))
            ys.append(anc[m]["Q_Ah"] + eps - H.Q_CK0)
            ws.append(1 / SD_ANCHOR ** 2)
    for _, s in st.iterrows():
        m = max([mm for mm, (t0, _, t1) in mon.items() if s["t_cv_end"] >= t0 and (t1 is None or s["t_cv_end"] < t1)],
                default=None)
        if m is None:
            continue
        r = qrow(s["t_cv_end"]) / beta
        r[i_s0] = 1.0
        r[i_dl] = 1.0 if s["setpoint_C"] == 45 else 0.0
        r[iA[m]] = np.exp(-_d(s["t_cv_end"], mon[m][0]) / tau)
        rows.append(r)
        ys.append(s["step_mean"])
        ws.append(1 / SD_STEP ** 2)

    def prior(idx, mean, sd, minus=None):
        r = np.zeros(P)
        r[idx] = 1.0
        if minus is not None:
            r[minus] = -1.0
        rows.append(r)
        ys.append(mean)
        ws.append(1 / sd ** 2)

    prior(i_s0, 30.0, 10.0)
    prior(i_dl, 0.18, 0.1)
    for m in range(K):
        prior(iA[m], 0.0, 0.5)
    prior(i45[0], -0.05, 0.1)
    for m in range(1, K):
        prior(i45[m], 0.0, rw, minus=i45[m - 1])
    if K > 1:
        prior(i25[1], -0.05, 0.1)
    for m in range(2, K):
        prior(i25[m], 0.0, rw, minus=i25[m - 1])
    X, y, w = np.array(rows), np.array(ys), np.array(ws)
    A = X.T @ (X * w[:, None])
    cov = np.linalg.inv(A)
    th = cov @ (X.T @ (w * y))
    c = qrow(ctx["at_date"])
    q = H.Q_CK0 + float(c @ th)
    sd = float(np.sqrt(c @ cov @ c))
    info = dict(pred_sd=sd, beta=beta, delta_fit=float(th[i_dl]), A_last=float(th[iA[K - 1]]),
                r45_last=float(th[i45[K - 1]]), r25_last=float(th[i25[K - 1]]) if K > 1 else np.nan)
    return q, info


def make(**kw):
    return lambda ctx: fit_predict(ctx, **kw)
