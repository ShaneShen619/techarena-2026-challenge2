"""V2 predictors: phase-matched 45 C step differencing with a physics beta (protocol.json).

Inputs are tables extracted from the cut operation data only:
fc (events.full_charges), st (events.step_programs), a4 (events.charge_step_split),
ck (all checkup dates, known in advance), and the checkup index k being predicted.
"""
import numpy as np
import pandas as pd

Q_CK0 = 100.41


def theil_sen(x, y):
    """Median of pairwise slopes (no intercept needed)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    i, j = np.triu_indices(len(x), 1)
    dx = x[j] - x[i]
    ok = dx != 0
    return float(np.median((y[j] - y[i])[ok] / dx[ok])) if ok.any() else 0.0


def anchors_by_checkup(fc, ck):
    """Map checkup index j -> anchor row (first full charge after CK_j)."""
    out = {}
    for _, r in fc.sort_values("t_end").iterrows():
        j = int((ck < r["t_end"]).sum()) - 1
        if j >= 0 and j not in out:
            out[j] = r
    return out


def month_steps(st, anc, m):
    """Steps of month m: after anchor_m, before anchor_(m+1) if visible."""
    if m not in anc:
        return st.iloc[0:0]
    sel = st["t_cv_end"] >= anc[m]["t_end"]
    if m + 1 in anc:
        sel &= st["t_cv_end"] < anc[m + 1]["t_start"]
    return st[sel].sort_values("t_cv_end")


def end45(st, anc, ck, m):
    """(E45(m), d(m), n45, rate) for month m, or None if no 45 C step."""
    s = month_steps(st, anc, m)
    s = s[(s["setpoint_C"] == 45) & s["step_mean"].notna()]
    if s.empty:
        return None
    last = s.iloc[-1]
    d = (ck[m + 1] - last["t_cv_end"]).total_seconds() / 86400.0
    t = (s["t_cv_end"] - s["t_cv_end"].iloc[0]).dt.total_seconds().to_numpy() / 86400.0
    rate = theil_sen(t, s["step_mean"].to_numpy()) if len(s) >= 3 else 0.0
    return dict(E=float(last["step_mean"]), d=d, n=len(s), r=rate)


def phase_diff(st, anc, ck, k, valid_days, use_rate=True):
    """Phase-matched step change from end of month k-2 to end of month k-1, or None."""
    if k < 2:
        return None
    cur, prev = end45(st, anc, ck, k - 1), end45(st, anc, ck, k - 2)
    if cur is None or prev is None or prev["n"] < 3 or prev["d"] > valid_days:
        return None
    if not (cur["d"] <= valid_days or cur["n"] >= 3):
        return None
    r = cur["r"] if (use_rate and cur["n"] >= 3) else 0.0
    return cur["E"] - prev["E"] + r * (cur["d"] - prev["d"])


def shrink(pairs, beta0, tau):
    """Shrinkage LS-through-origin slope of dQ on dX."""
    if not pairs:
        return beta0
    x, q = np.array(pairs, float).T
    s = float((x ** 2).sum())
    b = float((x * q).sum() / s) if s > 0 else beta0
    return (tau * beta0 + s * b) / (tau + s)


def beta_a4(fc, a4, ck, k, beta0, tau):
    """Beta from visible 25 C anchors 1..k-1: Q_fc change per Ah of step-to-top change."""
    anc = anchors_by_checkup(fc, ck)
    seg2j = {int(r["segment"]): j for j, r in anc.items()}
    t = {seg2j[int(r["segment"])]: r["step_to_top_mean"] for _, r in a4.iterrows()
         if int(r["segment"]) in seg2j}
    js = [j for j in range(1, k) if j in anc and j in t and anc[j]["setpoint_C"] == 25]
    if len(js) < 2:
        return beta0
    j1 = js[0]
    pairs = [(t[j] - t[j1], anc[j]["Q_Ah"] - anc[j1]["Q_Ah"]) for j in js[1:]]
    return shrink(pairs, beta0, tau)


def beta_direct(fc, st, ck, k, beta0, tau, valid_days, use_rate=True):
    """Beta from past phase-matched pairs (anchor j-1 -> j against step change of month j-1)."""
    anc = anchors_by_checkup(fc, ck)
    pairs = []
    for j in range(2, k):
        if j in anc and j - 1 in anc and anc[j - 1]["setpoint_C"] == 25:
            x = phase_diff(st, anc, ck, j, valid_days, use_rate)
            if x is not None:
                pairs.append((x, anc[j]["Q_Ah"] - anc[j - 1]["Q_Ah"]))
    return shrink(pairs, beta0, tau)


def m4(fc, st, eps):
    """Base-study M4 (beta 1, last1) re-stated for the fallback."""
    if fc.empty:
        return Q_CK0
    last = fc.sort_values("t_end").iloc[-1]
    q = Q_CK0 if last["setpoint_C"] == 45 else last["Q_Ah"] + eps
    s = st.dropna(subset=["step_mean"])
    s = s[s["t_cv_end"] >= last["t_end"]].sort_values("t_cv_end")
    return float(q + (s["step_mean"].iloc[-1] - s["step_mean"].iloc[0])) if len(s) else float(q)


def v2(fc, st, a4, ck, k, eps, beta0=1.0, tau=1.0, valid_days=10.0, use_rate=True,
       beta_mode="a4", beta_all=False):
    """Returns (Q_hat, branch, beta)."""
    anc = anchors_by_checkup(fc, ck)
    if beta_mode == "one":
        beta = 1.0
    elif beta_mode == "direct":
        beta = beta_direct(fc, st, ck, k, beta0, tau, valid_days, use_rate)
    else:
        beta = beta_a4(fc, a4, ck, k, beta0, tau)
    x = phase_diff(st, anc, ck, k, valid_days, use_rate) if (k - 1) in anc else None
    if x is not None and anc[k - 1]["setpoint_C"] == 25:
        return float(anc[k - 1]["Q_Ah"] + eps + beta * x), "phase", beta
    q = m4(fc, st, eps)
    if beta_all:
        q_anchor = m4(fc, st.iloc[0:0], eps)
        q = q_anchor + beta * (q - q_anchor)
    return float(q), "fallback", beta
