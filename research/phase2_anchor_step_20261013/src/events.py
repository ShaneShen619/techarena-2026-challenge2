"""Event extraction for the anchor + graphite-step study.

All quantities are computed from ``current_A`` integrated over real time steps
(the cycler counters book the 20 A pulse as charge, so they are not used for depth).
Charge current is positive.
"""
import numpy as np
import pandas as pd

CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]

MAIN_STEP = {"method": "midpoint_crossing", "current_band_A": (-12.5, -8.0),
             "upper_window_Ah": (15.0, 25.0), "lower_window_Ah": (42.0, 50.0),
             "search_from_Ah": 20.0, "ir_correction": False}
STEP_VARIANTS = {
    "main": {},
    "band_narrow": {"current_band_A": (-11.5, -9.0)},
    "windows_minus3": {"upper_window_Ah": (12.0, 22.0), "lower_window_Ah": (39.0, 47.0)},
    "windows_plus3": {"upper_window_Ah": (18.0, 28.0), "lower_window_Ah": (45.0, 53.0)},
    "dvdq_peak": {"method": "dvdq_peak"},
    "ir_corrected": {"ir_correction": True},
}


def segment_arrays(seg_df):
    """Return time [s], current [A], cumulative integrated Ah for one segment."""
    t = seg_df["elapsed_s"].to_numpy(float)
    current = seg_df["current_A"].to_numpy(float)
    dt = np.diff(t, prepend=t[0])
    dt[(dt > 600) | (dt <= 0)] = 0.0
    return t, current, np.cumsum(current * dt / 3600.0)


def iter_segments(op):
    if op is None or op.empty:
        return
    for seg, g in op.groupby("segment", sort=True):
        yield int(seg), g.reset_index(drop=True)


def full_charges(op):
    """First charge per segment that starts near empty and ends in CV at 14.0 V."""
    rows = []
    for seg, g in iter_segments(op):
        t, current, ah = segment_arrays(g)
        pack = g["pack_voltage_V"].to_numpy(float)
        pos = current > 0.5
        starts = np.where(pos & ~np.r_[False, pos[:-1]])[0]
        for s in starts:
            e = s
            while e + 1 < len(current) and current[e + 1] > 0.5:
                e += 1
            q = ah[e] - ah[s - 1 if s > 0 else s]
            if pack[s] >= 12.3 or pack[s:e + 1].max() < 13.95 or current[e] >= 6.0 or q < 50:
                break  # only the first charge of the segment is a candidate
            nz = np.where(current[:s] != 0)[0]
            rest_h = (t[s] - t[nz[-1]]) / 3600 if len(nz) else (t[s] - t[0]) / 3600
            cc = current[s:e + 1] > 20.0
            q_cc = (ah[s:e + 1][cc][-1] - ah[s - 1 if s > 0 else s]) if cc.any() else np.nan
            ctr = g["charge_Ah_cum"].iloc[e] - g["charge_Ah_cum"].iloc[s - 1 if s > 0 else s]
            rows.append(dict(
                segment=seg, t_start=g["timestamp"].iloc[s], t_end=g["timestamp"].iloc[e],
                temp_C=float(g["temp_mean_C"].iloc[s:e + 1].mean()),
                setpoint_C=int(g["chamber_temperature_C"].iloc[s]), rest_before_h=rest_h,
                Q_Ah=q, Q_CC_Ah=q_cc, counter_Ah=ctr, I_end_A=current[e],
                pack_start_V=pack[s], max_gap_s=float(np.diff(t[s:e + 1]).max()),
                **{f"start_{c}": float(g[c].iloc[s]) for c in CELLS},
                **{f"end_{c}": float(g[c].iloc[e]) for c in CELLS},
                _seg_index=(s, e)))
            break
        # only the first charge in a segment is considered
    return pd.DataFrame(rows)


def _cv_ends(current, pack):
    hi = (pack >= 13.95) & (current > 0) & (current < 6.0)
    return np.where(hi & ~np.r_[hi[1:], False])[0]


def _pulse_resistance(g, e, current, depth):
    """Apparent per-cell resistance at the start of the 20 A pulse after a CV end.
    Uses the last zero-current sample before the pulse and the sample ~20 s into it
    (voltage updates lag the current by one 10 s sample)."""
    idx = np.where(current[e + 1:] < -15)[0]
    if not len(idx):
        return np.full(4, np.nan)
    p = e + 1 + idx[0]
    if p - 1 <= e or p + 2 >= len(current):
        return np.full(4, np.nan)
    v0 = g[CELLS].iloc[p - 1].to_numpy(float)
    v1 = g[CELLS].iloc[p + 2].to_numpy(float)
    return (v0 - v1) / abs(current[p + 2])


