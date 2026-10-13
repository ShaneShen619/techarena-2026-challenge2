"""Stage B1: coverage audit of charges that end in pack-level CV (descriptive only)."""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
import harness as H  # noqa: E402
from events import iter_segments, segment_arrays  # noqa: E402


def cv_charges(op):
    rows = []
    for seg, g in iter_segments(op):
        t, cur, ah = segment_arrays(g)
        pack = g["pack_voltage_V"].to_numpy(float)
        hi = (pack >= 13.95) & (cur > 0) & (cur < 6.0)
        for e in np.where(hi & ~np.r_[hi[1:], False])[0]:
            s = e
            while s > 0 and cur[s - 1] > 0.5:
                s -= 1
            depth0 = ah[e] - ah[max(s - 1, 0)]
            cc = cur[s:e + 1]
            dom = float(np.median(cc[cc > 6.0])) if (cc > 6.0).any() else np.nan
            rows.append(dict(segment=seg, setpoint_C=int(g["chamber_temperature_C"].iloc[e]),
                             t_start=g["timestamp"].iloc[s], t_cv_end=g["timestamp"].iloc[e],
                             start_depth_Ah=float(depth0), dominant_cc_A=dom,
                             cc_iqr_A=float(np.subtract(*np.percentile(cc[cc > 6.0], [75, 25]))) if (cc > 6.0).sum() > 3 else np.nan,
                             start_pack_V=float(pack[s]), crosses_step=bool(depth0 >= 45.0)))
    return pd.DataFrame(rows)


cov = cv_charges(H.full_op())
cov.to_csv(os.path.join(HERE, "coverage.csv"), index=False)
pd.set_option("display.width", 200)
print(cov.groupby(["segment", "setpoint_C"]).agg(n=("crosses_step", "size"), n_cross=("crosses_step", "sum"),
      depth_med=("start_depth_Ah", "median"), cc_med=("dominant_cc_A", "median")).round(2))
print(cov["dominant_cc_A"].round(1).value_counts().head(10))
print(cov[cov.crosses_step][["segment", "t_start", "start_depth_Ah", "dominant_cc_A", "cc_iqr_A"]].round(2).to_string())
