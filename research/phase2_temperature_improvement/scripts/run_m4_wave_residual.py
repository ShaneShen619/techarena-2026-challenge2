"""Nested grouped validation of charge-window residual correction to B_age.

This is a development comparison, not the frozen final candidate.  Every
outer correction fit excludes the outer cell.  Every inner selection fit uses
three-cell age priors excluding outer, inner, and correction-training cell.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
RUN = TASK / "runs/M4_wave_residual_v1"
RIDGE = (.1, 1., 10., 100.)
SHRINK = (0., .05, .1, .25, .5, 1.)


def augment(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    names = [f"w{i:02d}_logratio" for i in range(24)]
    if not np.isfinite(frame[names].to_numpy(float)).all():
        raise ValueError("incomplete charge-window features")
    w = frame[names].to_numpy(float)
    frame["q_mean"] = w.mean(axis=1)
    frame["q_std"] = w.std(axis=1)
    frame["q_slope"] = w[:, -1]-w[:, 0]
    for group, slc in (("short", slice(0, 9)), ("mid", slice(9, 17)), ("long", slice(17, 24))):
        frame[f"q_{group}"] = w[:, slc].mean(axis=1)
    frame["age_fraction"] = frame.visible_last_charge_cycle/5500.
    frame["age_fraction_sq"] = frame.age_fraction**2
    frame["cc_ratio"] = np.log(frame.recent_cc_Ah/frame.initial_cc_Ah)
    frame["temp_interaction"] = frame.delta_temp_C*frame.q_mean
    return frame


COMMON = ["age_fraction", "age_fraction_sq", "q_mean", "q_std", "q_slope",
          "q_short", "q_mid", "q_long", "cc_ratio", "event_age_days"]
TEMP = ["temp_C", "initial_temp_C", "delta_temp_C", "delta_current_rel", "temp_interaction"]
SETS = {
    "summary_noT": COMMON,
    "full_noT": COMMON+[f"w{i:02d}_logratio" for i in range(24)],
    "summary_T": COMMON+TEMP,
    "full_T": COMMON+TEMP+[f"w{i:02d}_logratio" for i in range(24)],
}


def ridge_predict(train: pd.DataFrame, test: pd.DataFrame, baseline_col: str,
                  cols: list[str], lam: float) -> np.ndarray:
    x = train[cols].to_numpy(float)
    z = test[cols].to_numpy(float)
    y = (train.target_soh_pp-train[baseline_col]).to_numpy(float)
    if not (np.isfinite(x).all() and np.isfinite(z).all() and np.isfinite(y).all()):
        raise ValueError("nonfinite residual model input")
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale = np.where(scale < 1e-7, 1., scale)
    x = np.clip((x-mean)/scale, -6., 6.)
    z = np.clip((z-mean)/scale, -6., 6.)
    ym = float(y.mean())
    coefs = np.linalg.solve(x.T@x+lam*np.eye(len(cols)), x.T@(y-ym))
    return np.clip(ym+z@coefs, -8., 8.)


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    features = pd.read_csv(TASK / "runs/M4_feature_audit_v1/features.csv")
    panel = pd.read_csv(TASK / "outputs/panel_main.csv")
    base = pd.read_csv(TASK / "runs/M3_B_age_sixfold_v2/predictions.csv")
    nested4 = pd.read_csv(TASK / "runs/M4_nested_age_v1/predictions.csv")
    nested3 = pd.read_csv(TASK / "runs/M4_nested_inner_age_v1/predictions.csv")
    key = ["cell_id", "target_ordinal"]
    data = features.merge(base[key+["visible_last_charge_cycle", "prediction_soh_pp"]],
                          on=key, validate="one_to_one").rename(columns={"prediction_soh_pp": "outer_age_pp"})
    data = data.merge(panel[key+["target_soh_pp"]], on=key, validate="one_to_one")
    data = augment(data)
    if len(data) != 180:
        raise AssertionError("missing frozen targets")
    pair = nested4.rename(columns={"correction_training_cell": "cell_id",
                                   "nested_age_prediction_pp": "pair_age_pp"})
    triple = nested3.rename(columns={"correction_training_cell": "cell_id",
                                       "nested_inner_age_prediction_pp": "triple_age_pp"})
    cells = sorted(data.cell_id.unique())
    outputs = []
    selections = []
    for outer in cells:
        hold = data.loc[data.cell_id.eq(outer)].sort_values("target_ordinal")
        train = data.loc[data.cell_id.ne(outer)].merge(
            pair.loc[pair.outer_held_cell.eq(outer), key+["pair_age_pp"]],
            on=key, validate="one_to_one")
        if len(train) != 150:
            raise AssertionError("outer correction training incomplete")
        # Inner validation j has pair-prior predictions; its correction
        # training k has a triple-prior prediction without i,j,k labels.
        inner_sets = []
        for inner in (c for c in cells if c != outer):
            val = train.loc[train.cell_id.eq(inner)]
            sub = data.loc[~data.cell_id.isin([outer, inner])].merge(
                triple.loc[triple.outer_held_cell.eq(outer) &
                           triple.inner_validation_cell.eq(inner), key+["triple_age_pp"]],
                on=key, validate="one_to_one")
            if len(sub) != 120 or len(val) != 30:
                raise AssertionError("nested inner correction data incomplete")
            inner_sets.append((inner, sub, val))
        for family in ("noT", "T"):
            choices = []
            for name, cols in SETS.items():
                if name.rsplit("_", 1)[-1] != family:
                    continue
                for lam, shrink in itertools.product(RIDGE, SHRINK):
                    cell_maes = []
                    for inner, sub, val in inner_sets:
                        correction = ridge_predict(sub, val, "triple_age_pp", cols, lam)
                        pred = val.pair_age_pp.to_numpy(float)+shrink*correction
                        cell_maes.append(float(np.mean(np.abs(pred-val.target_soh_pp.to_numpy(float)))))
                    choices.append({"feature_set": name, "lambda": lam, "shrink": shrink,
                                    "inner_macro_mae_pp": float(np.mean(cell_maes)),
                                    "inner_cell_mae_pp": cell_maes})
            selected = min(choices, key=lambda x: (x["inner_macro_mae_pp"], len(SETS[x["feature_set"]]), x["lambda"]))
            correction = ridge_predict(train, hold, "pair_age_pp", SETS[selected["feature_set"]], selected["lambda"])
            pred = hold.outer_age_pp.to_numpy(float)+selected["shrink"]*correction
            method = "M4_wave_noT" if family == "noT" else "M4_wave_T"
            for target, p, c in zip(hold.itertuples(index=False), pred, correction):
                outputs.append({"run_id": RUN.name, "method": method, "cell_id": outer,
                                "target_ordinal": int(target.target_ordinal),
                                "target_cycle": int(target.target_cycle),
                                "target_discharge_start": target.target_discharge_start,
                                "input_end": target.input_end,
                                "prediction_soh_pp": float(p), "prediction_Ah": float(p*102/100),
                                "baseline_age_pp": float(target.outer_age_pp),
                                "wave_correction_pp": float(c),
                                "wave_shrink": selected["shrink"],
                                "recent_event_ids": target.recent_event_ids,
                                "evidence": "five recent strictly completed charge events; outer 5-cell fit; inner group selected"})
            selections.append({"outer_cell": outer, "family": family, "selected": selected,
                               "all_inner_choices": choices})
            ae = np.abs(pred-hold.target_soh_pp.to_numpy(float))
            print(outer, family, selected["feature_set"], selected["lambda"],
                  selected["shrink"], "mae", round(float(ae.mean()), 4), "max", round(float(ae.max()), 4), flush=True)
        pd.DataFrame(outputs).to_csv(RUN / "predictions.partial.csv", index=False)
        (RUN / "selections.partial.json").write_text(json.dumps(selections, indent=2)+"\n")
    pd.DataFrame(outputs).to_csv(RUN / "predictions.csv", index=False)
    (RUN / "selections.json").write_text(json.dumps(selections, indent=2)+"\n")
    out = pd.DataFrame(outputs).merge(panel[key+["target_soh_pp"]], on=key)
    for name, group in out.groupby("method"):
        err = (group.prediction_soh_pp-group.target_soh_pp).abs()
        print(name, "macro_mae", err.groupby(group.cell_id).mean().mean(),
              "p95", err.quantile(.95), "max", err.max(), flush=True)


if __name__ == "__main__":
    main()
