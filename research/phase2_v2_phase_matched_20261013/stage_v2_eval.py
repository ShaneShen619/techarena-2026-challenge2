"""V2 causal evaluation against the base-study proxies (protocol.json).

Every prediction for CK_k uses only load_dataset(data, until=CK_k). Proxies use the
post-CK_k full charge from the full data and are used for scoring only.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, "..", "phase2_anchor_step_20261013"))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "TechArena_Challenge2_Team_Package"))
sys.path[:0] = [os.path.join(HERE, "src"), os.path.join(BASE, "src"), ROOT]

from framework.data import load_dataset, load_eval_points  # noqa: E402
from events import STEP_VARIANTS, charge_step_split, full_charges, step_programs  # noqa: E402
from v2 import m4, v2  # noqa: E402

OUT = os.path.join(HERE, "outputs")
NOM = 102.0
DELTAS = (0.0, 0.4, 0.8)

CONFIGS = {
    "V2_main": {},
    "V2_beta1": {"beta_mode": "one"},
    "V2_no_rate": {"use_rate": False},
    "V2_beta_all": {"beta_all": True},
    "V2_beta_direct": {"beta_mode": "direct"},
    "V2_beta0_1.3": {"beta0": 1.3},
    "V2_tau0.25": {"tau": 0.25},
    "V2_tau4": {"tau": 4.0},
    "V2_valid7": {"valid_days": 7.0},
    "V2_valid14": {"valid_days": 14.0},
}


def predictions():
    data = os.path.join(ROOT, "data")
    pts = load_eval_points(data)
    ck = pd.DatetimeIndex(pts["date"])
    rows = []
    for k, p in enumerate(pts.itertuples()):
        if k == 0:
            continue
        op = load_dataset(data, until=p.date).operation
        fc = full_charges(op)
        eps0 = Q_eps0(fc)
        steps = {v: step_programs(op, **ov) for v, ov in STEP_VARIANTS.items()}
        a4 = {s: charge_step_split(op, fc, smooth_Ah=s) for s in (1.0, 2.0, 3.0)}
        for de in DELTAS:
            eps = eps0 + de
            base = dict(checkup=p.checkup, k=k, eps_offset=de)
            for v in STEP_VARIANTS:
                rows.append(dict(base, model="M4", step=v, a4s=2.0, Q=m4(fc, steps[v], eps), branch="m4", beta=1.0))
                for name, cfg in CONFIGS.items():
                    if v != "main" and name != "V2_main":
                        continue
                    q, br, b = v2(fc, steps[v], a4[2.0], ck, k, eps, **cfg)
                    rows.append(dict(base, model=name, step=v, a4s=2.0, Q=q, branch=br, beta=b))
            for s in (1.0, 3.0):
                q, br, b = v2(fc, steps["main"], a4[s], ck, k, eps)
                rows.append(dict(base, model=f"V2_a4s{s:g}", step="main", a4s=s, Q=q, branch=br, beta=b))
    return pd.DataFrame(rows)


def Q_eps0(fc):
    return 100.41 - fc[fc["setpoint_C"] == 45]["Q_Ah"].iloc[0]


def main():
    data = os.path.join(ROOT, "data")
    fc_full = full_charges(load_dataset(data).operation).sort_values("t_end").reset_index(drop=True)
    qfc = fc_full["Q_Ah"].to_numpy()          # anchors after CK0..CK7
    eps0 = 100.41 - qfc[0]
    pred = predictions()
    pred["proxy_Q"] = [qfc[k] + eps0 + de for k, de in zip(pred["k"], pred["eps_offset"])]
    pred["err_pp"] = (pred["Q"] - pred["proxy_Q"]) / NOM * 100
    pred["SOH"] = pred["Q"] / NOM * 100
    pred.to_csv(os.path.join(OUT, "V2_predictions_long.csv"), index=False)

    g = pred.groupby(["model", "step", "a4s", "eps_offset"])
    met = g["err_pp"].agg(MAE=lambda e: e.abs().mean(), MAX=lambda e: e.abs().max(),
                          RMSE=lambda e: np.sqrt((e ** 2).mean())).reset_index()
    ckf = pred[pred["k"] >= 2].groupby(["model", "step", "a4s", "eps_offset"])["err_pp"]
    met["CK2_7_MAE"] = ckf.apply(lambda e: e.abs().mean()).to_numpy()
    met.to_csv(os.path.join(OUT, "V2_metrics.csv"), index=False)

    wide = pred[(pred["step"] == "main") & (pred["a4s"] == 2.0) & (pred["eps_offset"] == 0.4)]
    per_ck = wide.pivot_table(index="checkup", columns="model", values="err_pp")
    per_ck.to_csv(os.path.join(OUT, "V2_errors_per_checkup_eps0.4.csv"))
    br = wide[wide["model"] == "V2_main"][["checkup", "branch", "beta", "SOH"]]
    br.to_csv(os.path.join(OUT, "V2_main_branch_beta.csv"), index=False)

    gates = evaluate_gates(met, per_ck)
    with open(os.path.join(OUT, "V2_gates.json"), "w") as f:
        json.dump(gates, f, indent=2)
    pd.set_option("display.width", 250)
    print(met[(met["step"] == "main") & (met["a4s"] == 2.0)].round(3).to_string(index=False))
    print(per_ck.round(3).to_string())
    print(br.round(3).to_string(index=False))
    print(json.dumps(gates, indent=1))


def evaluate_gates(met, per_ck):
    m = met.set_index(["model", "step", "a4s", "eps_offset"])
    out = {}
    h2 = []
    for de in DELTAS:
        a, b = m.loc[("V2_main", "main", 2.0, de)], m.loc[("M4", "main", 2.0, de)]
        h2.append(bool(a["MAE"] < b["MAE"] and a["MAX"] <= b["MAX"] + 0.10))
    out["H2_proxy"] = all(h2)
    a, b = m.loc[("V2_main", "main", 2.0, 0.0)], m.loc[("M4", "main", 2.0, 0.0)]
    out["H3_eps_free"] = dict(V2=float(a["CK2_7_MAE"]), M4=float(b["CK2_7_MAE"]),
                              passed=bool(a["CK2_7_MAE"] <= b["CK2_7_MAE"] - 0.05))
    wins = [bool(m.loc[("V2_main", v, 2.0, 0.4), "MAE"] < m.loc[("M4", v, 2.0, 0.4), "MAE"]) for v in STEP_VARIANTS]
    others = {n: bool(m.loc[(n, "main", 2.0, 0.4), "MAE"] < m.loc[("M4", "main", 2.0, 0.4), "MAE"])
              for n in ("V2_tau0.25", "V2_tau4", "V2_valid7", "V2_valid14")}
    out["H4_robust"] = dict(step_wins=int(sum(wins)), settings=others,
                            passed=bool(sum(wins) >= 5 and all(others.values())))
    regress = float((per_ck["V2_main"].abs() - per_ck["M4"].abs()).max())
    out["H5_no_large_regression"] = dict(max_abs_err_increase_pp=regress, passed=bool(regress <= 0.30))
    return out


if __name__ == "__main__":
    main()
