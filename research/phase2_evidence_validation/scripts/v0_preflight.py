"""Read-only source V0 checks; all outputs stay in this task's own run folder."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize_scalar

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/V0_preflight_20260929"
OUT.mkdir(parents=True, exist_ok=False)
T0 = time.perf_counter()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record(path: Path, source: str, role: str, entity: str, license_: str) -> dict:
    return {
        "source": source,
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
        "role": role,
        "physical_entities": entity,
        "license_or_access": license_,
        "verification": "full_sha256_this_run",
    }


official_files = sorted((ROOT / "data/operation").glob("segment_*.csv.gz"))
official_files += sorted((ROOT / "data/checkups").glob("*.csv*"))
panel_path = ROOT / "research/phase2_temperature_improvement/outputs/panel_main.csv"
seq_path = ROOT / "research/phase2_method_exploration/runs/M9_D1_v15_inputs_v1/native_sequences.npz"
map_path = ROOT / "research/phase2_method_exploration/runs/M9_D1_v15_target_map_v1/target_inputs.npz"
manifest_path = ROOT / "research/phase2_method_exploration/runs/M9_D1_v15_inputs_v1/sequence_manifest.csv"
files = [record(p, "official_D3", "original_input", "one 4S pack", "challenge package") for p in official_files]
for p, role in [(panel_path, "D1_proxy_label_panel"), (seq_path, "D1_prefix_sequences"),
                (map_path, "D1_target_mapping"), (manifest_path, "D1_prefix_manifest")]:
    files.append(record(p, "P1_D1_reused_six_cells", role, "six repeated single cells", "challenge package"))
inventory = TASK / "data_manifests/input_manifest.csv"
with inventory.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(files[0]))
    writer.writeheader()
    writer.writerows(files)

panel_hash = digest(panel_path)
assert panel_hash == "7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c"
panel = pd.read_csv(panel_path)
assert len(panel) == 180 and panel.cell_id.nunique() == 6
assert panel.groupby("cell_id").size().eq(30).all()
assert panel.target_ordinal.between(1, 30).all()

ck0_path = ROOT / "data/checkups/CK0_reference_discharge.csv.gz"
ck0 = pd.read_csv(ck0_path, parse_dates=["timestamp"])
required = {"timestamp", "current_A", "voltage_V", "discharged_Ah"}
assert required.issubset(ck0)
t = ck0.timestamp.astype("int64").to_numpy() / 1e9
dt = np.diff(t)
integral_ah = float(np.sum(-.5 * (ck0.current_A.to_numpy()[1:] + ck0.current_A.to_numpy()[:-1]) *
                           np.maximum(dt, 0) / 3600))
reference_ah = float(ck0.discharged_Ah.iloc[-1])
pack_minus_cells = ck0.voltage_V - ck0[[f"cell{i}_V" for i in range(1, 5)]].sum(axis=1)
published = pd.read_csv(ROOT / "data/checkups/checkup_capacities_released.csv")
published_ah = float(published.sort_values("date").capacity_Ah.iloc[0])
ck0_summary = {
    "rows": len(ck0), "discharged_Ah_last": reference_ah,
    "trapezoid_integrated_Ah": integral_ah, "published_Ah": published_ah,
    "duplicate_time_steps": int(np.sum(dt == 0)), "negative_time_steps": int(np.sum(dt < 0)),
    "pack_minus_cell_sum_median_V": float(pack_minus_cells.median()),
    "pack_minus_cell_sum_p95_abs_V": float(pack_minus_cells.abs().quantile(.95)),
    "reference_temperature_status": "unknown_from_CK0_columns",
}
assert abs(reference_ah - published_ah) < 0.05

# The official API's `<= until` behavior is exercised, not approximated by a custom loader.
sys.path.insert(0, str(ROOT))
from framework.data import load_dataset  # noqa: E402

ck1 = pd.Timestamp("2025-02-08")
dataset = load_dataset(str(ROOT / "data"), until=ck1)
op = dataset.operation
assert len(op) > 0 and op.timestamp.max() <= ck1
assert dataset.checkups_released.shape[0] == 1
prefix_summary = {
    "checkup": "CK1", "cutoff": str(ck1), "rows": len(op),
    "last_timestamp": str(op.timestamp.max()),
    "released_capacity_rows": len(dataset.checkups_released),
    "eval_points": len(dataset.eval_points),
    "strict_prefix_confirmed": bool(op.timestamp.max() <= ck1),
}

# One P1 raw event is reconstructed from original CSV using the v1.5 manifest identity.
sequence_manifest = pd.read_csv(manifest_path)
example = sequence_manifest.iloc[0]
event_id = str(example.event_id)
cell, cyc, source_start, shallow_end = event_id.split("|")
raw_parts = []
raw_paths = []
for raw_file in sorted((ROOT / "dataset original" / cell).glob("*.csv")):
    for chunk in pd.read_csv(raw_file, usecols=["absolute_time", "cycle_number", "step_type",
                                               "voltage_V", "current_A", "temperature_C"], chunksize=100000):
        sub = chunk.loc[chunk.cycle_number.eq(int(cyc)) & ~chunk.step_type.eq("cc_discharge")]
        if len(sub):
            raw_parts.append(sub)
            raw_paths.append(raw_file)
    if raw_parts:
        break
assert raw_parts
raw = pd.concat(raw_parts, ignore_index=True)
raw.absolute_time = pd.to_datetime(raw.absolute_time)
raw = raw.sort_values("absolute_time", kind="stable")
source_start_ts, end_ts = pd.Timestamp(source_start), pd.Timestamp(shallow_end)
event = raw.loc[raw.absolute_time.ge(source_start_ts) & raw.absolute_time.le(end_ts) & raw.current_A.ge(5)]
assert len(event) >= int(example.n_native_samples)
crossings = np.flatnonzero((raw.voltage_V.to_numpy()[:-1] < 3.50) &
                           (raw.voltage_V.to_numpy()[1:] >= 3.50))
assert len(crossings) > 0
first_cross_time = raw.absolute_time.iloc[int(crossings[0] + 1)]
assert first_cross_time == end_ts
event_summary = {
    "source": "original P1 CSV", "event_id": event_id,
    "physical_cell": cell, "cycle": int(cyc),
    "raw_file": str(raw_paths[0].relative_to(ROOT)),
    "first_3p50V_crossing": str(first_cross_time),
    "manifest_fragment_end": str(pd.Timestamp(example.fragment_end)),
    "native_samples_manifest": int(example.n_native_samples),
    "observed_rows_until_endpoint": len(event),
    "role": "D1 deep-charge-record cropped-prefix proxy smoke",
}

opt = minimize_scalar(lambda x: (x - 2.0) ** 2, bounds=(0, 4), method="bounded")
root = brentq(lambda x: x - 2.0, 0, 4)
assert opt.success and abs(opt.x - 2) < 1e-8 and abs(root - 2) < 1e-8

# One held physical cell, one target only: execution/serialization smoke, no method evaluation.
held = sorted(panel.cell_id.unique())[0]
train = panel.loc[panel.cell_id.ne(held)]
test = panel.loc[panel.cell_id.eq(held)].sort_values("target_ordinal").head(1)
age = (train.target_cycle - train.anchor_cycle).to_numpy(float)
target = (train.target_soh_pp - train.anchor_soh_pp).to_numpy(float)
coefficient = float(np.dot(age, target) / (np.dot(age, age) + 1e-6))
model_path = OUT / "one_fold_smoke_model.npz"
np.savez(model_path, coefficient=coefficient)
one_age = float((test.target_cycle - test.anchor_cycle).iloc[0])
prediction = float(test.anchor_soh_pp.iloc[0] + coefficient * one_age)
child = subprocess.run(
    [sys.executable, "-c",
     "import numpy as np,sys; z=np.load(sys.argv[1]); print(float(sys.argv[2])+float(z['coefficient'])*float(sys.argv[3]))",
     str(model_path), str(float(test.anchor_soh_pp.iloc[0])), str(one_age)],
    capture_output=True, text=True, check=True, timeout=30,
)
fresh_prediction = float(child.stdout.strip())
assert abs(prediction - fresh_prediction) < 1e-10

summary = {
    "run_id": OUT.name,
    "python": sys.version.split()[0], "platform": platform.platform(),
    "disk_free_GiB_at_finish": round(shutil.disk_usage(ROOT).free / 2 ** 30, 2),
    "cpu_count": os.cpu_count(), "elapsed_s": round(time.perf_counter() - T0, 3),
    "source_manifest_count": len(files), "panel_sha256": panel_hash,
    "d1_panel_targets": len(panel), "d1_physical_cells": panel.cell_id.nunique(),
    "ck0": ck0_summary, "official_prefix": prefix_summary,
    "p1_event": event_summary,
    "optimizer_known_answer": float(opt.x), "root_known_answer": float(root),
    "one_fold_held_cell": held, "one_fold_prediction_soh_pp": prediction,
    "fresh_process_prediction_abs_diff_pp": abs(prediction - fresh_prediction),
    "one_fold_note": "Execution smoke on repeated D1 development cell, not validated model performance",
    "code_sha256": digest(Path(__file__)),
}
(OUT / "result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
(OUT / "COMPLETED").write_text("V0 smoke complete; see result.json\n")
print(json.dumps({k: summary[k] for k in
                  ("run_id", "elapsed_s", "source_manifest_count", "d1_panel_targets", "d1_physical_cells")},
                 ensure_ascii=False), flush=True)
