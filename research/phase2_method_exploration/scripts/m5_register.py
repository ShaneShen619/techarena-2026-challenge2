"""Register M5 numerical, synthetic, delayed-proxy and official-prefix runs."""
from __future__ import annotations
import csv,hashlib
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
INDEX=TASK/'notes/EXPERIMENT_INDEX.csv'
def sha(p):return hashlib.sha256((TASK/p).read_bytes()).hexdigest()
with INDEX.open(newline='') as f:r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
assert fields
seen={x['run_id'] for x in rows}
entries=[
 ('M5_pack_v1','scripts/m5_pack_experiment.py','configs/m5_pack.json','synthetic_pack_predictions.csv','broad S stress: oracle four-cell MAE 0.070Ah; noisy-state uniform 2.419Ah vs explicit 2.543Ah'),
 ('M5_state_quality_v1','scripts/m5_state_quality.py','configs/m5_state_quality.json','quality_predictions.csv','post-main milder sensitivity: explicit needs very accurate cell state to beat uniform'),
 ('M5_shrinkage_v1','scripts/m5_shrinkage.py','configs/m5_shrinkage.json','predictions.csv','new-seed synthetic noise-aware shrinkage helps only when state quality is high'),
 ('M5_official_scenarios_v1','scripts/m5_official_scenarios.py','configs/m5_official_scenarios.json','assumption_draws.csv','strict-prefix CK1-CK7 assumption-driven envelopes, not calibrated capacity intervals'),
 ('M5_delayed_proxy_v1','scripts/m5_delayed_proxy.py','configs/m5_delayed_proxy.json','causal_predictions.csv','synthetic delayed deep-charge proxy biased under drift and step shifts')]
for run_id,code,config,artifact,note in entries:
 if run_id in seen:continue
 assert (TASK/'runs'/run_id/artifact).exists()
 rows.append({'run_id':run_id,'module':'M5','question':'4S 11.2V group cutoff and state/proxy uncertainty',
              'input_sha256':sha('data_manifests/source_inventory_summary.json'),
              'code_sha256':sha(code),'config_sha256':sha(config),
              'label_protocol':'S independently perturbed truth or D3 official unlabeled assumption scenarios',
              'split':'fixed synthetic seed; official event_end strictly before checkup',
              'seed':'see config','status':'completed_synthetic_only_official_labels_hidden',
              'metric_path':f'runs/{run_id}/summary.json','artifact_path':f'runs/{run_id}/{artifact}',
              'elapsed_s':'not_recorded','peak_rss_mb':'not_recorded','conclusion':note})
with INDEX.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print({'index_rows':len(rows)})
