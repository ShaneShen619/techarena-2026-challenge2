"""Per-step summary of Gotion 1P10S / cell cycling reports (Time, step, I, Q, U, cell V)."""
import sys, glob, os, pandas as pd, numpy as np
src, out = sys.argv[1], sys.argv[2]
rows = []
for f in sorted(glob.glob(src + "/*.txt")):
    d = pd.read_csv(f, sep="\t", low_memory=False)
    d.columns = [c.strip() for c in d.columns]
    d["step"] = d["Test step"].ffill()
    d = d[d["U, V"].notna()].copy()
    d["t"] = pd.to_datetime(d["Time"].str.slice(0, 23), format="%Y/%m/%d %H:%M:%S.%f", errors="coerce")
    cells = [c for c in d.columns if c.startswith("BmsExt")]
    blk = (d["step"] != d["step"].shift()).cumsum()
    for _, g in d.groupby(blk, sort=False):
        I = g["I, A"].astype(float); U = g["U, V"].astype(float)
        dt = g["t"].diff().dt.total_seconds().fillna(0).clip(upper=10)
        r = dict(file=os.path.basename(f), step=g["step"].iloc[0], t0=g["t"].iloc[0], dur_s=float(dt.sum()),
                 I_med=float(I.median()), I_end=float(I.iloc[-1]), U0=float(U.iloc[0]), U1=float(U.iloc[-1]),
                 Ah=float((I * dt).sum() / 3600), Q_As_span=float(g["Q, As"].astype(float).iloc[-1] - g["Q, As"].astype(float).iloc[0]),
                 T_med=float(g["Temp[1], C"].astype(float).median()))
        if cells:
            cv = g[cells].astype(float)
            r.update(cellmax_end=float(cv.iloc[-1].max()), cellmin_end=float(cv.iloc[-1].min()))
        rows.append(r)
    print(os.path.basename(f), len(d), flush=True)
pd.DataFrame(rows).to_csv(out, index=False)
