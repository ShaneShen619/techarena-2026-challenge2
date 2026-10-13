"""Describe nominal-capacity C-rates in all released operation files.

Weight: left-endpoint duration to next row, within the same file, only
0 < dt <= 30 s. No reconstruction across missing files or recording gaps.
Main active threshold: |I| > 0.5 A. Discharge statistics use |I|.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
NOMINAL_AH = 102.0


def weighted_quantile(values, weights, probs):
    order = np.argsort(values)
    v, w = values[order], weights[order]
    positions = np.cumsum(w) / w.sum()
    return [float(v[min(np.searchsorted(positions, p), len(v) - 1)]) for p in probs]


def describe(frame, threshold=0.5):
    valid = frame.loc[frame.weight_s > 0]
    total_s = float(valid.weight_s.sum())
    stats = {}
    states = {
        "charge": valid.current_A > threshold,
        "discharge": valid.current_A < -threshold,
        "near_zero": valid.current_A.abs() <= threshold,
    }
    for state, mask in states.items():
        x = valid.loc[mask]
        v = x.current_A.abs().to_numpy()
        w = x.weight_s.to_numpy()
        q = weighted_quantile(v, w, [0.05, 0.5, 0.95])
        row_mask = (frame.current_A > threshold if state == "charge" else
                    frame.current_A < -threshold if state == "discharge" else
                    frame.current_A.abs() <= threshold)
        mean = float(np.average(v, weights=w))
        stats[state] = {
            "threshold_A": threshold,
            "rows": int(row_mask.sum()),
            "observed_hours": float(w.sum() / 3600),
            "observed_time_fraction": float(w.sum() / total_s),
            "time_weighted_mean_abs_A": mean,
            "time_weighted_mean_C": mean / NOMINAL_AH,
            "row_mean_abs_A": float(frame.loc[row_mask, "current_A"].abs().mean()),
            "time_weighted_p5_A": q[0], "time_weighted_median_A": q[1],
            "time_weighted_p95_A": q[2],
            "time_weighted_p5_C": q[0]/NOMINAL_AH,
            "time_weighted_median_C": q[1]/NOMINAL_AH,
            "time_weighted_p95_C": q[2]/NOMINAL_AH,
            "min_abs_A": float(frame.loc[row_mask, "current_A"].abs().min()),
            "max_abs_A": float(frame.loc[row_mask, "current_A"].abs().max()),
            "sample_hold_throughput_Ah": float(np.dot(v, w) / 3600),
        }
    stats["all"] = {
        "observed_hours": total_s/3600,
        "mean_abs_A": float(np.average(valid.current_A.abs(), weights=valid.weight_s)),
        "mean_abs_C": float(np.average(valid.current_A.abs(), weights=valid.weight_s))/NOMINAL_AH,
        "mean_signed_A": float(np.average(valid.current_A, weights=valid.weight_s)),
    }
    return stats


frames, manifest = [], []
for path in sorted((ROOT / "data/operation").glob("*.csv.gz")):
    d = pd.read_csv(path, usecols=["timestamp", "current_A", "segment", "chamber_temperature_C"])
    d["timestamp"] = pd.to_datetime(d.timestamp)
    dt = d.timestamp.shift(-1).sub(d.timestamp).dt.total_seconds()
    d["weight_s"] = dt.where((dt > 0) & (dt <= 30), 0).fillna(0)
    if not np.isfinite(d.current_A).all():
        raise ValueError(f"Nonfinite current in {path}")
    frames.append(d)
    manifest.append({"path": str(path.relative_to(ROOT)), "rows": len(d),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "long_gap_count": int((dt > 30).sum()),
        "long_gap_elapsed_hours": float(dt[dt > 30].sum()/3600),
        "zero_dt_count": int((dt == 0).sum()),
        "negative_dt_count": int((dt < 0).sum())})

data = pd.concat(frames, ignore_index=True)
overall = describe(data)
by_temperature = {str(int(t)): describe(d) for t, d in data.groupby("chamber_temperature_C")}
by_segment = {str(int(s)): describe(d) for s, d in data.groupby("segment")}
sensitivity = {str(t): describe(data, t) for t in [0.0, 0.1, 0.5, 1.0]}
bins = [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.5, 1.0, np.inf]
hist = []
for state, mask in [("charge", data.current_A > .5), ("discharge", data.current_A < -.5)]:
    x = data.loc[mask & (data.weight_s > 0)]
    c = x.current_A.abs() / NOMINAL_AH
    for lo, hi in zip(bins[:-1], bins[1:]):
        sec = float(x.loc[(c >= lo) & (c < hi), "weight_s"].sum())
        hist.append({"state": state, "lower_C_inclusive": lo,
            "upper_C_exclusive": None if np.isinf(hi) else hi,
            "hours": sec/3600, "active_time_fraction": sec/float(x.weight_s.sum())})

result = {
    "analysis_date": "2026-10-09", "nominal_capacity_Ah": NOMINAL_AH,
    "files": len(manifest), "rows": len(data),
    "start": str(data.timestamp.min()), "end": str(data.timestamp.max()),
    "method": "Left-endpoint time-weighted currents; within-file 0 < dt <= 30 seconds; charging I > 0.5 A; discharging I < -0.5 A with magnitude reported; nominal C = |I| / 102 Ah.",
    "limitations": "Only recorded operation; missing segment 3 and long gaps excluded; checkup measurements excluded; all released rows including post-CK7, descriptive audit only.",
    "overall": overall, "by_temperature": by_temperature, "by_segment": by_segment,
    "threshold_sensitivity": sensitivity, "histogram": hist, "input_manifest": manifest,
}
(OUT / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
pd.DataFrame([{"state": k, **v} for k, v in overall.items()]).to_csv(OUT / "overall_statistics.csv", index=False)
pd.DataFrame([{"temperature_C": t, "state": k, **v}
              for t, stats in by_temperature.items() for k, v in stats.items()]).to_csv(OUT / "temperature_statistics.csv", index=False)
pd.DataFrame([{"segment": s, "state": k, **v}
              for s, stats in by_segment.items() for k, v in stats.items()]).to_csv(OUT / "segment_statistics.csv", index=False)
pd.DataFrame(hist).to_csv(OUT / "rate_distribution.csv", index=False)
print(json.dumps({k: result[k] for k in ["files", "rows", "start", "end", "overall", "by_temperature", "threshold_sensitivity"]}, ensure_ascii=False, indent=2))
