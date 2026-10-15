"""Extract LIC curves: 0.1C RPT full charges/discharges and every full 1C charge/discharge (V vs Ah)."""
import sys, pandas as pd, numpy as np
src, seg, out = sys.argv[1], sys.argv[2], sys.argv[3]
d = pd.read_csv(src, dtype="float64"); d.columns = ["t", "V", "I", "Tm", "Te"]
s = pd.read_csv(seg)
t = d.t.values; dt = np.diff(t, prepend=t[0]).clip(0, 10)
keep = s[(s.sign != 0) & (s.Ah.abs() > 250)].copy()
keep["kind"] = pd.Series(np.where(keep.I_med.abs() < 40, "rpt", "c1"), index=keep.index) + pd.Series(np.where(keep.sign > 0, "_chg", "_dis"), index=keep.index)
rows = []
for n, r in enumerate(keep.itertuples()):
    i0, i1 = np.searchsorted(t, [r.t0, r.t0 + r.dur + 0.5])
    q = np.cumsum(np.abs(d.I.values[i0:i1]) * dt[i0:i1]) / 3600
    rows.append(pd.DataFrame({"seg": n, "kind": r.kind, "t0": r.t0, "q": q, "V": d.V.values[i0:i1],
                              "I": d.I.values[i0:i1], "T": d.Tm.values[i0:i1]}))
c = pd.concat(rows, ignore_index=True)
c.to_parquet(out)
print(c.groupby("kind").seg.nunique())
