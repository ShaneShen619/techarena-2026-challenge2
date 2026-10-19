"""WP4: drivers of every post-checkup anchor charge (no 100.41, no proxies). Usage: python3 -B wp4_pack.py <study_dir> <package_data_dir>"""
import glob, json, os, sys
import numpy as np
import pandas as pd
from scipy import optimize, stats

ST, DATA = sys.argv[1], sys.argv[2]
CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]
rows = []
for f in sorted(glob.glob(os.path.join(DATA, "operation", "*.csv.gz"))):
    seg = int(os.path.basename(f).split("_")[1])
    if seg not in (1, 2, 4, 6, 8, 10, 12, 14):
        continue
    d = pd.read_csv(f, nrows=40000)
    t = d.elapsed_s.to_numpy(float); I = d.current_A.to_numpy(float); V = d.pack_voltage_V.to_numpy(float)
    i0 = int(np.argmax(I > 15))                                   # first row of the anchor charge (step-start duplicate row)
    i1 = i0 + int(np.argmax(I[i0:] < 1.0))                        # first row after the charge
    dt = np.diff(t, append=t[-1])                                 # forward rectangle: a row's current holds until the next row
    ah = I * dt / 3600
    cv0 = i0 + int(np.argmax(V[i0:i1] >= 13.995))
    rest = d.iloc[:i0]; rest = rest[rest.current_A.abs() < 0.5]
    tr = rest.elapsed_s.to_numpy(float); vr = rest.pack_voltage_V.to_numpy(float)
    last30 = tr >= tr[-1] - 1800
    slope_mV_h = float(np.polyfit((tr[last30] - tr[-1]) / 3600, vr[last30], 1)[0] * 1000) if last30.sum() > 3 else np.nan
    tcv = (t[cv0:i1] - t[cv0]); icv = I[cv0:i1]
    try:
        p, _ = optimize.curve_fit(lambda x, a, b, c: a + b * np.exp(-x / c), tcv, icv, p0=(4.0, 15.0, 300.0), maxfev=20000)
        tau_s, I_inf = float(p[2]), float(p[0])
    except Exception:
        tau_s, I_inf = np.nan, np.nan
    j30 = i1 + int(np.argmax(t[i1:] >= t[i1 - 1] + 1800))
    after_ok = np.all(np.abs(I[i1:j30 + 1]) < 0.5)
    rows.append(dict(
        anchor=[1, 2, 4, 6, 8, 10, 12, 14].index(seg), segment=seg, setpoint_C=int(d.chamber_temperature_C.iloc[i0]),
        Q_fc=float(ah[i0:i1].sum()), CC_Ah=float(ah[i0:cv0].sum()), CV_Ah=float(ah[cv0:i1].sum()), CV_h=float((t[i1 - 1] - t[cv0]) / 3600),
        tau_CV_s=tau_s, I_inf_fit=I_inf, I_end=float(I[i1 - 1]),
        V_pack_30min=float(V[j30]) if after_ok else np.nan, **{f"{c[:5]}_30min": float(d[c].iloc[j30]) for c in CELLS},
        spread_top_mV=float((d[CELLS].iloc[i1 - 1].max() - d[CELLS].iloc[i1 - 1].min()) * 1000),
        V_start=float(V[i0 - 1]), start_slope_mV_h=slope_mV_h, rest_h=float((t[i0] - tr[0]) / 3600) if len(tr) else 0.0,
        **{f"{c[:5]}_start": float(d[c].iloc[i0 - 1]) for c in CELLS},
        spread_start_mV=float((d[CELLS].iloc[i0 - 1].max() - d[CELLS].iloc[i0 - 1].min()) * 1000),
        T_charge_C=float(np.median(d.temp_mean_C.iloc[i0:i1])), T_end_C=float(d.temp_mean_C.iloc[i1 - 1]),
        flag={1: "seg1: 45 C, 0.5 h rest, unrelaxed", 6: "seg6: unrelaxed start"}.get(seg, "")))
p = pd.DataFrame(rows)
p["dQ_vs_anchor1"] = p.Q_fc.iloc[1] - p.Q_fc
p.to_csv(os.path.join(ST, "wp4/pack_drivers.csv"), index=False)
lic = json.load(open(os.path.join(ST, "wp2/lic_stats.json")))["drivers"]
m = p[p.anchor.between(1, 7)]
pairs = {  # pack driver -> LIC counterpart (wp1 registration "lic_counterparts")
    "V_start": "op_ch_V0", "rest_h": None, "CV_Ah": "op_ch_CV_Ah", "I_end": "op_ch_I_end",
    "V_pack_30min": "op_ch_V_after_rest", "T_charge_C": "dTm_op_minus_ref"}
tr = {}
for c in ["CC_Ah", "CV_Ah", "CV_h", "tau_CV_s", "I_end", "V_pack_30min", "spread_top_mV", "V_start", "start_slope_mV_h", "rest_h",
          "spread_start_mV", "T_charge_C", "T_end_C"]:
    rho = float(stats.spearmanr(m.anchor, m[c])[0]) if m[c].nunique() > 1 else 0.0
    slope = float(np.polyfit(m.dQ_vs_anchor1, m[c], 1)[0]) if m[c].nunique() > 1 else 0.0
    tr[c] = dict(rho_vs_anchor=rho, slope_per_Ah_of_Qfc_decline=slope, range=[float(m[c].min()), float(m[c].max())])
cmp_ = {}
for pk, lk in pairs.items():
    if lk is None:
        cmp_[pk] = dict(lic="op_ch_rest_before_h (constant 0.25 h)", lic_rho_vs_k=0.0, lic_rho_vs_T_path=None, pack_rho=tr[pk]["rho_vs_anchor"])
    else:
        cmp_[pk] = dict(lic=lk, lic_rho_vs_k=lic[lk]["rho_vs_k"], lic_rho_vs_T_path=lic[lk]["rho_vs_T_path"], pack_rho=tr[pk]["rho_vs_anchor"])
f1 = all((np.sign(v["pack_rho"]) == np.sign(v["lic_rho_vs_k"]) and abs(v["pack_rho"]) >= 0.6) for v in cmp_.values() if abs(v["lic_rho_vs_k"]) >= 0.6)
f0 = all(abs(v["pack_rho"]) < 0.3 for v in cmp_.values() if v["lic_rho_vs_T_path"] is not None and abs(v["lic_rho_vs_T_path"]) >= 0.6)
out = dict(trends_anchors_1_7=tr, lic_comparison=cmp_, factor_1_condition=bool(f1), factor_0_condition=bool(f0),
           Q_fc_check=p.Q_fc.round(2).tolist())
json.dump(out, open(os.path.join(ST, "wp4/pack_driver_trends.json"), "w"), indent=1)
pd.set_option("display.width", 250)
print(p.drop(columns=[c for c in p.columns if c.startswith("cell")]).round(3).to_string(index=False))
print(json.dumps(cmp_, indent=0)); print("factor1", f1, "factor0", f0)
print({k: (round(v["rho_vs_anchor"], 2), round(v["slope_per_Ah_of_Qfc_decline"], 4)) for k, v in tr.items()})
