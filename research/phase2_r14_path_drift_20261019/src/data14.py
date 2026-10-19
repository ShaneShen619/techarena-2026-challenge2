"""Shared data access for round 14: the full (uncut) operating data from the package loader, cached per segment,
and CV-end / anchor detection that reuses the package's own rules (model_template.py at the base commit)."""
import os, pickle, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(ST, "..", ".."))
PKG = os.path.join(WT, "TechArena_Challenge2_Team_Package")
DATA = os.path.join(PKG, "data")
CACHE = os.path.join(ST, "cache")
sys.path.insert(0, PKG)
from framework.data import load_dataset  # noqa: E402
from my_model import model_template as mt  # noqa: E402

CELLS = mt.CELLS
GAP_S = 60.0          # recording gap: dt between consecutive samples > 60 s (prompt section 3)
V30_S = 1800.0        # rest voltage 30 min after a CV end
V30_TOL_S = 30.0      # the pre-pulse rest sample must lie within 30 s of t_e + 1800 s
CK_DATES = None


def checkup_dates():
    ev = load_dataset(DATA).eval_points.sort_values("date")
    return pd.DatetimeIndex(ev["date"]), list(ev["checkup"])


def segments():
    """{segment: DataFrame} of the full operating data, reset index, cached as a pickle under cache/."""
    path = os.path.join(CACHE, "segments.pkl")
    if os.path.exists(path):
        return pickle.load(open(path, "rb"))
    op = load_dataset(DATA).operation
    segs = {int(s): g.reset_index(drop=True) for s, g in op.groupby("segment", sort=True)}
    os.makedirs(CACHE, exist_ok=True)
    pickle.dump(segs, open(path, "wb"))
    return segs


def cv_ends(seg):
    """Indices of CV ends, exactly the package rule in _step_depths: last sample of each run with
    pack >= CV_V_MIN, 0 < I < END_I_MAX_A."""
    i, _ = mt._integrated_ah(seg)
    u = seg["pack_voltage_V"].to_numpy(float)
    cv = (u >= mt.CV_V_MIN) & (i > 0) & (i < mt.END_I_MAX_A)
    return np.where(cv & ~np.r_[cv[1:], False])[0]


def charge_start(i, e):
    """First index of the charge (I > CHARGE_I_MIN_A run) that ends at CV end e."""
    s = e
    while s > 0 and i[s - 1] > mt.CHARGE_I_MIN_A:
        s -= 1
    return s


def cv_phase(seg, e):
    """(first CV sample c0, CV Ah over (t_c0, t_e], CV seconds t_e - t_c0, end current) of the charge ending at e.
    CV phase = samples of that charge with pack >= CV_V_MIN; Ah from the package's _integrated_ah increments."""
    i, ah = mt._integrated_ah(seg)
    u = seg["pack_voltage_V"].to_numpy(float)
    t = seg["elapsed_s"].to_numpy(float)
    s = charge_start(i, e)
    c0 = s + int(np.argmax(u[s:e + 1] >= mt.CV_V_MIN))
    return c0, float(ah[e] - ah[c0]), float(t[e] - t[c0]), float(i[e])


def rest_voltage(seg, e, after_s=V30_S):
    """Pack and cell voltages at the last rest sample (|I| <= CHARGE_I_MIN_A, contiguous rest from e + 1) with
    t <= t_e + after_s. The 20 A pulse starts at t_e + 1800-1801 s, so this is the pre-pulse rest sample. NaN unless
    that sample lies within V30_TOL_S of t_e + after_s and the rest has no recording gap."""
    t = seg["elapsed_s"].to_numpy(float)
    i = seg["current_A"].to_numpy(float)
    j = int(np.searchsorted(t, t[e] + after_s, side="right")) - 1
    busy = np.where(np.abs(i[e + 1:j + 1]) > mt.CHARGE_I_MIN_A)[0]
    if len(busy):
        j = e + busy[0]          # last rest sample is the one before the first non-rest sample
    ok = (j > e and t[j] >= t[e] + after_s - V30_TOL_S and np.all(np.diff(t[e:j + 1]) <= GAP_S))
    cols = ["pack_voltage_V"] + CELLS
    return {c: (float(seg[c].iloc[j]) if ok else np.nan) for c in cols}, bool(ok)


def gaps_between(seg, a, b):
    """(count, total seconds) of recording gaps (dt > GAP_S) between samples a and b of a segment."""
    t = seg["elapsed_s"].to_numpy(float)
    dt = np.diff(t[a:b + 1])
    g = dt > GAP_S
    return int(g.sum()), float(dt[g].sum())


def step_variants(seg, e):
    """Step depths of the deep program that starts at CV end e, by the package's own rules, or None if the package
    would not keep the program. Returns {'A3': robust step (package value), 'dvdq': median over cells of the dV/dQ
    variant (0.25 Ah grid), 'variants': 6 x 4 array (variant x cell)}."""
    i, ah = mt._integrated_ah(seg)
    v = seg[CELLS].to_numpy(float)
    depth = ah[e] - ah[e:]
    peak = np.maximum.accumulate(depth)
    back = np.where(peak - depth > mt.STEP_RECHARGE_AH)[0]
    d = depth[:back[0]] if len(back) else depth
    if d.max() < mt.STEP_MIN_DEPTH_AH:
        return None
    cur = i[e:e + len(d)]
    band = (cur > mt.STEP_BAND_A[0]) & (cur < mt.STEP_BAND_A[1])
    if band.sum() < mt.STEP_MIN_BAND_SAMPLES:
        return None
    if not np.isfinite(mt._locate_step(d[band], v[e:e + len(d)][band])).any():
        return None
    vv = v[e:e + len(d)]
    per_variant = []
    for band_a, upper, lower, method, ir in mt.STEP_VARIANTS:  # same loop as mt._robust_step
        b = (cur > band_a[0]) & (cur < band_a[1])
        if b.sum() < mt.STEP_MIN_BAND_SAMPLES:
            per_variant.append([np.nan] * len(CELLS))
            continue
        volts = vv + np.abs(cur)[:, None] * mt._pulse_resistance(seg, i, e)[None, :] if ir else vv
        per_variant.append(mt._locate_dvdq(d[b], volts[b]) if method == "dvdq"
                           else mt._locate_step(d[b], volts[b], upper, lower))
    arr = np.array(per_variant, float)
    a3 = mt._robust_step(seg, i, v, e, d)
    dv = arr[4][np.isfinite(arr[4])]
    return {"A3": a3, "dvdq": float(np.median(dv)) if len(dv) else np.nan, "variants": arr}


def anchor_index(seg):
    """CV-end index of the package anchor (_first_full_charge) of this segment, or None."""
    fc = mt._first_full_charge(seg)
    if fc is None:
        return None, None
    # end of the first charge run, exactly as in _first_full_charge (timestamps are not unique: 181 dt = 0 rows)
    i, _ = mt._integrated_ah(seg)
    e = int(np.where(i > mt.CHARGE_I_MIN_A)[0][0])
    while e + 1 < len(i) and i[e + 1] > mt.CHARGE_I_MIN_A:
        e += 1
    assert seg["timestamp"].iloc[e] == fc["t_end"] and e in set(cv_ends(seg))
    return e, fc
