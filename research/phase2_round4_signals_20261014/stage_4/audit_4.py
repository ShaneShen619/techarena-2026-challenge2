"""Stage 4 audit (no proxy metric): dV/dQ feature in the top 3-19 Ah of CV-ending charges."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from common4 import H  # noqa: E402
from dyncross import cv_ends  # noqa: E402
from events import CELLS, iter_segments, segment_arrays  # noqa: E402

OUT = os.path.join(HERE, "outputs")
op = H.full_op()
grid = np.arange(3.0, 19.0001, 0.25)
rows = []
for seg, g in iter_segments(op):
    _, cur, ah = segment_arrays(g)
    pack = g["pack_voltage_V"].to_numpy(float)
    V = g[CELLS].to_numpy(float)
    for e in cv_ends(cur, pack):
        s = e
        while s > 0 and cur[s - 1] > 0.5:
            s -= 1
        start_depth = ah[e] - ah[max(s - 1, 0)]
        cc = np.arange(s, e + 1)[cur[s:e + 1] > 20.0]
        if len(cc) < 20:
            continue
        depth = ah[e] - ah[cc]
        order = np.argsort(depth)
        dd, keep = np.unique(depth[order], return_index=True)
        if dd.min() > 2.0 or dd.max() < 20.0:
            continue
        for sm in (1.0, 2.0, 3.0):
            k = max(1, int(round(sm / 0.25)))
            pk, vl, pr = [], [], []
            for c in range(4):
                vg = np.interp(grid, dd, V[cc][order][keep][:, c])
                vs = np.convolve(vg, np.ones(k) / k, mode="same")
                dv = -np.gradient(vs, grid)  # dV per Ah of charge (depth decreases while charging)
                inner = slice(k, len(grid) - k)
                gi, di = grid[inner], dv[inner]
                pk.append(gi[np.argmax(di)]); vl.append(gi[np.argmin(di)])
                mad = np.median(np.abs(di - np.median(di))) or np.nan
                pr.append((di.max() - np.median(di)) / mad)
            rows.append(dict(segment=seg, setpoint=int(g["chamber_temperature_C"].iloc[e]), t_cv_end=g["timestamp"].iloc[e],
                             anchor=bool(start_depth >= 45), smooth=sm, peak=float(np.median(pk)), valley=float(np.median(vl)),
                             peak_cell_range=float(np.ptp(pk)), prominence=float(np.median(pr))))
f = pd.DataFrame(rows)
f["month"] = np.searchsorted(H.CK.values, f["t_cv_end"].values) - 1
f.to_csv(os.path.join(OUT, "audit_features.csv"), index=False)
res = {}
for sm in (1.0, 2.0, 3.0):
    d = f[(f.smooth == sm) & (~f.anchor)]
    for feat in ("peak", "valley"):
        x = d[feat]
        located = float(((x > 3.5) & (x < 18.5)).mean())
        g = d.groupby("month")[feat]
        sds = g.std()[g.size() >= 3]
        med = g.median()
        rho = float(pd.Series(med.index).corr(pd.Series(med.values), method="spearman")) if len(med) > 2 else np.nan
        ok = located >= 0.9 and bool((sds <= 0.3).all()) and abs(rho) >= 0.9
        res[f"{feat}_s{sm:g}"] = dict(located_frac=located, max_within_month_sd=float(sds.max()), month_medians=med.round(2).to_dict(),
                                       spearman=rho, prominence_median=float(d.prominence.median()), passed=bool(ok))
res["exit_passed"] = any(v["passed"] for k, v in res.items() if k.endswith("s2"))
json.dump(res, open(os.path.join(OUT, "audit_summary.json"), "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
