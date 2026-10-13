"""Stages B-D: proxy labels, pre-registered causal predictors, proxy evaluation.

Predictions for CK_k use only ``load_dataset(data, until=CK_k date)``; proxies use the
post-CK_k full charge from the full data and are used for scoring only.
"""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "TechArena_Challenge2_Team_Package"))
sys.path.insert(0, os.path.join(HERE, "src"))
sys.path.insert(0, ROOT)

from framework.data import load_dataset, load_eval_points  # noqa: E402
from my_model.model_example import ExampleModel  # noqa: E402
from events import STEP_VARIANTS, full_charges, step_programs  # noqa: E402
from predictors import m2, m3, m4, m5  # noqa: E402

OUT = os.path.join(HERE, "outputs")
# Copy of research/phase2_paper_transfer_20261012/implementation_v1/history_B_prior_baseline.csv
# from branch research-archive-20261010 (comparison only, not truth).
B_CSV = os.path.join(HERE, "inputs", "history_B_prior_baseline.csv")
NOM = 102.0


def predictions():
    data = os.path.join(ROOT, "data")
    full = load_dataset(data)
    ex = ExampleModel()
    ex.fit(full)
    pts = load_eval_points(data)
    pts = pts[pts["checkup"] != "CK0"]
    rows, inputs = [], []
    for p in pts.itertuples():
        ds = load_dataset(data, until=p.date)
        op = ds.operation
        fc = full_charges(op)
        eps0 = 100.41 - fc[fc["setpoint_C"] == 45]["Q_Ah"].iloc[0] if (fc["setpoint_C"] == 45).any() else np.nan
        steps = {v: step_programs(op, **ov) for v, ov in STEP_VARIANTS.items()}
        rec = {"checkup": p.checkup, "date": p.date, "eps0": eps0,
               "M0_SOH": round(float(ex.estimate_soh(ds, p.date)), 3)}
        for de in (0.0, 0.4, 0.8):
            eps = eps0 + de
            tag = f"d{de:.1f}"
            rec[f"M2_{tag}"] = m2(fc, p.date, eps, eps0)
            rec[f"M3_{tag}"] = m3(fc, p.date, eps, eps0)
            for v, beta, sl in itertools.product(STEP_VARIANTS, (0.7, 1.0, 1.3, 1.5), ("last1", "mean_last2")):
                rec[f"M4_{v}_b{beta}_{sl}_{tag}"] = m4(fc, steps[v], p.date, eps, eps0, beta, sl)
            q5, b5 = m5(fc, steps["main"], p.date, eps, eps0)
            rec[f"M5_{tag}"], rec[f"M5beta_{tag}"] = q5, b5
        st = steps["main"]
        inputs.append(dict(checkup=p.checkup, cutoff=p.date, n_full_charges=len(fc),
                           last_full_charge_end=fc["t_end"].max() if len(fc) else None,
                           n_step_programs=len(st), last_step_cv_end=st["t_cv_end"].max() if len(st) else None,
                           last_step_measured=st["t_measured"].max() if len(st) else None,
                           last_step_mean=st.sort_values("t_cv_end")["step_mean"].iloc[-1] if len(st) else None))
        rows.append(rec)
    return pd.DataFrame(rows), pd.DataFrame(inputs), full


def proxies(full):
    fc = full_charges(full.operation).sort_values("t_end").reset_index(drop=True)
    q0 = fc.loc[0, "Q_Ah"]
    return fc.loc[1:, "Q_Ah"].to_numpy(), 100.41 - q0


def metrics(err_pp):
    e = np.asarray(err_pp)
    return dict(MAE=float(np.abs(e).mean()), RMSE=float(np.sqrt((e ** 2).mean())), MAX=float(np.abs(e).max()))


def main():
    pred, inputs, full = predictions()
    qfc, eps0 = proxies(full)
    pred.to_csv(os.path.join(OUT, "C_predictions_wide.csv"), index=False)
    inputs.to_csv(os.path.join(OUT, "C_visible_inputs.csv"), index=False)
    b = pd.read_csv(B_CSV).set_index("checkup").loc[pred["checkup"], "B_SOH_pp"].to_numpy()

    table, per_ck = [], []
    model_cols = [c for c in pred.columns if c.startswith(("M2_", "M3_", "M4_", "M5_")) and "beta" not in c]
    for de in (0.0, 0.4, 0.8):
        tag = f"d{de:.1f}"
        proxy_soh = (qfc + eps0 + de) / NOM * 100
        cand = {"M0_ExampleModel": pred["M0_SOH"].to_numpy(), "M1_B": b}
        for c in model_cols:
            if c.endswith(tag):
                cand[c[: -len(tag) - 1]] = pred[c].to_numpy() / NOM * 100
        m0 = metrics(cand["M0_ExampleModel"] - proxy_soh)
        for name, soh in cand.items():
            err = soh - proxy_soh
            m = metrics(err)
            table.append(dict(eps_offset=de, eps=eps0 + de, model=name, **m,
                              MAE_ratio_vs_M0=m["MAE"] / m0["MAE"], MAX_ratio_vs_M0=m["MAX"] / m0["MAX"],
                              CK1_err=float(err[0]), CK2_7_MAE=float(np.abs(err[1:]).mean())))
            for k, e in enumerate(err):
                per_ck.append(dict(eps_offset=de, model=name, checkup=pred["checkup"].iloc[k],
                                   pred_SOH=float(soh[k]), proxy_SOH=float(proxy_soh[k]), err_pp=float(e)))
    t = pd.DataFrame(table)
    t.to_csv(os.path.join(OUT, "D_metrics_all.csv"), index=False)
    pd.DataFrame(per_ck).to_csv(os.path.join(OUT, "D_errors_per_checkup.csv"), index=False)

    # eps-free CK2..CK7 error: for anchor models with k>=2, error = (pred - (Q_fc,k + eps)),
    # where pred = Q_fc,k-1 + eps + update, so it does not depend on eps.
    ef = t[(t["eps_offset"] == 0.0)][["model", "CK2_7_MAE"]].rename(columns={"CK2_7_MAE": "CK2_7_MAE_eps_free"})
    main_rows = t[t["model"].isin(["M0_ExampleModel", "M1_B", "M2", "M3", "M4_main_b1.0_last1", "M5"])]
    summary = dict(eps0=float(eps0), proxy_Q=qfc.round(3).tolist(),
                   main_table=main_rows.round(3).to_dict("records"))
    with open(os.path.join(OUT, "D_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    pd.set_option("display.width", 250)
    print(main_rows.round(3).to_string(index=False))
    print(inputs.to_string(index=False))
    ef.to_csv(os.path.join(OUT, "D_eps_free_CK2_7.csv"), index=False)


if __name__ == "__main__":
    main()
