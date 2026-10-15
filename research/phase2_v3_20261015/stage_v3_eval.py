"""V3 causal evaluation against the base-study proxies (protocol.json).

Every prediction for CK_k uses only load_dataset(data, until=CK_k). Proxies use the
post-CK_k full charge from the full data and are used for scoring only.
"""
import glob
import json
import os
import shutil
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(RES, "..", "TechArena_Challenge2_Team_Package"))
sys.path[:0] = [os.path.join(HERE, "src"), os.path.join(RES, "phase2_v2_phase_matched_20261013", "src"),
                os.path.join(RES, "phase2_anchor_step_20261013", "src"), ROOT]

from framework.data import load_dataset, load_eval_points  # noqa: E402
from events import STEP_VARIANTS, charge_step_split, full_charges, step_programs  # noqa: E402
from v3 import v3  # noqa: E402

OUT = os.path.join(HERE, "outputs")
NOM = 102.0
DELTAS = (0.0, 0.4, 0.8)
INF = float("inf")
OFF = dict(use_sqrt=False, beta_cap=INF, median=False)

CONFIGS = {
    "V2": OFF,
    "V3": {},
    "V2+1": {**OFF, "use_sqrt": True},
    "V2+2": {**OFF, "beta_cap": 1.2},
    "V2+3": {**OFF, "median": True},
    "V2+1+2": {**OFF, "use_sqrt": True, "beta_cap": 1.2},
    "V2+1+3": {**OFF, "use_sqrt": True, "median": True},
    "V2+2+3": {**OFF, "beta_cap": 1.2, "median": True},
    "V3_G7": {"gap_days": 7.0},
    "V3_G14": {"gap_days": 14.0},
    "V3_cap1.1": {"beta_cap": 1.1},
    "V3_cap1.3": {"beta_cap": 1.3},
    "V3_p0.4": {"p": 0.4},
    "V3_p0.6": {"p": 0.6},
    "V3_origin-5": {"shift_days": -5.0},
    "V3_origin+5": {"shift_days": 5.0},
}
ALL_VARIANTS = ("V2", "V3")          # run on every step-detection variant


def features(data, until):
    op = load_dataset(data, until=until).operation
    fc = full_charges(op)
    steps = {v: step_programs(op, **ov) for v, ov in STEP_VARIANTS.items()}
    a4 = {s: charge_step_split(op, fc, smooth_Ah=s) for s in (1.0, 2.0, 3.0)}
    return fc, steps, a4


def predictions(data=None, models=None):
    data = data or os.path.join(ROOT, "data")
    pts = load_eval_points(data)
    ck = pd.DatetimeIndex(pts["date"])
    rows = []
    for k, p in enumerate(pts.itertuples()):
        if k == 0:
            continue
        fc, steps, a4 = features(data, p.date)
        eps0 = 100.41 - fc[fc["setpoint_C"] == 45]["Q_Ah"].iloc[0]
        for de in DELTAS:
            eps = eps0 + de
            base = dict(checkup=p.checkup, k=k, eps_offset=de)
            for name, cfg in CONFIGS.items():
                if models and name not in models:
                    continue
                for v in STEP_VARIANTS:
                    if v != "main" and name not in ALL_VARIANTS:
                        continue
                    q, br, b = v3(fc, steps[v], a4[2.0], ck, k, eps, **cfg)
                    rows.append(dict(base, model=name, step=v, a4s=2.0, Q=q, branch=br, beta=b))
                if name in ALL_VARIANTS:
                    for s in (1.0, 3.0):
                        q, br, b = v3(fc, steps["main"], a4[s], ck, k, eps, **cfg)
                        rows.append(dict(base, model=name, step="main", a4s=s, Q=q, branch=br, beta=b))
    return pd.DataFrame(rows)


def noise_copy(src, dst, cut):
    """Copy the data directory, replacing every operation value after `cut` by noise."""
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    rng = np.random.default_rng(0)
    for f in glob.glob(os.path.join(dst, "operation", "*.csv.gz")):
        d = pd.read_csv(f)
        late = pd.to_datetime(d["timestamp"]) > cut
        if late.any():
            num = [c for c in d.columns if c not in ("timestamp", "segment") and pd.api.types.is_numeric_dtype(d[c])]
            d[num] = d[num].astype(float)
            d.loc[late, num] = rng.normal(0, 50, size=(int(late.sum()), len(num)))
            d.to_csv(f, index=False)


def causality_check(tmp):
    data = os.path.join(ROOT, "data")
    pts = load_eval_points(data)
    ck = pd.DatetimeIndex(pts["date"])
    ok = []
    for k, p in enumerate(pts.itertuples()):
        if k == 0:
            continue
        noise_copy(data, tmp, p.date)
        res = []
        for d in (data, tmp):
            fc, steps, a4 = features(d, p.date)
            eps0 = 100.41 - fc[fc["setpoint_C"] == 45]["Q_Ah"].iloc[0]
            res.append([v3(fc, steps[v], a4[2.0], ck, k, eps0 + de)[0] for v in STEP_VARIANTS for de in DELTAS])
        ok.append(bool(np.array_equal(res[0], res[1])))
    shutil.rmtree(tmp, ignore_errors=True)
    return dict(per_checkup=ok, passed=all(ok))


