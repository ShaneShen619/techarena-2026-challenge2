"""Execute all frozen hard-test groups and emit auditable exit-code receipts."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
LOG_DIR = TASK / "runs/M6_hard_tests_v1"


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    groups = {}
    commands = {
        "causality": [sys.executable, str(TASK / "scripts/hard_checks.py"), "causality"],
        "isolation": [sys.executable, str(TASK / "scripts/hard_checks.py"), "isolation"],
        "math": [sys.executable, str(TASK / "scripts/hard_checks.py"), "math"],
        "event_quality": [sys.executable, "-m", "pytest", str(TASK / "tests"), "-q"],
        "serialization": [sys.executable, str(TASK / "candidates/multi_temp/validate_submission.py")],
        "official_interface": [sys.executable, str(TASK / "scripts/hard_checks.py"), "official_interface"],
        "synthetic_truth": [sys.executable, str(TASK / "scripts/hard_checks.py"), "synthetic_truth"],
    }
    for group, command in commands.items():
        started = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        log_path = LOG_DIR / f"{group}.log"
        log_path.write_text("COMMAND: "+" ".join(command)+"\n"+
                            "STDOUT:\n"+result.stdout+"\nSTDERR:\n"+result.stderr+"\n")
        groups[group] = {"exit_code": result.returncode,
                         "log": str(log_path.relative_to(TASK)),
                         "seconds": time.monotonic()-started}
        print(group, "exit", result.returncode, "seconds", round(groups[group]["seconds"], 2), flush=True)
    output = {"runner": str(Path(__file__).relative_to(ROOT)), "groups": groups}
    (TASK / "outputs/hard_tests.json").write_text(json.dumps(output, indent=2)+"\n")
    if any(x["exit_code"] != 0 for x in groups.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
