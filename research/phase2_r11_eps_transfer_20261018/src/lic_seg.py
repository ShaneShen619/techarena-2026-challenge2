"""Segment LIC into constant-sign current segments (same thresholds as _screening/lic_segments.py: |I| > 1 A,
dt clipped to 10 s) and add rest bookkeeping. Usage: python3 -I -B lic_seg.py <lic.npz> <segments.csv>"""
import sys
import numpy as np
import pandas as pd

z = np.load(sys.argv[1])
t, V, I, Tm = z["t"], z["V"].astype(float), z["I"], z["Tm"].astype(float)
dt = np.diff(t, prepend=t[0]).clip(0, 10)
sign = np.where(I > 1.0, 1, np.where(I < -1.0, -1, 0))
brk = np.flatnonzero(sign[1:] != sign[:-1]) + 1
st = np.concatenate([[0], brk]); en = np.concatenate([brk, [len(t)]]) - 1
Ah = np.add.reduceat(I * dt / 3600, st)
rows = []
for j, (a, b) in enumerate(zip(st, en)):
    seg = slice(a, b + 1)
    rows.append(dict(seg=j, sign=int(sign[a]), t0=t[a], t1=t[b], dur_h=(t[b] - t[a]) / 3600, Ah=Ah[j],
                     I_med=float(np.median(I[seg])), I_end=float(I[b]), V0=V[a], V1=V[b],
                     Vmax=float(V[seg].max()), Vmin=float(V[seg].min()), Tm=float(np.median(Tm[seg]))))
s = pd.DataFrame(rows)
s.to_csv(sys.argv[2], index=False)
print(len(t), "rows", len(s), "segments; total h", (t[-1] - t[0]) / 3600)
