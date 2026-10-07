from pathlib import Path
import csv,hashlib
T=Path(__file__).resolve().parents[1];R=T.parents[1]
entries=[
 ('V0_preflight_20260929','scripts/v0_preflight.py','configs/protocol.json','runs/V0_preflight_20260929/result.json'),
 ('V1_event_coverage_20260929_v2','scripts/v1_event_coverage.py','configs/r02.json','runs/V1_event_coverage_20260929_v2/result.json'),
 ('V2_R02_20260929_v1','scripts/v2_r02.py','configs/r02.json','runs/V2_R02_20260929_v1/result.json'),
 ('V2_R02_sensitivity_20260929_v3','scripts/v2b_r02_sensitivity.py','configs/r02.json','runs/V2_R02_sensitivity_20260929_v3/result.json'),
 ('V3_R05_D1_20260929_v1','scripts/v3_r05_d1.py','configs/r05_v2.json','runs/V3_R05_D1_20260929_v1/result.json'),
 ('V3_R05_controls_20260929_v2','scripts/v3_r05_controls.py','configs/r05_v2.json','runs/V3_R05_controls_20260929_v2/result.json'),
 ('V4_comparison_20260929_v1','scripts/v4_compare.py','configs/acceptance.json','runs/V4_comparison_20260929_v1/result.json'),
 ('V6_hard_tests_20260929_v1','scripts/v6_hard_tests.py','configs/protocol.json','runs/V6_hard_tests_20260929_v1/result.json')]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
rows=[]
for run,code,config,output in entries:
    rows.append({'run_id':run,'code_path':code,'code_sha256_current':sha(T/code),
      'config_path':config,'config_sha256':sha(T/config),'raw_input_manifest':'data_manifests/input_manifest.csv',
      'raw_input_manifest_sha256':sha(T/'data_manifests/input_manifest.csv'),
      'output_path':output,'output_sha256':sha(T/output),
      'note':'metadata assembled after immutable run; in-run result hash is authoritative if code later changed'})
p=T/'data_manifests/run_provenance.csv'
with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
print(p,len(rows))
