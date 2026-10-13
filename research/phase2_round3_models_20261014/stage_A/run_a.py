"""Stage A: registration table, identifiability, beta_reg, V2_reg evaluation and gates."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
import harness as H  # noqa: E402
import registration as R  # noqa: E402

OUT = os.path.join(HERE, "outputs")

# 1. registration table on the full data (each anchor's registration is cutoff-independent)
op = H.cut_op(7)
fc, st, a4 = H.tables(op, "real_ck7")
rows = []
for mode, fit in (("V", "full"), ("dVdQ", "full"), ("V", "bottom")):
    anc, reg = R.anchor_registrations(op, fc, a4[2.0], H.CK, mode, fit)
    for j, cells in reg.items():
        for c, rr in enumerate(cells):
            rows.append(dict(mode=mode, fit=fit, anchor=j, cell=c + 1, **rr))
tab = pd.DataFrame(rows)
tab.to_csv(os.path.join(OUT, "A_registration.csv"), index=False)
ident = tab.groupby(["mode", "fit"]).agg(n=("ident_b", "size"), ident_b=("ident_b", "mean"),
                                          ident_t=("ident_t", "mean")).reset_index()
print(tab[(tab["mode"] == "V") & (tab["fit"] == "full")][["anchor", "cell", "s_b", "s_t", "bottom", "p1", "loss", "span_b", "span_t", "ident_b", "ident_t"]].round(4).to_string(index=False))
print(ident)

# 2. dQ split per anchor (four-cell mean), main registration
anc, reg = R.anchor_registrations(op, fc, a4[2.0], H.CK, "V", "full")
split = []
for j, cells in reg.items():
    bottom = np.mean([c["bottom"] for c in cells])
    p1 = np.mean([c["p1"] for c in cells])
    dq = anc[j]["Q_Ah"] - anc[1]["Q_Ah"]
    split.append(dict(anchor=j, dQ=dq, dbottom=bottom - p1, dtop=dq - (bottom - p1),
                      top_share=(dq - (bottom - p1)) / dq if dq else np.nan))
split = pd.DataFrame(split)
split.to_csv(os.path.join(OUT, "A_split.csv"), index=False)
print(split.round(3))

# 3. evaluation
preds = {"M4": H.m4_pred, "V2": H.v2_pred,
         "V2_reg": lambda c: R.v2_reg(c, "V", "full"),
         "V2_reg_dvdq": lambda c: R.v2_reg(c, "dVdQ", "full"),
         "V2_reg_bottom": lambda c: R.v2_reg(c, "V", "bottom")}
df = H.run(preds, scenarios=("real", "PG1", "PG2", "PC5", "PC10"), variants=H.VARIANTS)
df.to_csv(os.path.join(OUT, "A_long.csv"), index=False)
met = H.metrics(df)
met.to_csv(os.path.join(OUT, "A_metrics.csv"), index=False)
pck = H.per_ck(df)
g = H.gates_vs_v2(met, pck, "V2_reg", variants_met=met)
ident_main = ident[(ident["mode"] == "V") & (ident["fit"] == "full")].iloc[0]
g["identifiability"] = dict(frac_bottom_identified=float(ident_main["ident_b"]),
                            exit_triggered=bool(ident_main["ident_b"] <= 0.5))
json.dump(g, open(os.path.join(OUT, "A_gates.json"), "w"), indent=1, default=float)
r = df[(df.scenario == "real") & (df.delta == 0.4) & (df.step == "main") & (df.model == "V2_reg")]
print(r[["checkup", "branch", "beta", "beta_reg", "err_pp"]].round(3).to_string(index=False))
print(pck.round(3))
m = met[(met.step == "main") & (met.delta == 0.4)]
print(m.pivot_table(index="model", columns="scenario", values="MAE").round(3))
print(met[(met.scenario == "real") & (met.step == "main")].pivot_table(index="model", columns="delta", values=["MAE", "MAX"]).round(3))
print(met[(met.scenario == "real") & (met.delta == 0.4)].pivot_table(index="step", columns="model", values="MAE").round(3))
print(json.dumps(g, indent=1, default=float))
