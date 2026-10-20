"""WP2: uncertainty-weighted fusion of S and SUB (protocol.json). Usage: run_wp2.py select | real"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
sys.path.insert(0, os.path.join(STUDY, "sources", "v3"))
from common6 import H  # noqa: E402
from preds5c import s_pred  # noqa: E402
from runner5c import COLD, PSEUDO, run, scen_mean  # noqa: E402
from smodel5c import LawFit  # noqa: E402
from v3 import v3  # noqa: E402

OUT = os.path.join(HERE, "outputs")
PARAMS = os.path.join(OUT, "wp2_estimated_params.json")
GAP = dict(law="two", steps=True, steps_mode="gap_endpoint", beta_mode="one", sigma_s=0.10)
S_CFG = {"S_A": dict(GAP), "S_B": dict(GAP, transient_ref="restart"), "S_C": dict(GAP, transient_ref="path")}
SVAR = {n: s_pred("WP2_" + n, cls=LawFit, cfg=c, uses_steps=True) for n, c in S_CFG.items()}
W_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
CLASSES = ("cold", "phase", "sqrt_gap", "fallback")


def sub_pred(ctx):
    q, br, b = v3(ctx["fc"], ctx["steps"][ctx["step"]], ctx["a4"][ctx["a4s"]], ctx["ck"], ctx["k"], ctx["eps"],
                  use_sqrt=True, beta_cap=float("inf"), median=False)
    return q, {"branch": br}


def cls_of(info_s, info_u):
    return "cold" if info_s.get("n_pairs", 0) == 0 else info_u["branch"]


def fused(sname, mode, prm):
    S = SVAR[sname]

    def f(ctx):
        qs, i_s = S(ctx)
        qu, i_u = sub_pred(ctx)
        c = cls_of(i_s, i_u)
        if mode == "F1":
            s2s = i_s["q_sd"] ** 2 + prm["sigma_S0"][sname] ** 2
            su = prm["sigma_SUB"].get(i_u["branch"], prm["sigma_SUB"]["pooled"])
            w = su ** 2 / (s2s + su ** 2)
        elif mode == "F2":
            w = prm["F2_w"][sname].get(c, 0.5)
        else:
            w = 0.5
        return w * qs + (1 - w) * qu, {"w": float(w), "cls": c, "branch": i_u["branch"]}
    return f


def base_predictors():
    P = {"V2": H.BASELINES["V2"], "SUB": sub_pred}
    P.update(SVAR)
    return P


def estimate():
    df = run(base_predictors(), PSEUDO + COLD, deltas=(0.4,))
    df.to_csv(os.path.join(OUT, "wp2_base_pseudo_cold.csv"), index=False)
    d = df.copy()
    d["err_Ah"] = d["Q"] - d["proxy"]
    sub = d[d.model == "SUB"].set_index(["scenario", "k"])
    prm = {"sigma_S0": {}, "sigma_SUB": {}, "F2_w": {}, "class_counts": {}}
    for n in S_CFG:
        e = d[d.model == n]["err_Ah"]
        prm["sigma_S0"][n] = float(np.sqrt(np.mean(e ** 2)))
    br = sub["branch"]
    pooled = float(np.sqrt(np.mean(sub["err_Ah"] ** 2)))
    prm["sigma_SUB"]["pooled"] = pooled
    for b in ("phase", "sqrt_gap", "fallback"):
        e = sub.loc[br == b, "err_Ah"]
        prm["sigma_SUB"][b] = float(np.sqrt(np.mean(e ** 2))) if len(e) >= 3 else pooled
        prm["class_counts"][f"SUB_{b}"] = int(len(e))
    for n in S_CFG:
        s = d[d.model == n].set_index(["scenario", "k"])
        j = s[["Q", "proxy", "n_pairs"]].join(sub[["Q", "branch"]], rsuffix="_sub")
        j["cls"] = np.where(j["n_pairs"] == 0, "cold", j["branch"])
        prm["F2_w"][n] = {}
        for c in CLASSES:
            g = j[j["cls"] == c]
            prm["class_counts"][f"{n}_{c}"] = int(len(g))
            if not len(g):
                prm["F2_w"][n][c] = 0.5
                continue
            mae = {w: float(np.mean(np.abs(w * g["Q"] + (1 - w) * g["Q_sub"] - g["proxy"]))) for w in W_GRID}
            best = min(mae.values())
            ties = [w for w in W_GRID if abs(mae[w] - best) < 1e-12]
            prm["F2_w"][n][c] = 0.5 if 0.5 in ties else min(ties)
    json.dump(prm, open(PARAMS, "w"), indent=1)
    return prm


def designs(prm):
    P = {}
    for sname in S_CFG:
        for mode in ("F1", "F2", "F3"):
            P[f"{mode}_{sname}"] = fused(sname, mode, prm)
    return P


def select():
    prm = estimate()
    P = base_predictors()
    P.update(designs(prm))
    df = run(P, PSEUDO + COLD)
    df.to_csv(os.path.join(OUT, "wp2_pseudo_cold_predictions.csv"), index=False)
    met = H.metrics(df)
    met.to_csv(os.path.join(OUT, "wp2_pseudo_cold_metrics.csv"), index=False)
    rows = []
    for m in P:
        ps, cs = scen_mean(met, PSEUDO, m), scen_mean(met, COLD, m)
        rows.append(dict(model=m, pseudo=ps, cold=cs, score=0.5 * (ps + cs)))
    sc = pd.DataFrame(rows).set_index("model")
    sp, scld = sc.loc["SUB", "pseudo"], sc.loc["SUB", "cold"]
    sc["G_pseudo"] = sc["pseudo"] <= sp + 0.02
    sc["G_coldstart"] = sc["cold"] <= scld
    order = {"F3_S_A": 0, "F2_S_A": 1, "F1_S_A": 2}
    ok = [n for n in order if sc.loc[n, "G_pseudo"] and sc.loc[n, "G_coldstart"]]
    main = min(ok, key=lambda n: (round(sc.loc[n, "score"], 9), order[n])) if ok else None
    sel = dict(main=main, passing_pre_gates=ok, SUB_pseudo=sp, SUB_cold=scld, params=prm,
               scores=sc.round(6).reset_index().to_dict(orient="records"))
    json.dump(sel, open(os.path.join(OUT, "wp2_selection.json"), "w"), indent=1, default=float)
    print(json.dumps(prm, indent=1))
    print(sc.round(4).to_string())
    print("main:", main)


def gates_vs_sub(met, pck, name):
    m = met[met["scenario"] == "real"].set_index(["model", "step", "a4s", "delta"])
    ok = []
    for dl in H.DELTAS:
        a, b = m.loc[(name, "main", 2.0, dl)], m.loc[("SUB", "main", 2.0, dl)]
        ok.append(bool(a["MAE"] < b["MAE"] and a["MAX"] <= b["MAX"] + 0.10))
    a, b = m.loc[(name, "main", 2.0, 0.0)], m.loc[("SUB", "main", 2.0, 0.0)]
    wins = [bool(m.loc[(name, v, 2.0, 0.4), "MAE"] < m.loc[("SUB", v, 2.0, 0.4), "MAE"]) for v in H.VARIANTS]
    inc = float((pck[name].abs() - pck["SUB"].abs()).max())
    return {"G-proxy": all(ok), "G-epsfree": dict(model=float(a["CK2_7_MAE"]), SUB=float(b["CK2_7_MAE"]),
                                                   passed=bool(a["CK2_7_MAE"] <= b["CK2_7_MAE"] - 0.02)),
            "G-robust": dict(wins=int(sum(wins)), passed=bool(sum(wins) >= 5)),
            "G-regress": dict(max_abs_err_increase_pp=inc, passed=bool(inc <= 0.30))}


def g_hyp(real_df):
    """WP1 real-grid max regret with each design added to the WP1 candidate set."""
    sys.path.insert(0, os.path.join(STUDY, "wp1"))
    import run_wp1 as W1
    base = pd.read_csv(os.path.join(STUDY, "wp1", "outputs", "wp1_predictions.csv"))
    base = base[(base.scenario == "real") & (base.step == "main") & (base.a4s == 2.0)][["scenario", "k", "model", "Q"]]
    add = real_df[(real_df.delta == 0.4) & (real_df.step == "main") & (real_df.a4s == 2.0)]
    add = add[~add.model.isin(base.model.unique())][["scenario", "k", "model", "Q"]]
    sc = W1.scores(pd.concat([base, add], ignore_index=True))
    cand = [m for m in sc.model.unique() if m != "EX"]
    real = sc[sc.scenario == "real"].pivot_table(index="h", columns="model", values="s")[cand]
    t, _ = W1.decision(real)
    return t


def real():
    sel = json.load(open(os.path.join(OUT, "wp2_selection.json")))
    prm = sel["params"]
    sc = pd.DataFrame(sel["scores"]).set_index("model")
    P = base_predictors()
    P.update(designs(prm))
    df = run(P, ("real",), variants=H.VARIANTS)
    df.to_csv(os.path.join(OUT, "wp2_real_predictions.csv"), index=False)
    met = H.metrics(df)
    met.to_csv(os.path.join(OUT, "wp2_real_metrics.csv"), index=False)
    pck = H.per_ck(df)
    pck.to_csv(os.path.join(OUT, "wp2_per_checkup_d04.csv"))
    hyp = g_hyp(df)
    hyp.to_csv(os.path.join(OUT, "wp2_hypothesis_decision_table.csv"))
    gates = {}
    for n in [m for m in P if m.startswith("F")]:
        g = gates_vs_sub(met, pck, n)
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
    tbl.to_csv(os.path.join(OUT, "wp2_summary_table.csv"))
    main = sel["main"]
    out = dict(main=main, main_passes_all=bool(main and gates[main]["all_performance_gates"]), gates=gates)
    json.dump(out, open(os.path.join(OUT, "wp2_gates.json"), "w"), indent=1, default=float)
    pd.set_option("display.width", 220)
    print(tbl.round(3).to_string())
    print(pck.round(3).to_string())
    for n, g in gates.items():
        print(n, {k: (v if isinstance(v, bool) else v.get("passed")) for k, v in g.items() if k != "all_performance_gates"},
              "ALL", g["all_performance_gates"])
    print("main", main, "passes all:", out["main_passes_all"])


if __name__ == "__main__":
    {"select": select, "real": real}[sys.argv[1]]()
