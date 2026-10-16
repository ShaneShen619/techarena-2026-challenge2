"""Temperature-weighted time for SUB's sqrt_gap branch (WP2 protocol.json). Research implementation."""
import numpy as np
import pandas as pd

from v2 import Q_CK0, anchors_by_checkup
from v3 import sqrt_branch, v3

R_GAS = 8.314
SEG3 = (pd.Timestamp("2025-02-19 09:50:00"), pd.Timestamp("2025-03-11 00:00:00"))
DESIGNS = {
    "T_main": dict(Ea=20600.0, T_gap=25.0, T_seg3=45.0),
    "T_ea37": dict(Ea=37300.0, T_gap=25.0, T_seg3=45.0),
    "T_gap45": dict(Ea=20600.0, T_gap=45.0, T_seg3=45.0),
    "T_seg25": dict(Ea=20600.0, T_gap=25.0, T_seg3=25.0),
}


def af(T_C, Ea):
    return np.exp(Ea / R_GAS * (1.0 / 318.15 - 1.0 / (np.asarray(T_C, float) + 273.15)))


def segments(op):
    if op is None or op.empty:
        return pd.DataFrame(columns=["t0", "t1", "sp"])
    g = op.groupby("segment").agg(t0=("timestamp", "min"), t1=("timestamp", "max"), sp=("chamber_temperature_C", "first"))
    return g.sort_values("t0")


def hourly_temperature(op, start, end, T_gap, T_seg3):
    """Registered T(tau) on an hourly grid [start, end): visible segment -> setpoint; segment-3 interval -> T_seg3;
    after the last visible sample -> 45 C (alternation schedule); any other gap -> T_gap."""
    grid = pd.date_range(start, end, freq="h", inclusive="left")
    T = np.full(len(grid), float(T_gap))
    seg = segments(op)
    last = seg["t1"].max() if len(seg) else pd.Timestamp(start)
    has3 = bool(len(seg)) and (seg.index == 3).any()
    T[grid > last] = 45.0
    if not has3:
        T[(grid >= SEG3[0]) & (grid < SEG3[1])] = float(T_seg3)
    for _, r in seg.iterrows():
        T[(grid >= r["t0"]) & (grid <= r["t1"])] = float(r["sp"])
    return grid, T


def t_eff_days(op, ck0, dates, Ea, T_gap, T_seg3):
    end = max(dates)
    grid, T = hourly_temperature(op, ck0, end, T_gap, T_seg3)
    cum = np.concatenate([[0.0], np.cumsum(af(T, Ea) / 24.0)])
    idx = [int(len(pd.date_range(ck0, d, freq="h", inclusive="left"))) for d in dates]
    return [float(cum[i]) for i in idx]


def sqrt_branch_T(fc, ck, k, eps, op, Ea, T_gap, T_seg3, p=0.5):
    anc = anchors_by_checkup(fc, ck)
    js = [j for j in range(1, k) if j in anc]
    te = t_eff_days(op, ck[0], [ck[j] for j in js] + [ck[k - 1], ck[k]], Ea, T_gap, T_seg3)
    tj, tk1, tk = np.array(te[:len(js)]), te[-2], te[-1]
    x = tj ** p
    loss = np.array([Q_CK0 - (anc[j]["Q_Ah"] + eps) for j in js])
    a = float((x * loss).sum() / (x ** 2).sum())
    return float(anc[k - 1]["Q_Ah"] + eps - a * (tk ** p - tk1 ** p))


def design_pred(name):
    def f(ctx):
        q, br, b = v3(ctx["fc"], ctx["steps"][ctx["step"]], ctx["a4"][ctx["a4s"]], ctx["ck"], ctx["k"], ctx["eps"],
                      use_sqrt=True, beta_cap=float("inf"), median=False)
        if br != "sqrt_gap":
            return q, {"branch": br}
        if name == "R_p044":
            return sqrt_branch(ctx["fc"], ctx["ck"], ctx["k"], ctx["eps"], p=0.44), {"branch": br}
        d = DESIGNS[name]
        return sqrt_branch_T(ctx["fc"], ctx["ck"], ctx["k"], ctx["eps"], ctx["op"], d["Ea"], d["T_gap"], d["T_seg3"]), {"branch": br}
    return f
