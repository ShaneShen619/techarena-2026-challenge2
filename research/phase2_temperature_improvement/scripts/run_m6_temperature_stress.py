"""Frozen-model sensor-bias replay for the P1 six-cell panel.

Uniform bias on the *entire visible history* is algebraically equivalent to
adding that bias to both early and recent event medians.  Event qualification
depends on finiteness, current, and voltage, so ±1°C preserves the clean
event set.  The stress run refits neither coefficients nor gates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
RUN = TASK / "runs/M6_temperature_stress_v1"
sys.path.insert(0, str(TASK / "src"))
sys.path.insert(0, str(TASK / "scripts"))
from multi_window_ridge import RidgeFeatureModel, add_derived_features  # noqa: E402
from register_final_candidate import make_evidence  # noqa: E402


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    features = pd.read_csv(TASK / "runs/M4_feature_audit_v1/features.csv")
    efc = pd.read_csv(TASK / "runs/M4_feature_audit_v1/throughput.csv")
    panel = pd.read_csv(TASK / "outputs/panel_main.csv")
    key = ["cell_id", "target_ordinal"]
    data = features.merge(efc[key+["qualified_charge_efc"]], on=key, validate="one_to_one")
    data = data.merge(panel[key+["anchor_soh_pp", "target_soh_pp"]], on=key, validate="one_to_one")
    frozen = json.loads((TASK / "runs/M4_multi_efc_T_v1/fold_models.json").read_text())
    original = pd.read_csv(TASK / "runs/M4_multi_efc_T_v1/predictions.csv")
    scenarios = {"clean": 0., "bias_+1C": 1., "bias_-1C": -1.,
                 "bias_+0.5C": .5, "bias_-0.5C": -.5,
                 "bias_+2C": 2., "bias_-2C": -2.,
                 "bias_+5C": 5., "bias_-5C": -5.}
    records = []
    for scenario, bias in scenarios.items():
        replay = data.copy()
        # These two medians represent the full affected temperature history
        # used by the model.  Their difference must be recomputed, not shifted.
        replay["temp_C"] += bias
        replay["initial_temp_C"] += bias
        replay["delta_temp_C"] = replay.temp_C-replay.initial_temp_C
        replay = add_derived_features(replay, age_col="qualified_charge_efc")
        for held in sorted(frozen):
            subset = replay.loc[replay.cell_id.eq(held)].sort_values("target_ordinal")
            model = RidgeFeatureModel(**frozen[held]["model"])
            pred = model.predict(subset)
            if scenario == "clean":
                expected = original.loc[original.cell_id.eq(held)].sort_values("target_ordinal").prediction_soh_pp.to_numpy(float)
                if np.max(np.abs(pred-expected)) > 1e-9:
                    raise AssertionError("stress clean replay differs from selected fold result")
            for row, value in zip(subset.itertuples(index=False), pred):
                records.append({"run_id": RUN.name, "scenario": scenario,
                                "cell_id": held, "target_cycle": int(row.target_cycle),
                                "target_ordinal": int(row.target_ordinal),
                                "input_end": row.input_end,
                                "prediction_soh_pp": float(value),
                                "temperature_bias_C": bias,
                                "target_soh_pp_diagnostic": float(row.target_soh_pp)})
    out = pd.DataFrame(records)
    if len(out) != 180*len(scenarios):
        raise AssertionError("stress scoring panel changed")
    out.to_csv(RUN / "predictions.csv", index=False)
    out.to_csv(TASK / "outputs/temperature_stress.csv", index=False)
    logs = pd.read_csv(TASK / "runs/M2_A_bugfix_180_v1/evidence_events.csv")
    evidence = pd.concat([make_evidence(features, logs, RUN.name, scenario=name)
                          for name in scenarios], ignore_index=True)
    evidence.to_csv(TASK / "outputs/temperature_stress_evidence.csv", index=False)
    summary = out.assign(ae=(out.prediction_soh_pp-out.target_soh_pp_diagnostic).abs()).groupby(
        "scenario", sort=False).apply(lambda x: pd.Series({
            "macro_mae_pp": x.groupby("cell_id").ae.mean().mean(),
            "p95_abs_pp": x.ae.quantile(.95), "max_abs_pp": x.ae.max(),
            "n": len(x),
        }), include_groups=False).reset_index()
    summary.to_csv(RUN / "summary.csv", index=False)
    print(summary.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
