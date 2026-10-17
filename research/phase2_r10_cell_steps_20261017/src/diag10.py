"""Cell-picture diagnostics on the full data (round 8 definitions)."""
import numpy as np
import pandas as pd

from common10 import H
import cellcand as CC
import gates10 as G
from residuals10 import r_seg, robust_sd


def full_steps():
    return H.tables(H.full_op(), "full")[1]


def long_cells(L):
    ev = G.full_events().reset_index()
    rows = []
    for c in CC.COLS:
        d = ev.copy()
        d["unit"] = c[5:-2]
        d["depth"] = L.reindex(d["t_cv_end"])[c].to_numpy(float)
        rows.append(d)
    return pd.concat(rows, ignore_index=True)


def sigma_cells(L):
    d = long_cells(L)
    seg_n = d[d.unit == "cell1"].groupby("segment").size()
    segs = [s for s in seg_n.index if seg_n[s] >= 4 and int(d[d.segment == s].setpoint.iloc[0]) == 45]
    d["R"] = r_seg(d, "depth")
    d = d[d.segment.isin(segs)]
    return dict(pooled=robust_sd(d["R"]), **{u: robust_sd(g["R"]) for u, g in d.groupby("unit")})


def cell_picture(L):
    d = long_cells(L)
    med = d.groupby("t_cv_end")["depth"].transform("median")
    d["R_cell"] = d["depth"] - med
    out = {}
    for u, g in d.groupby("unit"):
        bm = g.groupby("month")["R_cell"].mean()
        mean = float(g["R_cell"].mean())
        out[u] = dict(mean_R_cell=mean, months_same_sign=int((np.sign(bm) == np.sign(mean)).sum()), n_months=int(len(bm)))
    sp = d.groupby("t_cv_end").agg(spread=("depth", lambda s: s.max() - s.min()), month=("month", "first"))
    grp = pd.cut(sp["month"], [-1, 2, 5, 7], labels=["m0-2", "m3-5", "m6-7"])
    out["spread_by_month_group"] = {str(k): float(v) for k, v in sp.groupby(grp, observed=True)["spread"].mean().items()}
    return out
