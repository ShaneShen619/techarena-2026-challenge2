"""Stage F: run the candidate exactly like run_model.py, plus causality and
reimplementation checks, and a smoke run on sample_data."""
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "TechArena_Challenge2_Team_Package"))
sys.path.insert(0, os.path.join(HERE, "candidate_model"))
sys.path.insert(0, ROOT)

from framework.data import Dataset, load_dataset, load_eval_points  # noqa: E402
from anchor_step_model import AnchorStepModel  # noqa: E402

OUT = os.path.join(HERE, "outputs")


def run(data_dir, fit_ds=None):
    model = AnchorStepModel()
    model.fit(fit_ds if fit_ds is not None else load_dataset(data_dir))
    model = pickle.loads(pickle.dumps(model))  # framework pickles the fitted object
    rows = []
    for p in load_eval_points(data_dir).itertuples():
        ds = load_dataset(data_dir, until=p.date)
        rows.append(dict(checkup=p.checkup, date=p.date.strftime("%Y-%m-%d"),
                         SOH_est=round(float(model.estimate_soh(ds, p.date)), 3)))
    return pd.DataFrame(rows)


def main():
    data = os.path.join(ROOT, "data")
    res = run(data)
    res.to_csv(os.path.join(OUT, "F_candidate_predictions.csv"), index=False)
    checks = {}

    # G3a: fit() sees only data up to CK1 -> identical outputs (fit carries no future info)
    res_fit_cut = run(data, fit_ds=load_dataset(data, until=pd.Timestamp("2025-02-08")))
    checks["fit_on_cut_data_identical"] = bool((res["SOH_est"] == res_fit_cut["SOH_est"]).all())

    # G3b: corrupt every row after each cutoff, re-cut manually -> identical outputs
    full = load_dataset(data)
    model = AnchorStepModel()
    model.fit(full)
    same = []
    rng = np.random.default_rng(0)
    for p in load_eval_points(data).itertuples():
        op = full.operation.copy()
        fut = op["timestamp"] > p.date
        for c in ["current_A", "pack_voltage_V", "cell1_V", "cell2_V", "cell3_V", "cell4_V"]:
            op.loc[fut, c] = rng.normal(size=fut.sum())
        cut = Dataset(operation=op[~fut].reset_index(drop=True),
                      checkups_released=full.checkups_released[full.checkups_released["date"] <= p.date],
                      eval_points=full.eval_points, reference_discharge=full.reference_discharge, until=p.date)
        a = model.estimate_soh(cut, p.date)
        b = model.estimate_soh(load_dataset(data, until=p.date), p.date)
        same.append(a == b)
    checks["future_rows_corrupted_identical"] = bool(all(same))

    # reimplementation check against the research predictor M4 main, beta 1, eps0+0.4
    wide = pd.read_csv(os.path.join(OUT, "C_predictions_wide.csv"))
    ref = wide["M4_main_b1.0_last1_d0.4"].to_numpy() / 102 * 100
    diff = np.abs(res.loc[res["checkup"] != "CK0", "SOH_est"].to_numpy() - ref)
    checks["max_abs_diff_vs_research_M4_pp"] = float(diff.max())

    # smoke run on the tiny synthetic sample data
    sample = os.path.join(ROOT, "sample_data")
    try:
        sm = run(sample)
        checks["sample_data_smoke"] = sm.to_dict("records")
    except Exception as exc:  # report, do not hide
        checks["sample_data_smoke_error"] = repr(exc)

    with open(os.path.join(OUT, "F_checks.json"), "w") as f:
        json.dump(checks, f, indent=2, default=str)
    print(res.to_string(index=False))
    print(json.dumps(checks, indent=1, default=str))


if __name__ == "__main__":
    main()
