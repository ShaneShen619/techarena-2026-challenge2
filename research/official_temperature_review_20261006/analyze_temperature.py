"""Descriptive temperature audit of all released official operation rows.

Run from the project root with the existing research Python environment.
Outputs stay in this new directory; official files are read only.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)
COLS = ["timestamp", "segment", "chamber_temperature_C", "current_A",
        "temp_mean_C", "temp_min_C", "temp_max_C"]
frames, manifest = [], []
for p in sorted((ROOT / "data/operation").glob("*.csv.gz")):
    x = pd.read_csv(p, usecols=COLS, parse_dates=["timestamp"])
    x["source_file"] = p.name
    # Left-endpoint time weight, only within the file, never across large gaps.
    dt = (x.timestamp.shift(-1) - x.timestamp).dt.total_seconds()
    x["weight_s"] = dt.where((dt > 0) & (dt <= 30), 0).fillna(0)
    manifest.append({"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                     "rows": len(x), "zero_dt_intervals": int((dt == 0).sum()),
                     "negative_dt_intervals": int((dt < 0).sum()),
                     "over_30s_intervals": int((dt > 30).sum()),
                     "max_interval_s": float(dt.max())})
    frames.append(x)
d = pd.concat(frames, ignore_index=True)
d["mean_minus_set_C"] = d.temp_mean_C - d.chamber_temperature_C
d["min_minus_set_C"] = d.temp_min_C - d.chamber_temperature_C
d["max_minus_set_C"] = d.temp_max_C - d.chamber_temperature_C
d["mean_minus_min_C"] = d.temp_mean_C - d.temp_min_C
d["max_minus_mean_C"] = d.temp_max_C - d.temp_mean_C
d["spread_C"] = d.temp_max_C - d.temp_min_C
d["mean_minus_midpoint_C"] = d.temp_mean_C - (d.temp_max_C + d.temp_min_C) / 2
d["current_state"] = np.select([d.current_A > 0.5, d.current_A < -0.5], ["charge", "discharge"], default="near_zero")
TEMP_COLS = ["temp_mean_C", "temp_min_C", "temp_max_C"]
# Adjacent changes are evaluated only in acquisition order within a source file.
prev_dt = d.groupby("source_file", sort=False).timestamp.diff().dt.total_seconds()
steps = d.groupby("source_file", sort=False)[TEMP_COLS].diff()
valid_step = (prev_dt > 0) & (prev_dt <= 30)
max_step = steps.abs().max(axis=1)
# Explicit exploratory flags; these do NOT imply a broken sensor or unsafe battery.
wide_spread = d.spread_C > (2 + 1e-9)
jump_flag = valid_step & (max_step > (.5 + 1e-9))
candidate_flag = wide_spread | jump_flag
suspects = d.loc[candidate_flag, COLS + ["source_file", "mean_minus_set_C", "spread_C"]].copy()
suspects["wide_spread_over_2C"] = wide_spread[candidate_flag]
suspects["adjacent_step_over_0p5C"] = jump_flag[candidate_flag]
suspects["previous_dt_s"] = prev_dt[candidate_flag]
for c in TEMP_COLS:
    suspects["previous_" + c] = d.groupby("source_file", sort=False)[c].shift(1)[candidate_flag]
suspects.to_csv(OUT / "temperature_review_candidates.csv", index=False)
jump_stats = []
for threshold in [.5, 1, 2]:
    flag = valid_step & (max_step > (threshold + 1e-9))
    jump_stats.append({"threshold_C": threshold, "any_temperature_rows": int(flag.sum()),
                       **{c: int((valid_step & (steps[c].abs() > threshold + 1e-9)).sum()) for c in TEMP_COLS}})
duplicates = d[d.duplicated("timestamp", keep=False)]
duplicate_conflicts = duplicates.groupby("timestamp")[TEMP_COLS].nunique().max(axis=1)
duplicate_ranges = duplicates.groupby("timestamp")[TEMP_COLS].max() - duplicates.groupby("timestamp")[TEMP_COLS].min()
duplicate_ranges.to_csv(OUT / "duplicate_timestamp_temperature_ranges.csv")
gap_rows = d.loc[prev_dt > 30, COLS + ["source_file"]].copy()
gap_rows["previous_timestamp"] = d.groupby("source_file", sort=False).timestamp.shift(1)[prev_dt > 30]
gap_rows["gap_seconds"] = prev_dt[prev_dt > 30]
gap_rows.to_csv(OUT / "within_file_recording_gaps.csv", index=False)
jump_rows = d.loc[jump_flag, COLS + ["source_file"]].copy()
jump_rows["previous_dt_s"] = prev_dt[jump_flag]
for c in TEMP_COLS:
    jump_rows["previous_" + c] = d.groupby("source_file", sort=False)[c].shift(1)[jump_flag]
jump_rows.to_csv(OUT / "adjacent_temperature_steps.csv", index=False)
quality = {"temperature_fields": ["chamber_temperature_C"] + TEMP_COLS,
           "missing_temperature_cells": int(d[["chamber_temperature_C"] + TEMP_COLS].isna().sum().sum()),
           "any_missing_temperature_rows": int(d[["chamber_temperature_C"] + TEMP_COLS].isna().any(axis=1).sum()),
           "nonfinite_temperature_cells": int((~np.isfinite(d[["chamber_temperature_C"] + TEMP_COLS])).sum().sum()),
           "unexpected_setpoint_rows": int((~d.chamber_temperature_C.isin([25,45])).sum()),
           "zero_measured_temperature_cells": int((d[TEMP_COLS] == 0).sum().sum()),
           "measured_temperature_range_C": {c: [float(d[c].min()), float(d[c].max())] for c in TEMP_COLS},
           "adjacent_jump_eligible_pairs": int(valid_step.sum()), "jump_sensitivity": jump_stats,
           "over_2C_spread_rows": int(wide_spread.sum()), "over_3C_spread_rows": int((d.spread_C > 3 + 1e-9).sum()),
           "review_candidate_union_rows": int(candidate_flag.sum()),
           "duplicate_timestamp_groups": len(duplicate_conflicts),
           "duplicate_timestamp_temperature_conflict_groups": int((duplicate_conflicts > 1).sum()),
           "largest_temperature_difference_at_same_timestamp_C": float(duplicate_ranges.max().max()),
           "within_file_gap_over_30s_count": int((prev_dt > 30).sum()),
           "within_file_gap_over_30s_elapsed_hours": float(prev_dt[prev_dt > 30].sum()/3600),
           "within_file_gap_over_30s_excess_over_10s_hours": float((prev_dt[prev_dt > 30] - 10).sum()/3600),
           "within_file_gap_over_30s_max_s": float(prev_dt[prev_dt > 30].max()),
           "observed_weight_hours": float(d.weight_s.sum()/3600)}
(OUT / "quality_results.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n")
# Local context for the largest temperature spread; do not interpolate the episode.
extreme_time = d.loc[d.spread_C.idxmax(), "timestamp"]
episode = d[(d.timestamp >= extreme_time - pd.Timedelta(minutes=5)) &
            (d.timestamp <= extreme_time + pd.Timedelta(minutes=10))].copy()
episode.to_csv(OUT / "largest_spread_episode.csv", index=False)
METRICS = ["temp_mean_C", "temp_min_C", "temp_max_C", "mean_minus_set_C", "min_minus_set_C", "max_minus_set_C",
           "mean_minus_min_C", "max_minus_mean_C", "spread_C", "mean_minus_midpoint_C"]

def summarize(x, identity):
    rows = []
    for metric in METRICS:
        a = x[metric].replace([np.inf, -np.inf], np.nan)
        good = a.notna()
        w = x.loc[good, "weight_s"]
        rows.append({**identity, "metric": metric, "rows": len(x), "valid_rows": int(good.sum()),
                     "mean": float(a.mean()), "std": float(a.std()), "min": float(a.min()),
                     **{f"p{q}": float(a.quantile(q / 100)) for q in [1, 5, 50, 95, 99]},
                     "max": float(a.max()),
                     "time_weighted_mean": float(np.average(a[good], weights=w)) if w.sum() else None,
                     "observed_weight_hours": float(w.sum() / 3600)})
    return rows

stats = summarize(d, {"setpoint_C": "all"})
for setpoint, x in d.groupby("chamber_temperature_C"):
    stats.extend(summarize(x, {"setpoint_C": int(setpoint)}))
pd.DataFrame(stats).to_csv(OUT / "temperature_statistics.csv", index=False)
segment_stats, current_stats, thresholds = [], [], []
for (seg, setpoint), x in d.groupby(["segment", "chamber_temperature_C"]):
    segment_stats.append({"segment": int(seg), "setpoint_C": int(setpoint), "rows": len(x),
                          "start": str(x.timestamp.min()), "end": str(x.timestamp.max()),
                          "mean_temperature_C": float(x.temp_mean_C.mean()),
                          "mean_offset_C": float(x.mean_minus_set_C.mean()),
                          "offset_p05_C": float(x.mean_minus_set_C.quantile(.05)),
                          "offset_p95_C": float(x.mean_minus_set_C.quantile(.95)),
                          "offset_max_C": float(x.mean_minus_set_C.max()),
                          "mean_spread_C": float(x.spread_C.mean()),
                          "spread_p95_C": float(x.spread_C.quantile(.95)),
                          "spread_max_C": float(x.spread_C.max()),
                          "time_weighted_offset_C": float(np.average(x.mean_minus_set_C, weights=x.weight_s))})
for (setpoint, state), x in d.groupby(["chamber_temperature_C", "current_state"]):
    current_stats.extend(summarize(x, {"setpoint_C": int(setpoint), "current_state": state}))
for setpoint, x in d.groupby("chamber_temperature_C"):
    thresholds.append({"setpoint_C": int(setpoint), "rows": len(x),
                       "mean_above_setpoint_pct": float((x.mean_minus_set_C > 0).mean() * 100),
                       "min_above_setpoint_pct": float((x.min_minus_set_C > 0).mean() * 100),
                       "max_above_setpoint_pct": float((x.max_minus_set_C > 0).mean() * 100),
                       **{f"offset_above_{t}C_pct": float((x.mean_minus_set_C > t).mean() * 100) for t in [1, 2, 3, 5]},
                       **{f"spread_above_{t}C_pct": float((x.spread_C > t).mean() * 100) for t in [1, 2, 3]},
                       "mean_below_min_rows": int((x.temp_mean_C < x.temp_min_C).sum()),
                       "mean_above_max_rows": int((x.temp_mean_C > x.temp_max_C).sum())})
pd.DataFrame(segment_stats).to_csv(OUT / "segment_statistics.csv", index=False)
pd.DataFrame(current_stats).to_csv(OUT / "current_state_statistics.csv", index=False)
pd.DataFrame(thresholds).to_csv(OUT / "threshold_statistics.csv", index=False)

extreme_rows = []
for metric in ["mean_minus_set_C", "spread_C"]:
    for direction in ["min", "max"]:
        value = d[metric].min() if direction == "min" else d[metric].max()
        matches = d[d[metric] == value]
        r = matches.iloc[0]
        extreme_rows.append({"metric": metric, "direction": direction, "value_C": float(value),
                             "tied_rows": len(matches), **r[COLS + ["source_file"]].to_dict()})
pd.DataFrame(extreme_rows).to_csv(OUT / "extreme_rows.csv", index=False)

result = {"analysis_date": "2026-10-06", "rows": len(d), "files": len(frames),
          "start": str(d.timestamp.min()), "end": str(d.timestamp.max()),
          "segments": sorted(map(int, d.segment.unique())),
          "missing_cells": d[COLS].isna().sum().to_dict(),
          "nonfinite_numeric": {c: int((~np.isfinite(d[c])).sum()) for c in COLS if c != "timestamp"},
          "ordering_violation_rows": int(((d.temp_min_C > d.temp_mean_C) | (d.temp_mean_C > d.temp_max_C)).sum()),
          "duplicate_timestamp_rows": int(d.duplicated("timestamp").sum()),
          "weight_definition": "left-endpoint duration to next row within file; 0 < dt <= 30 seconds only",
          "input_manifest": manifest, "quality": quality, "setpoint_statistics": stats, "threshold_statistics": thresholds,
          "segment_statistics": segment_stats, "extreme_rows": extreme_rows}
(OUT / "analysis_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n")

# Static scientific figures: no filling across recording gaps or missing segments.
font_path = Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(font_path)).get_name()
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 130, "savefig.dpi": 180})
fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True, constrained_layout=True)
for _, x in d.groupby("source_file", sort=True):
    x = x.sort_values("timestamp")
    # Arithmetic sample means in 30-minute bins; empty bins stay NaN.
    b = x.set_index("timestamp")[["temp_mean_C", "temp_min_C", "temp_max_C", "chamber_temperature_C", "spread_C"]].resample("30min").mean()
    axes[0].fill_between(b.index, b.temp_min_C, b.temp_max_C, color="#527d9e", alpha=.17)
    axes[0].plot(b.index, b.temp_mean_C, color="#245b80", linewidth=1)
    axes[0].plot(b.index, b.chamber_temperature_C, color="#98653c", linewidth=1, linestyle="--")
    axes[1].plot(b.index, b.spread_C, color="#245b80", linewidth=1)
axes[0].plot([], [], color="#245b80", label="实测平均温度")
axes[0].plot([], [], color="#98653c", linestyle="--", label="温箱设定温度")
axes[0].fill_between([], [], [], color="#527d9e", alpha=.17, label="实测最低至最高温度")
axes[0].legend(loc="upper left", ncol=3, fontsize=9)
axes[0].set_title("实测电芯温度与温箱设定温度")
axes[0].set_ylabel("温度（°C）")
axes[1].set_title("同一时刻的传感器温差：最高温度减最低温度")
axes[1].set_ylabel("温差（°C）")
axes[1].set_xlabel("记录日期（2025 年，月-日）")
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
for ax in axes:
    ax.grid(axis="y", alpha=.2)
fig.suptitle("来源：官方四串 LFP 运行数据，2025 年 1-9 月｜每 30 分钟按样本取平均", fontsize=13)
fig.savefig(OUT / "temperature_timeline.png")
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.7), constrained_layout=True)
bins_offset = np.linspace(d.mean_minus_set_C.min() - .01, d.mean_minus_set_C.max() + .01, 75)
bins_spread = np.linspace(0, d.spread_C.max() + .01, 65)
for setpoint, color in [(25, "#245b80"), (45, "#98653c")]:
    x = d[d.chamber_temperature_C == setpoint]
    weights = np.full(len(x), 100 / len(x))
    axes[0].hist(x.mean_minus_set_C, bins=bins_offset, weights=weights, histtype="step", linewidth=1.6, color=color, label=f"设定 {setpoint}°C")
    axes[1].hist(x.spread_C, bins=bins_spread, weights=weights, histtype="step", linewidth=1.6, color=color, label=f"设定 {setpoint}°C")
axes[0].set_title("实测平均温度减温箱设定温度")
axes[0].set_xlabel("温度偏差（°C）")
axes[1].set_title("实测最高温度减最低温度")
axes[1].set_xlabel("温差（°C）")
for ax in axes:
    ax.set_ylabel("各区间样本占比（该温度档位内，%）")
    ax.legend(); ax.grid(axis="y", alpha=.2)
fig.suptitle("来源：官方运行数据，2025 年 1-9 月｜25°C、45°C 各自按记录行统计", fontsize=12)
fig.savefig(OUT / "temperature_distributions.png")
plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
for c, label, color in [("temp_min_C", "实测最低温度", "#98653c"), ("temp_mean_C", "实测平均温度", "#245b80"),
                        ("temp_max_C", "实测最高温度", "#668261"), ("chamber_temperature_C", "温箱设定温度", "#555555")]:
    ax.plot(episode.timestamp, episode[c], label=label, color=color, linestyle="--" if c == "chamber_temperature_C" else "-")
ax.set_title("最大温差片段｜来源：官方第 11 段，2025-07-11｜原始采样值")
ax.set_ylabel("温度（°C）"); ax.set_xlabel("记录时间（时:分:秒）")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S")); ax.legend(ncol=2); ax.grid(axis="y", alpha=.2)
fig.savefig(OUT / "largest_spread_episode.png")
plt.close(fig)

compact = []
for r in stats:
    if r["metric"] in ["temp_mean_C", "mean_minus_set_C", "mean_minus_min_C", "max_minus_mean_C", "spread_C", "mean_minus_midpoint_C"]:
        compact.append({k: r[k] for k in ["setpoint_C", "metric", "rows", "mean", "p5", "p50", "p95", "min", "max", "time_weighted_mean"]})
print(json.dumps({"scope": {k: result[k] for k in ["rows", "start", "end", "ordering_violation_rows", "duplicate_timestamp_rows", "missing_cells"]},
                  "statistics": compact, "thresholds": thresholds, "segments": segment_stats, "extremes": extreme_rows,
                  "quality": quality}, ensure_ascii=False, indent=2, default=str))
