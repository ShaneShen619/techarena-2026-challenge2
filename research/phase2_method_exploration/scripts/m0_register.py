"""Register M0 runs and machine-check exact historical reproductions."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OLD=ROOT/'research/phase2_temperature_improvement/reassessment_20260928'
RUNS=TASK/'runs'
INDEX=TASK/'notes/EXPERIMENT_INDEX.csv'

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

checks={}
for name,run in [('diagnostic_summary.json','M0_ablation_replay_v1'),
                 ('pulse_candidate_summary.json','M0_pulse_replay_v1')]:
    old=json.loads((OLD/name).read_text())
    new=json.loads((RUNS/run/name).read_text())
    checks[name]={'exact_json_match':old==new,'old_sha256':sha(OLD/name),
                  'new_sha256':sha(RUNS/run/name)}
    if old!=new: raise AssertionError(f'historical reproduction mismatch: {name}')
(TASK/'data_manifests/m0_reproduction_comparison.json').write_text(json.dumps(checks,indent=2)+'\n')

rows=[
    ('M0_ablation_replay_v1','复现历史七组消融','scripts/m0_reproduce_ablation.py',
     'runs/M0_ablation_replay_v1/diagnostic_summary.json','runs/M0_ablation_replay_v1',
     'P1 existing 180-target proxy','leave one physical cell/temperature group out','success',
     '七组汇总与历史 JSON 完全一致；D0 特权输入结果不得转为 D1 排名'),
    ('M0_pulse_replay_v1','复现 20 A 脉冲初筛数','scripts/m0_reproduce_pulses.py',
     'runs/M0_pulse_replay_v1/pulse_candidate_summary.json','runs/M0_pulse_replay_v1',
     'none','all official unlabeled retrospective input audit','success',
     '41 候选，CK7 前 39；尚未逐项认证'),
    ('M0_smoke_v1','折训练序列化首次冒烟','scripts/m0_smoke.py',
     'notes/FAILURES.md','runs/M0_smoke_v1',
     'single P1 proxy point','one held cell','failed',
     '新进程缺旧模型模块搜索路径；保留失败并在 v2 修复'),
    ('M0_smoke_v2','折训练/事件/官方前缀/序列化/图形冒烟','scripts/m0_smoke.py',
     'runs/M0_smoke_v2/smoke.json','runs/M0_smoke_v2',
     'single P1 proxy point; official CK1 unlabeled','one held cell','success',
     '新进程预测差 0；官方仅接口与回退分支冒烟'),
    ('M0_source_inventory_v1','原始文件和字段资格','scripts/m0_inventory.py',
     'data_manifests/source_inventory_summary.json','data_manifests/source_inventory.csv',
     'none','not applicable','success',
     'P1/官方哈希匹配；TU 本轮仅大小与修改时间匹配旧全量哈希'),
    ('M0_official_support_v1','官方浅充无标签输入支持','scripts/m0_official_support.py',
     'data_manifests/official_charge_support_summary.json','data_manifests/official_charge_support.csv',
     'none','retrospective D3 input audit; not online calibration','success',
     '41 合格充电段，33 段 <50 Ah；3.38–3.42 V 四芯全覆盖'),
    ('M0_D1_crop_raw_v1','P1 原始30秒局部片段与因果可见性','scripts/m0_crop_p1.py',
     'data_manifests/d1_target_visibility_final_summary.json','data_manifests/d1_cropped_events.csv',
     'P1 180-target proxy (labels separate)','six physical cells, 15/20/30 Ah, cold/persistent','success',
     '914 原事件，910 有三预算原始越线片段；1080 目标视图，无未来片段'),
    ('M0_visibility_adversarial_v1','适配器未来行和标签注入反证','tests/test_visibility_boundary.py',
     'data_manifests/d1_target_visibility_final_summary.json','src/visibility.py',
     'none','1080 target views','success',
     '1080 视图逐条检查；未来行、目标标签和完整 CC 深度注入均拒绝'),
]
with INDEX.open(newline='') as stream:
    reader=csv.DictReader(stream)
    fields=reader.fieldnames
    existing=list(reader)
assert fields is not None
seen={x['run_id'] for x in existing}
config_sha=sha(TASK/'configs/acceptance.json')
input_sha=sha(TASK/'data_manifests/source_inventory_summary.json')
for run_id,question,code,metric,artifact,label,split,status,conclusion in rows:
    if run_id in seen: continue
    existing.append({'run_id':run_id,'module':'M0','question':question,'input_sha256':input_sha,
                     'code_sha256':sha(TASK/code),'config_sha256':config_sha,
                     'label_protocol':label,'split':split,'seed':'20260928' if 'ablation' in run_id else 'n/a',
                     'status':status,'metric_path':metric,'artifact_path':artifact,
                     'elapsed_s':'not_recorded','peak_rss_mb':'not_recorded','conclusion':conclusion})
with INDEX.open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader()
    writer.writerows(existing)
print(json.dumps({'historical_checks':checks,'index_rows':len(existing)},ensure_ascii=False))
