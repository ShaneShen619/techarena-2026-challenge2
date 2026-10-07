"""Normalize point predictions and independently recompute tier-separated scores."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
OUT = TASK / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
chunks = []


def add(frame, run, tier, entity, target, method, truth, pred, unit, protocol, budget, seed=None):
    d = frame.copy()
    required = [entity, target, method, truth, pred]
    assert all(c in d for c in required), (run, [c for c in required if c not in d])
    o = pd.DataFrame({"run_id": run, "tier": tier, "entity": d[entity].astype(str),
        "target_id": d[target].astype(str), "method": d[method].astype(str),
        "seed": d[seed].astype(str) if seed else "frozen",
        "unit": unit, "label_protocol": protocol, "input_budget": budget,
        "truth": pd.to_numeric(d[truth], errors="coerce"),
        "prediction": pd.to_numeric(d[pred], errors="coerce")})
    o["error"] = o.prediction - o.truth
    o["true_label_available"] = o.truth.notna()
    chunks.append(o)


def csv(path): return pd.read_csv(TASK / "runs" / path)


spec = [
    ("M0_ablation_replay_v1", "D0_privileged", "cell_id", "target_ordinal", "method", "target_soh_pp", "prediction_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "historical full-depth privileged"),
    ("M2_primary_v2", "D1_v14_retired", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "20Ah 3.50V 15-event persistent"),
    ("M2_spline_v1", "D1_v14_retired", "cell_id", "target_ordinal", "method", "actual_pp", "pred_pp", "SOH_pp", "P1 high-rate single-cell proxy", "20Ah 3.50V 15-event persistent"),
    ("M3_prefix_temperature_v1", "D1_v14_extra_retired", "cell_id", "target_ordinal", "method", "actual_pp", "pred_pp", "SOH_pp", "P1 high-rate single-cell proxy", "all prior full-event temperature scalar extra"),
    ("M3_static_vs_rolling_v1", "D1_v14_extra_retired", "cell_id", "target_ordinal", "method", "actual_pp", "pred_pp", "SOH_pp", "P1 high-rate single-cell proxy", "initial10 full-event temperature scalar extra"),
    ("M7_linear_representation_v1", "D1_v14_retired", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "20Ah 3.50V 15-event persistent"),
    ("M7_TCN_v1", "D1_v14_retired", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "20Ah 3.50V 15-event persistent"),
    ("M7_TCN_no_voltage_v1", "D1_v14_retired", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "20Ah 3.50V 15-event persistent no voltage"),
    ("M7_TCN_meta_only_v1", "D1_v14_retired", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "20Ah 3.50V 15-event persistent mask/meta only"),
    ("M8_D1_fusion_v1", "D1_v14_retired", "cell_id", "target_ordinal", "method", "truth_pp", "prediction_pp", "SOH_pp", "P1 high-rate single-cell proxy", "20Ah 3.50V 15-event persistent"),
    ("M9_scalar_models_v1", "D1_v14_retired", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "20Ah 3.50V scalar metadata only"),
    ("M9_prefix_temperature_v1", "D1_v14_retired", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "20Ah 3.50V allowed fragment temperature scalar"),
    ("M9_causal_postprocess_v1", "D1_v14_retired", "cell_id", "target_ordinal", "method", "truth_pp", "pred_pp", "SOH_pp", "P1 high-rate single-cell proxy", "20Ah 3.50V causal postprocess"),
    ("M9_D1_v15_M2_20Ah_persistent_v1", "D1_v15_primary", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V persistent"),
    ("M9_D1_v15_M2_15Ah_persistent_v1", "D1_v15_sensitivity", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 15Ah 3.50V persistent"),
    ("M9_D1_v15_M2_30Ah_persistent_v1", "D1_v15_sensitivity", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 30Ah 3.50V persistent"),
    ("M9_D1_v15_M2_20Ah_cold_v1", "D1_v15_sensitivity", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V cold"),
    ("M9_D1_v15_M2_3p45_20Ah_persistent_v1", "D1_v15_sensitivity", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.45V persistent"),
    ("M9_D1_v15_M2_3p55_20Ah_persistent_v1", "D1_v15_sensitivity", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.55V persistent"),
    ("M9_D1_v15_signal_ablation_3p45_v1", "D1_v15_sensitivity", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.45V voltage/current/window ablation"),
    ("M9_D1_v15_signal_ablation_3p55_v1", "D1_v15_sensitivity", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.55V voltage/current/window ablation"),
    ("M9_D1_v15_linear_v1", "D1_v15_primary", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V persistent"),
    ("M9_D1_v15_spline_v1", "D1_v15_primary", "cell_id", "target_ordinal", "method", "actual_pp", "pred_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V persistent"),
    ("M9_D1_v15_TCN_v1", "D1_v15_primary", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V persistent"),
    ("M9_D1_v15_no_voltage_v1", "D1_v15_primary", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V persistent no voltage"),
    ("M9_D1_v15_meta_only_v1", "D1_v15_primary", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V persistent mask/meta only"),
    ("M9_D1_v15_scalar_models_v1", "D1_v15_primary", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V scalar metadata only"),
    ("M9_D1_v15_prefix_temperature_v1", "D1_v15_primary", "cell_id", "target_ordinal", "method", "target_soh_pp", "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V scalar plus allowed fragment temperature"),
    ("M9_D1_v15_fusion_v2", "D1_v15_primary", "cell_id", "target_ordinal", "method", "truth_pp", "prediction_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V persistent fusion"),
]
for run, tier, ent, target, method, truth, pred, unit, protocol, budget in spec:
    file = "diagnostic_predictions.csv" if run == "M0_ablation_replay_v1" else "predictions.csv"
    frame = csv(f"{run}/{file}")
    seed = "seed" if "seed" in frame else None
    if run == "M0_ablation_replay_v1":
        frame["method"] = frame["method"] + ":" + frame["outer_group"].astype(str)
    if run == "M3_static_vs_rolling_v1":
        frame["method"] = frame["method"] + ":" + frame["split"].astype(str)
    if run == "M9_causal_postprocess_v1":
        frame["method"] = frame["source"] + ":" + frame["method"]
    if run == "M9_D1_v15_scalar_models_v1":
        frame["method"] = frame["method"] + ":seed" + frame["seed"].astype(str)
    add(frame, run, tier, ent, target, method, truth, pred, unit, protocol, budget, seed)

for run, method in [("M7_TCN_v1", "TCN_from_scratch"),
                    ("M7_TCN_no_voltage_v1", "TCN_scratch_no_voltage"),
                    ("M7_TCN_meta_only_v1", "TCN_scratch_meta_only"),
                    ("M9_scalar_models_v1", "scalar_MLP"),
                    ("M9_prefix_temperature_v1", "prefix_temperature_MLP"),
                    ("M9_D1_v15_TCN_v1", "TCN_from_scratch"),
                    ("M9_D1_v15_TCN_v1", "TCN_finetune"),
                    ("M9_D1_v15_TCN_v1", "TCN_frozen_ridge"),
                    ("M9_D1_v15_no_voltage_v1", "TCN_scratch_no_voltage"),
                    ("M9_D1_v15_meta_only_v1", "TCN_scratch_meta_only"),
                    ("M9_D1_v15_scalar_models_v1", "scalar_MLP"),
                    ("M9_D1_v15_prefix_temperature_v1", "prefix_temperature_MLP")]:
    d = csv(f"{run}/predictions.csv")
    d = d.loc[d.method.eq(method)].groupby(["cell_id", "target_ordinal"], as_index=False).agg(
        target_soh_pp=("target_soh_pp", "first"), pred_soh_pp=("pred_soh_pp", "mean"))
    d["method"] = method + "_three_seed_ensemble"
    tier = "D1_v15_primary" if run.startswith("M9_D1_v15") else "D1_v14_retired"
    add(d, run + "_ensemble", tier, "cell_id", "target_ordinal", "method", "target_soh_pp",
        "pred_soh_pp", "SOH_pp", "P1 high-rate single-cell proxy", "strict prefix 20Ah 3.50V persistent, seed ensemble" if tier == "D1_v15_primary" else "retired v1.4 20Ah 3.50V persistent, seed ensemble")

voltage_channels = []
for run in ("M1_voltage_forecast_v1", "M4_state_identifiability_v4"):
    file = "forward_voltage_predictions.csv" if run.startswith("M1") else "official_forward_predictions.csv"
    d = csv(f"{run}/{file}")
    d["entity"] = "official_4S"
    d["target"] = d["start"].astype(str) + ":cell" + d["cell"].astype(str) + ":" + d["q_Ah"].astype(str)
    d["truth_mV"] = d.actual_V * 1000
    d["prediction_mV"] = d.predicted_V * 1000
    add(d, run, "D3_voltage_only", "entity", "target", "method", "truth_mV", "prediction_mV",
        "mV", "official future pulse voltage, no capacity label", "past certified pulses only")
    for (method, channel), part in d.groupby(["method", "cell"]):
        voltage_channels.append({"run_id": run, "method": method, "cell_channel": channel,
                                 "physical_pack_entities": 1, "n_voltage_samples": len(part),
                                 "MAE_mV": float(np.mean(abs(part.prediction_mV-part.truth_mV)))})
pd.DataFrame(voltage_channels).to_csv(OUT / "official_voltage_channel_scores.csv", index=False)

d = csv("M6_workpoint_time_v5/LOSO_online_predictions.csv")
d["target"] = d["timestamp"].astype(str) + ":cell" + d["cell"].astype(str)
add(d, "M6_workpoint_time_v5", "TU_resistance_only", "held_system", "target", "method",
    "actual_R_mOhm", "pred_R_mOhm", "mOhm", "TU step resistance proxy, no capacity label",
    "whole-system holdout; target chronological prefix")

d = csv("M5_pack_v1/synthetic_pack_predictions.csv")
d["target"] = d.family.astype(str) + ":" + d.scenario.astype(str) + ":" + d.information.astype(str)
d["method"] = d.information.astype(str) + ":" + d.method.astype(str)
add(d, "M5_pack_v1", "S_pack", "scenario", "target", "method", "truth_group_capacity_Ah",
    "prediction_Ah", "Ah", "constructed four-series cutoff", "synthetic true/noisy states")

d = csv("M8_pack_fusion_v2/predictions.csv")
# Weight selection and interval calibration used scenarios 0–299. Only the
# separately held 300–599 scenarios belong in the development-test comparison.
d = d.loc[d.scenario.between(300, 599)].copy()
assert d.scenario.nunique() == 300
d["target"] = d.scenario.astype(str) + ":" + d.quality.astype(str)
d["method"] = d.quality.astype(str) + ":" + d.method.astype(str)
add(d, "M8_pack_fusion_v2", "S_pack", "scenario", "target", "method", "truth_Ah", "prediction_Ah",
    "Ah", "constructed four-series cutoff", "synthetic injected quality; weight first200/calibration next100/test last300")

d = pd.read_csv(OUT / "official_predictions.csv")
d["target"] = d.checkup
d["entity"] = "official_4S"
add(d, "M9_official_replay_v1", "D3_capacity_hidden", "entity", "target", "method", "true_SOH_pp",
    "SOH_est_pp", "SOH_pp", "official 4S C/20; CK1-CK7 hidden", "strict prefix through each CK")

long = pd.concat(chunks, ignore_index=True)
# The D0/D1 scorer does not trust the label field embedded in any run file.
# It reopens the frozen P1 panel, verifies the hash, and demands the complete
# 180-key set for every method/seed, including failed and sensitivity runs.
panel_path = ROOT / "research/phase2_temperature_improvement/outputs/panel_main.csv"
assert hashlib.sha256(panel_path.read_bytes()).hexdigest() == "7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c"
panel = pd.read_csv(panel_path, usecols=["cell_id", "target_ordinal", "target_soh_pp"])
panel["target_ordinal"] = panel.target_ordinal.astype(str)
assert len(panel) == 180 and not panel.duplicated(["cell_id", "target_ordinal"]).any()
d1mask = (long.tier.eq("D0_privileged") | long.tier.str.startswith("D1_"))
expected = set(zip(panel.cell_id, panel.target_ordinal))
for (run, method, seed), part in long.loc[d1mask].groupby(["run_id", "method", "seed"]):
    observed = list(zip(part.entity, part.target_id))
    if len(observed) != 180 or len(set(observed)) != 180 or set(observed) != expected:
        raise AssertionError(f"incomplete or duplicate D0/D1 target set: {run}:{method}:{seed}")
reference = long.loc[d1mask, ["entity", "target_id", "truth"]].merge(
    panel, left_on=["entity", "target_id"], right_on=["cell_id", "target_ordinal"],
    how="left", validate="many_to_one", sort=False)
if reference.target_soh_pp.isna().any() or np.max(abs(reference.truth-reference.target_soh_pp)) > 1e-4:
    raise AssertionError("D0/D1 run-embedded label disagrees with frozen panel")
long.loc[d1mask, "truth"] = reference.target_soh_pp.to_numpy(float)
long.loc[d1mask, "error"] = long.loc[d1mask, "prediction"] - long.loc[d1mask, "truth"]
assert np.isfinite(long.prediction.to_numpy(float)).all()
assert np.isfinite(long.loc[long.true_label_available, "error"].to_numpy(float)).all()
long.to_csv(OUT / "predictions_long.csv", index=False)
comp = []
for (tier, run, method, seed, unit, protocol, budget), part in long.groupby(
    ["tier", "run_id", "method", "seed", "unit", "label_protocol", "input_budget"], dropna=False):
    entities = part.entity.nunique()
    has_capacity = tier.startswith("D1_") or tier == "D0_privileged"
    labelled = part.loc[part.true_label_available]
    if tier == "D3_capacity_hidden":
        macro = worst = maximum = np.nan
        status = "CK1-CK7 capacity hidden; no accuracy score"
    elif len(labelled) == 0:
        macro = worst = maximum = np.nan
        status = "no scoreable labels"
    else:
        per = labelled.assign(abs_error=labelled.error.abs()).groupby("entity").abs_error.mean()
        macro, worst, maximum = float(per.mean()), float(per.max()), float(labelled.error.abs().max())
        status = ("D1 v1.5 six-cell development only" if tier.startswith("D1_v15") else "retired retrospective D1 v1.4" if tier.startswith("D1_v14") else "D0 historical development") if has_capacity else "signal only" if tier in ("D3_voltage_only", "TU_resistance_only") else "synthetic mechanism only"
    comp.append({"tier": tier, "run_id": run, "method": method, "seed": seed,
                 "unit": unit, "label_protocol": protocol, "input_budget": budget,
                 "physical_entities": entities, "prediction_rows": len(part),
                 "capacity_truth_rows": int(part.true_label_available.sum()) if unit in ("Ah", "SOH_pp") else 0,
                 "macro_MAE": macro, "worst_entity_MAE": worst, "max_abs_error": maximum,
                 "validation_status": status, "source": "outputs/predictions_long.csv"})
comparison = pd.DataFrame(comp)
comparison.to_csv(OUT / "method_comparison.csv", index=False)
summary = {"long_rows": len(long), "comparison_rows": len(comparison),
           "D1_v15_primary_methods": int(comparison.tier.eq("D1_v15_primary").sum()),
           "hidden_capacity_rows": int(long.tier.eq("D3_capacity_hidden").sum()),
           "official_capacity_accuracy_verified": False,
           "warning": "Never rank different tiers or units by a single MAE; D1 is reused six-cell development."}
(TASK / "runs/M9_official_replay_v1/compiled_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False), flush=True)
