"""Fresh-process official candidate causality, state and fault tests."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--candidate", choices=["ck0_hold", "exploratory_fallback"], required=True)
args = parser.parse_args()
package = TASK / "candidates" / args.candidate
sys.path.insert(0, str(package))
from my_model import ActiveModel
from framework.data import load_dataset

OUT = TASK / "runs" / f"M10_{args.candidate}_hard_tests_v2"
OUT.mkdir(parents=True, exist_ok=False)
full = load_dataset(str(ROOT / "data"))
points = full.eval_points.set_index("checkup")
assert points.index.tolist() == [f"CK{i}" for i in range(8)]


def at(name, operation=None, released=None):
    cutoff = pd.Timestamp(points.loc[name, "date"])
    op = full.operation.loc[full.operation.timestamp <= cutoff] if operation is None else operation
    ck = full.checkups_released.loc[full.checkups_released.date <= cutoff] if released is None else released
    return replace(full, operation=op.copy(), checkups_released=ck.copy(), until=cutoff), cutoff


def fitted(dataset=full):
    model = ActiveModel()
    model.fit(dataset)
    return model


results = []


def check(name, condition, detail=""):
    results.append({"test": name, "passed": bool(condition), "detail": str(detail)})
    print(name, "PASS" if condition else "FAIL", detail, flush=True)


model = fitted()
ds1, t1 = at("CK1")
ds3, t3 = at("CK3")
ds7, t7 = at("CK7")
p1 = float(model.estimate_soh(ds1, t1))
p7 = float(model.estimate_soh(ds7, t7))
p3 = float(model.estimate_soh(ds3, t3))
p7_repeat = float(model.estimate_soh(ds7, t7))
check("repeat_query", np.isclose(p7_repeat, p7, rtol=0, atol=1e-9), f"{p7} versus {p7_repeat}")
check("out_of_order_query", np.isclose(p3, float(fitted().estimate_soh(ds3, t3)), rtol=0, atol=1e-9),
      "CK7 -> CK3 equals fresh CK3")
check("strict_operation_prefix", bool((ds1.operation.timestamp <= t1).all()), str(ds1.operation.timestamp.max()))

future = replace(ds1, operation=full.operation.copy())
p1_future = float(fitted().estimate_soh(future, t1))
check("future_row_contamination", np.isclose(p1, p1_future, rtol=0, atol=1e-9), f"{p1} versus {p1_future}")

fake = pd.concat([full.checkups_released,
    pd.DataFrame({"checkup": ["FAKE_FUTURE"], "date": [pd.Timestamp("2026-01-01")],
                  "capacity_Ah": [55.0], "SOH_pct": [55.0/102*100]})], ignore_index=True)
p1_fake = float(fitted(replace(full, checkups_released=fake)).estimate_soh(ds1, t1))
check("future_label_injection_fit", np.isclose(p1, p1_fake, rtol=0, atol=1e-9), f"{p1} versus {p1_fake}")

cold = replace(ds7, operation=ds7.operation.iloc[:0].copy())
p_cold = float(fitted().estimate_soh(cold, t7))
check("cold_start_finite", np.isfinite(p_cold) and 50 <= p_cold <= 110, p_cold)
stale = replace(ds7, operation=ds7.operation.loc[ds7.operation.timestamp <= t1].copy())
p_stale = float(fitted().estimate_soh(stale, t7))
check("long_gap_finite", np.isfinite(p_stale) and 50 <= p_stale <= 110, p_stale)

op_perm = ds7.operation.copy()
cols = [f"cell{i}_V" for i in range(1, 5)]
assert all(col in op_perm for col in cols)
op_perm[cols] = ds7.operation[cols[::-1]].to_numpy()
p_perm = float(fitted().estimate_soh(replace(ds7, operation=op_perm), t7))
check("cell_permutation_invariance", np.isclose(p7, p_perm, rtol=0, atol=1e-9), f"{p7} versus {p_perm}")
check("finite_all_test_outputs", all(np.isfinite(v) and 50 <= v <= 110 for v in [p1, p3, p7, p_cold, p_stale, p_perm]))

summary = {"candidate": args.candidate, "tests": results,
           "hard_correctness_pass": all(r["passed"] for r in results),
           "official_capacity_accuracy_verified": False,
           "cold_start_SOH_pp": p_cold, "long_gap_SOH_pp": p_stale,
           "note": "Long gap test checks stability only; no labeled group capacity proves a stale forecast is calibrated."}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
if not summary["hard_correctness_pass"]:
    raise SystemExit(1)
