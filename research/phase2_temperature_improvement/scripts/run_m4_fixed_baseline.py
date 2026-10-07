"""Frozen B_multi_noT baseline: grouped Ridge on partial-charge features.

Uses only charge age/current/window shape, no measured or nominal temperature.
Width and ridge penalty are selected on the five training cells by inner
leave-one-physical-cell-out validation.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
RUN = TASK / "runs/M4_B_multi_noT_v1"
LAMBDAS = (.1, 1., 10., 100.)
WIDTHS = {"0.04V": list(range(0, 9)), "0.07V": list(range(9, 17)), "0.10V": list(range(17, 24))}


def columns(width: str, with_temperature: bool = False) -> list[str]:
    result = ["age_fraction", "age_fraction_sq", "event_age_days", "cc_ratio",
              "delta_current_rel", "q_mean", "q_std", "q_slope"] + [f"w{i:02d}_logratio" for i in WIDTHS[width]]
    if with_temperature:
        result += ["temp_C", "initial_temp_C", "delta_temp_C", "temp_interaction"]
    return result


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str], lam: float) -> np.ndarray:
    x = train[cols].to_numpy(float)
    z = test[cols].to_numpy(float)
    y = (train.target_soh_pp-train.anchor_soh_pp).to_numpy(float)
    if not (np.isfinite(x).all() and np.isfinite(z).all() and np.isfinite(y).all()):
        raise ValueError("nonfinite fixed baseline feature")
    mean = x.mean(axis=0)
    sd = np.where(x.std(axis=0) < 1e-7, 1., x.std(axis=0))
    xs = np.clip((x-mean)/sd, -6., 6.)
    zs = np.clip((z-mean)/sd, -6., 6.)
    ym = y.mean()
    coef = np.linalg.solve(xs.T@xs+lam*np.eye(len(cols)), xs.T@(y-ym))
    return test.anchor_soh_pp.to_numpy(float)+ym+zs@coef


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portable-age", action="store_true")
    parser.add_argument("--with-temperature", action="store_true")
    args = parser.parse_args()
    run_name = ("M4_multi_efc_T_v1" if args.portable_age and args.with_temperature else
                "M4_B_multi_noT_efc_v1" if args.portable_age else "M4_B_multi_noT_v1")
    run = TASK / "runs" / run_name
    run.mkdir(parents=True, exist_ok=True)
    f = pd.read_csv(TASK / "runs/M4_feature_audit_v1/features.csv")
    panel = pd.read_csv(TASK / "outputs/panel_main.csv")
    ages = (pd.read_csv(TASK / "runs/M4_feature_audit_v1/throughput.csv")
            if args.portable_age else pd.read_csv(TASK / "runs/M3_B_age_sixfold_v2/predictions.csv"))
    key = ["cell_id", "target_ordinal"]
    frame = f.merge(panel[key+["anchor_soh_pp", "target_soh_pp"]], on=key, validate="one_to_one")
    age_col = "qualified_charge_efc" if args.portable_age else "visible_last_charge_cycle"
    frame = frame.merge(ages[key+[age_col]], on=key, validate="one_to_one")
    frame["age_fraction"] = frame[age_col]/5500.
    frame["age_fraction_sq"] = frame.age_fraction**2
    frame["cc_ratio"] = np.log(frame.recent_cc_Ah/frame.initial_cc_Ah)
    frame["temp_interaction"] = frame.delta_temp_C*frame[[f"w{i:02d}_logratio" for i in range(24)]].mean(axis=1)
    for width, idx in WIDTHS.items():
        vals = frame[[f"w{i:02d}_logratio" for i in idx]].to_numpy(float)
        frame["q_mean"] = vals.mean(axis=1)
        frame["q_std"] = vals.std(axis=1)
        frame["q_slope"] = vals[:, -1]-vals[:, 0]
        # Width-specific columns cannot coexist in frame; copied for each fit.
        frame[f"{width}_mean"] = frame.q_mean
        frame[f"{width}_std"] = frame.q_std
        frame[f"{width}_slope"] = frame.q_slope
    results = []
    selections = []
    cells = sorted(frame.cell_id.unique())
    for held in cells:
        train = frame.loc[frame.cell_id.ne(held)]
        test = frame.loc[frame.cell_id.eq(held)].sort_values("target_ordinal")
        choices = []
        for width, lam in itertools.product(WIDTHS, LAMBDAS):
            cols = columns(width, args.with_temperature)
            cols = [f"{width}_{c[2:]}" if c in ("q_mean", "q_std", "q_slope") else c for c in cols]
            inner = []
            for val in (c for c in cells if c != held):
                sub = train.loc[train.cell_id.ne(val)]
                hold = train.loc[train.cell_id.eq(val)]
                pred = fit_predict(sub, hold, cols, lam)
                inner.append(float(np.mean(np.abs(pred-hold.target_soh_pp.to_numpy(float)))))
            choices.append({"width": width, "lambda": lam, "inner_macro_mae_pp": float(np.mean(inner)),
                            "inner_cell_mae_pp": inner})
        best = min(choices, key=lambda item: (item["inner_macro_mae_pp"], item["lambda"]))
        cols = columns(best["width"], args.with_temperature)
        cols = [f"{best['width']}_{c[2:]}" if c in ("q_mean", "q_std", "q_slope") else c for c in cols]
        pred = fit_predict(train, test, cols, best["lambda"])
        for target, estimate in zip(test.itertuples(index=False), pred):
            method = ("M4_multi_efc_T" if args.portable_age and args.with_temperature else
                      "B_multi_noT_efc" if args.portable_age else "B_multi_noT")
            results.append({"run_id": run.name, "method": method, "cell_id": held,
                            "target_ordinal": int(target.target_ordinal),
                            "target_cycle": int(target.target_cycle),
                            "target_discharge_start": target.target_discharge_start,
                            "input_end": target.input_end,
                            "prediction_soh_pp": float(estimate),
                            "prediction_Ah": float(estimate*102/100),
                            "width": best["width"], "ridge_lambda": best["lambda"],
                            "evidence": "P1 five other physical cells; charge windows and qualified charge throughput"
                                        + ("; measured temperature" if args.with_temperature else "; no temperature columns")})
        selections.append({"heldout_cell": held, "selected": best, "all_choices": choices})
        print(held, best["width"], best["lambda"],
              "mae", float(np.mean(np.abs(pred-test.target_soh_pp.to_numpy(float)))), flush=True)
    out = pd.DataFrame(results)
    out.to_csv(run / "predictions.csv", index=False)
    (run / "selections.json").write_text(json.dumps(selections, indent=2)+"\n")
    existing = pd.read_csv(TASK / "outputs/predictions.csv")
    method = ("M4_multi_efc_T" if args.portable_age and args.with_temperature else
              "B_multi_noT_efc" if args.portable_age else "B_multi_noT")
    existing = existing.loc[~existing.method.eq(method)]
    pd.concat([existing, out], ignore_index=True).to_csv(TASK / "outputs/predictions.csv", index=False)
    joined = out.merge(panel[key+["target_soh_pp"]], on=key)
    ae = (joined.prediction_soh_pp-joined.target_soh_pp).abs()
    print("B_multi_noT_macro_mae", ae.groupby(joined.cell_id).mean().mean(),
          "p95", ae.quantile(.95), "max", ae.max(), flush=True)


if __name__ == "__main__":
    main()
