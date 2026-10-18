"""WP3: eps_j = C_RPT,j - Q_ch,j on the Yagci cycling cells (protocol.json). Reads the round-6 download in place.
Usage: python3 -I -B eps_yagci.py <yagci_unzipped_Data_dir> <out_dir>"""
import json
import os
import sys

import numpy as np
import pandas as pd

X, OUT = sys.argv[1], sys.argv[2]
SCALE = 102.0 / 180.0
CELLS = {"CA-181103-19": 35, "CA-181103-42": 35, "CA-181103-22": 50, "CA-181103-28": 50}
CKS = (0, 100, 500, 1000)

cap = pd.read_excel(os.path.join(X, "Capacities in checkups - all cells.xlsx"), sheet_name=None, header=None)
assert (cap["Checkup_#1500"].iloc[2:, 2:].values == cap["Checkup_#1000"].iloc[2:, 2:].values).all()
rpt = {}
for k in CKS:
    t = cap[f"Checkup_#{k}"]
    hr = int(t.index[t.apply(lambda r: (r == "Cell").any(), axis=1)][0])
    u = t.iloc[hr + 1:]
    u.columns = t.iloc[hr]
    u = u.loc[:, u.columns.notna()].dropna(subset=["Cell"])
    for _, r in u.iterrows():
        if r["Cell"] in CELLS:
            rpt[(r["Cell"], k)] = (float(r["max_CCCV_DIS"]), float(r["max_CCCV_CHA"]))
per = pd.read_excel(os.path.join(X, "Analysis individual cycles - cyclic aging cells.xlsx"), sheet_name=None, header=None)
rows = []
for c, T in CELLS.items():
    t = per[c]
    hr = int(t.index[t.apply(lambda r: (r == "cycle_no").any(), axis=1)][0])
    u = t.iloc[hr + 1:]
    u.columns = t.iloc[hr]
    u = u.loc[:, u.columns.notna()].astype(float).set_index("cycle_no")
    q = u["max_CCCV_CHA"]
    c0 = rpt[(c, 0)][0]
    for k in CKS:
        first = float(q.loc[k + 1])
        nxt = float(np.median(q.loc[k + 2:k + 4]))
        partial = bool(abs(first - nxt) > 0.01 * 180.0)
        q_main = nxt if partial else first
        q_sens = float(q.loc[k + 1:k + 3].mean())
        c_rpt, c_rpt_cha = rpt[(c, k)]
        rows.append(dict(cell=c, T_C=T, checkup=k, C_RPT_dis=c_rpt, C_RPT_cha=c_rpt_cha, Q_first=first,
                         Q_next_median=nxt, partial_start=partial, Q_main=q_main, Q_sens=q_sens,
                         eps_main=(c_rpt - q_main) * SCALE, eps_sens=(c_rpt - q_sens) * SCALE, eps_first=(c_rpt - first) * SCALE,
                         L=(c0 - c_rpt) * SCALE, T_mean_first=float(u["T_mean"].loc[k + 1])))
df = pd.DataFrame(rows)
res = {}
for c, g in df.groupby("cell"):
    out = {}
    for col in ("eps_main", "eps_sens", "eps_first"):
        d = float(np.polyfit(g["L"], g[col], 1)[0])
        loo = [float(np.polyfit(g["L"].drop(i), g[col].drop(i), 1)[0]) for i in g.index]
        out[col] = dict(d=d, loo_min=min(loo), loo_max=max(loo))
    res[c] = dict(T_C=int(g["T_C"].iloc[0]), **out, eps0_main=float(g[g.checkup == 0]["eps_main"].iloc[0]),
                  fade_end_Ah102=float(g["L"].max()), n_partial=int(g["partial_start"].sum()))
df.to_csv(os.path.join(OUT, "wp3_yagci_eps.csv"), index=False)
json.dump(res, open(os.path.join(OUT, "wp3_yagci_d_by_cell.json"), "w"), indent=1)
pd.set_option("display.width", 250)
print(df.round(3).to_string(index=False))
print(json.dumps(res, indent=1))