def metrics(pred):
    g = pred.groupby(["model", "step", "a4s", "eps_offset"])
    met = g["err_pp"].agg(MAE=lambda e: e.abs().mean(), MAX=lambda e: e.abs().max(),
                          RMSE=lambda e: np.sqrt((e ** 2).mean())).reset_index()
    sub = pred[pred["k"] >= 3].groupby(["model", "step", "a4s", "eps_offset"])["err_pp"]
    met["CK3_7_MAE"] = sub.apply(lambda e: e.abs().mean()).to_numpy()
    return met


def gates(met, per_ck, k1):
    m = met.set_index(["model", "step", "a4s", "eps_offset"])
    out = {"K1_causality": k1}
    k2 = [bool(m.loc[("V3", "main", 2.0, d), "MAE"] < m.loc[("V2", "main", 2.0, d), "MAE"]
               and m.loc[("V3", "main", 2.0, d), "MAX"] <= m.loc[("V2", "main", 2.0, d), "MAX"]) for d in DELTAS]
    out["K2_proxy"] = dict(per_delta=k2, passed=all(k2))
    a, b = m.loc[("V3", "main", 2.0, 0.0), "CK3_7_MAE"], m.loc[("V2", "main", 2.0, 0.0), "CK3_7_MAE"]
    out["K3_eps_scope"] = dict(V3_CK3_7=float(a), V2_CK3_7=float(b), passed=bool(a <= b + 0.02))
    wins = {v: bool(m.loc[("V3", v, 2.0, 0.4), "MAE"] < m.loc[("V2", v, 2.0, 0.4), "MAE"]) for v in STEP_VARIANTS}
    sens = {n: bool(m.loc[(n, "main", 2.0, 0.4), "MAE"] < m.loc[("V2", "main", 2.0, 0.4), "MAE"])
            for n in CONFIGS if n.startswith("V3_")}
    out["K4_robust"] = dict(step_wins=wins, sensitivity=sens,
                            passed=bool(sum(wins.values()) >= 5 and all(sens.values())))
    inc = float((per_ck["V3"].abs() - per_ck["V2"].abs()).max())
    out["K5_no_large_regression"] = dict(max_abs_err_increase_pp=inc, passed=bool(inc <= 0.15))
    out["all_passed"] = all(v["passed"] for v in out.values() if isinstance(v, dict))
    return out


def main():
    data = os.path.join(ROOT, "data")
    qfc = full_charges(load_dataset(data).operation).sort_values("t_end")["Q_Ah"].to_numpy()
    eps0 = 100.41 - qfc[0]
    pred = predictions()
    pred["proxy_Q"] = [qfc[k] + eps0 + de for k, de in zip(pred["k"], pred["eps_offset"])]
    pred["err_pp"] = (pred["Q"] - pred["proxy_Q"]) / NOM * 100
    pred["SOH"] = pred["Q"] / NOM * 100
    pred.to_csv(os.path.join(OUT, "V3_predictions_long.csv"), index=False)
    met = metrics(pred)
    met.to_csv(os.path.join(OUT, "V3_metrics.csv"), index=False)

    main_rows = pred[(pred["step"] == "main") & (pred["a4s"] == 2.0)]
    per_ck = main_rows[main_rows["eps_offset"] == 0.4].pivot_table(index="checkup", columns="model", values="err_pp")
    per_ck.to_csv(os.path.join(OUT, "V3_errors_per_checkup_eps0.4.csv"))
    ck2 = main_rows[main_rows["checkup"] == "CK2"].pivot_table(index="model", columns="eps_offset", values="err_pp")
    ck2.to_csv(os.path.join(OUT, "V3_CK2_by_delta.csv"))
    br = main_rows[(main_rows["model"] == "V3") & (main_rows["eps_offset"] == 0.4)][["checkup", "branch", "beta", "SOH"]]
    br.to_csv(os.path.join(OUT, "V3_branch_beta.csv"), index=False)

    # V2 reproduction check against the V2 study's own output
    v2_old = pd.read_csv(os.path.join(RES, "phase2_v2_phase_matched_20261013", "outputs", "V2_predictions_long.csv"))
    v2_old = v2_old[v2_old["model"] == "V2_main"].set_index(["checkup", "eps_offset", "step", "a4s"])["Q"]
    v2_new = pred[pred["model"] == "V2"].set_index(["checkup", "eps_offset", "step", "a4s"])["Q"]
    repro = float((v2_new - v2_old.reindex(v2_new.index)).abs().max())

    k1 = causality_check(os.path.join(HERE, "outputs", "_noise_tmp"))
    g = gates(met, per_ck, k1)
    g["V2_reproduction_max_abs_diff_Ah"] = repro
    with open(os.path.join(OUT, "V3_gates.json"), "w") as f:
        json.dump(g, f, indent=2)

    pd.set_option("display.width", 250)
    show = met[(met["step"] == "main") & (met["a4s"] == 2.0)].pivot_table(index="model", columns="eps_offset",
                                                                       values=["MAE", "MAX", "CK3_7_MAE"])
    print(show.round(3).to_string())
    print(per_ck.round(3).to_string())
    print(ck2.round(3).to_string())
    print(br.round(3).to_string(index=False))
    print(met[(met["model"].isin(ALL_VARIANTS)) & (met["eps_offset"] == 0.4)].round(3).to_string(index=False))
    print(json.dumps(g, indent=1))


if __name__ == "__main__":
    main()
