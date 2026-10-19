"""Per deep-program raw arrays from the full operation data (same event definition as events.step_programs, main
configuration): charge start, CV end, discharge stop, per-cell voltages, current, temperature, depth.
Diagnostic only (uses the full data)."""
import numpy as np
import pandas as pd

from events import CELLS, MAIN_STEP, _cv_ends, iter_segments, segment_arrays

GRID = np.arange(18.0, 46.0, 0.25)       # dV/dQ grid, as the dvdq_peak variant
SMOOTH_AH = 2.0
PEAK_WIN = (22.0, 42.0)


def programs(op):
    out = []
    for seg, g in iter_segments(op):
        t, cur, ah = segment_arrays(g)
        pack = g["pack_voltage_V"].to_numpy(float)
        V = g[CELLS].to_numpy(float)
        for e in _cv_ends(cur, pack):
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
            c = cur[e:e + stop]
            lo, hi = MAIN_STEP["current_band_A"]
            band = (c > lo) & (c < hi)
            if band.sum() < 50:
                continue
            s = e
            while s > 0 and cur[s - 1] > 0.5:
                s -= 1
            out.append(dict(segment=int(seg), e=int(e), s=int(s), stop=int(stop), t_cv_end=g["timestamp"].iloc[e],
                            g=g, t=t, cur=cur, ah=ah, pack=pack, V=V, depth=d, band=band))
    return out


def sharpness(depth, volt):
    """dV/dQ peak height (mV/Ah) and FWHM (Ah) of the discharge step: 0.25 Ah grid, 2 Ah moving average."""
    order = np.argsort(depth, kind="stable")
    dd, vv = depth[order], volt[order]
    dd, keep = np.unique(dd, return_index=True)
    vv = vv[keep]
    if dd.min() > GRID[0] or dd.max() < GRID[-1]:
        return np.nan, np.nan, np.nan
    vs = np.convolve(np.interp(GRID, dd, vv), np.ones(int(SMOOTH_AH / 0.25)) / int(SMOOTH_AH / 0.25), mode="same")
    slope = -np.gradient(vs, GRID) * 1000.0
    m = np.where((GRID >= PEAK_WIN[0]) & (GRID <= PEAK_WIN[1]))[0]
    i = m[np.argmax(slope[m])]
    h = slope[i]
    half = h / 2.0
    lft = i
    while lft > 0 and slope[lft - 1] >= half:
        lft -= 1
    rgt = i
    while rgt < len(GRID) - 1 and slope[rgt + 1] >= half:
        rgt += 1
    if lft == 0 or rgt == len(GRID) - 1 or lft <= 3 or rgt >= len(GRID) - 4:
        return float(h), np.nan, float(GRID[i])   # half-maximum not reached inside the clean grid
    xl = np.interp(half, [slope[lft - 1], slope[lft]], [GRID[lft - 1], GRID[lft]])
    xr = np.interp(half, [slope[rgt + 1], slope[rgt]], [GRID[rgt + 1], GRID[rgt]])
    return float(h), float(xr - xl), float(GRID[i])


def curve_on_grid(depth, volt, grid):
    order = np.argsort(depth, kind="stable")
    dd, vv = depth[order], volt[order]
    dd, keep = np.unique(dd, return_index=True)
    return np.interp(grid, dd, vv[keep], left=np.nan, right=np.nan)


def plateau(depth, volt, win):
    sel = (depth >= win[0]) & (depth <= win[1])
    return float(np.median(volt[sel])) if sel.sum() >= 5 else np.nan


def as_frame(progs):
    return pd.DataFrame([{k: p[k] for k in ("segment", "e", "s", "stop", "t_cv_end")} for p in progs])
