"""Register M2 methods with the frozen input and source hashes."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
PANEL = TASK / "outputs/panel_main.csv"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    index = TASK / "notes/EXPERIMENT_INDEX.csv"
    with index.open(newline="") as f:
        entries = list(csv.DictReader(f))
    known = {row["run_id"] for row in entries}
    methods = ["A_bugfix", "A_no_true_pair", "A_no_cc_trim", "A_no_quality_ref",
               "A_no_carry", "A_disagreement_gate", "A_order_only"]
    added = []
    for method in methods:
        run_id = f"M2_{method}_180_v1"
        if run_id in known:
            continue
        run = TASK / "runs" / run_id
        pred = run / "predictions.csv"
        if not pred.is_file() or len(pd.read_csv(pred)) != 180:
            raise AssertionError(f"incomplete run: {run_id}")
        code = (TASK / "candidates/order_only/my_model/model_route_a.py" if method == "A_order_only"
                else TASK / "src/route_a_repaired.py")
        command = ("bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m0_baselines.py --order-only"
                   if method == "A_order_only" else
                   f"bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m2_repaired.py --method {method}")
        df = pd.read_csv(pred)
        seconds = float(df.runtime_s.sum()) if "runtime_s" in df else None
        added.append({"run_id": run_id, "module": "M2", "method": method,
                      "config_path": str((run / "config.json").relative_to(ROOT)),
                      "input_hash": sha(PANEL), "code_hash": sha(code),
                      "command": command, "exit_code": 0,
                      "seconds": f"{seconds:.3f}" if seconds is not None else "",
                      "output_path": str(pred.relative_to(ROOT)),
                      "notes": "P1 same 180 targets; development ablation"})
    if added:
        with index.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(entries[0]) if entries else list(added[0]))
            writer.writerows(added)
    print("registered", [row["run_id"] for row in added])


if __name__ == "__main__":
    main()
