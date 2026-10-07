"""Append the two M2 primary development runs without erasing prior rows."""
from __future__ import annotations
import csv,hashlib
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
INDEX=TASK/'notes/EXPERIMENT_INDEX.csv'
def sha(path:str)->str:return hashlib.sha256((TASK/path).read_bytes()).hexdigest()
with INDEX.open(newline='') as stream:
    read=csv.DictReader(stream);fields=read.fieldnames;rows=list(read)
assert fields
seen={r['run_id'] for r in rows}
for run_id,code,conf,note in [
 ('M2_primary_v1','scripts/m2_primary.v1.py','configs/m2_primary.v1.json',
  '协议v1.3同输入六芯开发集；最佳固定窗口宏MAE3.764pp；15片段计数饱和，结果保留'),
 ('M2_primary_v2','scripts/m2_primary.py','configs/m2_primary.json',
  '协议v1.4加入统一前缀事件数；最佳年龄Ridge宏MAE3.680pp，最差芯7.588pp，未达标')]:
    if run_id in seen:continue
    rows.append({'run_id':run_id,'module':'M2','question':'20Ah持续历史同输入容量代理比较',
                 'input_sha256':sha('data_manifests/d1_target_visibility.csv'),
                 'code_sha256':sha(code),'config_sha256':sha(conf),
                 'label_protocol':'P1 single-cell high-rate discharge capacity / 102Ah',
                 'split':'nested leave one of 6 physical cells out','seed':'20260928',
                 'status':'completed_below_target','metric_path':f'runs/{run_id}/summary.json',
                 'artifact_path':f'runs/{run_id}/predictions.csv',
                 'elapsed_s':'not_recorded','peak_rss_mb':'not_recorded','conclusion':note})
extra=[]
for run_id in ['M2_20Ah_no_count_v1','M2_15Ah_persistent_v1','M2_30Ah_persistent_v1',
               'M2_20Ah_cold_v1','M2_3p45_persistent_v1','M2_3p55_persistent_v1',
               'M2_full_tail_persistent_v1','M2_mid_event_persistent_v1',
               'M2_mid_rbf_age_only_v1','M2_mid_rbf_age_voltage_v1',
               'M2_mid_rbf_age_current_v1','M2_mid_rbf_age_voltage_current_v1',
               'M2_mid_rbf_age_window_v1','M2_primary_rbf_age_voltage_v1',
               'M2_primary_rbf_age_current_v1','M2_primary_rbf_age_voltage_current_v1',
               'M2_15Ah_replay_v2']:
    extra.append((run_id,'scripts/m2_sensitivity.py','predictions.csv',
                  'D1 20/15/30 Ah budget, history/crop/feature ablation; executable current script is replay-compatible'))
for mode in ['3p45','3p55','full_tail','mid_event']:
    extra.append((f'M2_crop_{mode}_v1','scripts/m2_crop_sensitivity.py','cropped_events.csv',
                  'Raw P1 alternate event position reconstructed without target labels'))
for run_id,code,artifact,note in [
    ('M2_crop_counterfactual_v1','scripts/m2_counterfactual.py','same_capacity_crop_shifts.csv',
     'Primary model refit is frozen; same capacity alternate crop exposes up to 15.914pp prediction shift'),
    ('M2_spline_v1','scripts/m2_spline.py','predictions.csv',
     'Age and rate spline negative; temperature-rate interaction best exploratory 3.616pp'),
    ('M2_quality_gate_v1','scripts/m2_quality_gate.v1.py','predictions.csv',
     'Input-domain gate improves brittle mask model but not main target'),
    ('M2_quality_gate_v2','scripts/m2_quality_gate.py','predictions.csv',
     'Stable prefix fallback reduces alternate crop tail shifts but still misses main target'),
    ('M2_stable_prefix_prior_v1','scripts/m2_stable_prior.py','predictions.csv',
     'Fragment-independent fallback 3.809pp macro MAE'),
    ('M2_Che_shape_v1','scripts/m2_che_shape.py','same_charge_diagnostics.csv',
     '11 cells; same-charge partial-Q diagnostic only, protocol incompatible'),
    ('M2_compiled_v1','scripts/m2_compile.py','all_conditions_independent_scores.csv',
     'Independent score recomputation: D1 target not met')]:
    extra.append((run_id,code,artifact,note))
for run_id,code,artifact,note in extra:
    if run_id in seen:continue
    metric_name='interim_acceptance.json' if run_id=='M2_compiled_v1' else 'summary.json'
    rows.append({'run_id':run_id,'module':'M2','question':'预算/截取/机制反证与外部字段核验',
                 'input_sha256':sha('data_manifests/d1_target_visibility.csv'),
                 'code_sha256':sha(code),'config_sha256':sha('configs/acceptance.json'),
                 'label_protocol':'P1 proxy or explicitly unlabeled input check',
                 'split':'nested physical-cell LOCO where labeled','seed':'20260928',
                 'status':'completed','metric_path':f'runs/{run_id}/{metric_name}',
                 'artifact_path':f'runs/{run_id}/{artifact}',
                 'elapsed_s':'not_recorded','peak_rss_mb':'not_recorded','conclusion':note})
with INDEX.open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
print({'index_rows':len(rows)})
