"""WP2: LIC eps decomposition (wp1/protocol.json). Usage: python3 -I -B wp2_lic.py <study_dir>"""
import json, os, sys
import numpy as np
import pandas as pd
from scipy import stats

ST = sys.argv[1]; sys.path.insert(0, os.path.join(ST, "src"))
import stats11 as S

seg = pd.read_csv(os.path.join(ST, "cache/lic_segments_all.csv"))
seq = pd.read_csv(os.path.join(ST, "wp1/lic_sequence.csv"))
z = np.load(os.path.join(ST, "cache/lic.npz")); t, V, I, Tm = z["t"], z["V"].astype(float), z["I"], z["Tm"].astype(float)
# backward rectangle with the global sample spacing (same as lic_seg.py / _screening): each record closes its interval
DT = np.diff(t, prepend=t[0]).clip(0, 10)


def charge_detail(j):
    a, b = seg.t0[j], seg.t1[j]
    m = (t >= a) & (t <= b); tt, vv, ii = t[m], V[m], I[m]
    ah = ii * DT[m] / 3600
    cv = np.flatnonzero(vv >= 3.649); i0 = cv[0] if len(cv) else len(vv)
    return dict(Ah=float(ah.sum()), CC_Ah=float(ah[:i0].sum()), CV_Ah=float(ah[i0:].sum()), CV_h=float((tt[-1] - tt[i0]) / 3600) if i0 < len(tt) else 0.0,
                V0=float(vv[0]), I_end=float(ii[-1]), Tm=float(np.median(Tm[m])), rest_before_h=float(seg.dur_h[j - 1]),
                V_after_rest=float(seg.V1[j + 1]) if seg.sign[j + 1] == 0 else np.nan)


rows = []
for k in sorted(seq[seq.test.astype(str).str.isdigit()].test.astype(int).unique()):
    q = seq[seq.test.astype(str) == str(k)]
    rd = int(q[q.role == "ref_dis_0.1C"].seg.iloc[0]); rc = int(q[q.role == "ref_ch_0.1C_CCCV"].seg.iloc[0])
    oc = q[q.role == "op_ch_first_1C_CCCV"].seg
    r = dict(k=k, Q_ref_dis=-float(seg.Ah[rd]), Tm_ref=float(seg.Tm[rd]))
    for p, d in charge_detail(rc).items(): r[f"ref_ch_{p}"] = d
    if len(oc):
        for p, d in charge_detail(int(oc.iloc[0])).items(): r[f"op_ch_{p}"] = d
    rows.append(r)
d = pd.DataFrame(rows)
d["fade"] = d.Q_ref_dis.iloc[0] - d.Q_ref_dis
d["T_CE"] = d.Q_ref_dis - d.ref_ch_Ah
d["T_path"] = d.ref_ch_Ah - d.op_ch_Ah
d["eps_total"] = d.T_CE + d.T_path
d["T_path_CC"] = d.ref_ch_CC_Ah - d.op_ch_CC_Ah
d["T_path_CV"] = d.ref_ch_CV_Ah - d.op_ch_CV_Ah
d["dTm_op_minus_ref"] = d.op_ch_Tm - d.ref_ch_Tm
d["step_after_k4"] = (d.k >= 5).astype(int)
d["temp_regime"] = np.where(d.k <= 1, 0, np.where(d.k <= 4, 1, 2))
fl = S.mad_flags(d.op_ch_V0.fillna(d.op_ch_V0.median())) | S.mad_flags(d.op_ch_rest_before_h.fillna(0.25))
d["flag"] = fl | d.k.isin([5, 10])
d.loc[d.op_ch_Ah.isna(), "flag"] = False
d.to_csv(os.path.join(ST, "wp2/lic_terms.csv"), index=False)

