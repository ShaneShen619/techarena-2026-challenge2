"""Pre-registered causal predictors (see protocol.json).

Every predictor receives only what the framework returns for ``until=CK date``:
the cut operation data plus CK0. Outputs are capacities in Ah.
"""
import numpy as np
import pandas as pd
from scipy.stats import theilslopes

from events import full_charges, step_programs, STEP_VARIANTS

Q_CK0 = 100.41
CK0_DATE = pd.Timestamp("2025-01-14")


def visible_events(op, step_variant="main"):
    fc = full_charges(op)
    st = step_programs(op, **STEP_VARIANTS[step_variant])
    return fc, st


def _anchor(fc, eps, eps0):
    """Latest visible post-checkup full charge as an anchor capacity.
    The post-CK0 charge (45 C) maps to CK0 by definition of eps0."""
    if fc.empty:
        return Q_CK0, CK0_DATE, None
    last = fc.sort_values("t_end").iloc[-1]
    q = Q_CK0 if last["setpoint_C"] == 45 else last["Q_Ah"] + eps
    return q, last["t_end"], last


def m2(fc, at, eps, eps0):
    return _anchor(fc, eps, eps0)[0]


def m3(fc, at, eps, eps0):
    q_anchor, _, _ = _anchor(fc, eps, eps0)
    pts = fc[fc["setpoint_C"] == 25]
    if len(pts) < 2:
        return q_anchor
    t = (pts["t_end"] - CK0_DATE).dt.total_seconds().to_numpy() / 86400
    x = np.c_[np.ones(len(t)), np.sqrt(t)]
    a, b = np.linalg.lstsq(x, pts["Q_Ah"].to_numpy() + eps, rcond=None)[0]
    pred = a + b * np.sqrt((pd.Timestamp(at) - CK0_DATE).days)
    return float(min(pred, q_anchor))


def _step_after(st, t0):
    after = st[st["t_cv_end"] >= t0].sort_values("t_cv_end")
    return after.iloc[0]["step_mean"] if len(after) else np.nan


def m4(fc, st, at, eps, eps0, beta=1.0, s_last="last1"):
    q_anchor, t_anchor, _ = _anchor(fc, eps, eps0)
    st = st.dropna(subset=["step_mean"])
    if st.empty:
        return q_anchor
    s_a = _step_after(st, t_anchor)
    if np.isnan(s_a):
        return q_anchor
    tail = st.sort_values("t_cv_end")
    tail = tail[tail["t_cv_end"] >= t_anchor]
    s_l = tail["step_mean"].iloc[-1] if s_last == "last1" else tail["step_mean"].iloc[-2:].mean()
    return float(q_anchor + beta * (s_l - s_a))


def m5(fc, st, at, eps, eps0):
    pts = fc[fc["setpoint_C"] == 25].sort_values("t_end")
    pairs = []
    for _, r in pts.iterrows():
        s = _step_after(st.dropna(subset=["step_mean"]), r["t_end"])
        if not np.isnan(s):
            pairs.append((s, r["Q_Ah"]))
    beta = 1.0
    if len(pairs) >= 2:
        s, q = np.array(pairs).T
        beta = float(theilslopes(q, s)[0])
    return m4(fc, st, at, eps, eps0, beta=beta), beta
