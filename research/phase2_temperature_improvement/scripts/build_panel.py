"""Freeze target dates without consulting any candidate predictions.

The released first-cycle capacity is an anchor. Later labels are scoring-only;
their discharge start time defines when all charging input must stop.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
SOURCE = Path("/Users/shane/Desktop/项目/Current State_Challenge1/framework/data.py")
INVENTORY = ROOT / "research/phase2_validation/preflight/downloaded_data/phase1_label_inventory.csv"


def source_label_function():
    spec = importlib.util.spec_from_file_location("first_phase_label_definition", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._derive_soh


def discharge_starts(folder: Path) -> pd.Series:
    starts: dict[int, pd.Timestamp] = {}
    files = sorted(folder.glob("*.csv"))
    if not files:
        raise FileNotFoundError(folder)
    for path in files:
        for chunk in pd.read_csv(
            path,
            usecols=["absolute_time", "cycle_number", "step_type"],
            chunksize=200_000,
        ):
            dis = chunk.loc[chunk.step_type.eq("cc_discharge"),
                            ["absolute_time", "cycle_number"]]
            if dis.empty:
                continue
            dis = dis.copy()
            dis["absolute_time"] = pd.to_datetime(dis.absolute_time, errors="raise")
            grouped = dis.groupby("cycle_number", sort=False).absolute_time.min()
            for cycle, stamp in grouped.items():
                cycle = int(cycle)
                old = starts.get(cycle)
                if old is None or stamp < old:
                    starts[cycle] = stamp
    return pd.Series(starts, name="target_discharge_start")


def select_indices(count: int, number: int = 30) -> np.ndarray:
    if count < number:
        raise ValueError(f"only {count} post-anchor valid labels, need {number}")
    ideal = np.rint(np.linspace(.05, .95, number) * (count - 1)).astype(int)
    if len(set(ideal)) != number:
        raise ValueError("quantile positions duplicated; record before resolving")
    return ideal


def main() -> None:
    derive = source_label_function()
    inventory = pd.read_csv(INVENTORY)
    all_rows = []
    manifest: dict[str, object] = {
        "panel_protocol": "notes/PROTOCOL.md v1",
        "label_source": str(SOURCE),
        "label_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "inventory_sha256": hashlib.sha256(INVENTORY.read_bytes()).hexdigest(),
        "cells": {},
    }
    for cell_id, inv in inventory.groupby("cell_id", sort=True):
        inv = inv.sort_values("cycle", kind="stable")
        # One row per cycle is sufficient to exercise the exact framework
        # trailing/fallback label rule; the capacity max is already audited.
        label_input = pd.DataFrame({
            "cycle_number": inv.cycle.to_numpy(int),
            "step_type": "cc_discharge",
            "step_capacity_Ah": inv.capacity_Ah.to_numpy(float),
        })
        replay = derive(label_input)
        found = replay.soh_percent.notna().to_numpy()
        expected = inv.old_official_label_valid.to_numpy(bool)
        if not np.array_equal(found, expected):
            different = inv.cycle.to_numpy()[found != expected]
            raise AssertionError(f"label inventory disagrees with framework: {cell_id} {different[:15]}")
        by_cycle = replay.set_index("cycle_number").soh_percent
        starts = discharge_starts(ROOT / "dataset original" / cell_id)
        lab = inv.loc[inv.old_official_label_valid].copy()
        lab["target_discharge_start"] = lab.cycle.map(starts)
        if lab.target_discharge_start.isna().any():
            raise AssertionError(f"valid label without discharge start in {cell_id}")
        lab = lab.sort_values(["target_discharge_start", "cycle"], kind="stable")
        anchor = lab.iloc[0]
        targets = lab.loc[lab.target_discharge_start > anchor.target_discharge_start].reset_index(drop=True)
        chosen = targets.iloc[select_indices(len(targets))]
        for serial, row in enumerate(chosen.itertuples(index=False), start=1):
            label_soh = float(by_cycle.loc[int(row.cycle)])
            all_rows.append({
                "cell_id": cell_id,
                "target_ordinal": serial,
                "target_cycle": int(row.cycle),
                "target_discharge_start": pd.Timestamp(row.target_discharge_start).isoformat(),
                "target_capacity_Ah": float(row.capacity_Ah),
                "target_soh_pp": label_soh,
                "anchor_cycle": int(anchor.cycle),
                "anchor_discharge_start": pd.Timestamp(anchor.target_discharge_start).isoformat(),
                "anchor_capacity_Ah": float(anchor.capacity_Ah),
                "anchor_soh_pp": float(by_cycle.loc[int(anchor.cycle)]),
                "evidence": "E3-P1 single-cell high-rate discharge proxy, not official C/20 pack capacity",
            })
        manifest["cells"][cell_id] = {
            "framework_valid_labels": int(len(lab)),
            "anchor_cycle": int(anchor.cycle),
            "anchor_Ah": float(anchor.capacity_Ah),
            "post_anchor_valid_labels": int(len(targets)),
            "selected_cycles": chosen.cycle.astype(int).tolist(),
        }
        print(cell_id, "valid", len(lab), "targets", len(chosen), flush=True)
    out = TASK / "outputs"
    out.mkdir(exist_ok=True)
    panel = pd.DataFrame(all_rows)
    if len(panel) != 180 or panel.cell_id.nunique() != 6:
        raise AssertionError("main panel must have 6 cells x 30 targets")
    if panel.duplicated(["cell_id", "target_cycle"]).any():
        raise AssertionError("duplicate target")
    panel_path = out / "panel_main.csv"
    panel.to_csv(panel_path, index=False, float_format="%.10f", lineterminator="\n")
    manifest["panel_sha256"] = hashlib.sha256(panel_path.read_bytes()).hexdigest()
    manifest["n_targets"] = len(panel)
    (out / "panel_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print("panel_sha256", manifest["panel_sha256"])


if __name__ == "__main__":
    main()
