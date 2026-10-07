"""Append immutable M1 experiment references to the shared ledger."""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
INDEX=TASK/'notes/EXPERIMENT_INDEX.csv'
def sha(name:str)->str:
    return hashlib.sha256((TASK/name).read_bytes()).hexdigest()

with INDEX.open(newline='') as stream:
    reader=csv.DictReader(stream)
    fields=reader.fieldnames
    rows=list(reader)
assert fields
seen={x['run_id'] for x in rows}
config=sha('configs/acceptance.json')
entries=[
 ('M1_certification_v1','首次逐条信号认证','scripts/m1_certify_events.v1.py',
  'runs/M1_certification_v1/summary.json','runs/M1_certification_v1','failed',
  '2 段因前序充电同秒重复时间戳误拒；代码与输出保留'),
 ('M1_certification_v2','修正同秒重复行后认证','scripts/m1_certify_events.py',
  'runs/M1_certification_v2/summary.json','runs/M1_certification_v2','success',
  '41/41 认证，39 段在 CK7 前；命名放电计数器对这类脉冲不增长'),
 ('M1_voltage_forecast_v1','同输入未来脉冲电压预测与温度反证','scripts/m1_voltage_forecast.py',
  'runs/M1_voltage_forecast_v1/summary.json','runs/M1_voltage_forecast_v1','success',
  '上一同温曲线首1Ah校正 MAE 0.680mV，三种候选均未整体胜出；容量不可评分'),
 ('M1_event_gallery_v1','全 41 条认证事件图册','scripts/m1_event_gallery.py',
  'runs/M1_voltage_forecast_v1/all_41_certified_pulses.pdf','runs/M1_voltage_forecast_v1','success',
  '41 页全事件图册和前向方法误差图'),
]
for run_id,question,code,metric,artifact,status,conclusion in entries:
    if run_id in seen:continue
    rows.append({'run_id':run_id,'module':'M1','question':question,
                 'input_sha256':sha('data_manifests/source_inventory_summary.json'),
                 'code_sha256':sha(code),'config_sha256':config,
                 'label_protocol':'official operation only; CK1–CK7 truth hidden',
                 'split':'chronological within same temperature and physical pack',
                 'seed':'n/a','status':status,'metric_path':metric,
                 'artifact_path':artifact,'elapsed_s':'not_recorded',
                 'peak_rss_mb':'not_recorded','conclusion':conclusion})
with INDEX.open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader();writer.writerows(rows)
print({'index_rows':len(rows)})
