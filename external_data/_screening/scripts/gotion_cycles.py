import pandas as pd, numpy as np, sys
steps, calx, out = sys.argv[1], sys.argv[2], sys.argv[3]
s = pd.read_csv(steps)
s["fdate"] = pd.to_datetime(s.file.str.extract(r"_(\d{4}-\d{2}-\d{2}_\d{2}\.\d{2}\.\d{2})")[0], format="%Y-%m-%d_%H.%M.%S")
s["row"] = np.arange(len(s))
s = s.sort_values(["fdate", "row"]).reset_index(drop=True)   # file order, then original in-file order
s["sub"] = s.step.str.extract(r"Main: 5\.(\d+)\.")[0].astype(float)
cyc = []; cur = None
for _, r in s.iterrows():
    if r["sub"] == 2:
        if cur: cyc.append(cur)
        cur = dict(file=r.file, qc=0.0, nchg=0, qd=np.nan)
    elif cur is not None and 3 <= r["sub"] <= 11 and r.Ah > 0:
        cur["qc"] += r.Ah; cur["nchg"] += 1
    elif cur is not None and r["sub"] == 14:
        cur["qd"] = -r.Ah; cur["T"] = r.T_med
if cur: cyc.append(cur)
c = pd.DataFrame(cyc); full = c[(c.nchg == 9) & c.qd.notna()].reset_index(drop=True)
full["n"] = np.arange(1, len(full) + 1)
full.to_csv(out, index=False)
cal = pd.read_excel(calx); cal.columns = ["cyc", "cap", "soh"]
rows = []
for _, k in cal.iterrows():
    w = full[(full.n > k.cyc - 5) & (full.n <= k.cyc + 5)]
    if len(w): rows.append((int(k.cyc), k.cap, w.qc.median(), w.qd.median()))
R = pd.DataFrame(rows, columns=["cyc", "cal", "qc", "qd"]); R["qc-cal"] = R.qc - R.cal; R["qd-cal"] = R.qd - R.cal
print("complete cycles", len(full)); print(R.round(3).to_string())
print("slope of (qd-cal) vs cal-loss:", np.polyfit(R.cal.iloc[0]-R.cal, R["qd-cal"], 1).round(3))
