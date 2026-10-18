"""Segment LIC 280 Ah raw data into constant-sign current segments and summarise each."""
import sys, pandas as pd, numpy as np
src, out = sys.argv[1], sys.argv[2]
d = pd.read_csv(src, dtype="float64")
d.columns = ["t", "V", "I", "Tm", "Te"]
dt = np.diff(d.t.values, prepend=d.t.values[0]).clip(0, 10)
sign = np.where(d.I > 1.0, 1, np.where(d.I < -1.0, -1, 0))
blk = np.concatenate([[0], np.cumsum(sign[1:] != sign[:-1])])
d["sign"], d["blk"], d["Ah"] = sign, blk, d.I.values * dt / 3600
g = d.groupby("blk")
s = pd.DataFrame({"sign": g.sign.first(), "t0": g.t.first(), "dur": g.t.last() - g.t.first(),
                  "Ah": g.Ah.sum(), "I_med": g.I.median(), "I_end": g.I.last(),
                  "V0": g.V.first(), "V1": g.V.last(), "Vmax": g.V.max(), "Vmin": g.V.min(), "Tm": g.Tm.median()})
s.to_csv(out)
print(len(d), "rows", len(s), "segments")