def step_programs(op, **overrides):
    """Locate the graphite step depth (Ah below CV end) on every deep program."""
    cfg = {**MAIN_STEP, **overrides}
    rows = []
    for seg, g in iter_segments(op):
        t, current, ah = segment_arrays(g)
        pack = g["pack_voltage_V"].to_numpy(float)
        volts = g[CELLS].to_numpy(float)
        for e in _cv_ends(current, pack):
            depth = ah[e] - ah[e:]
            run_max, stop = 0.0, len(depth)
            for k in range(1, len(depth)):
                run_max = max(run_max, depth[k])
                if run_max - depth[k] > 2.0:
                    stop = k
                    break
            d = depth[:stop]
            if d.max() < 50.0:
                continue
            sl = slice(e, e + stop)
            cur = current[sl]
            lo, hi = cfg["current_band_A"]
            band = (cur > lo) & (cur < hi)
            if band.sum() < 50:
                continue
            v = volts[sl].copy()
            if cfg["ir_correction"]:
                r_hat = _pulse_resistance(g, e, current, depth)
                v = v + np.abs(cur)[:, None] * r_hat[None, :]
            db, vb = d[band], v[band]
            loc = []
            for c in range(4):
                loc.append(_locate(db, vb[:, c], cfg))
            rows.append(dict(segment=seg, t_cv_end=g["timestamp"].iloc[e],
                             t_measured=g["timestamp"].iloc[e + stop - 1],
                             setpoint_C=int(g["chamber_temperature_C"].iloc[e]),
                             max_depth_Ah=float(d.max()),
                             **{f"step_{c}": x for c, x in zip(CELLS, loc)},
                             step_mean=float(np.nanmean(loc)) if np.isfinite(loc).any() else np.nan,
                             step_range=float(np.nanmax(loc) - np.nanmin(loc)) if np.isfinite(loc).all() else np.nan))
    return pd.DataFrame(rows)


def _locate(depth, volt, cfg):
    if cfg["method"] == "dvdq_peak":
        order = np.argsort(depth, kind="stable")
        dd, vv = depth[order], volt[order]
        dd, keep = np.unique(dd, return_index=True)
        vv = vv[keep]
        grid = np.arange(18.0, 46.0, 0.25)
        if dd.min() > grid[0] or dd.max() < grid[-1]:
            return np.nan
        vg = np.interp(grid, dd, vv)
        vs = np.convolve(vg, np.ones(8) / 8, mode="same")
        slope = -np.gradient(vs, grid)
        m = (grid >= 22.0) & (grid <= 42.0)
        return float(grid[m][np.argmax(slope[m])])
    up = (depth >= cfg["upper_window_Ah"][0]) & (depth <= cfg["upper_window_Ah"][1])
    low = (depth >= cfg["lower_window_Ah"][0]) & (depth <= cfg["lower_window_Ah"][1])
    if up.sum() < 5 or low.sum() < 5:
        return np.nan
    thr = 0.5 * (np.median(volt[up]) + np.median(volt[low]))
    idx = np.where((depth > cfg["search_from_Ah"]) & (volt < thr))[0]
    return float(depth[idx[0]]) if len(idx) else np.nan


def charge_step_split(op, fc, smooth_Ah=2.0):
    """Charge-direction step inside each full charge: Ah bottom->step and step->top."""
    rows = []
    for _, r in fc.iterrows():
        g = op[op["segment"] == r["segment"]].reset_index(drop=True)
        s, e = r["_seg_index"]
        _, current, ah = segment_arrays(g)
        q = ah[s:e + 1] - ah[s - 1 if s > 0 else s]
        cc = current[s:e + 1] > 20.0
        out = {"segment": r["segment"], "Q_Ah": r["Q_Ah"], "smooth_Ah": smooth_Ah}
        qq, keep = np.unique(q[cc], return_index=True)
        grid = np.arange(0.0, qq.max(), 0.25)
        k = max(1, int(round(smooth_Ah / 0.25)))
        for c in CELLS:
            vv = np.interp(grid, qq, g[c].to_numpy(float)[s:e + 1][cc][keep])
            vs = np.convolve(vv, np.ones(k) / k, mode="same")
            slope = np.gradient(vs, grid)
            m = (grid > 50.0) & (grid < 80.0)
            pk = float(grid[m][np.argmax(slope[m])])
            out[f"bottom_to_step_{c}"] = pk
            out[f"step_to_top_{c}"] = r["Q_Ah"] - pk
        out["bottom_to_step_mean"] = np.mean([out[f"bottom_to_step_{c}"] for c in CELLS])
        out["step_to_top_mean"] = np.mean([out[f"step_to_top_{c}"] for c in CELLS])
        rows.append(out)
    return pd.DataFrame(rows)


def ck0_reference_step(ref):
    """Step depth on the CK0 C/20 discharge (constant 5.1 A), same two methods."""
    d = ref["discharged_Ah"].to_numpy(float)
    out = {}
    for c in CELLS:
        v = ref[c].to_numpy(float)
        out[f"mid_{c}"] = _locate(d, v, MAIN_STEP)
        out[f"dvdq_{c}"] = _locate(d, v, {**MAIN_STEP, "method": "dvdq_peak"})
    return out


def tail_margin_Ah(ref, start_cell_V):
    """Upper bound on charge remaining at a rest voltage, read off the loaded CK0 tail.
    At equal SOC the rest voltage exceeds the loaded voltage, so the true remaining
    charge is not larger than this bound."""
    d = ref["discharged_Ah"].to_numpy(float)
    q_end = d.max()
    out = []
    for c, v0 in start_cell_V.items():
        v = ref[c].to_numpy(float)
        below = np.where(v <= v0)[0]
        out.append(q_end - d[below[0]] if len(below) else 0.0)
    return float(max(out))
