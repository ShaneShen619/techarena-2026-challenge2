"""Compile official-prefix diagnostics and a conservative deployment decision."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "outputs"
frames = [pd.read_csv(OUT / f"r6_{name}_official_prefix.csv")
          for name in ("ck0_hold", "exploratory_fallback")]
official = pd.concat(frames, ignore_index=True)
assert len(official) == 16 and official.checkup.nunique() == 8
official.to_csv(OUT / "official_prefix_diagnostics.csv", index=False)

decision = {
    "average_error_research_candidate": "R1_paired_TCN_full_v1",
    "post_audit_observed_macro_leader": "R1_paired_TCN_no_temperature_strict_v1",
    "post_audit_observed_macro_leader_selection_valid": False,
    "tail_risk_exploratory_comparator": "R1_paired_TCN_full_tail_weight2_v1",
    "tail_risk_candidate_locked": False,
    "official_safe_backup": "ck0_hold",
    "official_exploratory_candidate": "exploratory_fallback",
    "fusion_performed": False,
    "fusion_reason": "Paired ablation did not establish incremental capacity information in the voltage waveform; correlated channels therefore were not fused.",
    "quality_gate": "closed_for_capacity_update",
    "interval_status": "no_finite_group_level_coverage_guarantee",
    "official_capacity_accuracy_verified": False,
    "independent_capacity_confirmation": False,
    "selection_reason": "CK0 hold is the safer fallback under hidden truth. The exploratory branch is causal and interface-correct but makes large uncalibrated changes after CK2. Strict temperature removal and tail weighting were not selected by a nested inner-entity rule, so neither replaces the frozen full TCN research comparator.",
}
(OUT / "r6_decision.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(decision, ensure_ascii=False, indent=2))
