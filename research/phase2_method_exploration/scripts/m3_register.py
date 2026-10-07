"""Register M3 input-transfer, paired-event and capacity-proxy experiments."""
from __future__ import annotations
import csv,hashlib
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
INDEX=TASK/'notes/EXPERIMENT_INDEX.csv'
def sha(name):return hashlib.sha256((TASK/name).read_bytes()).hexdigest()
with INDEX.open(newline='') as f:r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
assert fields
seen={z['run_id'] for z in rows}
entries=[
 ('M3_transfer_pairs_v1','scripts/m3_transfer_and_pairs.py','official_charge_transfer.csv',
  '旧温度面官方25C偏约+10C而不可迁移；P1匹配仅6对，官方34条脉冲夹心差为信号证据'),
 ('M3_temperature_models_v1','scripts/m3_temperature_models.py','LOCO_predictions.csv',
  '当前/有限历史温度及Arrhenius形式未优于M2主年龄基线；偏置敏感性已测'),
 ('M3_spline_temperature_group_v1','scripts/m3_spline_group_holdout.py','predictions.csv',
  '整个温度组留出时温度×倍率样条宏MAE4.272pp，未达目标'),
 ('M3_spline_sensor_bias_v1','scripts/m3_spline_bias.py','predictions.csv',
  '最佳温度样条±1C偏置令24/180目标移动超过0.5pp'),
 ('M3_prefix_temperature_v1','scripts/m3_prefix_exposure.py','predictions.csv',
  '额外全事件温度标量补充输入，均温+当前T开发集宏MAE2.991pp，不入主预算排名'),
 ('M3_static_vs_rolling_v1','scripts/m3_static_vs_rolling.py','predictions.csv',
  '静态最早10事件温度优于滚动全前缀温度，累计热暴露机制未证实')
]
for run_id,code,artifact,note in entries:
    if run_id in seen:continue
    rows.append({'run_id':run_id,'module':'M3','question':'即时T/历史T/设备迁移/传感器偏置分离',
                 'input_sha256':sha('data_manifests/source_inventory_summary.json'),
                 'code_sha256':sha(code),'config_sha256':sha('configs/m3_validation.json'),
                 'label_protocol':'P1 high-rate single-cell proxy or official unlabeled pulse signal',
                 'split':'nested physical-cell LOCO or whole temperature group holdout',
                 'seed':'20260928','status':'completed_with_causal_limit',
                 'metric_path':f'runs/{run_id}/summary.json',
                 'artifact_path':f'runs/{run_id}/{artifact}',
                 'elapsed_s':'not_recorded','peak_rss_mb':'not_recorded','conclusion':note})
with INDEX.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print({'index_rows':len(rows)})
