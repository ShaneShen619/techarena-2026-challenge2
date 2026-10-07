"""Compare M2 variants on the same frozen panel, including event coverage."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "scripts"))
from check_acceptance import evidence_coverage  # noqa: E402


def main() -> None:
    panel = pd.read_csv(TASK / "outputs/panel_main.csv")
    pred = pd.read_csv(TASK / "outputs/predictions.csv")
    joined = pred.merge(panel[["cell_id", "target_cycle", "target_soh_pp"]],
                        on=["cell_id", "target_cycle"], validate="many_to_one")
    joined["abs_error_pp"] = (joined.prediction_soh_pp-joined.target_soh_pp).abs()
    rows = []
    detailed = {}
    for method, frame in joined.groupby("method", sort=True):
        if len(frame) != len(panel):
            continue
        per = frame.groupby("cell_id").abs_error_pp.mean()
        output = {"method": method, "n_targets": len(frame), "macro_mae_pp": float(per.mean()),
                  "worst_cell_mae_pp": float(per.max()),
                  "p95_abs_error_pp": float(np.quantile(frame.abs_error_pp, .95)),
                  "max_abs_error_pp": float(frame.abs_error_pp.max()),
                  "per_cell_mae_pp": {str(k): float(v) for k, v in per.items()}}
        evidence_path = TASK / f"runs/M2_{method}_180_v1/evidence_events.csv"
        if evidence_path.exists():
            reasons = []
            coverage = evidence_coverage(panel, method, evidence_path, reasons)
            if reasons:
                raise AssertionError(reasons)
            output["coverage"] = coverage
            logs = pd.read_csv(evidence_path)
            output["evidence_reasons"] = {str(k): int(v) for k, v in logs.reason.value_counts().items()}
            if "carried_forward" in frame:
                output["carried_forward_fraction"] = float(frame.carried_forward.mean())
        rows.append({k: v for k, v in output.items() if not isinstance(v, dict)})
        detailed[method] = output
    if "A_old" in detailed:
        old = detailed["A_old"]["macro_mae_pp"]
        old_worst = detailed["A_old"]["worst_cell_mae_pp"]
        for name, item in detailed.items():
            item["reduction_vs_old_fraction"] = (old-item["macro_mae_pp"])/old
            item["worst_cell_reduction_vs_old_fraction"] = (old_worst-item["worst_cell_mae_pp"])/old_worst
    pd.DataFrame(rows).to_csv(TASK / "outputs/m2_method_summary.csv", index=False)
    (TASK / "outputs/m2_diagnostics.json").write_text(json.dumps(detailed, ensure_ascii=False, indent=2) + "\n")
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