res = {}
for term, rng in [("T_CE", d), ("T_path", d[d.op_ch_Ah.notna()]), ("eps_total", d[d.op_ch_Ah.notna()]),
                  ("T_path_CC", d[d.op_ch_Ah.notna()]), ("T_path_CV", d[d.op_ch_Ah.notna()])]:
    x, y = rng.fade.values, rng[term].values
    steps2 = np.c_[(rng.k >= 2).astype(float), (rng.k >= 5).astype(float)]
    bic = S.bic_models(x, y, rng.step_after_k4.values, steps2)
    sl = S.slopes(x, y)
    nf = ~rng.flag.values
    sl_nf = S.slopes(x[nf], y[nf]); bic_nf = S.bic_models(x[nf], y[nf], rng.step_after_k4.values[nf])
    res[term] = dict(slopes=sl, bic=bic, transfer_slope=S.transfer_slope(x, y, bic),
                     no_flagged=dict(slopes=sl_nf, bic_winner=bic_nf["winner"], transfer_slope=S.transfer_slope(x[nf], y[nf], bic_nf)),
                     within_regime_ts={str(g): (float(stats.theilslopes(gg[term], gg.fade)[0]) if len(gg) >= 3 else None)
                                       for g, gg in rng.groupby("temp_regime")})
tot = res["eps_total"]["transfer_slope"]
for term in ("T_CE", "T_path"):
    res[term]["share_of_total_abs"] = abs(res[term]["transfer_slope"]) / (abs(res["T_CE"]["transfer_slope"]) + abs(res["T_path"]["transfer_slope"]))
# drivers of T_path inside LIC (Spearman over k = 0..13)
o = d[d.op_ch_Ah.notna()]
drv = ["op_ch_V0", "op_ch_CV_Ah", "op_ch_CV_h", "op_ch_I_end", "op_ch_V_after_rest", "dTm_op_minus_ref", "op_ch_Tm",
       "ref_ch_V0", "ref_ch_CV_Ah", "ref_ch_V_after_rest", "ref_ch_I_end"]
res["drivers"] = {c: dict(rho_vs_k=float(stats.spearmanr(o.k, o[c])[0]), rho_vs_T_path=float(stats.spearmanr(o.T_path, o[c])[0]))
                  for c in drv}
sh = {t_: res[t_]["share_of_total_abs"] for t_ in ("T_CE", "T_path")}
res["dominant_term_LIC"] = max(sh, key=sh.get) if max(sh.values()) > 0.6 else "mixed"
res["step_type_wins"] = {t_: res[t_]["bic"]["winner"] in ("b", "c") for t_ in ("T_CE", "T_path", "eps_total")}
json.dump(res, open(os.path.join(ST, "wp2/lic_stats.json"), "w"), indent=1)
pd.set_option("display.width", 250)
print(d[["k", "fade", "Q_ref_dis", "ref_ch_Ah", "op_ch_Ah", "T_CE", "T_path", "eps_total", "T_path_CC", "T_path_CV",
         "op_ch_V0", "ref_ch_V0", "op_ch_I_end", "op_ch_V_after_rest", "ref_ch_V_after_rest", "dTm_op_minus_ref", "flag"]].round(3).to_string(index=False))
for term in ("T_CE", "T_path", "eps_total", "T_path_CC", "T_path_CV"):
    r = res[term]; b = r["bic"]
    print(term, "TS", round(r["slopes"]["theil_sen"], 4), "OLS", round(r["slopes"]["ols"], 4), "LOO_TS", np.round(r["slopes"]["loo_ts"], 4),
          "BIC a/b/c/b2", [round(b[m]["bic"], 1) for m in ("a", "b", "c", "b2")], "win", b["winner"],
          "c: slope/step", round(b["c"]["slope"], 4), round(b["c"]["step"], 3), "transfer", round(r["transfer_slope"], 4),
          "| no-flag", r["no_flagged"]["bic_winner"], round(r["no_flagged"]["transfer_slope"], 4), "| within regimes", r["within_regime_ts"])
print({k_: round(v["share_of_total_abs"], 3) for k_, v in res.items() if isinstance(v, dict) and "share_of_total_abs" in v}, res["dominant_term_LIC"])
print(json.dumps(res["drivers"], indent=0))
