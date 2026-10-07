"""Append immutable M7/M8 experiment provenance rows without duplicating run IDs."""
from pathlib import Path
import csv
import hashlib

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
INDEX = TASK / "notes/EXPERIMENT_INDEX.csv"
PANEL = ROOT / "research/phase2_temperature_improvement/outputs/panel_main.csv"
CK0 = ROOT / "data/checkups/CK0_reference_discharge.csv.gz"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = [
    ("M7_sequences_v1", "M7", "native 30s causal charge fragments", PANEL, "m7_build_sequences.py", "m7_representation.json", "P1 D1 high-rate single-cell proxy", "strict prefix manifest", "n/a", "runs/M7_sequences_v1/summary.json", "910 native fragments"),
    ("M7_target_map_v1", "M7", "visible target-to-event mapping", PANEL, "m7_build_target_map.py", "m7_representation.json", "no labels in inputs", "strict prefix per target", "n/a", "runs/M7_target_map_v1/summary.json", "180 targets with 15-event history cap"),
    ("M7_linear_representation_v1", "M7", "PCA reconstruction versus capacity transfer", PANEL, "m7_linear_representation.py", "m7_representation.json", "P1 D1 high-rate single-cell proxy", "nested leave entire cell out", "n/a", "runs/M7_linear_representation_v1/summary.json", "PCA 0.633mV reconstruction but 18.192pp capacity MAE"),
    ("M7_TCN_smoke_v1", "M7", "CPU TCN execution smoke", PANEL, "m7_tcn_experiment.py", "m7_representation.json", "P1 D1 high-rate single-cell proxy", "one outer cell", "20260928", "runs/M7_TCN_smoke_v1/summary.json", "smoke only; not capacity conclusion"),
    ("M7_TCN_v1", "M7", "self-supervised TCN frozen finetune scratch", PANEL, "m7_tcn_experiment.py", "m7_representation.json", "P1 D1 high-rate single-cell proxy", "six outer cells; pretrain held cell excluded", "20260928/29/30", "runs/M7_TCN_v1/summary.json", "scratch mean2.585pp vs age3.680; self-supervision no stable benefit"),
    ("M7_TCN_no_voltage_v1", "M7", "charge voltage ablation", PANEL, "m7_tcn_no_voltage.py", "m7_representation.json", "P1 D1 high-rate single-cell proxy", "six outer cells", "20260928/29/30", "runs/M7_TCN_no_voltage_v1/summary.json", "no voltage mean2.592pp; voltage adds no demonstrated value"),
    ("M7_TCN_meta_only_v1", "M7", "all charge signal channels ablated", PANEL, "m7_tcn_meta_only.py", "m7_representation.json", "P1 D1 high-rate single-cell proxy", "six outer cells", "20260928/29/30", "runs/M7_TCN_meta_only_v1/summary.json", "meta/mask only mean2.530pp; improvement is not waveform evidence"),
    ("M8_D1_fusion_v1", "M8", "D1 fixed-weight fusion and rank interval", PANEL, "m8_d1_fusion.py", "m8_fusion.json", "P1 D1 high-rate single-cell proxy", "six outer cells; five-cell interval calibration", "fixed", "runs/M8_D1_fusion_v1/summary.json", "best single TCN ensemble2.512pp; gate2.760pp; 90pct group interval infeasible"),
    ("M8_pack_fusion_v1", "M8", "synthetic 4S quality gate and interval", CK0, "m8_pack_fusion.py", "m8_pack_fusion.json", "S synthetic constructed pack cutoff", "300 calibration / 300 scenario test", "20260930 upstream", "runs/M8_pack_fusion_v1/summary.json", "oracle noise gate helps only when quality known; +3Ah drift breaks it"),
]

with INDEX.open(newline="") as f:
    old = list(csv.DictReader(f))
    fields = list(old[0])
seen = {r["run_id"] for r in old}
for run, module, question, input_path, code, config, label, split, seed, metric, conclusion in spec:
    if run in seen:
        continue
    artifact = TASK / "runs" / run
    assert artifact.exists() and (TASK / metric).exists()
    old.append(dict(run_id=run, module=module, question=question, input_sha256=sha(input_path),
                    code_sha256=sha(TASK / "scripts" / code), config_sha256=sha(TASK / "configs" / config),
                    label_protocol=label, split=split, seed=seed, status="completed_development_only",
                    metric_path=metric, artifact_path=f"runs/{run}", elapsed_s="not_recorded",
                    peak_rss_mb="not_recorded", conclusion=conclusion))
with INDEX.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(old)
print(f"index rows {len(old)}")
