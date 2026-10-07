"""Fresh causal event-history replay with frozen six outer-fold models.

The ±1°C scenarios are the hard sensor-bias acceptance runs.  Each scenario
starts with empty event/state caches and recomputes initial/recent features
and newly-used evidence from the perturbed event history at every cutoff.
Current/voltage-derived event boundaries and Ah are temperature invariant;
temperature is perturbed before event selection and feature construction.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
RUN = TASK / "runs/M6_event_stress_v1"
sys.path.insert(0, str(TASK / "src"))
from multi_window_ridge import RidgeFeatureModel, add_derived_features  # noqa: E402
from thermal_surface import effective_temperature  # noqa: E402

SCENARIOS = ("clean_event_replay", "bias_+1C", "bias_-1C", "drift_+3C", "stuck_35C", "random_missing_20pct",
             "contiguous_missing_20pct", "temperature_event_shift_1")


def deterministic_missing(event_id: str) -> bool:
    number = int(hashlib.sha256(("20260928|"+event_id).encode()).hexdigest()[:12], 16)
    return number % 100 < 20


def temperatures(frame: pd.DataFrame, scenario: str) -> pd.DataFrame:
    out = frame.copy().sort_values("event_end").reset_index(drop=True)
    if scenario == "bias_+1C":
        out["temp_C"] += 1.
    elif scenario == "bias_-1C":
        out["temp_C"] -= 1.
    elif scenario == "drift_+3C":
        out["temp_C"] += 3.*np.linspace(0., 1., len(out))
    elif scenario == "stuck_35C":
        out["temp_C"] = 35.
    elif scenario == "random_missing_20pct":
        out.loc[out.event_id.map(deterministic_missing), "temp_C"] = np.nan
    elif scenario == "contiguous_missing_20pct":
        out.loc[int(.4*len(out)):int(.6*len(out)), "temp_C"] = np.nan
    elif scenario == "temperature_event_shift_1":
        out["temp_C"] = np.r_[out.temp_C.iloc[0], out.temp_C.to_numpy(float)[:-1]]
    return out


def feature_from_events(visible: pd.DataFrame, target, fallback_temp: float) -> dict | None:
    keep = visible.loc[np.isfinite(visible.temp_C)].sort_values("event_end")
    if len(keep) < 2:
        return None
    initial = keep.head(min(10, len(keep)))
    recent = keep.tail(min(5, len(keep)))
    cutoff = pd.Timestamp(target.target_discharge_start)
    row = {"anchor_soh_pp": float(target.anchor_soh_pp),
           "qualified_charge_efc": float(keep.total_Ah.sum()/102.),
           "event_age_days": (cutoff-recent.event_end.iloc[-1]).total_seconds()/86400,
           "temp_C": float(recent.temp_C.median()) if len(recent) else fallback_temp,
           "initial_temp_C": float(initial.temp_C.median()) if len(initial) else fallback_temp,
           "delta_current_rel": float(recent.current_A.median()/initial.current_A.median()-1),
           "recent_cc_Ah": float(recent.cc_Ah.median()),
           "initial_cc_Ah": float(initial.cc_Ah.median()),
           "recent_event_ids": "|#|".join(recent.event_id.astype(str)),
           "input_end": recent.event_end.iloc[-1].isoformat()}
    row["delta_temp_C"] = row["temp_C"]-row["initial_temp_C"]
    for wi in range(24):
        name = f"w{wi:02d}"
        early = initial[name].dropna()
        now = recent[name].dropna()
        if len(early) == 0 or len(now) == 0:
            return None
        e = float(early.median()); n = float(now.median())
        if e <= 0 or n <= 0:
            return None
        row[f"{name}_logratio"] = float(np.log(n/e))
    return row


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    event_table = pd.read_csv(TASK / "runs/M4_feature_audit_v1/events.csv", parse_dates=["event_end"])
    logs = pd.read_csv(TASK / "runs/M2_A_bugfix_180_v1/evidence_events.csv")
    panel = pd.read_csv(TASK / "outputs/panel_main.csv")
    frozen = json.loads((TASK / "runs/M4_multi_efc_T_v1/fold_models.json").read_text())
    folds = {x["heldout_cell"]: x for x in json.loads((TASK / "runs/M3_B_age_sixfold_v2/folds.json").read_text())}
    records = []
    for cell in sorted(panel.cell_id.unique()):
        targets = panel.loc[panel.cell_id.eq(cell)].sort_values("target_ordinal")
        events = event_table.loc[event_table.cell_id.eq(cell)].copy()
        subset_logs = logs.loc[logs.cell_id.eq(cell)]
        model = RidgeFeatureModel(**frozen[cell]["model"])
        match = re.fullmatch(r"102Ah_(\d+)degC_(0p5C|1C)_cell\d+", cell)
        assert match is not None
        nominal = int(match.group(1)); rate = .5 if match.group(2) == "0p5C" else 1.
        fallback_temp = float(effective_temperature(folds[cell]["temperature_theta_train_only"], nominal, rate))
        for scenario in SCENARIOS:
            perturbed = temperatures(events, scenario).set_index("event_id", drop=False)
            seen_ids: set[str] = set()
            previous = pd.Timestamp(targets.anchor_discharge_start.iloc[0])
            for target in targets.itertuples(index=False):
                new = subset_logs.loc[subset_logs.target_cycle.eq(int(target.target_cycle))]
                seen_ids.update(str(x) for x in new.event_id)
                visible = perturbed.loc[perturbed.index.isin(seen_ids)].copy()
                cutoff = pd.Timestamp(target.target_discharge_start)
                if not visible.event_end.lt(cutoff).all():
                    raise AssertionError("future event in stress replay")
                row = feature_from_events(visible, target, fallback_temp)
                if row is None:
                    estimate = float(target.anchor_soh_pp)
                    mode = "insufficient_or_missing_window"
                    recent_ids = set()
                else:
                    frame = add_derived_features(pd.DataFrame([row]), age_col="qualified_charge_efc")
                    estimate = float(model.predict(frame)[0])
                    mode = "ridge_event_replay"
                    recent_ids = set(str(row["recent_event_ids"]).split("|#|"))
                used_new = [str(ev.event_id) for ev in new.itertuples(index=False)
                            if str(ev.event_id) in recent_ids and bool(ev.used_for_update) and
                            pd.Timestamp(ev.event_end) >= previous and pd.Timestamp(ev.event_end) < cutoff]
                records.append({"run_id": RUN.name, "scenario": scenario, "cell_id": cell,
                                "target_cycle": int(target.target_cycle),
                                "target_ordinal": int(target.target_ordinal),
                                "prediction_soh_pp": estimate,
                                "target_soh_pp_diagnostic": float(target.target_soh_pp),
                                "mode": mode, "n_new_evidence_events": len(set(used_new)),
                                "new_evidence_ids": "|#|".join(sorted(set(used_new))),
                                "input_end": row["input_end"] if row is not None else "",
                                "temperature_bias_C": (1. if scenario == "bias_+1C" else
                                                       -1. if scenario == "bias_-1C" else 0.)})
                previous = cutoff
            print(cell, scenario, "done", flush=True)
        pd.DataFrame(records).to_csv(RUN / "predictions.partial.csv", index=False)
    out = pd.DataFrame(records)
    out.to_csv(RUN / "predictions.csv", index=False)
    summary = out.assign(ae=(out.prediction_soh_pp-out.target_soh_pp_diagnostic).abs()).groupby(
        "scenario", sort=False).apply(lambda g: pd.Series({
            "macro_mae_pp": float(g.groupby("cell_id").ae.mean().mean()),
            "p95_abs_pp": float(g.ae.quantile(.95)), "max_abs_pp": float(g.ae.max()),
            "evidence_coverage": float((g.n_new_evidence_events>0).mean()),
            "fallback_fraction": float(g["mode"].ne("ridge_event_replay").mean()),
            "n": len(g)}), include_groups=False).reset_index()
    summary.to_csv(RUN / "summary.csv", index=False)
    hard = out.loc[out.scenario.isin(("clean_event_replay", "bias_+1C", "bias_-1C"))].copy()
    hard.loc[hard.scenario.eq("clean_event_replay"), "scenario"] = "clean"
    hard.to_csv(TASK / "outputs/temperature_stress.csv", index=False)
    event_end = event_table.set_index("event_id").event_end
    evidence_rows = []
    for pred in hard.itertuples(index=False):
        if not isinstance(pred.new_evidence_ids, str) or not pred.new_evidence_ids:
            continue
        for event_id in pred.new_evidence_ids.split("|#|"):
            evidence_rows.append({"run_id": RUN.name, "method": "final", "cell_id": pred.cell_id,
                                  "target_cycle": int(pred.target_cycle), "event_id": event_id,
                                  "event_end": event_end.loc[event_id].isoformat(),
                                  "quality_pass": True, "reference_only": False,
                                  "used_for_update": True,
                                  "reason": "freshly replayed qualified event in recent-five feature",
                                  "scenario": pred.scenario})
    pd.DataFrame(evidence_rows).to_csv(TASK / "outputs/temperature_stress_evidence.csv", index=False)
    print(summary.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
