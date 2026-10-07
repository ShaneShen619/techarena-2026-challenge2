"""Complete run ledger with honest unknown timing for earlier scripts."""
import csv,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
T=Path(__file__).resolve().parents[1];N=T/'notes';O=T/'outputs'
old=N/'EXPERIMENT_INDEX.csv'
if not (N/'EXPERIMENT_INDEX_v1.csv').exists():shutil.copy2(old,N/'EXPERIMENT_INDEX_v1.csv')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else ''
scripts={
 'N0_causality':'n0_causality.py','N0_original_leak':'n0_original_leak.py','N0_preflight':'n0_preflight.py','N0_stress_hit':'n0_hit_audit.py',
 'N1_registry':'n1_registry.py','N2_transfer_split':'n2_stage_transfer.py','N2_transfer_development':'n2_transfer_dev.py',
 'N3_N4_mechanisms':'n3_n4_mechanisms.py','N5_candidate_causality':'n5_causality_candidate.py','N5_pipeline':'capacity_pipeline.py',
 'N6_Ji_holdout':'capacity_pipeline.py','N7_measurement_plan':'n7_measurement_templates.py','N8_audit_response':'n8_audit_response.py',
 'N9_report_reader':'n9_build_docx.py'}
rows=[]
run=T/'runs/N9_run_index_20260930_v2';run.mkdir(exist_ok=True)
(run/'result.json').write_text(json.dumps({'status':'index_generation_in_progress','note':'updated after index creation'},indent=2))
(run/'COMPLETED').write_text('complete\n')
for p in sorted((T/'runs').iterdir()):
 if not p.is_dir():continue
 script=next((value for key,value in scripts.items() if p.name.startswith(key)), '')
 result=json.loads((p/'result.json').read_text()) if (p/'result.json').exists() else {}
 if not isinstance(result,dict):result={'record_type':'list_result'}
 end=datetime.fromtimestamp((p/'COMPLETED').stat().st_mtime,timezone.utc).isoformat() if (p/'COMPLETED').exists() else ''
 cfg=T/'configs/freeze_manifest.json' if p.name.startswith(('N5_pipeline','N6','N8','N9')) else T/'configs/protocol_v1.json'
 if p.name.startswith('N2_transfer_development'):
  cfg=T/('configs/transfer_final_freeze_v2.json' if p.name.endswith('v2') else 'configs/transfer_initial_v1.json')
 rows.append(dict(module=p.name.split('_')[0],run_id=p.name,
  started_utc=result.get('started_utc','unknown_not_recorded_at_start'),ended_utc=end,
  time_basis='start_run_result_if_present_else_unknown; end_COMPLETED_mtime',
  command=('research/phase2_validation/.venv/bin/python ' if script!='n2_transfer_dev.py' else 'python3 ')+('research/phase2_capacity_validation/scripts/'+script if script else 'independent_readonly_or_historical_substages'),
  code_sha256_current=sha(T/'scripts'/script) if script else '',
  code_hash_limit='current_code_may_differ_from_early_v1; frozen_candidate_hash_in_freeze_manifest',
  config_path=str(cfg.relative_to(T)),config_sha256_current=sha(cfg),
  source_manifest='manifests/input_code_config_sha256.csv',source_zip_sha256=sha(T/'downloads/SLBs_LFP_charging_data.zip'),
  output_result=str((p/'result.json').relative_to(T)) if (p/'result.json').exists() else '',
  completion_marker=str((p/'COMPLETED').relative_to(T)) if (p/'COMPLETED').exists() else '',
  status='complete' if (p/'COMPLETED').exists() else 'incomplete',
  notes='historical run details in result.json; no retuning after sealed score'))
with old.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
(run/'result.json').write_text(json.dumps({'indexed_runs':len(rows),'known_start_times':sum(x['started_utc']!='unknown_not_recorded_at_start' for x in rows),
 'unknown_start_times':sum(x['started_utc']=='unknown_not_recorded_at_start' for x in rows),'note':'unknowns not invented'},indent=2))
print((run/'result.json').read_text())
