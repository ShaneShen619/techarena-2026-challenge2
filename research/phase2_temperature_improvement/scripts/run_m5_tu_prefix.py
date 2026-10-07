"""Stream fixed 100k-row continuous prefixes of TU systems 25, 1, 8.

Field systems have no independent capacity labels.  Active balancing and
sampling gaps are reported; no BMS SOC is used as SOH truth.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "src"))
from event_core import extract_charge_events  # noqa: E402


def main() -> None:
    columns = ["Timestamp", "I_Battery", "U_Battery", "SOC_Battery"]
    columns += [f"U_Cell_{i}" for i in range(1, 9)]
    columns += [f"I_CNV_Cell_{i}" for i in range(1, 9)]
    columns += [f"Temperature_{i}" for i in range(1, 5)]
    records = []
    for system in (25, 1, 8):
        path = ROOT / "TU Darmstadt" / f"data_sys_{system}.csv"
        chunks = []
        left = 100_000
        for chunk in pd.read_csv(path, usecols=columns, chunksize=25_000):
            take = chunk.head(left)
            chunks.append(take)
            left -= len(take)
            if left == 0:
                break
        data = pd.concat(chunks, ignore_index=True)
        if len(data) != 100_000:
            raise AssertionError("fixed TU prefix truncated")
        temp = data[[f"Temperature_{i}" for i in range(1, 5)]].to_numpy(float)
        balance = data[[f"I_CNV_Cell_{i}" for i in range(1, 9)]].to_numpy(float)
        current = data.I_Battery.to_numpy(float)
        t = pd.to_datetime(data.Timestamp, errors="coerce")
        dt = t.diff().dt.total_seconds()
        frame = pd.DataFrame({"timestamp": t, "current_A": current,
                              "temp_mean_C": np.nanmean(temp, axis=1),
                              "segment": np.zeros(len(data), int)})
        for ci in range(1, 9):
            frame[f"cell{ci}_V"] = data[f"U_Cell_{ci}"].to_numpy(float)
        events = extract_charge_events(frame, time_col="timestamp",
                                       voltage_cols=tuple(f"cell{i}_V" for i in range(1, 9)),
                                       temp_col="temp_mean_C", segment_col="segment",
                                       counter_col=None)
        records.append({"system": system, "prefix_rows": len(data),
                        "time_start": t.iloc[0].isoformat(), "time_end": t.iloc[-1].isoformat(),
                        "temperature_sensor_valid_fraction": float(np.isfinite(temp).mean()),
                        "temperature_median_C": float(np.nanmedian(temp)),
                        "balancing_any_fraction": float(np.mean(np.any(abs(balance)>.01, axis=1))),
                        "current_abs_gt_5A_fraction": float(np.mean(abs(current)>=5.)),
                        "positive_5A_completed_events": len(events),
                        "nonpositive_time_steps": int((dt<=0).sum()),
                        "gaps_gt_60s": int((dt>60).sum()),
                        "capacity_label_available": False,
                        "eligible_for_P1_model": False})
        print(system, "events", len(events), "temp_valid", records[-1]["temperature_sensor_valid_fraction"], flush=True)
    pd.DataFrame(records).to_csv(TASK / "runs/M5_tu_prefix_diagnostics.csv", index=False)


if __name__ == "__main__":
    main()
