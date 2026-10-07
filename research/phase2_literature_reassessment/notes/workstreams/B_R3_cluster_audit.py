"""Read-only audit of the independent unit in frozen R3 voltage scores."""
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "research/phase2_method_exploration/runs/M1_voltage_forecast_v1/forward_voltage_predictions.csv"
SCORES = ROOT / "research/phase2_next_round/outputs/r3_voltage_scores_all.csv"
OUTPUT = Path(__file__).with_suffix(".json")

pred = pd.read_csv(SOURCE)
scores = pd.read_csv(SCORES).set_index("method")
pred["abs_mV"] = pred["error_mV"].abs()
for method in ("fixed_ECM", "matched_last_shift"):
    rows = pred[pred["method"] == method]
    assert len(rows) == int(scores.loc[method, "points"])
    assert np.isclose(rows["abs_mV"].mean(), float(scores.loc[method, "MAE_mV"]))
ev = pred.groupby(["start", "cell", "method"], as_index=False)["abs_mV"].mean()
wide = ev.pivot(index=["start", "cell"], columns="method", values="abs_mV")
wide["advantage_mV"] = wide["fixed_ECM"] - wide["matched_last_shift"]
paired = wide["advantage_mV"].dropna().reset_index()
pack = paired.groupby("start", as_index=False)["advantage_mV"].mean()

rng = np.random.default_rng(20260929)
boot = 10000
values = paired["advantage_mV"].to_numpy()
pack_values = pack["advantage_mV"].to_numpy()
naive = rng.choice(values, size=(boot, len(values)), replace=True).mean(axis=1)
clustered = rng.choice(pack_values, size=(boot, len(pack_values)), replace=True).mean(axis=1)

out = {
    "source": str(SOURCE),
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "published_scores_source": str(SCORES),
    "published_scores_sha256": hashlib.sha256(SCORES.read_bytes()).hexdigest(),
    "physical_pack_pulses": int(len(pack_values)),
    "cell_events": int(len(values)),
    "cell_events_per_pack_pulse": paired.groupby("start").size().value_counts().sort_index().to_dict(),
    "mean_advantage_mV": float(values.mean()),
    "naive_cell_event_bootstrap_95pct_mV": np.quantile(naive, [0.025, 0.975]).tolist(),
    "pack_pulse_cluster_bootstrap_95pct_mV": np.quantile(clustered, [0.025, 0.975]).tolist(),
    "naive_interval_width_mV": float(np.diff(np.quantile(naive, [0.025, 0.975]))[0]),
    "cluster_interval_width_mV": float(np.diff(np.quantile(clustered, [0.025, 0.975]))[0]),
    "bootstrap_replicates": boot,
    "seed": 20260929,
    "interpretation": "Shared current and same pulse start make four cell events one physical pack pulse. Existing R3 summary already bootstrapped pulse starts, which is the appropriate unit. Neither interval concerns capacity SOH.",
}
OUTPUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(out, ensure_ascii=False, indent=2))
