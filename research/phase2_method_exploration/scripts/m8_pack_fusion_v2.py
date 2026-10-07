"""Quality gating and scenario-level interval calibration on synthetic M5 outputs."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/M8_pack_fusion_v2"
OUT.mkdir(parents=True, exist_ok=False)
cfg = json.loads((TASK / "configs/m8_pack_fusion_v2.json").read_text())
raw = pd.read_csv(TASK / "runs/M5_shrinkage_v1/predictions.csv")
assert raw.groupby(["scenario", "quality"]).size().eq(4).all()
wide = raw.pivot(index=["scenario", "quality"], columns="method", values="pred_Ah").reset_index()
truth = raw.groupby(["scenario", "quality"], as_index=False).truth_group_Ah.first()
d = wide.merge(truth, on=["scenario", "quality"], validate="one_to_one")
assert d.scenario.nunique() == 600 and d.groupby("quality").size().eq(600).all()
d = d.rename(columns={"uniform_mean_cell": "uniform", "explicit_four_cell": "explicit",
                      "noise_aware_shrunk_four_cell": "shrunk", "truth_group_Ah": "truth_Ah"})
d["half_blend"] = 0.5 * d.uniform + 0.5 * d.explicit
weights = {"oracle": 1.0, "ultra_quality": 1.0, "high_quality": 0.5,
           "moderate_quality": 0.0, "low_quality": 0.0, "M4_unidentified": 0.0}
d["oracle_quality_gate_weight"] = d.quality.map(weights).astype(float)
d["oracle_quality_gate"] = d.uniform + d.oracle_quality_gate_weight * (d.explicit - d.uniform)
chosen = {}
for quality, part in d.loc[d.scenario.lt(200)].groupby("quality"):
    trials = [(float(np.mean(abs(part.uniform + w * (part.explicit - part.uniform) - part.truth_Ah))), w)
              for w in cfg["train_selected_weight_grid"]]
    chosen[quality] = min(trials)[1]
d["selected_weight"] = d.quality.map(chosen).astype(float)
d["selected_blend"] = d.uniform + d.selected_weight * (d.explicit - d.uniform)
d["explicit_missing_fallback"] = d.uniform
d["gate_with_explicit_plus3Ah"] = d.uniform + d.oracle_quality_gate_weight * (d.explicit + 3 - d.uniform)
methods = ["uniform", "explicit", "shrunk", "half_blend", "oracle_quality_gate", "selected_blend",
           "explicit_missing_fallback", "gate_with_explicit_plus3Ah"]
long = d.melt(id_vars=["scenario", "quality", "truth_Ah"], value_vars=methods,
              var_name="method", value_name="prediction_Ah")
long["error_Ah"] = long.prediction_Ah - long.truth_Ah
long.to_csv(OUT / "predictions.csv", index=False)
scores = []
for (quality, method), part in long.loc[long.scenario.ge(300)].groupby(["quality", "method"]):
    scores.append({"quality": quality, "method": method, "n_scenarios": len(part),
                   "MAE_Ah": float(part.error_Ah.abs().mean()),
                   "P95_abs_Ah": float(part.error_Ah.abs().quantile(0.95)),
                   "max_abs_Ah": float(part.error_Ah.abs().max()),
                   "bias_Ah": float(part.error_Ah.mean())})
pd.DataFrame(scores).to_csv(OUT / "test_scores.csv", index=False)
interval = []
for (quality, method), calibrate in long.loc[long.scenario.ge(200) & long.scenario.lt(300) & long.method.isin(["uniform", "oracle_quality_gate", "selected_blend"])].groupby(["quality", "method"]):
    test = long.loc[long.scenario.ge(300) & long.quality.eq(quality) & long.method.eq(method)]
    absolute = np.sort(abs(calibrate.error_Ah.to_numpy(float)))
    rank = min(len(absolute), int(np.ceil((len(absolute) + 1) * 0.9)))
    radius = float(absolute[rank - 1])
    interval.append({"quality": quality, "method": method, "calibration_scenarios": len(calibrate),
                     "test_scenarios": len(test), "rank": rank, "half_width_Ah": radius,
                     "test_coverage": float(np.mean(abs(test.error_Ah) <= radius))})
pd.DataFrame(interval).to_csv(OUT / "synthetic_interval_scores.csv", index=False)
summary = {"weight_selection_scenarios": 200, "interval_calibration_scenarios": 100,
           "development_test_scenarios": 300,
           "selected_explicit_weights_by_quality": chosen,
           "quality_gate_uses_injected_noise_oracle": True,
           "scores": scores, "interval": interval,
           "claim_limit": cfg["claim_limit"]}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"selected_weights": chosen, "test_MAE_Ah":
                  pd.DataFrame(scores).pivot(index="quality", columns="method", values="MAE_Ah").round(3).to_dict()},
                 ensure_ascii=False), flush=True)
