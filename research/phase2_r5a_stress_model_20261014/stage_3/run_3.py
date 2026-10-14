"""Stage 3 evaluation (protocol.json). Usage: run_3.py pseudo | real"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common5a import H  # noqa: E402
from smodel import StressFit  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
PROTO = json.load(open(os.path.join(HERE, "protocol.json")))

# ---------------------------------------------------------------- configurations
CONFIGS = {"S_main": {}}
for g, spec in PROTO["variants"].items():
    if "settings" in spec:
        for name, s in spec["settings"].items():
            CONFIGS[f"{g}:{name}"] = s
    else:
        CONFIGS[g] = {k: v for k, v in spec.items() if k != "note"}
for g, spec in PROTO["report_only_variants"].items():
    CONFIGS[g] = {k: v for k, v in spec.items() if k != "note"}
GROUPS = {g: [n for n in CONFIGS if n == g or n.startswith(g + ":")] for g in PROTO["variants"]}

_TAB = {}
_S = {}


def s_pred(name):
    cfg = CONFIGS[name]

    def f(ctx):
        key = (ctx["key"], name, ctx["delta"])
        if key not in _S:
            _S[key] = StressFit(cfg).run(ctx["op"], ctx["fc"], ctx["ck"], ctx["at_date"], ctx["eps"],
                                         tab_cache=_TAB, key=ctx["key"])
        return _S[key]
    return f


S_MAIN = s_pred("S_main")


def ens50(ctx):
    qs, _ = S_MAIN(ctx)
    qv, iv = H.v2_pred(ctx)
    return 0.5 * qs + 0.5 * qv, {"branch": iv["branch"]}


def v2_sfb(ctx):
    qv, iv = H.v2_pred(ctx)
    if iv["branch"] == "fallback":
        return S_MAIN(ctx)[0], {"branch": "S_fallback"}
    return qv, {"branch": iv["branch"]}


PREDICTORS = dict(H.BASELINES)
PREDICTORS.update({n: s_pred(n) for n in CONFIGS})
PREDICTORS.update({"ENS50": ens50, "V2_Sfb": v2_sfb})


def filtered_scenarios(kmin):
    for s in ("PG1", "PG2", "PC5", "PC10"):
        H.SCENARIOS[s + f"_k{kmin}"] = [(k, spec) for k, spec in H.SCENARIOS[s] if k >= kmin]
    return tuple(s + f"_k{kmin}" for s in ("PG1", "PG2", "PC5", "PC10"))


def pseudo():
    scen = filtered_scenarios(3)
    df = H.run(PREDICTORS, scenarios=scen, variants=H.VARIANTS)
    df.to_csv(os.path.join(OUT, "S3_pseudo_predictions.csv"), index=False)
    met = H.metrics(df)
    met.to_csv(os.path.join(OUT, "S3_pseudo_metrics.csv"), index=False)
    m = met[(met["step"] == "main") & (met["a4s"] == 2.0) & (met["delta"] == 0.4)]
    pm = m.groupby("model")["MAE"].mean().rename("pseudo_mean_MAE").sort_values()
    pm.to_csv(os.path.join(OUT, "S3_pseudo_mean.csv"))
    print(m.pivot_table(index="model", columns="scenario", values="MAE").join(pm).round(3).to_string())


def real():
    df = H.run(PREDICTORS, scenarios=("real",), variants=H.VARIANTS)
    df.to_csv(os.path.join(OUT, "S3_real_predictions.csv"), index=False)
    met = H.metrics(df)
    met.to_csv(os.path.join(OUT, "S3_real_metrics.csv"), index=False)
    # PC5 / PC10 including k = 2, for final reporting only
    rep = H.run(PREDICTORS, scenarios=("PC5", "PC10"), variants=("main",))
    rep.to_csv(os.path.join(OUT, "S3_pc_k2_reporting_predictions.csv"), index=False)
    H.metrics(rep).to_csv(os.path.join(OUT, "S3_pc_k2_reporting_metrics.csv"), index=False)

    pmean = pd.read_csv(os.path.join(OUT, "S3_pseudo_mean.csv"), index_col=0)["pseudo_mean_MAE"]
    mm = met[(met["scenario"] == "real") & (met["step"] == "main") & (met["a4s"] == 2.0)]
    tbl = mm.pivot_table(index="model", columns="delta", values=["MAE", "MAX", "RMSE"])
    ef = mm[mm["delta"] == 0.0].set_index("model")["CK2_7_MAE"]
    tbl.columns = [f"{a}_d{b}" for a, b in tbl.columns]
    tbl = tbl.join(ef.rename("CK2_7_MAE_epsfree")).join(pmean)
    tbl.to_csv(os.path.join(OUT, "S3_summary_table.csv"))
    pck = H.per_ck(df)
    pck.to_csv(os.path.join(OUT, "S3_per_checkup_d04.csv"))

    v2 = mm.set_index(["model", "delta"])
    gates = {}
    for name in ("S_main", "ENS50", "V2_Sfb"):
        g = H.gates_vs_v2(met, pck, name, variants_met=met if name != "S_main" else None)
        if name == "S_main":
            wins = {}
            for grp, members in GROUPS.items():
                wins[grp] = bool(all(v2.loc[(n, 0.4), "MAE"] < v2.loc[("V2", 0.4), "MAE"] for n in members))
            g["G-robust"] = dict(group_wins=wins, wins=int(sum(wins.values())), passed=bool(sum(wins.values()) >= 6))
        g["G-pseudo"] = dict(model=float(pmean[name]), V2=float(pmean["V2"]),
                             passed=bool(pmean[name] <= pmean["V2"] + 0.02))
        g["all_performance_gates"] = bool(g["G-proxy"] and g["G-epsfree"]["passed"] and g["G-robust"]["passed"]
                                          and g["G-pseudo"]["passed"] and g["G-regress"]["passed"])
        gates[name] = g
    passing = [n for n in gates if gates[n]["all_performance_gates"]]
    chosen = min(passing, key=lambda n: pmean[n]) if passing else None
    gates["selection"] = dict(passing=passing, chosen=chosen)
    json.dump(gates, open(os.path.join(OUT, "S3_gates.json"), "w"), indent=1)

    # parameters per cutoff (real, main step, delta 0.4) and diagnostics
    keep = ["k", "checkup", "model", "Q", "proxy", "err_pp", "SOH", "A_cal", "A_cyc", "o45", "z", "n_pairs",
            "horizon_lag_d", "loss_cal", "loss_cyc", "sd_logA_cal", "sd_logA_cyc", "sd_o45"]
    sel = df[(df["step"] == "main") & (df["a4s"] == 2.0) & (df["delta"] == 0.4) &
             df["model"].isin(["S_main", "X_prior_only", "X_z05", "G4_z1", "G1_zfree"])]
    sel[[c for c in keep if c in sel.columns]].to_csv(os.path.join(OUT, "S3_parameters_d04.csv"), index=False)
    e = pck[["S_main", "V2"]].dropna()
    diag = dict(corr_err_S_main_V2=float(np.corrcoef(e["S_main"], e["V2"])[0, 1]),
                note="7 exposed checkups; diagnostic only")
    json.dump(diag, open(os.path.join(OUT, "S3_diagnostics.json"), "w"), indent=1)
    print(tbl.round(3).to_string())
    print(pck.round(3).to_string())
    print(json.dumps(gates, indent=1))
    print(diag)


if __name__ == "__main__":
    {"pseudo": pseudo, "real": real}[sys.argv[1]]()
