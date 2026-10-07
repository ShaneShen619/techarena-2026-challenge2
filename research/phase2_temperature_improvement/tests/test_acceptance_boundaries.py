from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


PATH = Path(__file__).resolve().parents[1] / "scripts/check_acceptance.py"
SPEC = importlib.util.spec_from_file_location("phase2_acceptance", PATH)
assert SPEC is not None and SPEC.loader is not None
acceptance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance)


def test_old_event_cannot_count_twice_as_new_coverage(tmp_path: Path) -> None:
    panel = pd.DataFrame({
        "cell_id": ["c", "c"], "target_cycle": [10, 20],
        "target_discharge_start": ["2021-01-10", "2021-01-20"],
        "anchor_discharge_start": ["2021-01-01", "2021-01-01"],
    })
    evidence = pd.DataFrame({
        "method": ["final", "final"], "cell_id": ["c", "c"],
        "target_cycle": [10, 20], "event_id": ["event-7", "event-7"],
        "event_end": ["2021-01-07", "2021-01-07"],
        "quality_pass": [True, True], "used_for_update": [True, True],
        "reference_only": [False, False],
    })
    path = tmp_path / "evidence.csv"
    evidence.to_csv(path, index=False)
    reasons: list[str] = []
    result = acceptance.evidence_coverage(panel, "final", path, reasons)
    assert not reasons
    assert result is not None
    assert result["fraction"] == .5
    assert result["qualified_distinct_event_ids"] == 1
