"""Read-only CK0 measurement-chain audit; scenario sensitivity is not instrument spec."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / "runs" / "L0_measurement_20260929"
CK0 = ROOT / "data" / "checkups" / "CK0_reference_discharge.csv.gz"
SEG1 = ROOT / "data" / "operation" / "segment_01_45degC.csv.gz"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ck = pd.read_csv(CK0, parse_dates=["timestamp"])
    op = pd.read_csv(SEG1, parse_dates=["timestamp"])
    dt = ck["timestamp"].diff().dt.total_seconds().dropna()
    v_sum = ck[[f"cell{i}_V" for i in range(1, 5)]].sum(axis=1)
    v_delta_mv = (ck["voltage_V"] - v_sum) * 1000
    duration_h = (ck["timestamp"].iloc[-1] - ck["timestamp"].iloc[0]).total_seconds() / 3600
    capacity = float(ck["discharged_Ah"].iloc[-1] - ck["discharged_Ah"].iloc[0])
    op_dt = op["timestamp"].diff().dt.total_seconds().dropna()
    # Hypothetical fixed bias over the reference-discharge duration; no measured error spec supplied.
    scenarios = [{"current_bias_A_assumed": bias,
                  "capacity_error_Ah": bias * duration_h,
                  "soh_error_pp": 100 * bias * duration_h / 102}
                 for bias in (0.005, 0.01, 0.05, 0.1)]
    result = {
        "run_id": "L0_measurement_20260929", "ck0_sha256": sha256(CK0),
        "segment01_sha256": sha256(SEG1),
        "ck0_rows": len(ck), "ck0_duration_h": duration_h,
        "ck0_curve_discharged_Ah": capacity, "released_capacity_Ah": 100.41,
        "ck0_current_median_A": float(ck["current_A"].median()),
        "ck0_duplicate_timestamps": int(ck["timestamp"].duplicated().sum()),
        "ck0_dt_seconds_counts": {str(k): int(v) for k, v in dt.value_counts().head(8).items()},
        "ck0_pack_minus_cell_sum_mV_median": float(v_delta_mv.median()),
        "ck0_pack_minus_cell_sum_mV_p01": float(v_delta_mv.quantile(.01)),
        "ck0_pack_minus_cell_sum_mV_p99": float(v_delta_mv.quantile(.99)),
        "ck0_pack_minus_cell_sum_mV_at_first_cutoff": float(v_delta_mv.iloc[-1]),
        "segment01_rows": len(op),
        "segment01_duplicate_timestamps": int(op["timestamp"].duplicated().sum()),
        "segment01_dt_gt_10s_count": int((op_dt > 10).sum()),
        "segment01_dt_max_s": float(op_dt.max()),
        "current_bias_scenarios_are_assumptions": scenarios,
        "limits": "No instrument accuracy/synchronization/repeatability specifications; scenarios are propagation examples, not observed errors."
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
