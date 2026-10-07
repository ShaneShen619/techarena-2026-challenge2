"""Register the frozen portable temperature+waveform candidate for scoring.

Evidence is conservative: an event counts only when it was used by the M2
strict-prefix replay and is among the five events entering this model's
window medians.  This does not manufacture coverage from age coordinates.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]


def make_evidence(features: pd.DataFrame, logs: pd.DataFrame, run_id: str,
                  *, scenario: str | None = None) -> pd.DataFrame:
    records = []
    grouped = {(str(cell), int(cycle)): group for (cell, cycle), group in
               logs.groupby(["cell_id", "target_cycle"])}
    for target in features.itertuples(index=False):
        recent_ids = set(str(target.recent_event_ids).split("|#|"))
        source = grouped.get((str(target.cell_id), int(target.target_cycle)))
        if source is None:
            continue
        for ev in source.itertuples(index=False):
            if not (bool(ev.used_for_update) and bool(ev.quality_pass) and
                    not bool(ev.reference_only) and str(ev.event_id) in recent_ids):
                continue
            row = {"run_id": run_id, "method": "final", "cell_id": target.cell_id,
                   "target_cycle": int(target.target_cycle), "event_id": str(ev.event_id),
                   "event_end": ev.event_end, "quality_pass": True,
                   "reference_only": False, "used_for_update": True,
                   "reason": "new qualified event in recent-five partial-charge feature"}
            if scenario is not None:
                row["scenario"] = scenario
            records.append(row)
    return pd.DataFrame(records)


def main() -> None:
    run = TASK / "runs/M4_multi_efc_T_v1"
    if not (run / "fold_models.json").exists():
        raise RuntimeError("fold coefficients not frozen")
    source = pd.read_csv(run / "predictions.csv")
    if len(source) != 180 or not np.isfinite(source.prediction_soh_pp).all():
        raise AssertionError("incomplete final candidate")
    output = source.copy()
    output["method"] = "final"
    output["run_id"] = "M4_multi_efc_T_v1_final_candidate"
    existing = pd.read_csv(TASK / "outputs/predictions.csv")
    existing = existing.loc[~existing.method.eq("final")]
    pd.concat([existing, output], ignore_index=True).to_csv(TASK / "outputs/predictions.csv", index=False)
    features = pd.read_csv(TASK / "runs/M4_feature_audit_v1/features.csv")
    logs = pd.read_csv(TASK / "runs/M2_A_bugfix_180_v1/evidence_events.csv")
    evidence = make_evidence(features, logs, "M4_multi_efc_T_v1_final_candidate")
    evidence.to_csv(TASK / "outputs/evidence_events.csv", index=False)
    print("final predictions", len(output), "evidence rows", len(evidence),
          "targets with evidence", evidence.groupby(["cell_id", "target_cycle"]).ngroups)


if __name__ == "__main__":
    main()
