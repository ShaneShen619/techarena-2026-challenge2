"""WP3: E1 ensemble curves for M = R3_T (partners V2 and SUB) and FINAL (= REF) against SUB, causal only."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from eval17 import CAUSAL, paired  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
DELTA = json.load(open(os.path.join(STUDY, "wp0", "outputs", "noise.json")))["delta"]

base = pd.read_csv(os.path.join(STUDY, "wp0", "outputs", "wp0_base_predictions.csv"))
base = base[(base["step"] == "main") & (base["scenario"].isin(CAUSAL))]
sub = pd.read_csv(os.path.join(STUDY, "sources", "r10_wp1_predictions.csv"))
sub = sub[(sub["model"] == "A3") & (sub["step"] == "main") & sub["scenario"].isin(CAUSAL)].assign(model="SUB")
df = pd.concat([base, sub[base.columns.intersection(sub.columns)]], ignore_index=True)
W = (0.0, 0.25, 0.5, 0.75, 1.0)


def piv(d):
    return df[df["delta"] == d].pivot_table(index=["scenario", "k"], columns="model", values="err_pp")


curves, loko = [], {}
for d in (0.0, 0.4, 0.8):
    e = piv(d)
    for partner in ("V2", "SUB"):
        for w in W:
            err = w * e["R3_T"] + (1 - w) * e[partner]      # errors are linear in Q (same proxy per case)
            a = err.abs()
            curves.append(dict(delta=d, partner=partner, w=w, mae_cases=float(a.mean()),
                               mae_scen=float(a.groupby(level="scenario").mean().mean()),
                               pseudo=float(a.groupby(level="scenario").mean().reindex(["PG1", "PG2", "PC5", "PC10"]).mean()),
                               cold=float(a.groupby(level="scenario").mean().reindex(["CS", "CSE"]).mean())))
        if d == 0.4:
            picks = {}
            for kk in sorted(e.index.get_level_values("k").unique()):
                keep = e.index.get_level_values("k") != kk
                sc = {w: float((w * e["R3_T"] + (1 - w) * e[partner])[keep].abs().mean()) for w in W}
                picks[int(kk)] = min(sc, key=sc.get)
            loko[partner] = picks
curves = pd.DataFrame(curves)
curves.to_csv(os.path.join(OUT, "e1_curves.csv"), index=False)

# step 3: FINAL (= REF) against SUB
fin = df.copy()
st = paired(fin, "REF", "SUB", delta=0.4)
crit = {"1_mean_r": st["mean"] <= -DELTA, "2_pos_blocks": st["n_pos_blocks"] <= 1, "3_loko": st["max_loko"] <= 0,
        "4_worst": st["worst"] <= 0.30}
st["cases"].to_csv(os.path.join(OUT, "final_vs_sub_cases.csv"), index=False)
res = dict(M="R3_T", FINAL="0.75 R3_T + 0.25 V2 (= REF)", E2="not run (D3.0)",
           e1_delta04=curves[curves["delta"] == 0.4].round(4).to_dict(orient="records"),
           e1_loko_argmin_w=loko,
           final_vs_sub={k: v for k, v in st.items() if k != "cases"}, final_vs_sub_criteria=crit,
           causally_better_than_SUB=bool(all(crit.values())))
json.dump(res, open(os.path.join(OUT, "wp3.json"), "w"), indent=1)
print(curves[curves["delta"] == 0.4].round(4).to_string())
print("LOKO", loko)
print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in res["final_vs_sub"].items()}, crit,
      res["causally_better_than_SUB"])
