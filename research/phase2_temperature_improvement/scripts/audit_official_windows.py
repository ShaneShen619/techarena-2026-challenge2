"""Read-only official 4S window/quality audit; no hidden capacity labels."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "src"))
from event_core import extract_charge_events, partial_ah  # noqa: E402
from route_a_repaired import stable_cc_prefix  # noqa: E402

def main() -> None:
    operation = pd.concat([pd.read_csv(p, parse_dates=["timestamp"])
                           for p in sorted((ROOT / "data/operation").glob("segment_*.csv.gz"))],
                          ignore_index=True)
    evals = pd.read_csv(ROOT / "data/checkups/evaluation_points.csv", parse_dates=["date"])
    windows = json.loads((TASK / "runs/M4_feature_audit_v1/config.json").read_text())["windows"]
    events = extract_charge_events(operation, time_col="timestamp",
                                   voltage_cols=("cell1_V", "cell2_V", "cell3_V", "cell4_V"),
                                   temp_col="temp_mean_C", segment_col="segment",
                                   counter_col="charge_Ah_cum")
    rows = []
    coverage = np.zeros((4, len(windows)), dtype=int)
    n_pass = 0
    for ev in events:
        cc, status = stable_cc_prefix(ev)
        if status == "pass":
            n_pass += 1
        cells = []
        for ci in range(4):
            vals = [partial_ah(cc, ci, lo, hi) if cc is not None else None for lo, hi in windows]
            if status == "pass":
                coverage[ci] += np.asarray([x is not None for x in vals], int)
            cells.append({"n_windows": sum(x is not None for x in vals),
                          "mid_windows": sum(vals[i] is not None for i in range(9, 17)),
                          "all_mid": all(vals[i] is not None for i in range(9, 17))})
        rows.append({"event_end": ev.end, "segment": ev.segment, "status": status,
                     "total_Ah": ev.ah, "temp_C": ev.median_temp,
                     **{f"cell{ci+1}_{key}": cell[key] for ci, cell in enumerate(cells)
                        for key in ("n_windows", "mid_windows", "all_mid")}})
    out = pd.DataFrame(rows)
    out.to_csv(TASK / "runs/M4_feature_audit_v1/official_window_audit.csv", index=False)
    pd.DataFrame({"index": range(len(windows)), "lo_V": [w[0] for w in windows],
                  "hi_V": [w[1] for w in windows],
                  **{f"cell{i+1}_n": coverage[i] for i in range(4)}}).to_csv(
                      TASK / "runs/M4_feature_audit_v1/official_window_frequency.csv", index=False)
    print("quality_events", n_pass, "frequency_by_window")
    print(pd.read_csv(TASK / "runs/M4_feature_audit_v1/official_window_frequency.csv").to_string(index=False))
    for ck in evals.itertuples(index=False):
        subset = out.loc[out.event_end.lt(ck.date)]
        recent = subset.loc[subset.status.eq("pass")].tail(5)
        print(ck.checkup, "all_events", len(subset), "pass_events", int(subset.status.eq("pass").sum()),
              "recent_mid_all", [int(recent[f"cell{i}_all_mid"].sum()) for i in range(1,5)],
              "recent_mid_median", [float(recent[f"cell{i}_mid_windows"].median()) if len(recent) else np.nan for i in range(1,5)],
              flush=True)

if __name__ == "__main__":
    main()
