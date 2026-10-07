"""Non-tautological whole-cell permutation recheck of the M5 cutoff solver."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/M5_permutation_recheck_v1"
OUT.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(TASK / "src"))
from m5_pack import CK0Pack, PackState

reference = pd.read_csv(ROOT / "data/checkups/CK0_reference_discharge.csv.gz")
pack = CK0Pack(reference)
rng = np.random.default_rng(20260928)
rows = []
for scenario in range(100):
    state = PackState(rng.uniform(85, 105, 4), rng.uniform(.94, 1, 4), rng.uniform(0, .002, 4))
    shape = rng.uniform(-20, 20, 4)
    original = pack.cutoff(state, truth_shape_mV=shape, truth_dynamic_R=True)
    perm = rng.permutation(4)
    renamed_pack = CK0Pack(reference)
    for attr in ("curves", "start", "end", "tail_slope", "head_slope"):
        setattr(renamed_pack, attr, getattr(renamed_pack, attr)[perm])
    renamed_state = PackState(state.capacity_Ah[perm], state.initial_SOC[perm], state.delta_R_ohm[perm])
    renamed = renamed_pack.cutoff(renamed_state, truth_shape_mV=shape[perm], truth_dynamic_R=True)
    mapping_back = int(perm[renamed["lowest_voltage_cell"] - 1] + 1)
    rows.append({"scenario": scenario, "group_Ah_delta": renamed["group_capacity_Ah"] - original["group_capacity_Ah"],
                 "sum_voltage_delta_V": renamed["cutoff_voltage_sum_V"] - original["cutoff_voltage_sum_V"],
                 "original_lowest_cell": original["lowest_voltage_cell"],
                 "renamed_lowest_cell_mapped_back": mapping_back})
result = pd.DataFrame(rows)
result.to_csv(OUT / "checks.csv", index=False)
summary = {"scenarios": len(result), "max_abs_group_Ah_delta": float(result.group_Ah_delta.abs().max()),
           "max_abs_sum_voltage_delta_V": float(result.sum_voltage_delta_V.abs().max()),
           "lowest_cell_identity_matches": bool(result.original_lowest_cell.eq(result.renamed_lowest_cell_mapped_back).all()),
           "passed": bool(result.group_Ah_delta.abs().max() < 1e-8 and
                          result.sum_voltage_delta_V.abs().max() < 1e-8 and
                          result.original_lowest_cell.eq(result.renamed_lowest_cell_mapped_back).all()),
           "reason": "M5_pack_v1 script checked only commutativity of summing one voltage vector; this recheck permutes reference curves, states and truth shapes together."}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False), flush=True)
if not summary["passed"]:
    raise SystemExit(1)
