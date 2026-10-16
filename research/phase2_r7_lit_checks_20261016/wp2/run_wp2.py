"""WP2: temperature-weighted sqrt time (protocol.json). Usage: python3 -B run_wp2.py causal | real"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
sys.path.insert(0, os.path.join(STUDY, "sources", "v3"))
sys.path.insert(0, os.path.join(STUDY, "wp1"))
from common6 import H  # noqa: E402
from runner5c import COLD, PSEUDO, run, scen_mean  # noqa: E402
import grid7 as G  # noqa: E402
import tsqrt as T  # noqa: E402

OUT = os.path.join(HERE, "outputs")
NAMES = ["T_main", "T_ea37", "T_gap45", "T_seg25", "R_p044"]
P = {"SUB": G.SUB, **{n: T.design_pred(n) for n in NAMES}}


def gap_mae(df, scen, model):
    g = df[(df.scenario == scen) & (df.model == model) & (df.delta == 0.4) & (df.branch == "sqrt_gap") & (df.k >= 3)]
    return float(g["err_pp"].abs().mean()), int(len(g))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "causal":
        df = run(P, PSEUDO + COLD)
        df.to_csv(os.path.join(OUT, "wp2_causal_predictions.csv"), index=False)
        met = H.metrics(df)
        rows = []
        for m in P:
            cut_mae, n_cut = gap_mae(df, "PC10", m)
            cse_mae, n_cse = gap_mae(df, "CSE", m)
            rows.append(dict(model=m, gap_cut_MAE=cut_mae, n_cut=n_cut, gap_CSE_MAE=cse_mae, n_cse=n_cse,
                             pseudo=scen_mean(met, PSEUDO, m), cold=scen_mean(met, COLD, m)))
        t = pd.DataFrame(rows).set_index("model")
        sub = t.loc["SUB"]
        for m in t.index:
            t.loc[m, "G_gapcases"] = bool(t.loc[m, "gap_cut_MAE"] <= sub["gap_cut_MAE"] - 0.005)
            t.loc[m, "G_pseudo"] = bool(t.loc[m, "pseudo"] <= sub["pseudo"] + 0.005)
            t.loc[m, "G_coldstart"] = bool(t.loc[m, "cold"] <= sub["cold"] + 0.005)
        per = df[(df.delta == 0.4) & (df.branch == "sqrt_gap") & df.scenario.isin(["PC10", "CSE"])].pivot_table(
            index=["scenario", "checkup"], columns="model", values="err_pp")
        per.to_csv(os.path.join(OUT, "wp2_gapcase_errors.csv"))
        t.to_csv(os.path.join(OUT, "wp2_causal_table.csv"))
        pd.set_option("display.width", 220)
        print(t.round(4).to_string())
        print(per.round(3).to_string())
    else:
        df = run(P, ("real",))
        df.to_csv(os.path.join(OUT, "wp2_real_predictions.csv"), index=False)
        met = H.metrics(df)
        m = met[(met.scenario == "real") & (met.step == "main")]
        real = m.pivot_table(index="model", columns="delta", values=["MAE", "MAX"])
        per = df[df.delta == 0.4].pivot_table(index="model", columns="checkup", values="err_pp")
        soh = df[df.delta == 0.4].pivot_table(index="model", columns="checkup", values="SOH")
        # TUM consistency: CK2 increment relative to SUB (delta 0.4)
        r = df[(df.delta == 0.4) & (df.k == 2)].set_index("model")["Q"]
        r1 = df[(df.delta == 0.4) & (df.k == 1)].set_index("model")["Q"]
        q1 = float(H.QFC[1] + H.EPS0 + 0.4)   # anchor 1 + eps: the branch base for CK2
        inc = {mm: float(q1 - r[mm]) for mm in P}
        tum = {mm: inc[mm] / inc["SUB"] for mm in P}
        # grid: round-6 candidates + SUB+drift + designs, round-6 grid + H_ov_after (b0 median)
        from run_wp1 import ov_targets
        p6 = pd.read_csv(os.path.join(G.R6, "wp1", "outputs", "wp1_predictions.csv"))
        p6 = p6[(p6.scenario == "real") & (p6.step == "main") & (p6.a4s == 2.0)][["scenario", "k", "model", "Q"]]
        sub = p6[p6.model == "SUB"].copy()
        sub["Q"] = sub["Q"] - 0.031 * np.maximum(0.0, 100.41 - sub["Q"])
        sub["model"] = "SUB+drift-0.031"
        des = df[(df.delta == 0.4) & (df.model != "SUB")][["scenario", "k", "model", "Q"]]
        pred = pd.concat([p6, sub, des], ignore_index=True)
        tab = pd.read_csv(os.path.join(STUDY, "wp1", "outputs", "anchor_state_table.csv"))
        ovt, _ = ov_targets(tab, "median")
        sc = G.scores(pred, {**G.targets6(), **ovt})
        cand = [x for x in sc.model.unique() if x != "EX"]
        s = sc.pivot_table(index="h", columns="model", values="s")[cand]
        tg, _ = G.decision(s)
        tg.sort_values("max_regret").to_csv(os.path.join(OUT, "wp2_grid_decision.csv"))
        caus = pd.read_csv(os.path.join(OUT, "wp2_causal_table.csv"), index_col="model")
        gates = caus[["G_gapcases", "G_pseudo", "G_coldstart"]].copy()
        for mm in gates.index:
            gates.loc[mm, "G_hyp"] = bool(tg.loc[mm, "max_regret"] <= tg.loc["SUB", "max_regret"] + 0.005)
        gates["data_gates_all"] = gates[["G_gapcases", "G_pseudo", "G_coldstart", "G_hyp"]].all(axis=1)
        gates.loc["R_p044", "data_gates_all"] = False   # non-causal reference, never selectable
        gates.to_csv(os.path.join(OUT, "wp2_gates.csv"))
        out = dict(real_MAE={mm: [float(real.loc[mm, ("MAE", d)]) for d in (0.0, 0.4, 0.8)] for mm in P},
                   real_MAX={mm: [float(real.loc[mm, ("MAX", d)]) for d in (0.0, 0.4, 0.8)] for mm in P},
                   CK2_err_pp_d04={mm: float(per.loc[mm, "CK2"]) for mm in P},
                   CK2_SOH={mm: float(soh.loc[mm, "CK2"]) for mm in P},
                   CK2_increment_Ah=inc, ratio_to_SUB_increment=tum, TUM_median_ratio=0.87,
                   grid_max_regret={mm: float(tg.loc[mm, "max_regret"]) for mm in P},
                   gates=gates.astype(object).to_dict(orient="index"),
                   T_main_passes=bool(gates.loc["T_main", "data_gates_all"]))
        json.dump(out, open(os.path.join(OUT, "wp2_real_summary.json"), "w"), indent=1, default=bool)
        per.to_csv(os.path.join(OUT, "wp2_real_errors_d04.csv"))
        soh.to_csv(os.path.join(OUT, "wp2_real_SOH_d04.csv"))
        pd.set_option("display.width", 220)
        print(json.dumps(out, indent=1, default=bool))
        print(per.round(3).to_string())
