"""Graphite-step location on Challenge 1 curves through the submitted locator functions.

The submitted functions work on four cell columns. A single cell is passed as four identical
columns, so every cell-level median reduces to that cell's own value. Only the current bands
are rescaled (the pack locates the step near 10 A; these cells discharge at 51 or 102 A).
"""
import numpy as np
import pandas as pd

from .common import PROTOCOL, mt, patched

N_CELLS = len(mt.CELLS)
PACK_REF_A = PROTOCOL["steps"]["pack_ref_current_a"]
INFO = PROTOCOL["information_structure"]


def replicate(v):
    """One voltage column as the four columns the submitted functions expect."""
    return np.repeat(np.asarray(v, float)[:, None], N_CELLS, axis=1)


def scaled_variants(i_dis_a):
    """The submitted STEP_VARIANTS with current bands scaled from ~10 A to |i_dis_a|."""
    f = abs(i_dis_a) / PACK_REF_A
    return tuple(((band[0] * f, band[1] * f), upper, lower, method, ir)
                 for band, upper, lower, method, ir in mt.STEP_VARIANTS)


def scaled_main_band(i_dis_a):
    """The submitted STEP_BAND_A scaled the same way."""
    f = abs(i_dis_a) / PACK_REF_A
    return (mt.STEP_BAND_A[0] * f, mt.STEP_BAND_A[1] * f)


def locate_step_interp(depth, volts, upper_ah=mt.STEP_UPPER_AH, lower_ah=mt.STEP_LOWER_AH):
    """``mt._locate_step`` with the threshold crossing interpolated between two samples.

    Adaptation, not submitted code: at 30 s and 0.5C/1C one sample spans 0.4-0.85 Ah,
    against 0.03 Ah on the pack.
    """
    upper = (depth >= upper_ah[0]) & (depth <= upper_ah[1])
    lower = (depth >= lower_ah[0]) & (depth <= lower_ah[1])
    locs = []
    for c in range(N_CELLS):
        if upper.sum() < mt.STEP_MIN_PLATEAU_SAMPLES or lower.sum() < mt.STEP_MIN_PLATEAU_SAMPLES:
            locs.append(np.nan)
            continue
        v = volts[:, c]
        thr = 0.5 * (np.median(v[upper]) + np.median(v[lower]))
        idx = np.where((depth > mt.STEP_SEARCH_FROM_AH) & (v < thr))[0]
        if not len(idx):
            locs.append(np.nan)
            continue
        j = idx[0]
        if j > 0 and v[j - 1] >= thr and depth[j] > depth[j - 1] and v[j - 1] > v[j]:
            frac = (v[j - 1] - thr) / (v[j - 1] - v[j])
            locs.append(float(depth[j - 1] + frac * (depth[j] - depth[j - 1])))
        else:
            locs.append(float(depth[j]))
    return locs


def robust_step(cur, volts, depth, variants, resistance, interp=False):
    """Mirror of ``mt._robust_step`` for arbitrary variant bands.

    cur: signed current (discharge negative), volts: (n, 4), depth: Ah below full,
    resistance: (4,) apparent resistance for the IR variant. Returns (value, per-variant array).
    """
    per_variant = []
    for band_a, upper, lower, method, ir in variants:
        band = (cur > band_a[0]) & (cur < band_a[1])
        if band.sum() < mt.STEP_MIN_BAND_SAMPLES:
            per_variant.append([np.nan] * N_CELLS)
            continue
        vv = volts + np.abs(cur)[:, None] * resistance[None, :] if ir else volts
        if method == "dvdq":
            per_variant.append(mt._locate_dvdq(depth[band], vv[band]))
        else:
            locate = locate_step_interp if interp else mt._locate_step
            per_variant.append(locate(depth[band], vv[band], upper, lower))
    arr = np.array(per_variant, float)
    cells = []
    for c in range(N_CELLS):
        x = arr[:, c][np.isfinite(arr[:, c])]
        cells.append(float(np.median(x)) if len(x) >= mt.STEP_MIN_VARIANTS else np.nan)
    cells = np.array(cells)
    value = float(np.median(cells[np.isfinite(cells)])) if np.isfinite(cells).any() else np.nan
    return value, arr


