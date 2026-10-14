"""Stage 3a audit (no proxy metric): rest-point pseudo-OCV around the graphite step."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from common4 import H  # noqa: E402
from dyncross import cv_ends  # noqa: E402
from events import CELLS, iter_segments, segment_arrays, step_programs  # noqa: E402

OUT = os.path.join(HERE, "outputs")
op = H.full_op()
prog = step_programs(op).dropna(subset=["step_mean"]).sort_values("t_cv_end")
rows = []
for seg, g in iter_segments(op):
    t, cur, ah = segment_arrays(g)
    pack = g["pack_voltage_V"].to_numpy(float)
    ce = cv_ends(cur, pack)
    rest = np.abs(cur) < 0.5
    idx = np.where(rest)[0]
    if not len(idx) or not len(ce):
        continue
    br = np.where(np.diff(idx) > 1)[0]
    for s, e in zip(np.r_[idx[0], idx[br + 1]], np.r_[idx[br], idx[-1]]):
        dur = (t[e] - t[s]) / 60.0
        prev_ce = ce[ce < s]
        if dur < 10 or not len(prev_ce):
            continue
        c = prev_ce[-1]
        act = np.where(~rest[:s])[0]
        direction = "chg" if len(act) and cur[act[-1]] > 0 else "dis"
        ts = g["timestamp"].iloc[e]
        pv = prog[prog["t_cv_end"] < ts]
        rows.append(dict(segment=seg, setpoint=int(g["chamber_temperature_C"].iloc[e]), t=ts, dur_min=dur,
                         depth=float(ah[c] - ah[e]), days_since_cv=(t[e] - t[c]) / 86400, direction=direction,
                         V=float(g[CELLS].iloc[e].mean()), exp=float(pv["step_mean"].iloc[-1]) if len(pv) else 32.8))
r = pd.DataFrame(rows)
r["month"] = np.searchsorted(H.CK.values, r["t"].values) - 1
r.to_csv(os.path.join(OUT, "audit_rests.csv"), index=False)


def fit(d, v):
    best = None
    prof = {}
    for s in np.arange(15, 45.0001, 0.05):
        sse_s = np.inf
        for w in (0.5, 0.75, 1, 1.5, 2, 3):
            X = np.c_[np.ones_like(d), 1 / (1 + np.exp((d - s) / w))]
            coef, *_ = np.linalg.lstsq(X, v, rcond=None)
            sse_s = min(sse_s, float(((X @ coef - v) ** 2).sum()))
        prof[round(s, 2)] = sse_s
    ss = np.array(list(prof)); ee = np.array(list(prof.values()))
    i = int(np.argmin(ee))
    n = len(d)
    ok = n * np.log(np.maximum(ee, 1e-18) / max(ee[i], 1e-18)) <= 3.84
    return float(ss[i]), float(ss[ok].max() - ss[ok].min())


res = []
for minutes in (10, 30):
    rr = r[(r.dur_min >= minutes) & (r.depth >= 15) & (r.depth <= 45)]
    for (m, sp, dr), g in rr.groupby(["month", "setpoint", "direction"]):
        exp = g["exp"].iloc[-1]
        spans = bool((g.depth < exp - 3).any() and (g.depth > exp + 3).any())
        s_hat, width = fit(g.depth.to_numpy(), g.V.to_numpy()) if len(g) >= 4 else (np.nan, np.nan)
        res.append(dict(min_rest=minutes, month=m, setpoint=sp, direction=dr, n=len(g), spans=spans, exp=exp,
                        s_hat=s_hat, width95=width))
res = pd.DataFrame(res)
res.to_csv(os.path.join(OUT, "audit_fits.csv"), index=False)
main = res[(res.min_rest == 10) & (res.setpoint == 45)]
ok = main[(main.n >= 8) & main.spans & (main.width95 <= 1.0)]
summ = dict(n_rests_total=len(r), n_rests_15_45=int(((r.depth >= 15) & (r.depth <= 45)).sum()),
            rest_duration_median_min=float(r.dur_min.median()) if len(r) else None,
            months_45C_qualifying=int(ok.month.nunique()), exit_passed=bool(ok.month.nunique() >= 5))
json.dump(summ, open(os.path.join(OUT, "audit_summary.json"), "w"), indent=1, default=str)
pd.set_option("display.width", 200)
print(r.groupby(["setpoint", "direction"]).agg(n=("depth", "size"), dmin=("depth", "min"), dmax=("depth", "max"), dur=("dur_min", "median")).round(2))
print(res.round(3).to_string(index=False))
print(json.dumps(summ, indent=1))
