"""WP0 facts F1-F6, equivalence checks of the round-17 code paths, and the shared month structure."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from eval17 import H, R3_T_CFG, CAUSAL  # noqa: E402
from runner5c import SCEN, scenario_tables  # noqa: E402
from smodel import anchors  # noqa: E402
from smodel5c import LawFit  # noqa: E402
from smodel17 import LawFit17  # noqa: E402
from stress import horizon_lag_days, stress_table  # noqa: E402
from stress17 import clock, contains_ck_day, soc_series, stress_table17  # noqa: E402

OUT = os.path.join(HERE, "outputs")
CK = H.CK
rep = {}


def month_of(t):
    return int((CK <= t).sum()) - 1


def cases(scens=("real",) + CAUSAL):
    for scen in scens:
        for k, spec in SCEN[scen]:
            t = scenario_tables(k, spec)
            if t is None:
                continue
            yield scen, k, t


# ---------------------------------------------------------------- equivalence checks
eq_tab, eq_pred = [], []
for scen, k, (op, fc, st, a4, key) in cases():
    L = horizon_lag_days(fc, CK, CK[k])
    hz = CK[k] + pd.Timedelta(days=L)
    a = stress_table(op, CK[k], CK, horizon=hz)
    b = stress_table17(op, CK[k], CK, horizon=hz)
    cols = ["t0", "t1", "days", "T_time", "T_thr", "thr_Ah", "kind"]
    same = len(a) == len(b) and all(
        (a[c].reset_index(drop=True).equals(b[c].reset_index(drop=True)) if c in ("t0", "t1", "kind")
         else np.allclose(a[c].to_numpy(float), b[c].to_numpy(float), equal_nan=True)) for c in cols)
    eq_tab.append(same)
    if scen == "real" or k in (4, 7):
        q0 = LawFit(R3_T_CFG).run(op, fc, CK, CK[k], H.EPS0 + 0.4, steps=st["main"], a4=a4[2.0])[0]
        q1 = LawFit17(R3_T_CFG).run(op, fc, CK, CK[k], H.EPS0 + 0.4, steps=st["main"], a4=a4[2.0])[0]
        eq_pred.append(abs(q0 - q1) / 102 * 100)
rep["equivalence"] = dict(stress_table17_equals_stress_table=bool(all(eq_tab)), n_tables=len(eq_tab),
                          lawfit17_max_abs_diff_pp=float(max(eq_pred)), n_pred=len(eq_pred))
print(rep["equivalence"])

# ---------------------------------------------------------------- F1 checkup-row classes
f1_rows, mism = [], 0
for scen, k, (op, fc, st, a4, key) in cases():
    L = horizon_lag_days(fc, CK, CK[k])
    hz = CK[k] + pd.Timedelta(days=L)
    tab = stress_table17(op, CK[k], CK, horizon=hz)
    hid = tab[tab["kind"] == "checkup"]
    for _, r in hid.iterrows():
        contains = contains_ck_day(CK, r["t0"], r["t1"])
        cls = "true_ck" if contains else "switch"
        mism += int(cls != r["ck_class"])
        f1_rows.append(dict(scenario=scen, k=k, month=month_of(r["t0"]), cls=cls, built=r["ck_class"],
                            t0=r["t0"], t1=r["t1"], days=r["days"]))
f1 = pd.DataFrame(f1_rows)
f1.to_csv(os.path.join(OUT, "f1_checkup_rows.csv"), index=False)
real7 = f1[(f1["scenario"] == "real") & (f1["k"] == 7)]
rep["F1"] = dict(
    construction_vs_containment_mismatches=int(mism),
    real_ck7_days_by_month=real7.pivot_table(index="month", columns="cls", values="days", aggfunc="sum").round(3)
    .fillna(0).to_dict(orient="index"),
    real_ck7_switch_hours=real7[real7["cls"] == "switch"]["days"].mul(24).round(1).tolist(),
)
# share of R3_T's Arrhenius-weighted tau per class at the real CK7 cut
op, fc, st, a4, key = scenario_tables(7, None)
L = horizon_lag_days(fc, CK, CK[7])
hz = CK[7] + pd.Timedelta(days=L)
tab = stress_table17(op, CK[7], CK, horizon=hz)
aT = np.exp(-37.3e3 / 8.314462618 * (1 / (tab["T_time"].to_numpy(float) + 273.15) - 1 / 298.15))
dtau = tab["days"].to_numpy(float) * np.nan_to_num(aT, nan=1.0)
cls = np.where(tab["kind"] == "checkup", tab["ck_class"], tab["kind"])
share = pd.Series(dtau).groupby(cls).sum()
rep["F1"]["real_ck7_tau_share"] = (share / share.sum()).round(4).to_dict()
rep["F1"]["real_ck7_days_by_kind"] = pd.Series(tab["days"].to_numpy(float)).groupby(cls).sum().round(3).to_dict()
print(rep["F1"])

# ---------------------------------------------------------------- F2 SOC history (real CK7 cut = all visible data)
soc = soc_series(op, fc, CK)
o = op.assign(soc=soc)
dt = o.groupby("segment")["elapsed_s"].diff().fillna(0).clip(lower=0, upper=600).to_numpy()
o["dt"] = dt
o["month"] = [month_of(t) for t in o["timestamp"]]


def wq(x, w, q):
    i = np.argsort(x)
    c = np.cumsum(w[i]) / w[i].sum()
    return float(x[i][np.searchsorted(c, q)])


f2 = []
for (m, sp), g in o[np.isfinite(o["soc"])].groupby(["month", "chamber_temperature_C"]):
    x, w = g["soc"].to_numpy(), g["dt"].to_numpy()
    f2.append(dict(month=int(m), setpoint=int(sp), days=float(w.sum() / 86400), mean_soc=float((x * w).sum() / w.sum()),
                   p10=wq(x, w, 0.10), p90=wq(x, w, 0.90)))
f2 = pd.DataFrame(f2)
f2.to_csv(os.path.join(OUT, "f2_soc_by_month.csv"), index=False)
last = o.groupby("segment").agg(t_last=("timestamp", "last"), soc_last=("soc", "last"),
                                setpoint=("chamber_temperature_C", "first"), v_last=("pack_voltage_V", "last"))
last.to_csv(os.path.join(OUT, "f2_segment_last_soc.csv"))
rep["F2"] = dict(nan_share=float(np.isnan(soc).mean()),
                 monthly_mean_spread={str(sp): dict(min=float(g["mean_soc"].min()), max=float(g["mean_soc"].max()),
                                                    sd=float(g["mean_soc"].std()))
                                      for sp, g in f2.groupby("setpoint")},
                 table=f2.round(3).to_dict(orient="records"),
                 segment_last_soc=last.reset_index().assign(t_last=lambda d: d["t_last"].astype(str))
                 .round(3).to_dict(orient="records"))
print(f2.round(3).to_string())

# ---------------------------------------------------------------- F3 term sizes (real CK7 cut, delta 0.4, main)
m = LawFit17(R3_T_CFG)
q, info = m.run(op, fc, CK, CK[7], H.EPS0 + 0.4, steps=st["main"], a4=a4[2.0], return_fit=True)
fit = info["_fit"]
tab = fit["tab"]
ev = list(CK[:8]) + [hz]
cl = m.clocks(tab, ev)
mu, sd = m._prior(fit["names"])
out = {}
for lab, xv in (("prior_mean", mu), ("map_real_ck7", fit["x"])):
    p = dict(zip(fit["names"], xv))
    brk, cal, cyc = m.terms(p, cl)
    d = pd.DataFrame({"breakin": brk, "calendar": cal, "cycle": cyc}, index=[f"CK{i}" for i in range(8)] + ["hz7"])
    inc = d.diff().iloc[1:8]
    out[lab] = dict(params={n: float(v) for n, v in p.items()},
                    cumulative_to_CK7_Ah=d.loc["CK7"].round(4).to_dict(),
                    cumulative_to_CK7_pp=(d.loc["CK7"] / 102 * 100).round(4).to_dict(),
                    per_month_Ah=inc.round(4).to_dict(orient="index"))
out["tau_b_days"] = m._tau_b()
rep["F3"] = out
print(json.dumps(out["map_real_ck7"]["cumulative_to_CK7_Ah"]), json.dumps(out["prior_mean"]["cumulative_to_CK7_Ah"]))

# ---------------------------------------------------------------- F5 SUB clock, F6 V2 regime
sub = pd.read_csv(os.path.join(STUDY, "sources", "r10_wp1_predictions.csv"))
sub = sub[(sub["model"] == "A3") & (sub["step"] == "main") & sub["scenario"].isin(("real",) + CAUSAL)]
rep["F5"] = dict(effective_Ea_on_k_kJ=10.3, sqrt_gap_cases=sub[(sub["branch"] == "sqrt_gap") & (sub["delta"] == 0.4)]
                 [["scenario", "k"]].astype(str).agg("_k".join, axis=1).tolist())
base = pd.read_csv(os.path.join(OUT, "wp0_base_predictions.csv"))
v2 = base[(base["model"] == "V2") & (base["delta"] == 0.4) & (base["step"] == "main")]
f6 = v2.pivot_table(index="scenario", columns="branch", values="k", aggfunc="count").fillna(0).astype(int)
rep["F6"] = dict(counts=f6.to_dict(orient="index"),
                 per_case=v2[["scenario", "k", "branch"]].astype(str).agg(":".join, axis=1).tolist(),
                 causal_phase=int(((v2["scenario"] != "real") & (v2["branch"] == "phase")).sum()),
                 causal_fallback=int(((v2["scenario"] != "real") & (v2["branch"] == "fallback")).sum()))
print(rep["F5"], rep["F6"]["counts"])

# ---------------------------------------------------------------- SUB matching cases and month structure (rule 6)
s4 = sub[sub["delta"] == 0.4].set_index(["scenario", "k"])
b4 = base[(base["delta"] == 0.4) & (base["step"] == "main")]
ref = b4[b4["model"] == "REF"].set_index(["scenario", "k"])
common = ref.index.intersection(s4.index)
real_soh = s4.loc["real"]["SOH"].round(3).tolist()
rep["SUB_match"] = dict(n_common=int(len(common)), n_ref=int(len(ref)), n_sub=int(len(s4)),
                        missing_in_sub=[f"{a}_k{b}" for a, b in ref.index.difference(s4.index)],
                        real_soh_d04=real_soh,
                        proxy_equal=bool(np.allclose(ref.loc[common, "proxy"], s4.loc[common, "proxy"], atol=1e-9)))
allm = pd.concat([b4[["scenario", "k", "model", "err_pp"]],
                  s4.reset_index()[["scenario", "k"]].assign(model="SUB", err_pp=s4["err_pp"].to_numpy())])
allm = allm[allm["scenario"] != "real"]
rep["month_structure"] = allm.pivot_table(index="k", columns="model", values="err_pp", aggfunc="mean").round(3) \
    .to_dict(orient="index")
print(rep["SUB_match"], rep["month_structure"])
json.dump(rep, open(os.path.join(OUT, "wp0_facts.json"), "w"), indent=1, default=str)
