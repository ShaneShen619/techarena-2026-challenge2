"""WP6: expected score differences of leaderboard probes vs SUB on the WP1 hypothesis grid (protocol.json)."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "wp1"))
import run_wp1 as W1  # noqa: E402

OUT = os.path.join(HERE, "outputs")
COLS = ["scenario", "k", "model", "Q"]


def sel(df, d=0.4):
    m = (df.scenario == "real") & (df.delta == d) & (df.step == "main") & (df.a4s == 2.0)
    return df[m]


w1 = sel(pd.read_csv(os.path.join(STUDY, "wp1", "outputs", "wp1_predictions.csv")))[COLS]
w2 = sel(pd.read_csv(os.path.join(STUDY, "wp2", "outputs", "wp2_real_predictions.csv")))
w3 = sel(pd.read_csv(os.path.join(STUDY, "wp3", "outputs", "wp3_real_predictions_d04.csv")))
probes = {"P_drift": (w3, "SUB|3b-0.031"), "P_drift_mild": (w3, "SUB|3b-0.02"), "P_stress_early": (w2, "F1_S_B"),
          "P_stress_noexp": (w2, "F1_S_A"), "P_start": (w3, "SUB|3a_ref1")}
add = []
for p, (df, name) in probes.items():
    x = df[df.model == name][COLS].copy()
    x["model"] = p
    add.append(x)
allp = pd.concat([w1] + add, ignore_index=True)
sc = W1.scores(allp)
real = sc[sc.scenario == "real"].pivot_table(index="h", columns="model", values="s")
d = real[list(probes)].sub(real["SUB"], axis=0)
d.to_csv(os.path.join(OUT, "wp6_delta_s_vs_SUB_by_h.csv"))
hyp = pd.DataFrame([dict(h=W1.hname(h), **h) for h in W1.HYP]).set_index("h")
wd = pd.Series(W1.prior_weights("diagnosis"), index=[W1.hname(h) for h in W1.HYP])
summ = {}
for p in probes:
    x = d[p]
    summ[p] = dict(E_diag=float((x * wd).sum()), E_uniform=float(x.mean()), worst_loss=float(x.max()), best_gain=float(x.min()),
                   mean_d0=float(x[hyp["d"] == 0.0].mean()), mean_d031=float(x[hyp["d"] == -0.031].mean()),
                   mean_f0=float(x[hyp["f"] == 0.0].mean()), mean_f1=float(x[hyp["f"] == 1.0].mean()),
                   mean_D0=float(x[hyp["Delta"] == 0.0].mean()), mean_D08=float(x[hyp["Delta"] == 0.8].mean()),
                   wins=int((x < 0).sum()))
S = pd.DataFrame(summ).T
S.to_csv(os.path.join(OUT, "wp6_probe_summary.csv"))
# registered ordering among the three discriminating probes
target = {"P_drift": "mean_d031", "P_stress_early": "mean_D0", "P_start": "E_diag"}
order = sorted(target, key=lambda p: (S.loc[p, "E_diag"], S.loc[p, "worst_loss"]))
soh = {}
for p, (df, name) in probes.items():
    soh[p] = df[df.model == name].sort_values("k")["SOH"].round(3).tolist()
soh["SUB"] = sel(pd.read_csv(os.path.join(STUDY, "wp2", "outputs", "wp2_real_predictions.csv")))
soh["SUB"] = soh["SUB"][soh["SUB"].model == "SUB"].sort_values("k")["SOH"].round(3).tolist()
json.dump(dict(order=order, summary=S.round(4).to_dict(orient="index"), soh=soh), open(os.path.join(OUT, "wp6_probe_plan.json"), "w"),
          indent=1)
pd.set_option("display.width", 220)
print(S.round(4).to_string())
print("order:", order)
print(pd.DataFrame(soh, index=[f"CK{k}" for k in range(1, 8)]).to_string())