def main_detected(cur, volts, depth, band):
    """The submitted keep-rule of ``mt._step_depths``: the main detection finds a step."""
    b = (cur > band[0]) & (cur < band[1])
    if b.sum() < mt.STEP_MIN_BAND_SAMPLES:
        return False
    return bool(np.isfinite(mt._locate_step(depth[b], volts[b])).any())


def cc_current(i_abs):
    """Constant-current level of a step: median of the samples within 10 % of the maximum."""
    i_abs = np.asarray(i_abs, float)
    return float(np.median(i_abs[i_abs >= 0.9 * i_abs.max()])) if len(i_abs) else np.nan


def program_steps(i_abs, v, q, v_rest, visible_depth=INFO["visible_depth_ah"]):
    """Step depths of one discharge, seen only down to ``visible_depth`` Ah below full.

    Returns a dict: detected (submitted keep-rule), robust, robust_interp, v0..v5 (submitted
    single variants), i0..i5 (the same with interpolated midpoint crossings), n_visible,
    i_dis, resistance.
    """
    keep = q <= visible_depth
    depth = np.asarray(q, float)[keep]
    i_vis = np.asarray(i_abs, float)[keep]
    cur = -i_vis
    volts = replicate(np.asarray(v, float)[keep])
    i_dis = cc_current(i_vis)
    r = (v_rest - v[0]) / i_abs[0] if np.isfinite(v_rest) and i_abs[0] > 0 else np.nan
    resistance = np.full(N_CELLS, r)
    variants = scaled_variants(i_dis)
    out = {"detected": main_detected(cur, volts, depth, scaled_main_band(i_dis)),
           "n_visible": int(keep.sum()), "i_dis": i_dis, "resistance": float(r)}
    out["robust"], arr = robust_step(cur, volts, depth, variants, resistance)
    out["robust_interp"], arr_i = robust_step(cur, volts, depth, variants, resistance, interp=True)
    for n in range(len(variants)):
        out[f"v{n}"] = float(arr[n, 0])
        out[f"i{n}"] = float(arr_i[n, 0])
    return out


def charge_top(i_abs, q, v, i_cc, cc_min_a=None):
    """Ah from the charge-direction step to the top, via ``mt._charge_step_to_top``.

    A rest sample at 0 Ah is prepended so the Ah axis starts at the start of the charge,
    as on the pack. The CC threshold is cc_current_frac x the CC current of this charge,
    unless ``cc_min_a`` gives it directly. ``v`` may be (n,) or (n, 4).
    """
    i2 = np.r_[0.0, np.asarray(i_abs, float)]
    q2 = np.r_[0.0, np.asarray(q, float)]
    v = np.asarray(v, float)
    v4 = replicate(v) if v.ndim == 1 else v
    v2 = np.vstack([v4[:1], v4])
    seg = pd.DataFrame({c: v2[:, n] for n, c in enumerate(mt.CELLS)})
    cc_min = PROTOCOL["structure"]["cc_current_frac"] * i_cc if cc_min_a is None else cc_min_a
    with patched(mt, CC_I_MIN_A=cc_min):
        return float(mt._charge_step_to_top(seg, i2, q2, 1, len(i2) - 1, float(q2[-1])))


def partial_charge(q, v, top_ah=INFO["visible_charge_top_ah"], v_lo=None):
    """ExampleModel analogue: Ah from the first visible sample at >= v_lo to the end of charge."""
    v_lo = PROTOCOL["baseline"]["v_lo_cell"] if v_lo is None else v_lo
    q = np.asarray(q, float)
    v = np.asarray(v, float)
    vis = q >= q[-1] - top_ah
    hit = np.where(v[vis] >= v_lo)[0]
    return float(q[-1] - q[vis][hit[0]]) if len(hit) else 0.0
