"""WP3: Yagci (T_CE, T_path, eps_total) and Gotion (eps_total) under wp1/protocol.json. Usage: python3 -I -B wp3_ext.py <study_dir> <gotion_calibration_xlsx>"""
import json, os, sys
import numpy as np
import pandas as pd

ST, CALX = sys.argv[1], sys.argv[2]; sys.path.insert(0, os.path.join(ST, "src"))
import stats11 as S

SC = 102.0 / 180.0
y = pd.read_csv(os.path.join(ST, "cache/r7_repro/wp3_yagci_eps.csv"))
r7 = json.load(open(os.path.join(ST, "sources/r7_wp3_wp3_yagci_d_by_cell.json")))
mine = json.load(open(os.path.join(ST, "cache/r7_repro/wp3_yagci_d_by_cell.json")))
repro = {c: dict(r7=r7[c]["eps_main"]["d"], here=mine[c]["eps_main"]["d"]) for c in r7}
grp_r7 = {T: np.mean([v["eps_main"]["d"] for v in r7.values() if v["T_C"] == T]) for T in (35, 50)}
grp_here = {T: np.mean([v["eps_main"]["d"] for v in mine.values() if v["T_C"] == T]) for T in (35, 50)}
repro_ok = all(abs(grp_r7[T] - grp_here[T]) <= 0.005 for T in (35, 50))
y["T_CE"] = (y.C_RPT_dis - y.C_RPT_cha) * SC
y["T_path"] = (y.C_RPT_cha - y.Q_main) * SC
y["eps_total"] = y.eps_main
y.to_csv(os.path.join(ST, "wp3/yagci_terms.csv"), index=False)
res = dict(yagci_reproduction=dict(per_cell=repro, group_r7=grp_r7, group_here=grp_here, passed=bool(repro_ok)))
for variant, sub in [("all_checkups", y), ("without_checkup0", y[y.checkup != 0])]:
    per = {}
    for c, g in sub.groupby("cell"):
        per[c] = {"T_C": int(g.T_C.iloc[0])}
        for term in ("T_CE", "T_path", "eps_total"):
            sl = S.slopes(g.L, g[term]); per[c][term] = dict(theil_sen=sl["theil_sen"], ols=sl["ols"], loo_ts=sl["loo_ts"])
    grp = {}
    for T in (35, 50):
        cells = [c for c in per if per[c]["T_C"] == T]
        grp[f"Yagci{T}"] = {term: dict(transfer=float(np.mean([per[c][term]["theil_sen"] for c in cells])),
                                       ols=float(np.mean([per[c][term]["ols"] for c in cells])),
                                       cells=[per[c][term]["theil_sen"] for c in cells]) for term in ("T_CE", "T_path", "eps_total")}
    res[variant] = dict(per_cell=per, groups=grp)
# Gotion cell: eps_total only
cal = pd.read_excel(CALX); cal.columns = ["cyc", "cap", "soh"]
cyc = pd.read_csv(os.path.join(ST, "sources/gotion_cell_cycles.csv"))
rows = []
for _, k in cal.iterrows():
    w = cyc[(cyc.n > k.cyc - 5) & (cyc.n <= k.cyc + 5)]
    if len(w):
        rows.append(dict(cyc=int(k.cyc), Q_ref=float(k.cap), Q_op_ch=float(w.qc.median()), n_cycles=len(w)))
g = pd.DataFrame(rows); g["fade"] = g.Q_ref.iloc[0] - g.Q_ref; g["eps_total"] = g.Q_ref - g.Q_op_ch
g.to_csv(os.path.join(ST, "wp3/gotion_terms.csv"), index=False)
sl = S.slopes(g.fade, g.eps_total); bic = S.bic_models(g.fade, g.eps_total)
res["gotion_cell"] = dict(eps_total=dict(slopes=sl, bic_winner=bic["winner"], transfer=S.transfer_slope(g.fade.values, g.eps_total.values, bic)),
                          T_CE="not identifiable", T_path="not identifiable", n=len(g),
                          note="calibration capacity has 0.1 Ah resolution; window = complete cycles in (cyc-5, cyc+5]")
json.dump(res, open(os.path.join(ST, "wp3/ext_stats.json"), "w"), indent=1, default=float)
pd.set_option("display.width", 250)
print("repro", repro_ok, grp_r7, grp_here)
print(y[["cell", "T_C", "checkup", "L", "T_CE", "T_path", "eps_total"]].round(3).to_string(index=False))
for v in ("all_checkups", "without_checkup0"):
    print(v, json.dumps({k: {t: round(x["transfer"], 4) for t, x in d.items()} for k, d in res[v]["groups"].items()}))
    print("  cells", json.dumps({c: {t: round(p[t]["theil_sen"], 3) for t in ("T_CE", "T_path", "eps_total")} for c, p in res[v]["per_cell"].items()}))
print(g.round(3).to_string(index=False)); print("gotion", res["gotion_cell"]["eps_total"])
