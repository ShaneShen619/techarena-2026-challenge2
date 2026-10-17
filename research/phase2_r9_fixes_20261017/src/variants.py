"""SUB (T_main) with switchable fixes for the round-8 patterns #1 (step scale) and #2 (cell aggregation).
Defaults reproduce SUB exactly. Research implementation on the harness tables (cut data only)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R8_SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), "phase2_r8_error_table_20261017", "src")
if R8_SRC not in sys.path:
    sys.path.insert(0, R8_SRC)

from common8 import H  # noqa: E402,F401
from v2 import Q_CK0, anchors_by_checkup, beta_a4, beta_direct, phase_diff  # noqa: E402
from v3 import coverage_gap_days  # noqa: E402
import tsqrt as T  # noqa: E402

CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]
TM = T.DESIGNS["T_main"]


def aggregate(st, agg):
    if agg == "mean" or st.empty:
        return st
    st = st.copy()
    v = st[[f"step_{c}" for c in CELLS]].to_numpy(float)
    st["step_mean"] = np.nanmedian(v, axis=1) if agg == "median" else np.nanmin(v, axis=1)
    return st


def make(fb_beta=False, skip1=False, beta_mode="a4", beta0=1.0, agg="mean"):
    def f(ctx):
        fc, a4, ck, k, eps, op = ctx["fc"], ctx["a4"][ctx["a4s"]], ctx["ck"], ctx["k"], ctx["eps"], ctx["op"]
        st = aggregate(ctx["steps"][ctx["step"]], agg)
        anc = anchors_by_checkup(fc, ck)
        if k >= 2 and (k - 1) in anc and coverage_gap_days(st, ck, k) > 10.0:
            return T.sqrt_branch_T(fc, ck, k, eps, op, TM["Ea"], TM["T_gap"], TM["T_seg3"]), {"branch": "sqrt_gap"}
        if beta_mode == "direct":
            beta = beta_direct(fc, st, ck, k, beta0, 1.0, 10.0, True)
        else:
            beta = beta_a4(fc, a4, ck, k, beta0, 1.0)
        x = phase_diff(st, anc, ck, k, 10.0, True) if (k - 1) in anc else None
        if x is not None and anc[k - 1]["setpoint_C"] == 25:
            return float(anc[k - 1]["Q_Ah"] + eps + beta * x), {"branch": "phase", "beta": beta}
        if fc.empty:
            return Q_CK0, {"branch": "fallback"}
        last = fc.sort_values("t_end").iloc[-1]
        q = Q_CK0 if last["setpoint_C"] == 45 else last["Q_Ah"] + eps
        s = st.dropna(subset=["step_mean"])
        s = s[s["t_cv_end"] >= last["t_end"]].sort_values("t_cv_end")["step_mean"].to_numpy()
        if not len(s):
            return float(q), {"branch": "fallback"}
        i0 = 1 if (skip1 and len(s) >= 3) else 0
        inc = float(s[-1] - s[i0])
        return float(q + (beta if fb_beta else 1.0) * inc), {"branch": "fallback", "beta": beta}
    return f


B_FULL = 0.745   # round 8 WP2 free-slope fit on the FULL data: using 1/B_FULL is not causal (reference only)
CANDIDATES = {
    "SUB": make(),
    "P1a_fb_beta": make(fb_beta=True),
    "P1b_fb_beta_skip1": make(fb_beta=True, skip1=True),
    "P1c_beta_direct": make(beta_mode="direct"),
    "P1ref_prior_1_over_b": make(fb_beta=True, beta0=1.0 / B_FULL),
    "P2a_median": make(agg="median"),
    "P2b_min": make(agg="min"),
}
NON_CAUSAL = {"P1ref_prior_1_over_b"}
