"""Copy of round-3 harness.candidate_checks (G-causal + G-impl) with one change: corrupted columns are
cast to float first, because pandas 3 refuses float noise in the int64 chamber set-point column (D3.2)."""
import pickle

import numpy as np

from common17 import H
from framework.data import Dataset, load_dataset

CK = H.CK
DATA = H.DATA


def candidate_checks(model_cls, research_soh, data_dir=DATA):
    """G-causal and G-impl: run like run_model.py, corrupt future rows, compare to research."""
    full = load_dataset(data_dir)
    model = model_cls()
    model.fit(full)
    model = pickle.loads(pickle.dumps(model))
    res, same = [], []
    rng = np.random.default_rng(0)
    for k, d in enumerate(CK):
        ds = load_dataset(data_dir, until=d)
        a = model.estimate_soh(ds, d)
        op = full.operation.copy()
        for c in ["current_A", "pack_voltage_V", "cell1_V", "cell2_V", "cell3_V", "cell4_V",
                  "chamber_temperature_C", "temp_mean_C"]:
            op[c] = op[c].astype(float)   # deviation D3.2: allow float noise in int columns (pandas 3)
        fut = op["timestamp"] > d
        for c in ["current_A", "pack_voltage_V", "cell1_V", "cell2_V", "cell3_V", "cell4_V",
                  "chamber_temperature_C", "temp_mean_C"]:
            op.loc[fut, c] = rng.normal(size=int(fut.sum()))
        cut = Dataset(operation=op[~fut].reset_index(drop=True),
                      checkups_released=full.checkups_released[full.checkups_released["date"] <= d],
                      eval_points=full.eval_points, reference_discharge=full.reference_discharge, until=d)
        same.append(model.estimate_soh(cut, d) == a)
        res.append(round(float(a), 3))
    m2 = model_cls()
    m2.fit(load_dataset(data_dir, until=CK[1]))
    fit_cut_same = all(round(float(m2.estimate_soh(load_dataset(data_dir, until=d), d)), 3) == r
                       for d, r in zip(CK, res))
    diff = float(np.max(np.abs(np.array(res[1:]) - np.asarray(research_soh))))
    return dict(predictions=res, future_rows_corrupted_identical=bool(all(same)),
                fit_on_cut_data_identical=bool(fit_cut_same), max_abs_diff_vs_research_pp=diff,
                passed=bool(all(same) and fit_cut_same and diff <= 0.001))
