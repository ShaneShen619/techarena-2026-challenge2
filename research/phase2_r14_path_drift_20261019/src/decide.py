"""Registered decision rules (round 14 WP1), applied in this order: noise gate, identifiability, O1, O2, O3.
E = d_path * 8.2 Ah. No rule uses P_k or proxy errors."""
import numpy as np

NOISE_MAX_AH = 0.30       # noise gate: sigma_TT,25 <= 0.30 Ah
ID_WIDTH_MAX_AH = 0.30    # identifiability: LOO range of E at most 0.30 Ah wide
O1_BAND_AH = 0.10         # O1: LOO range of E within [-0.10, +0.10] Ah
O1_P1B_AH = 0.15          # O1: P1b median E within +-0.15 Ah
O2_MIN_AH = 0.10          # O2: |median E| > 0.10 Ah
BIC_MARGIN = 2.0          # O2: BIC prefers (b) by >= 2


def decide(sigma_tt25, p1, p1b):
    """sigma_tt25: the gate value (Ah). p1, p1b: stats14.analyze() results for P1 and P1b.
    A condition that needs P1b is not met when P1b is not estimable (fewer than 5 points)."""
    c = {"sigma_tt25": sigma_tt25}
    c["noise_gate_pass"] = bool(np.isfinite(sigma_tt25) and sigma_tt25 <= NOISE_MAX_AH)
    if not c["noise_gate_pass"]:
        return {"outcome": "not identifiable", "reason": "noise gate failed", "checks": c}
    m = p1["main"]
    c["p1_estimable"] = bool(m["estimable"])
    if not m["estimable"]:
        return {"outcome": "O3 not identifiable", "reason": "P1 has fewer than 5 points", "checks": c}
    lo, hi = m["loo_range_E"]
    c["E_median"] = m["E"]
    c["loo_range_E"] = [lo, hi]
    c["loo_width_E"] = m["loo_width_E"]
    c["identifiable"] = bool(m["loo_width_E"] <= ID_WIDTH_MAX_AH)
    if not c["identifiable"]:
        return {"outcome": "O3 not identifiable", "reason": "LOO range of E wider than 0.30 Ah", "checks": c}
    pb = p1b["main"]
    c["p1b_estimable"] = bool(pb["estimable"])
    c["p1b_E_median"] = pb["E"] if pb["estimable"] else None
    c["o1_loo_within_band"] = bool(lo >= -O1_BAND_AH and hi <= O1_BAND_AH)
    c["o1_p1b_within"] = bool(pb["estimable"] and abs(pb["E"]) <= O1_P1B_AH)
    c["o2_loo_excludes_0"] = bool(lo > 0 or hi < 0)
    c["o2_abs_E_gt_min"] = bool(abs(m["E"]) > O2_MIN_AH)
    c["dBIC"] = p1["bic"]["dBIC_const_minus_linear"]
    c["o2_bic"] = bool(c["dBIC"] >= BIC_MARGIN)
    c["o2_p1b_same_sign"] = bool(pb["estimable"] and np.sign(pb["E"]) == np.sign(m["E"]) and m["E"] != 0)
    if c["o1_loo_within_band"] and c["o1_p1b_within"]:
        return {"outcome": "O1 path drift small", "reason": "all O1 conditions met", "checks": c}
    if c["o2_loo_excludes_0"] and c["o2_abs_E_gt_min"] and c["o2_bic"] and c["o2_p1b_same_sign"]:
        return {"outcome": "O2 path drift material", "reason": "all O2 conditions met", "checks": c}
    unmet = [k for k in ("o1_loo_within_band", "o1_p1b_within") if not c[k]]
    unmet2 = [k for k in ("o2_loo_excludes_0", "o2_abs_E_gt_min", "o2_bic", "o2_p1b_same_sign") if not c[k]]
    return {"outcome": "O3 inconclusive", "reason": f"O1 unmet: {unmet}; O2 unmet: {unmet2}", "checks": c}


def combine_top(d_path, d_path_range, d_tail, d_tail_range):
    """d_top = d_tail + d_path: medians added, ranges added endpoint-wise. Reported only; decides nothing."""
    return {"d_top": d_path + d_tail,
            "d_top_range": [d_path_range[0] + d_tail_range[0], d_path_range[1] + d_tail_range[1]],
            "E_top": (d_path + d_tail) * 8.2,
            "E_top_range": [(d_path_range[0] + d_tail_range[0]) * 8.2, (d_path_range[1] + d_tail_range[1]) * 8.2]}
