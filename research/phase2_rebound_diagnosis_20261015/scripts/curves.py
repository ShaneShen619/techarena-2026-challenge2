"""Loaded cell voltages vs depth below CV end for every deep program (cell mean and per cell), on a 0.25 Ah grid."""
import sys, numpy as np, pandas as pd
PKG = "/Users/shane/Desktop/Arena_1013_model/TechArena_Challenge2_Team_Package"
sys.path.insert(0, "/Users/shane/Desktop/Arena_1013_model/research/phase2_anchor_step_20261013/src"); sys.path.insert(0, PKG)
from framework.data import load_dataset
from events import CELLS, iter_segments, segment_arrays, _cv_ends
op = load_dataset(PKG + "/data").operation
grid = np.arange(0.5, 55.5, 0.25); rows = []
for seg, g in iter_segments(op):
    t, cur, ah = segment_arrays(g); pack = g["pack_voltage_V"].to_numpy(float); V = g[CELLS].to_numpy(float)
    ts = pd.to_datetime(g["timestamp"]).to_numpy()
    for e in _cv_ends(cur, pack):
        depth = ah[e] - ah[e:]
        stop = len(depth); run = 0.0
        for k in range(1, len(depth)):
            run = max(run, depth[k])
            if run - depth[k] > 2.0: stop = k; break
        d = depth[:stop]
        if d.max() < 50: continue
        band = (cur[e:e + stop] > -12.5) & (cur[e:e + stop] < -8.0)
        dd = d[band]; o = np.argsort(dd, kind="stable"); dd = dd[o]; dd, keep = np.unique(dd, return_index=True)
        r = {"segment": seg, "t_cv_end": pd.Timestamp(ts[e])}
        for ci, c in enumerate(CELLS):
            vv = V[e:e + stop, ci][band][o][keep]
            r[c] = np.interp(grid, dd, vv, left=np.nan, right=np.nan)
        rows.append(r)
np.savez("curves.npz", grid=grid, meta=np.array([[r["segment"], str(r["t_cv_end"])] for r in rows]),
         V=np.array([[r[c] for c in CELLS] for r in rows]))
print(len(rows), "events; band coverage depth", np.nanmin([np.nanmin(np.where(np.isfinite(r[CELLS[0]]), grid, np.nan)) for r in rows]))
