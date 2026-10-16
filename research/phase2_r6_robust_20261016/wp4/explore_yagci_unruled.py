"""WP4 EXPLORATORY (not registered, not a candidate): S_A with the unruled Yagci calendar fit
(A_b, tau_b, A_cal as fitted, ignoring the bound / jackknife fallback; A_cyc from prior2).
Answers only: could the open-data break-in term remove the CK1 cold-start error?
Usage: python3 explore_yagci_unruled.py"""
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
sys.path.insert(0, os.path.join(STUDY, "wp2"))
from common6 import H  # noqa: E402
from preds5c import s_pred  # noqa: E402
from runner5c import COLD, PSEUDO, run, scen_mean  # noqa: E402
from smodel5c import LawFit  # noqa: E402
import run_wp2 as W2  # noqa: E402

P3 = json.load(open(os.path.join(HERE, "prior3.json")))
cf = P3["calendar_fit"]
PR = {"logA_b": (cf["logA_b"], 1.0986), "logtau_b": (cf["logtau_b"], 0.5), "logA_cal": (cf["logA_cal"], 1.0986),
      "logA_cyc": (P3["logA_cyc"]["mean"], P3["logA_cyc"]["sd"])}
P = {"SUB": W2.sub_pred, "S_A3": s_pred("WP4_S_A3x", cls=LawFit, cfg=dict(W2.GAP, prior2={k: (P3[k]["mean"], P3[k]["sd"]) for k in PR}),
                                           uses_steps=True),
     "S_A_yagci_unruled": s_pred("WP4_S_Ayu", cls=LawFit, cfg=dict(W2.GAP, prior2=PR), uses_steps=True)}
df = run(P, PSEUDO + COLD)
met = H.metrics(df)
rows = [dict(model=m, pseudo=scen_mean(met, PSEUDO, m), cold=scen_mean(met, COLD, m)) for m in P]
dr = run(P, ("real",), deltas=(0.4,))
mr = H.metrics(dr)
mr = mr[(mr.scenario == "real") & (mr.step == "main") & (mr.a4s == 2.0)].set_index("model")
pck = H.per_ck(dr)
out = pd.DataFrame(rows).set_index("model").join(mr[["MAE", "MAX"]].rename(columns=lambda c: f"real_{c}_d0.4"))
os.makedirs(os.path.join(HERE, "outputs", "exploratory"), exist_ok=True)
out.to_csv(os.path.join(HERE, "outputs", "exploratory", "wp4x_yagci_unruled_summary.csv"))
pck.to_csv(os.path.join(HERE, "outputs", "exploratory", "wp4x_yagci_unruled_per_checkup_d04.csv"))
print(json.dumps(PR))
print(out.round(3).to_string())
print(pck.round(3).to_string())
