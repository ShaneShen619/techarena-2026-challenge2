"""Independent formula replay, provenance check and online replay cross-check.

This intentionally does not import the candidate RidgeFeatureModel or the
candidate's acceptance scorer. It verifies raw/source hashes, repeats matrix
arithmetic over cached features, checks each target and physical event, and
checks the separate full 180-target packaged input-to-score online replay.
It is not an independently coded raw feature builder or independent refit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]


def feature_matrix(features: pd.DataFrame, age: pd.DataFrame) -> pd.DataFrame:
    key = ["cell_id", "target_ordinal"]
    data = features.merge(age[key+["qualified_charge_efc"]], on=key, validate="one_to_one")
    data["age_fraction"] = data.qualified_charge_efc/5500.
    data["age_fraction_sq"] = data.age_fraction**2
    data["cc_ratio"] = np.log(data.recent_cc_Ah/data.initial_cc_Ah)
    logratios = data[[f"w{i:02d}_logratio" for i in range(24)]].to_numpy(float)
    data["temp_interaction"] = data.delta_temp_C*logratios.mean(axis=1)
    for width, indices in (("0.04V", range(0, 9)), ("0.07V", range(9, 17)),
                           ("0.10V", range(17, 24))):
        w = logratios[:, list(indices)]
        data[f"{width}_mean"] = w.mean(axis=1)
        data[f"{width}_std"] = w.std(axis=1)
        data[f"{width}_slope"] = w[:, -1]-w[:, 0]
    return data


def independent_coverage(panel: pd.DataFrame, features: pd.DataFrame,
                         evidence: pd.DataFrame) -> dict:
    panel = panel.sort_values(["cell_id", "target_discharge_start"]).copy()
    panel["left"] = panel.groupby("cell_id").target_discharge_start.shift(1).fillna(panel.anchor_discharge_start)
    feat = features.set_index(["cell_id", "target_cycle"])
    grouped = {(c, int(k)): group for (c, k), group in evidence.groupby(["cell_id", "target_cycle"])}
    seen = set()
    flags = []
    for row in panel.itertuples(index=False):
        sub = grouped.get((row.cell_id, int(row.target_cycle)))
        recent = set(str(feat.loc[(row.cell_id, int(row.target_cycle)), "recent_event_ids"]).split("|#|"))
        valid = False
        for ev in sub.itertuples(index=False) if sub is not None else ():
            end = pd.Timestamp(ev.event_end)
            key = (row.cell_id, str(ev.event_id))
            if key in seen:
                continue
            if not (pd.Timestamp(row.left) <= end < pd.Timestamp(row.target_discharge_start)):
                continue
            if not (bool(ev.quality_pass) and bool(ev.used_for_update) and not bool(ev.reference_only)):
                continue
            if str(ev.event_id) not in recent:
                continue
            seen.add(key)
            valid = True
        flags.append({"cell_id": row.cell_id, "target_cycle": int(row.target_cycle), "covered": valid})
    flags = pd.DataFrame(flags)
    return {"overall": float(flags.covered.mean()),
            "per_cell": flags.groupby("cell_id").covered.mean().to_dict(),
            "distinct_event_ids": len(seen)}


def main() -> None:
    manifest = json.loads((TASK / "runs/M7_frozen_manifest.json").read_text())
    root = TASK.parents[1]
    for item in manifest["files"]:
        file = TASK / item["path"]
        if hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"]:
            raise AssertionError(f"frozen input changed: {item['path']}")
    for item in manifest["raw_p1_files"]:
        file = root / item["path"]
        if hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"]:
            raise AssertionError(f"raw P1 input changed: {item['path']}")
    label = manifest["label_source"]
    if hashlib.sha256(Path(label["path"]).read_bytes()).hexdigest() != label["sha256"]:
        raise AssertionError("external P1 label rule changed")
    inventory = manifest["label_inventory"]
    if hashlib.sha256((root / inventory["path"]).read_bytes()).hexdigest() != inventory["sha256"]:
        raise AssertionError("P1 label inventory changed")
    panel = pd.read_csv(TASK / "outputs/panel_main.csv", parse_dates=["target_discharge_start", "anchor_discharge_start"])
    features = pd.read_csv(TASK / "runs/M4_feature_audit_v1/features.csv")
    age = pd.read_csv(TASK / "runs/M4_feature_audit_v1/throughput.csv")
    data = feature_matrix(features, age)
    data = data.merge(panel[["cell_id", "target_ordinal", "anchor_soh_pp"]],
                      on=["cell_id", "target_ordinal"], validate="one_to_one")
    frozen = json.loads((TASK / "runs/M4_multi_efc_T_v1/fold_models.json").read_text())
    predictions = pd.read_csv(TASK / "outputs/predictions.csv")
    final = predictions.loc[predictions.method.eq("final")]
    old = predictions.loc[predictions.method.eq("A_old")]
    fixed = predictions.loc[predictions.method.eq("B_multi_noT")]
    if any(len(x) != 180 for x in (panel, data, final, old, fixed)):
        raise AssertionError("incomplete frozen panel/method")
    rebuilt = []
    for cell in sorted(panel.cell_id.unique()):
        subset = data.loc[data.cell_id.eq(cell)].sort_values("target_ordinal")
        weights = frozen[cell]["model"]
        assert cell not in weights["training_cells"] and len(weights["training_cells"]) == 5
        matrix = subset[weights["columns"]].to_numpy(float)
        mean = np.asarray(weights["feature_mean"], float)
        scale = np.asarray(weights["feature_scale"], float)
        coefs = np.asarray(weights["coefficients"], float)
        values = (subset.anchor_soh_pp.to_numpy(float)+float(weights["response_mean"])+
                  np.clip((matrix-mean)/scale, -6., 6.)@coefs)
        for target, estimate in zip(subset.itertuples(index=False), values):
            rebuilt.append({"cell_id": cell, "target_ordinal": int(target.target_ordinal),
                            "target_cycle": int(target.target_cycle),
                            "independent_prediction_pp": float(estimate)})
    built = pd.DataFrame(rebuilt)
    comparison = built.merge(final[["cell_id", "target_ordinal", "prediction_soh_pp"]],
                             on=["cell_id", "target_ordinal"], validate="one_to_one")
    max_diff = float(np.max(np.abs(comparison.independent_prediction_pp-comparison.prediction_soh_pp)))
    if max_diff > 1e-9:
        raise AssertionError(f"independent formula differs from final predictions by {max_diff}")
    online = pd.read_csv(TASK / "runs/M7_online_replay_v1/predictions.csv")
    if len(online) != 180 or not np.isfinite(online.difference_pp).all():
        raise AssertionError("online adapter replay incomplete")
    online_max = float(online.difference_pp.abs().max())
    if online_max > 1e-9:
        raise AssertionError(f"delivered online adapter differs by {online_max}")
    scored = comparison.merge(panel[["cell_id", "target_ordinal", "target_soh_pp"]],
                              on=["cell_id", "target_ordinal"], validate="one_to_one")
    scored["ae"] = (scored.independent_prediction_pp-scored.target_soh_pp).abs()
    scored["se"] = (scored.independent_prediction_pp-scored.target_soh_pp)**2
    per_mae = scored.groupby("cell_id").ae.mean()
    per_rmse = np.sqrt(scored.groupby("cell_id").se.mean())
    old_join = old.merge(panel[["cell_id", "target_ordinal", "target_soh_pp"]],
                         on=["cell_id", "target_ordinal"])
    old_mae = old_join.assign(ae=(old_join.prediction_soh_pp-old_join.target_soh_pp).abs()).groupby("cell_id").ae.mean().mean()
    fixed_join = fixed.merge(panel[["cell_id", "target_ordinal", "target_soh_pp"]],
                             on=["cell_id", "target_ordinal"])
    fixed_mae = fixed_join.assign(ae=(fixed_join.prediction_soh_pp-fixed_join.target_soh_pp).abs()).groupby("cell_id").ae.mean().mean()
    evidence = pd.read_csv(TASK / "outputs/evidence_events.csv")
    coverage = independent_coverage(panel, features, evidence)
    stress = pd.read_csv(TASK / "outputs/temperature_stress.csv")
    stress_metrics = {}
    for name in ("bias_+1C", "bias_-1C"):
        subset = stress.loc[stress.scenario.eq(name)]
        if len(subset) != 180:
            raise AssertionError("hard temperature scenario incomplete")
        values = subset.merge(panel[["cell_id", "target_cycle", "target_soh_pp"]],
                              on=["cell_id", "target_cycle"], validate="one_to_one")
        mae = values.assign(ae=(values.prediction_soh_pp-values.target_soh_pp).abs()).groupby("cell_id").ae.mean().mean()
        stress_metrics[name] = {"macro_mae_pp": float(mae),
                                "increase_over_clean_pp": float(mae-per_mae.mean())}
    panel_sha = next(x["sha256"] for x in manifest["files"] if x["path"] == "outputs/panel_main.csv")
    report = {"development_data_only": True, "panel_sha256": panel_sha,
              "scope": "independent formula replay over cached features; full packaged online input replay checked",
              "formula_replay_max_abs_diff_pp": max_diff, "online_replay_max_abs_diff_pp": online_max,
              "macro_mae_pp": float(per_mae.mean()), "macro_rmse_pp": float(per_rmse.mean()),
              "worst_cell_mae_pp": float(per_mae.max()), "p95_abs_error_pp": float(scored.ae.quantile(.95)),
              "max_abs_error_pp": float(scored.ae.max()),
              "old_a_macro_mae_pp": float(old_mae), "fixed_noT_macro_mae_pp": float(fixed_mae),
              "old_a_reduction_fraction": float(1.-per_mae.mean()/old_mae),
              "coverage": coverage, "stress": stress_metrics}
    (TASK / "outputs/M7_independent_recompute.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
