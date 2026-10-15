"""WP4 evaluation of S_A3 (S_A with prior3) alone and in the WP2 fusion designs. Usage: run_wp4.py select | real"""
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

OUT = os.path.join(HERE, "outputs")
P3 = json.load(open(os.path.join(HERE, "prior3.json")))
PRIOR3 = {k: (P3[k]["mean"], P3[k]["sd"]) for k in ("logA_b", "logtau_b", "logA_cal", "logA_cyc")}
CFG = dict(W2.GAP, prior2=PRIOR3)
# route WP2's estimation helpers to this WP's outputs and to the S_A3 variant only
W2.OUT = OUT
W2.PARAMS = os.path.join(OUT, "wp4_estimated_params.json")
W2.S_CFG = {"S_A3": CFG}
W2.SVAR = {"S_A3": s_pred("WP4_S_A3", cls=LawFit, cfg=CFG, uses_steps=True)}
S_A_REF = s_pred("WP4_S_A_ref", cls=LawFit, cfg=dict(W2.GAP), uses_steps=True)


def predictors(prm):
    P = {"V2": H.BASELINES["V2"], "SUB": W2.sub_pred, "S_A (prior2)": S_A_REF, "S_A3": W2.SVAR["S_A3"]}
    P["F2_S_A3"] = W2.fused("S_A3", "F2", prm)
    P["F1_S_A3"] = W2.fused("S_A3", "F1", prm)
    return P


def select():
    prm = W2.estimate()
    P = predictors(prm)
    df = run(P, PSEUDO + COLD)
    df.to_csv(os.path.join(OUT, "wp4_pseudo_cold_predictions.csv"), index=False)
    met = H.metrics(df)
    rows = []
    for m in P:
        ps, cs = scen_mean(met, PSEUDO, m), scen_mean(met, COLD, m)
        rows.append(dict(model=m, pseudo=ps, cold=cs, score=0.5 * (ps + cs)))
    sc = pd.DataFrame(rows).set_index("model")
    sc["G_pseudo"] = sc["pseudo"] <= sc.loc["SUB", "pseudo"] + 0.02
    sc["G_coldstart"] = sc["cold"] <= sc.loc["SUB", "cold"]
    sel = dict(params=prm, SUB_pseudo=float(sc.loc["SUB", "pseudo"]), SUB_cold=float(sc.loc["SUB", "cold"]),
               scores=sc.round(6).reset_index().to_dict(orient="records"))
    json.dump(sel, open(os.path.join(OUT, "wp4_selection.json"), "w"), indent=1, default=float)
    print(json.dumps(prm, indent=1))
    print(sc.round(4).to_string())


def real():
    sel = json.load(open(os.path.join(OUT, "wp4_selection.json")))
    sc = pd.DataFrame(sel["scores"]).set_index("model")
    P = predictors(sel["params"])
    df = run(P, ("real",), variants=H.VARIANTS)
    df.to_csv(os.path.join(OUT, "wp4_real_predictions.csv"), index=False)
    met = H.metrics(df)
    met.to_csv(os.path.join(OUT, "wp4_real_metrics.csv"), index=False)
    pck = H.per_ck(df)
    pck.to_csv(os.path.join(OUT, "wp4_per_checkup_d04.csv"))
    hyp = W2.g_hyp(df)
    hyp.to_csv(os.path.join(OUT, "wp4_hypothesis_decision_table.csv"))
    gates = {}
    for n in ("S_A3", "F2_S_A3", "F1_S_A3"):
        g = W2.gates_vs_sub(met, pck, n)
        g["G-pseudo"] = bool(sc.loc[n, "pseudo"] <= sel["SUB_pseudo"] + 0.02)
        g["G-coldstart"] = bool(sc.loc[n, "cold"] <= sel["SUB_cold"])
        g["G-hyp"] = dict(model=float(hyp.loc[n, "max_regret"]), SUB=float(hyp.loc["SUB", "max_regret"]),
                          passed=bool(hyp.loc[n, "max_regret"] <= hyp.loc["SUB", "max_regret"]))
        g["all_performance_gates"] = bool(g["G-proxy"] and g["G-epsfree"]["passed"] and g["G-robust"]["passed"]
                                          and g["G-pseudo"] and g["G-coldstart"] and g["G-regress"]["passed"]
                                          and g["G-hyp"]["passed"])
        gates[n] = g
    mm = met[(met.scenario == "real") & (met.step == "main") & (met.a4s == 2.0)]
    tbl = mm.pivot_table(index="model", columns="delta", values=["MAE", "MAX"])
    tbl.columns = [f"{a}_d{b}" for a, b in tbl.columns]
    tbl = tbl.join(mm[mm.delta == 0.0].set_index("model")["CK2_7_MAE"].rename("epsfree"))
    tbl = tbl.join(sc[["pseudo", "cold", "score"]]).join(hyp[["max_regret", "worst_s", "E_diagnosis"]])
    tbl.to_csv(os.path.join(OUT, "wp4_summary_table.csv"))
    json.dump(gates, open(os.path.join(OUT, "wp4_gates.json"), "w"), indent=1, default=float)
    pd.set_option("display.width", 220)
    print(tbl.round(3).to_string())
    print(pck.round(3).to_string())
    for n, g in gates.items():
        print(n, {k: (v if isinstance(v, bool) else v.get("passed")) for k, v in g.items() if k != "all_performance_gates"},
              "ALL", g["all_performance_gates"])


if __name__ == "__main__":
    {"select": select, "real": real}[sys.argv[1]]()
