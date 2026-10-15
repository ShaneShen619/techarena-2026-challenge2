"""Stage 2, design round 2 (protocol_round2.json). Usage: run_2.py select | real"""
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
sys.path.insert(0, os.path.join(STUDY, "stage_1"))
from common5c import H  # noqa: E402
from preds5c import ens, s_pred  # noqa: E402
from runner5c import COLD, PSEUDO, run, scen_mean  # noqa: E402
from smodel5c import LawFit  # noqa: E402

OUT = os.path.join(HERE, "outputs")
TAG = "R2"
GAP = dict(steps=True, steps_mode="gap_endpoint", beta_mode="one")
DESIGNS = {"R2_A": dict(law="power", sigma_s=0.10, **GAP),
           "R2_B": dict(law="two", sigma_s=0.10, **GAP),
           "R2_C": dict(law="two", sigma_s=0.20, **GAP)}
ENS_OF, W_GRID = "R2_B", (0.25, 0.5, 0.75, 1.0)
ORDER = ["R2_A", "R2_B", "R2_C", "R2_D"]


def build():
    B = {n: s_pred(n, cls=LawFit, cfg=c, uses_steps=True) for n, c in DESIGNS.items()}
    P = dict(H.BASELINES)
    P.update(B)
    for w in W_GRID[:-1]:
        P[f"R2_D_w{w}"] = ens(B[ENS_OF], w)
    return P


P = build()


def scores(met):
    rows = []
    for m in P:
        ps, cs = scen_mean(met, PSEUDO, m), scen_mean(met, COLD, m)
        rows.append(dict(model=m, pseudo=ps, cold=cs, score=0.5 * (ps + cs)))
    return pd.DataFrame(rows).set_index("model")


def select():
    df = run(P, COLD + PSEUDO)
    df.to_csv(os.path.join(OUT, f"S2_{TAG}_pseudo_cold_predictions.csv"), index=False)
    met = H.metrics(df)
    met.to_csv(os.path.join(OUT, f"S2_{TAG}_pseudo_cold_metrics.csv"), index=False)
    sc = scores(met)
    v2p, v2c = sc.loc["V2", "pseudo"], sc.loc["V2", "cold"]
    sc["G_pseudo"] = sc["pseudo"] <= v2p + 0.02
    sc["G_coldstart"] = sc["cold"] <= v2c
    cw = {w: (sc.loc[f"R2_D_w{w}", "score"] if w < 1 else sc.loc[ENS_OF, "score"]) for w in W_GRID}
    w = min(cw, key=lambda x: (cw[x], -x))
    cand = ["R2_A", "R2_B", "R2_C"] + ([f"R2_D_w{w}"] if w < 1 else [])
    ok = [n for n in cand if sc.loc[n, "G_pseudo"] and sc.loc[n, "G_coldstart"]]
    order = {n: i for i, n in enumerate(cand)}
    main = min(ok, key=lambda n: (round(sc.loc[n, "score"], 9), order[n])) if ok else None
    sel = dict(chosen_w=w, candidates=cand, passing_pre_gates=ok, main=main, V2_pseudo=v2p, V2_cold=v2c,
               scores=sc.round(6).reset_index().to_dict(orient="records"))
    json.dump(sel, open(os.path.join(OUT, f"S2_{TAG}_selection.json"), "w"), indent=1, default=float)
    print(sc.round(4).to_string())
    print(json.dumps({k: v for k, v in sel.items() if k != "scores"}, indent=1, default=float))


def real():
    from run_1 import targets
    sel = json.load(open(os.path.join(OUT, f"S2_{TAG}_selection.json")))
    sc = pd.DataFrame(sel["scores"]).set_index("model")
    df = run(P, ("real",), variants=H.VARIANTS)
    df.to_csv(os.path.join(OUT, f"S2_{TAG}_real_predictions.csv"), index=False)
    met = H.metrics(df)
    met.to_csv(os.path.join(OUT, f"S2_{TAG}_real_metrics.csv"), index=False)
    H.metrics(run(P, ("PC5_all", "PC10_all"))).to_csv(os.path.join(OUT, f"S2_{TAG}_pc_k2_reporting_metrics.csv"), index=False)
    mm = met[(met["step"] == "main") & (met["a4s"] == 2.0)]
    tbl = mm.pivot_table(index="model", columns="delta", values=["MAE", "MAX"])
    tbl.columns = [f"{a}_d{b}" for a, b in tbl.columns]
    tbl = tbl.join(mm[mm["delta"] == 0.0].set_index("model")["CK2_7_MAE"].rename("epsfree"))
    pck = H.per_ck(df)
    tbl = tbl.join(pck.T[["CK1", "CK2"]]).join(sc[["pseudo", "cold", "score"]])
    gates, tg = {}, {}
    for n in P:
        if n in ("V2", "M4"):
            continue
        g = H.gates_vs_v2(met, pck, n, variants_met=met)
        g["G-pseudo"] = bool(sc.loc[n, "pseudo"] <= sel["V2_pseudo"] + 0.02)
        g["G-coldstart"] = bool(sc.loc[n, "cold"] <= sel["V2_cold"])
        g["all_performance_gates"] = bool(g["G-proxy"] and g["G-epsfree"]["passed"] and g["G-robust"]["passed"]
                                          and g["G-pseudo"] and g["G-coldstart"] and g["G-regress"]["passed"])
        gates[n] = g
        tg[n] = targets(tbl.loc[n], sc.loc[n])
    passing = [n for n in sel["candidates"] if gates[n]["all_performance_gates"]]
    cand = min(passing, key=lambda n: sc.loc[n, "score"]) if passing else None
    out = dict(main=sel["main"], registered_candidates=sel["candidates"], passing_registered=passing, candidate=cand,
               passing_any_reported=[n for n in gates if gates[n]["all_performance_gates"]], gates=gates, targets=tg)
    json.dump(out, open(os.path.join(OUT, f"S2_{TAG}_gates_targets.json"), "w"), indent=1, default=float)
    tbl.to_csv(os.path.join(OUT, f"S2_{TAG}_summary_table.csv"))
    pck.to_csv(os.path.join(OUT, f"S2_{TAG}_per_checkup_d04.csv"))
    print(tbl.round(3).to_string())
    print(pck.round(3).to_string())
    print(json.dumps({k: v for k, v in out.items() if k not in ("gates",)}, indent=1, default=float))


if __name__ == "__main__":
    {"select": select, "real": real}[sys.argv[1]]()
