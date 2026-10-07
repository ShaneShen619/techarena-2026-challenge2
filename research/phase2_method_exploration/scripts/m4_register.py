"""Register M4 revisions, completed mechanism and causal deep-charge audits."""
from __future__ import annotations
import csv,hashlib
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
INDEX=TASK/'notes/EXPERIMENT_INDEX.csv'
def sha(path):return hashlib.sha256((TASK/path).read_bytes()).hexdigest()
with INDEX.open(newline='') as f:r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
assert fields
seen={x['run_id'] for x in rows}
entries=[
 ('M4_state_identifiability_v1','scripts/m4_state_identifiability.v1.py','configs/m4_state.json','summary.json','superseded: official early profile used four-cell median reference instead of corresponding cell'),
 ('M4_state_identifiability_v2','scripts/m4_state_identifiability.v2.py','configs/m4_state.json','summary.json','superseded: corrected per-cell reference; no prior RC baseline'),
 ('M4_state_identifiability_v3','scripts/m4_state_identifiability.v3.py','configs/m4_state.json','summary.json','superseded: prior RC added; uncertainty did not accumulate by event'),
 ('M4_state_identifiability_v4','scripts/m4_state_identifiability.py','configs/m4_state.json','summary.json','final M4 pulse protocol: 0/148 gated Q updates; CK0+RC 2.813mV vs last pulse 0.680mV'),
 ('M4_confounds_v2','scripts/m4_confounds.py','configs/m4_state.json','summary.json','synthetic multistart: shallow excellent voltage fit with broad Q; constant I bias/R exact confounding'),
 ('M4_deep_charge_audit_v1','scripts/m4_deep_charge_audit.py','configs/m4_deep_audit.json','summary.json','posthoc deep-charge proxy strict prefix; 2025-09-02 after CK7 excluded'),
 ('M4_deep_curve_profile_v1','scripts/m4_deep_curve_profile.py','configs/m4_deep_audit.json','summary.json','charge/discharge shape transfer needs ~77mV offset; Q profile structure-sensitive')]
for run_id,code,config,metric,note in entries:
 if run_id in seen:continue
 assert (TASK/'runs'/run_id/metric).exists()
 rows.append({'run_id':run_id,'module':'M4','question':'capacity/SOC observability under official pulse and delayed deep-charge evidence',
              'input_sha256':sha('data_manifests/source_inventory_summary.json'),
              'code_sha256':sha(code),'config_sha256':sha(config),
              'label_protocol':'D3 official unlabeled voltage or S synthetic truth; deep charge Ah is not capacity label',
              'split':'causal previous same-temperature pulse; synthetic morphology mismatch; deep charge strict checkup prefix',
              'seed':'20260928','status':'completed_with_capacity_label_limit',
              'metric_path':f'runs/{run_id}/{metric}','artifact_path':f'runs/{run_id}/{metric}',
              'elapsed_s':'not_recorded','peak_rss_mb':'not_recorded','conclusion':note})
with INDEX.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print({'index_rows':len(rows)})
