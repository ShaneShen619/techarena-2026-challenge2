"""Stage 1 (design round 1). Usage: run_1.py select | real"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common5c import H  # noqa: E402
from preds5c import ens, hybrid_v2_at, s_pred  # noqa: E402
from runner5c import COLD, PSEUDO, run, scen_mean  # noqa: E402
from smodel5c import LawFit  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
W_GRID = (0.25, 0.5, 0.75, 1.0)

DESIGNS = {
    "D1": {"law": "power", "steps": True},
    "D1:sigma_s_half": {"law": "power", "steps": True, "sigma_s": 0.025},
    "D1:sigma_s_double": {"law": "power", "steps": True, "sigma_s": 0.10},
    "D1:beta_free": {"law": "power", "steps": True, "beta_mode": "free"},
    "D1:with_25C": {"law": "power", "steps": True, "include_25C": True},
    "D2": {"law": "two"},
    "D2:tau_b_free": {"law": "two", "tau_b_free": True},
    "D3": {"law": "two", "steps": True},
    "D3:sigma_s_half": {"law": "two", "steps": True, "sigma_s": 0.025},
    "D3:sigma_s_double": {"law": "two", "steps": True, "sigma_s": 0.10},
    "D3:tau_b_free": {"law": "two", "steps": True, "tau_b_free": True},
}
BASES = {}
for n, cfg in DESIGNS.items():
    BASES[n] = s_pred("R1_" + n, cls=LawFit, cfg=cfg, uses_steps=bool(cfg.get("steps")))
P = dict(H.BASELINES)
P.update(BASES)
for d in ("D1", "D2", "D3"):
    for w in W_GRID[:-1]:
        P[f"D4_{d}_w{w}"] = ens(BASES[d], w)
P["D5_exposedCK1"] = hybrid_v2_at(BASES["D3"], ks=(1,))
STEP_MODELS = [n for n in P if n not in ("M4", "V2", "D2", "D2:tau_b_free")]


def score_table(met):
    rows = []
    for m in P:
        ps, cs = scen_mean(met, PSEUDO, m), scen_mean(met, COLD, m)
        rows.append(dict(model=m, pseudo=ps, cold=cs, score=0.5 * (ps + cs)))
    return pd.DataFrame(rows).set_index("model")


def select():
    df = run(P, COLD + PSEUDO)
    df.to_csv(os.path.join(OUT, "S1_pseudo_cold_predictions.csv"), index=False)
    met = H.metrics(df)
    met.to_csv(os.path.join(OUT, "S1_pseudo_cold_metrics.csv"), index=False)
    sc = score_table(met)
    v2p, v2c = sc.loc["V2", "pseudo"], sc.loc["V2", "cold"]
    sc["G_pseudo"] = sc["pseudo"] <= v2p + 0.02
    sc["G_coldstart"] = sc["cold"] <= v2c
    # D4: choose w per design on the score (w = 1 is the design itself)
    chosen_w = {}
    for d in ("D1", "D2", "D3"):
        cands = {w: (sc.loc[f"D4_{d}_w{w}", "score"] if w < 1 else sc.loc[d, "score"]) for w in W_GRID}
        chosen_w[d] = min(cands, key=lambda w: (cands[w], -w))
    cand = ["D2", "D1", "D3"] + [f"D4_{d}_w{chosen_w[d]}" for d in ("D1", "D2", "D3") if chosen_w[d] < 1]
    order = {n: i for i, n in enumerate(cand)}
    ok = [n for n in cand if sc.loc[n, "G_pseudo"] and sc.loc[n, "G_coldstart"]]
    main = min(ok, key=lambda n: (round(sc.loc[n, "score"], 9), order[n])) if ok else None
    sel = dict(chosen_w=chosen_w, candidates=cand, passing_pre_gates=ok, round1_main=main,
               scores=sc.round(6).reset_index().to_dict(orient="records"), V2_pseudo=v2p, V2_cold=v2c)
    json.dump(sel, open(os.path.join(OUT, "S1_selection.json"), "w"), indent=1, default=float)
    print(sc.round(4).to_string())
    print(json.dumps({k: v for k, v in sel.items() if k != "scores"}, indent=1, default=float))


def targets(row, sc_row):
    t = {}
    t["T1_MAE_all_delta_le_0.15"] = bool(all(row[f"MAE_d{d}"] <= 0.15 for d in (0.0, 0.4, 0.8)))
    t["T2_MAX_all_delta_le_0.45"] = bool(all(row[f"MAX_d{d}"] <= 0.45 for d in (0.0, 0.4, 0.8)))
    t["T3_CK1_CK2_le_0.30"] = bool(abs(row["CK1"]) <= 0.30 and abs(row["CK2"]) <= 0.30)
    t["T4_epsfree_le_0.15"] = bool(row["epsfree"] <= 0.15)
    t["T5_pseudo_le_0.12"] = bool(sc_row["pseudo"] <= 0.12)
    t["T6_cold_le_0.20"] = bool(sc_row["cold"] <= 0.20)
    return t


def real():
    sel = json.load(open(os.path.join(OUT, "S1_selection.json")))
    sc = pd.DataFrame(sel["scores"]).set_index("model")
    df = run(P, ("real",), variants=H.VARIANTS)
    df.to_csv(os.path.join(OUT, "S1_real_predictions.csv"), index=False)
    met = H.metrics(df)
    met.to_csv(os.path.join(OUT, "S1_real_metrics.csv"), index=False)
    rep = run(P, ("PC5_all", "PC10_all"))
    H.metrics(rep).to_csv(os.path.join(OUT, "S1_pc_k2_reporting_metrics.csv"), index=False)
    mm = met[(met["step"] == "main") & (met["a4s"] == 2.0)]
    tbl = mm.pivot_table(index="model", columns="delta", values=["MAE", "MAX"])
    tbl.columns = [f"{a}_d{b}" for a, b in tbl.columns]
    tbl = tbl.join(mm[mm["delta"] == 0.0].set_index("model")["CK2_7_MAE"].rename("epsfree"))
    pck = H.per_ck(df)
    tbl = tbl.join(pck.T[["CK1", "CK2"]])
    tbl = tbl.join(sc[["pseudo", "cold", "score"]])
    gates, tg = {}, {}
    v2 = mm.set_index(["model", "delta"])
    for n in P:
        if n in ("V2", "M4"):
            continue
        g = H.gates_vs_v2(met, pck, n, variants_met=met if n in STEP_MODELS else None)
        if n not in STEP_MODELS:   # D2 family: >= 75 % of registered variant groups (one group: tau_b_free)
            win = bool(v2.loc[("D2:tau_b_free", 0.4), "MAE"] < v2.loc[("V2", 0.4), "MAE"])
            g["G-robust"] = dict(groups={"tau_b_free": win}, passed=win)
        g["G-pseudo"] = bool(sc.loc[n, "pseudo"] <= sel["V2_pseudo"] + 0.02)
        g["G-coldstart"] = bool(sc.loc[n, "cold"] <= sel["V2_cold"])
        g["all_performance_gates"] = bool(g["G-proxy"] and g["G-epsfree"]["passed"] and g["G-robust"]["passed"]
                                          and g["G-pseudo"] and g["G-coldstart"] and g["G-regress"]["passed"])
        gates[n] = g
        tg[n] = targets(tbl.loc[n], sc.loc[n])
    passing = [n for n in gates if gates[n]["all_performance_gates"] and not n.startswith("D5")
               and ":" not in n]
    cand = min(passing, key=lambda n: sc.loc[n, "score"]) if passing else None
    out = dict(round1_main=sel["round1_main"], passing_all_gates=passing,
               D5_passes=gates["D5_exposedCK1"]["all_performance_gates"], candidate=cand,
               gates=gates, targets=tg)
    json.dump(out, open(os.path.join(OUT, "S1_gates_targets.json"), "w"), indent=1, default=float)
    tbl.to_csv(os.path.join(OUT, "S1_summary_table.csv"))
    pck.to_csv(os.path.join(OUT, "S1_per_checkup_d04.csv"))
    print(tbl.round(3).to_string())
    print(pck.round(3).to_string())
    print(json.dumps({k: v for k, v in out.items() if k not in ("gates",)}, indent=1, default=float))


if __name__ == "__main__":
    {"select": select, "real": real}[sys.argv[1]]()
