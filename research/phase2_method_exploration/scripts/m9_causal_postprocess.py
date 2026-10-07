"""Causal, label-free monotonic and smoothing postprocess checks."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/M9_causal_postprocess_v1"
OUT.mkdir(parents=True, exist_ok=False)
sources = [("TCN_full", "M7_TCN_v1", "TCN_from_scratch"),
           ("TCN_meta_mask", "M7_TCN_meta_only_v1", "TCN_scratch_meta_only")]
rows = []
for source_name, directory, method in sources:
    d = pd.read_csv(TASK / "runs" / directory / "predictions.csv")
    d = d.loc[d.method.eq(method)]
    d = d.groupby(["cell_id", "target_ordinal"], as_index=False).agg(
        pred=("pred_soh_pp", "mean"), truth=("target_soh_pp", "first"))
    assert len(d) == 180
    for cell, part in d.sort_values(["cell_id", "target_ordinal"]).groupby("cell_id"):
        pred = part.pred.to_numpy(float)
        variants = {"raw": pred, "causal_running_min": np.minimum.accumulate(pred)}
        ema = np.empty_like(pred)
        ema[0] = pred[0]
        for j in range(1, len(pred)):
            ema[j] = 0.5 * pred[j] + 0.5 * ema[j - 1]
        variants["causal_half_EMA"] = ema
        variants["causal_half_EMA_then_running_min"] = np.minimum.accumulate(ema)
        for rule, values in variants.items():
            for (_, r), value in zip(part.iterrows(), values):
                rows.append({"source": source_name, "cell_id": cell, "target_ordinal": int(r.target_ordinal),
                             "method": rule, "truth_pp": r.truth, "pred_pp": float(value),
                             "error_pp": float(value-r.truth)})
pred = pd.DataFrame(rows)
pred.to_csv(OUT / "predictions.csv", index=False)
scores = []
for (source, method), part in pred.groupby(["source", "method"]):
    per = part.assign(abs_pp=part.error_pp.abs()).groupby("cell_id").abs_pp.mean()
    scores.append({"source": source, "method": method, "macro_MAE_pp": float(per.mean()),
                   "worst_cell_MAE_pp": float(per.max()), "max_abs_error_pp": float(part.error_pp.abs().max()),
                   "n_targets": len(part)})
pd.DataFrame(scores).to_csv(OUT / "scores.csv", index=False)
(OUT / "summary.json").write_text(json.dumps({"scores": scores, "status": "D1 development only"}, ensure_ascii=False, indent=2)+"\n")
print(pd.DataFrame(scores).to_string(index=False), flush=True)
