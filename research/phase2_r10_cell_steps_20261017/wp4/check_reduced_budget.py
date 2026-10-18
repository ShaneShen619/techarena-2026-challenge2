"""Wiring check (post round 10): reduced-budget smoke test of the A3 class against the submitted T_main class.
40 random data reductions x 8 checkups = 320 calls per model; every call must return a finite SOH without error."""
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common10 import H  # noqa: E402
from framework.data import Dataset, load_dataset  # noqa: E402

PKG = os.path.join(STUDY, "cache", "submitted_package", "TechArena_Challenge2_Team_Package")
N_CFG, SEED = 40, 20261018


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MyModel


def reduce(op, rng):
    """One random reduction: drop segments, thin rows, cut the start and/or blank a contiguous block."""
    segs = op["segment"].unique()
    keep = rng.choice(segs, size=rng.integers(max(1, len(segs) // 3), len(segs) + 1), replace=False)
    o = op[op["segment"].isin(keep)]
    if rng.random() < 0.4:
        o = o.iloc[::int(rng.choice([2, 3, 6]))]
    if rng.random() < 0.4:
        t0 = o["timestamp"].min() + pd.Timedelta(days=float(rng.uniform(0, 60)))
        o = o[o["timestamp"] >= t0]
    if rng.random() < 0.4 and len(o):
        a = o["timestamp"].min() + (o["timestamp"].max() - o["timestamp"].min()) * float(rng.uniform(0, 0.8))
        o = o[(o["timestamp"] < a) | (o["timestamp"] > a + pd.Timedelta(days=float(rng.uniform(2, 20))))]
    return o.reset_index(drop=True)


if __name__ == "__main__":
    full = load_dataset(H.DATA)
    models = {"A3": load(os.path.join(HERE, "candidate_model", "model_template.py"), "cand_a3_rb"),
              "T_main": load(os.path.join(PKG, "my_model", "model_template.py"), "sub_tmain_rb")}
    fitted = {}
    for n, cls in models.items():
        m = cls()
        m.fit(full)
        fitted[n] = m
    rng = np.random.default_rng(SEED)
    rows = []
    for cfg in range(N_CFG):
        red = reduce(full.operation, rng)
        for k, d in enumerate(H.CK):
            ds = Dataset(operation=red[red["timestamp"] <= d].reset_index(drop=True),
                         checkups_released=full.checkups_released[full.checkups_released["date"] <= d],
                         eval_points=full.eval_points, reference_discharge=full.reference_discharge, until=d)
            r = dict(cfg=cfg, checkup=H.CK_NAMES[k], n_rows=len(ds.operation))
            for n, m in fitted.items():
                try:
                    r[n] = float(m.estimate_soh(ds, d))
                    r[f"{n}_error"] = ""
                except Exception as exc:  # recorded, the check fails
                    r[n] = np.nan
                    r[f"{n}_error"] = repr(exc)[:200]
            rows.append(r)
    t = pd.DataFrame(rows)
    os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
    t.to_csv(os.path.join(HERE, "outputs", "wiring_reduced_budget.csv"), index=False)
    res = dict(calls_per_model=len(t),
               A3_errors=int((t["A3_error"] != "").sum()), A3_nonfinite=int((~np.isfinite(t["A3"])).sum()),
               Tmain_errors=int((t["T_main_error"] != "").sum()), Tmain_nonfinite=int((~np.isfinite(t["T_main"])).sum()),
               max_abs_diff_A3_vs_Tmain_pp=float((t["A3"] - t["T_main"]).abs().max()),
               median_abs_diff_pp=float((t["A3"] - t["T_main"]).abs().median()),
               SOH_range_A3=[float(t["A3"].min()), float(t["A3"].max())])
    res["passed"] = bool(res["A3_errors"] == 0 and res["A3_nonfinite"] == 0)
    json.dump(res, open(os.path.join(HERE, "outputs", "wiring_reduced_budget.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))
