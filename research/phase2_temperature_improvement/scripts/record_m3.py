"""Register immutable M3 development runs without rewriting earlier records."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
INDEX = TASK / "notes/EXPERIMENT_INDEX.csv"
PANEL_HASH = hashlib.sha256((TASK / "outputs/panel_main.csv").read_bytes()).hexdigest()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = list(csv.DictReader(INDEX.open(newline="")))
    existing = {row["run_id"] for row in rows}
    with INDEX.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        for version, code, note in (
            ("v1", TASK / "runs/M3_B_age_sixfold_v1/source_snapshot.py",
             "prefix maximum cycle; retained failed time-order development variant"),
            ("v2", TASK / "scripts/run_m3_age_prior.py",
             "strict completed-charge prefix; all six cells excluded from their own fold fit"),
        ):
            run_id = f"M3_B_age_sixfold_{version}"
            if run_id in existing:
                continue
            run = TASK / "runs" / run_id
            if not (run / "predictions.csv").exists():
                raise FileNotFoundError(run)
            writer.writerow({
                "run_id": run_id, "module": "M3", "method": "B_age",
                "config_path": str((run / "config.json").relative_to(TASK)),
                "input_hash": PANEL_HASH, "code_hash": digest(code),
                "command": "bash research/phase2_validation/run_python.sh "
                           "research/phase2_temperature_improvement/scripts/run_m3_age_prior.py",
                "exit_code": 0, "seconds": "",
                "output_path": str((run / "predictions.csv").relative_to(TASK)),
                "notes": note,
            })


if __name__ == "__main__":
    main()
