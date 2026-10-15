"""V3 predictors (protocol.json): V2 + sqrt(t) gap branch + beta cap + median-of-cells steps.

Inputs are the same tables as V2, extracted from the cut operation data only:
fc (events.full_charges), st (events.step_programs), a4 (events.charge_step_split),
ck (all checkup dates, known in advance), and the checkup index k being predicted.
"""
import numpy as np

from v2 import Q_CK0, anchors_by_checkup, beta_a4, m4, phase_diff

CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]


def median_cells(st, a4):
    """Change 3: replace the 4-cell means by 4-cell medians (mean of the middle two)."""
    st, a4 = st.copy(), a4.copy()
    if len(st):
        st["step_mean"] = np.nanmedian(st[[f"step_{c}" for c in CELLS]].to_numpy(float), axis=1)
    if len(a4):
        a4["step_to_top_mean"] = np.nanmedian(a4[[f"step_to_top_{c}" for c in CELLS]].to_numpy(float), axis=1)
    return st, a4


def coverage_gap_days(st, ck, k):
    """Days between the end of the last visible deep step program and CK_k."""
    s = st.dropna(subset=["step_mean"])
    if s.empty:
        return np.inf
    return (ck[k] - s["t_measured"].max()).total_seconds() / 86400.0


def sqrt_branch(fc, ck, k, eps, p=0.5, shift_days=0.0):
    """Change 1: anchored power-law (default sqrt) extrapolation from visible anchors 1..k-1."""
    anc = anchors_by_checkup(fc, ck)
    t = lambda j: max((ck[j] - ck[0]).total_seconds() / 86400.0 - shift_days, 0.0)
    js = [j for j in range(1, k) if j in anc]
    x = np.array([t(j) ** p for j in js])
    loss = np.array([Q_CK0 - (anc[j]["Q_Ah"] + eps) for j in js])
    a = float((x * loss).sum() / (x ** 2).sum())
    return float(anc[k - 1]["Q_Ah"] + eps - a * (t(k) ** p - t(k - 1) ** p))


def v3(fc, st, a4, ck, k, eps, use_sqrt=True, beta_cap=1.2, median=True, gap_days=10.0,
       p=0.5, shift_days=0.0, beta0=1.0, tau=1.0, valid_days=10.0, use_rate=True):
    """Returns (Q_hat, branch, beta). With use_sqrt=False, beta_cap=inf, median=False it equals V2_main."""
    if median:
        st, a4 = median_cells(st, a4)
    anc = anchors_by_checkup(fc, ck)
    if use_sqrt and k >= 2 and (k - 1) in anc and coverage_gap_days(st, ck, k) > gap_days:
        return sqrt_branch(fc, ck, k, eps, p, shift_days), "sqrt_gap", np.nan
    beta = min(beta_a4(fc, a4, ck, k, beta0, tau), beta_cap)
    x = phase_diff(st, anc, ck, k, valid_days, use_rate) if (k - 1) in anc else None
    if x is not None and anc[k - 1]["setpoint_C"] == 25:
        return float(anc[k - 1]["Q_Ah"] + eps + beta * x), "phase", beta
    return float(m4(fc, st, eps)), "fallback", beta
