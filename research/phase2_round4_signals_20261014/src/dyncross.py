"""Stage 2: graphite-step crossings during daily dynamic operation (stage_2/audit_protocol.json)."""
import numpy as np
import pandas as pd

from common4 import H  # noqa: F401
from events import CELLS, iter_segments, segment_arrays, step_programs

BANDS = {"dis10": (-12.5, -8.0), "dis20": (-22.0, -18.0), "chg10": (8.0, 12.5), "chg20": (18.0, 22.0)}
DEFAULT_STEP = 32.8


def cv_ends(cur, pack):
    hi = (pack >= 13.95) & (cur > 0) & (cur < 6.0)
    return np.where(hi & ~np.r_[hi[1:], False])[0]


def _runs(mask):
    idx = np.where(mask)[0]
    if not len(idx):
        return []
    br = np.where(np.diff(idx) > 1)[0]
    starts = np.r_[idx[0], idx[br + 1]]
    ends = np.r_[idx[br], idx[-1]]
    return list(zip(starts, ends))


def _locate(depth, v, exp, discharge):
    up = (depth >= exp - 6) & (depth <= exp - 3)
    lo = (depth >= exp + 3) & (depth <= exp + 6)
    if up.sum() < 5 or lo.sum() < 5:
        return np.nan
    thr = 0.5 * (np.median(v[up]) + np.median(v[lo]))
    if discharge:
        hit = np.where((depth > exp - 3) & (v < thr))[0]
    else:
        hit = np.where((depth < exp + 3) & (v > thr))[0]
    return float(depth[hit[0]]) if len(hit) else np.nan


def crossings(op, programs=None):
    """All band-run crossings with location, plus closure table between consecutive CV ends."""
    if programs is None:
        programs = step_programs(op)
    prog = programs.dropna(subset=["step_mean"]).sort_values("t_cv_end")
    rows, clos = [], []
    for seg, g in iter_segments(op):
        _, cur, ah = segment_arrays(g)
        pack = g["pack_voltage_V"].to_numpy(float)
        V = g[CELLS].to_numpy(float)
        ts = g["timestamp"]
        ce = cv_ends(cur, pack)
        cnt = (g["charge_Ah_cum"] - g["discharge_Ah_cum"]).to_numpy(float)
        for a, b in zip(ce[:-1], ce[1:]):
            clos.append(dict(segment=seg, t0=ts.iloc[a], t1=ts.iloc[b], closure_Ah=float(ah[b] - ah[a]),
                             counter_diff_Ah=float(cnt[b] - cnt[a]), days=(ts.iloc[b] - ts.iloc[a]).total_seconds() / 86400))
        bounds = list(ce) + [len(cur)]
        for e, nxt in zip(bounds[:-1], bounds[1:]):
            depth = ah[e] - ah
            for band, (lo, hi) in BANDS.items():
                inb = np.zeros(len(cur), bool)
                inb[e + 1:nxt] = (cur[e + 1:nxt] > lo) & (cur[e + 1:nxt] < hi)
                for s, t in _runs(inb):
                    d = depth[s:t + 1]
                    t_start = ts.iloc[s]
                    pv = prog[prog["t_cv_end"] < t_start]
                    exp = float(pv["step_mean"].iloc[-1]) if len(pv) else DEFAULT_STEP
                    if d.min() > exp - 6 or d.max() < exp + 6:
                        continue
                    dis = band.startswith("dis")
                    locs = [_locate(d, V[s:t + 1, c], exp, dis) for c in range(4)]
                    in_prog = prog[(prog["t_cv_end"] <= t_start) & (prog["t_measured"] >= t_start)]
                    rows.append(dict(segment=seg, setpoint=int(g["chamber_temperature_C"].iloc[s]), band=band,
                                     t_start=t_start, t_cv_ref=ts.iloc[e], days_since_cv=(t_start - ts.iloc[e]).total_seconds() / 86400,
                                     exp=exp, **{f"loc_{c}": x for c, x in zip(CELLS, locs)},
                                     loc_mean=float(np.mean(locs)) if np.isfinite(locs).all() else np.nan,
                                     loc_range=float(np.ptp(locs)) if np.isfinite(locs).all() else np.nan,
                                     program=bool(len(in_prog)),
                                     program_step=float(in_prog["step_mean"].iloc[0]) if len(in_prog) else np.nan))
    return pd.DataFrame(rows), pd.DataFrame(clos)
