"""Portable ageing coordinate: cumulative completed, qualified charge Ah / 102.

Only event IDs in each target's strict-prefix replay count.  This coordinate
can be reproduced on official 4S data without pretending segment IDs are P1
cycle numbers.  It is a diagnostic alternative to the source cycle coordinate.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

TASK = Path(__file__).resolve().parents[1]


def main() -> None:
    run = TASK / "runs/M4_feature_audit_v1"
    features = pd.read_csv(run / "features.csv")
    events = pd.read_csv(run / "events.csv")
    logs = pd.read_csv(TASK / "runs/M2_A_bugfix_180_v1/evidence_events.csv")
    values = events.set_index("event_id").total_Ah.to_dict()
    rows = []
    for cell, targets in features.groupby("cell_id", sort=True):
        seen = set()
        for target in targets.sort_values("target_ordinal").itertuples(index=False):
            recent = logs.loc[logs.cell_id.eq(cell) & logs.target_cycle.eq(target.target_cycle)]
            seen.update(str(eid) for eid in recent.event_id)
            ah = sum(float(values[eid]) for eid in seen if eid in values)
            rows.append({"cell_id": cell, "target_ordinal": int(target.target_ordinal),
                         "target_cycle": int(target.target_cycle),
                         "qualified_charge_throughput_Ah": ah,
                         "qualified_charge_efc": ah/102.})
    out = pd.DataFrame(rows)
    if len(out) != 180 or out.qualified_charge_efc.le(0).any():
        raise AssertionError("charge throughput coordinate incomplete")
    out.to_csv(run / "throughput.csv", index=False)
    print(out.groupby("cell_id").qualified_charge_efc.agg(["min", "max"]).to_string())


if __name__ == "__main__":
    main()
