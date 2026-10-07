"""Register TU full-scan, causal model revisions, anomaly and transfer tests."""
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
 ('M6_TU_inventory_v1','scripts/m6_tu_inventory.py','configs/m6_tu_sampling.json','system_inventory.csv','28-system stratified inventory, 3.92M sampled rows; 34.1% eligible rows have active balancing'),
 ('M6_TU_steps_v1','scripts/m6_extract_steps.py','configs/m6_step_extraction.json','extraction_summary_by_system.csv','all 132.78M source rows scanned; 14,778 10A physical step events retained'),
 ('M6_workpoint_time_v3','scripts/m6_workpoint_time.v3.py','configs/m6_model.v1.json','LOSO_online_predictions.csv','RBF+time initially beats global constant but temporal matching absent'),
 ('M6_workpoint_time_v4','scripts/m6_workpoint_time.v4.py','configs/m6_model.v2.json','LOSO_online_predictions.csv','matched temporal controls show global+time better than RBF+time'),
 ('M6_workpoint_time_v5','scripts/m6_workpoint_time.py','configs/m6_model.json','LOSO_online_predictions.csv','global+target-prefix adaptive workpoint macro MAE0.225mOhm; RBF+same0.233'),
 ('M6_workpoint_time_20A_v1','scripts/m6_workpoint_time_20A.py','configs/m6_model_20A.json','LOSO_online_predictions.csv','20A threshold sensitivity on 9 systems, nonidentical event mix'),
 ('M6_threshold_common_v1','scripts/m6_threshold_compare.py','configs/m6_model_20A.json','matched_event_predictions.csv','71,255 exact common events: 10A vs20A 9-system macro0.144 vs0.138mOhm'),
 ('M6_fault_monitor_v1','scripts/m6_fault_monitor.py','configs/m6_fault.json','synthetic_injection_results.csv','synthetic +0.5/1mOhm persistent injection detected in80/80 streams; real alerts unlabeled'),
 ('M6_official_R_aux_v1','scripts/m6_official_R_aux.py','configs/m6_official_R_aux.json','forward_predictions.csv','official R10 auxiliary gives only0.0014mV future-voltage gain; wrong-cell negative control similar')]
for run_id,code,config,artifact,note in entries:
 if run_id in seen:continue
 assert (TASK/'runs'/run_id/artifact).exists()
 rows.append({'run_id':run_id,'module':'M6','question':'TU 8S field step response, operating point/time, anomaly, official auxiliary transfer',
              'input_sha256':sha('data_manifests/source_inventory_summary.json'),
              'code_sha256':sha(code),'config_sha256':sha(config),
              'label_protocol':'TU unlabeled resistance proxy; D3 official unlabeled pulse voltage; synthetic anomaly injection',
              'split':'leave whole TU system out and target chronological online prefix; official pulse walk-forward',
              'seed':'20260928','status':'completed_signal_only_capacity_unverifiable',
              'metric_path':f'runs/{run_id}/summary.json','artifact_path':f'runs/{run_id}/{artifact}',
              'elapsed_s':'not_recorded','peak_rss_mb':'not_recorded','conclusion':note})
with INDEX.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print({'index_rows':len(rows)})
