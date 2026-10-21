"""WP2 step 1: prediction screen (predictions only, no labels). dSOH = SOH(X) - SOH(R3_T) per case at delta 0.4, main, a4s 2."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))

# guard: this script must not touch label columns (tokens split so the check does not match itself)
_SRC = open(os.path.abspath(__file__)).read()
for tok in ("Q" + "FC", "pro" + "xy", "err" + "_pp"):
    assert tok not in _SRC, tok

from designs17 import TAU_GRID, predictors  # noqa: E402
from eval17 import CAUSAL, H  # noqa: E402
from runner5c import SCEN, scenario_tables  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
NOISE = json.load(open(os.path.join(STUDY, "wp0", "outputs", "noise.json")))
T_MOVE = NOISE["T_move"]

P = predictors(with_ens=False, sens=True)
P.pop("V2")
rows = []
for scen in ("real",) + CAUSAL:
    for k, spec in SCEN[scen]:
        t = scenario_tables(k, spec)
        if t is None:
            continue
        op, fc, st, a4, key = t
        ctx = dict(k=k, at_date=H.CK[k], ck=H.CK, op=op, fc=fc, steps=st, step="main", a4=a4, a4s=2.0,
                   eps=H.EPS0 + 0.4, eps0=H.EPS0, delta=0.4, scenario=scen, key=key)
        for name, f in P.items():
            q, info = f(ctx)
            rows.append(dict(scenario=scen, k=k, model=name, SOH=q / H.NOM * 100,
                             w_top=info.get("w_top", np.nan), tau_top=info.get("tau_top", np.nan)))
df = pd.DataFrame(rows)
base = df[df["model"] == "R3_T"].set_index(["scenario", "k"])["SOH"]
df["dSOH"] = df["SOH"] - df.set_index(["scenario", "k"]).index.map(base)
df.to_csv(os.path.join(OUT, "screen_predictions.csv"), index=False)

MAIN = ["B0", "S", "C", "O1", "O2", "D"]
summ = []
for m, g in df[df["model"] != "R3_T"].groupby("model"):
    c = g[g["scenario"] != "real"]["dSOH"].abs()
    r = g[g["scenario"] == "real"]["dSOH"].abs()
    s_c, s_r = float(np.percentile(c, 90)), float(r.max())
    summ.append(dict(model=m, main=m in MAIN, S_causal=s_c, S_real=s_r,
                     S_real_k=int(g[g["scenario"] == "real"].set_index("k")["dSOH"].abs().idxmax()),
                     moves=bool(s_c >= T_MOVE or s_r >= 2 * T_MOVE),
                     mean_dSOH_causal=float(g[g["scenario"] != "real"]["dSOH"].mean()),
                     real_dSOH=g[g["scenario"] == "real"].set_index("k")["dSOH"].round(4).to_dict()))
summ = pd.DataFrame(summ).sort_values(["main", "model"], ascending=[False, True])
summ.to_csv(os.path.join(OUT, "screen_summary.csv"), index=False)

# O1 identifiability (main variant): top Laplace weight per causal case
o1 = df[(df["model"] == "O1") & (df["scenario"] != "real")]
ident = dict(n=int(len(o1)), n_top_ge_0_8=int((o1["w_top"] >= 0.8).sum()),
             identified=bool((o1["w_top"] >= 0.8).sum() >= len(o1) / 2),
             tau_top_counts={f"{t:.1f}": int((o1["tau_top"].round(1) == round(t, 1)).sum()) for t in TAU_GRID},
             per_case=o1[["scenario", "k", "w_top", "tau_top"]].round(3).to_dict(orient="records"),
             real=df[(df["model"] == "O1") & (df["scenario"] == "real")][["k", "w_top", "tau_top"]].round(3)
             .to_dict(orient="records"))
res = dict(T_move=T_MOVE, rule="moves if S_causal >= T_move or S_real >= 2 T_move",
           screen=summ.to_dict(orient="records"), O1_identifiability=ident)
json.dump(res, open(os.path.join(OUT, "screen.json"), "w"), indent=1)
print(summ[["model", "main", "S_causal", "S_real", "S_real_k", "moves", "mean_dSOH_causal"]].round(4).to_string())
print({k: v for k, v in ident.items() if k not in ("per_case", "real")})
