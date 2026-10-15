import sys, glob, os, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_pkl import load
B = sys.argv[1]
for p in sorted(glob.glob(B + "/ESSL*/*/*.pkl")):
    L = load(p); ts = []; meta = []
    for i, it in enumerate(L):
        t = it["timeseries_data"].copy(); t.insert(0, "item", i); ts.append(t)
        m = it["constant_metadata"].copy(); m.insert(0, "item", i); meta.append(m)
    T = pd.concat(ts, ignore_index=True); M = pd.concat(meta, ignore_index=True)
    for D in (T, M):
        for c in D.columns[D.dtypes == object]:
            num = pd.to_numeric(D[c], errors="coerce")
            bad = int(num.isna().sum() - D[c].isna().sum())
            if bad: print("  non-numeric", c, bad, D[c][num.isna() & D[c].notna()].unique()[:5])
            D[c] = num
    rel = os.path.relpath(p, B); out = os.path.join(B, "_converted", rel[:-4])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    T.to_parquet(out + "__timeseries.parquet")
    M.to_parquet(out + "__meta.parquet")
    print(rel, len(L))
