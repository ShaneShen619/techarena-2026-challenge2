"""Final acceptance, run index and artifact hashes after Word/PDF visual QA."""
import csv,hashlib,json,subprocess
from pathlib import Path
T=Path(__file__).resolve().parents[1];O=T/'outputs'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
required=['LFP_SOH_真实容量验证与测量计划.md','LFP_SOH_真实容量验证与测量计划.docx','LFP_SOH_真实容量验证与测量计划.pdf',
 'EXECUTIVE_SUMMARY.md','NEXT_STEPS.md','REPRODUCE.md','DATA_HANDOFF.md','PRIOR_EVIDENCE_CORRECTIONS.md',
 'source_registry.csv','data_eligibility.csv','download_log.csv','label_provenance.csv',
 'causal_coverage.csv','causal_mutations.csv','event_state_comparison.csv','counter_semantics.csv','integration_sensitivity.csv',
 'split_manifest.csv','per_target_predictions.csv','per_entity_metrics.csv','candidate_comparison.csv',
 'measurement_plan.csv','acquisition_template.csv','pipeline_result_v2.json']
missing=[x for x in required if not (O/x).is_file()]
assert not missing,missing
assert len(list((T/'rendered').glob('word_native_verified_page-*.png')))==3
flags={'A_research_completeness':{'status':'passed','basis':'N0-N9 executable work, source qualification, reports, audit and reader 12/12'},
 'B_pipeline_causality_interface':{'status':'passed','basis':'8 CK future rows; 120 prior and 96 candidate mutation cases; 3 RPT rejection/acceptance tests; one-shot score guard'},
 'C_mechanism_evidence':{'status':'partially_supported_capacity_effect_not_testable','basis':'41 start windows and 2701 current pieces; 41 pulse counter exception, no causal SOC identification'},
 'D_prior_development_proxy_performance':{'status':'historical_only_not_independent_confirmation','basis':'D1/P1 six previously used single cells not rescored as new confirmation'},
 'E_different_protocol_real_capacity':{'status':'exploratory_scored_not_official_pp','n_cells':8,'macro_MAE_Ah':0.1380913073880914,'worst_Ah':0.25872712511490237,
  'basis':'author prior mean of 3 tests; single-cell one stage; researcher nonblind source filenames'},
 'F_independent_same_protocol_4S_capacity':{'status':'not_testable_no_matched_capacity_labels','macro_MAE_pp':None,'worst_entity_MAE_pp':None,'late_MAE_pp':None},
 'G_official_hidden_CK1_CK7':{'status':'not_testable_hidden_truth','n_unique_hidden_checkups':7,'macro_MAE_pp':None,'worst_entity_MAE_pp':None,'late_MAE_pp':None},
 'high_performance_target':{'status':'not_testable','goals':'macro<=1pp,worst<=2pp,max<=5pp,>=20pct relative strong legal baseline and no worst/late regression'}}
(O/'acceptance_results.json').write_text(json.dumps(flags,indent=2,ensure_ascii=False))
for run_id,summary in [('N5_pipeline_20260930_v1','inventory qualify freeze extract predict completed; official 40 unlabeled predictions'),
 ('N6_Ji_holdout_20260930_v1','sealed 8-cell single protocol-different score exactly once'),
 ('N8_independent_audit_20260930_v1','readonly independent recomputation; issues versioned in audit response'),
 ('N9_report_reader_20260930_v1','12/12 fresh-reader, Word native PDF 3 pages each visually checked')]:
 r=T/'runs'/run_id;r.mkdir(exist_ok=True)
 (r/'result.json').write_text(json.dumps({'run_id':run_id,'summary':summary,'task_version':'2026-09-30',
  'freeze_sha256':sha(T/'configs/freeze_manifest.json'),'source_zip_sha256':sha(T/'downloads/SLBs_LFP_charging_data.zip'),
  'script_sha256':sha(Path(__file__))},indent=2))
 (r/'COMPLETED').write_text('complete\n')
entries=[]
for p in sorted(T.rglob('*')):
 if not p.is_file() or any(x in p.parts for x in ['__pycache__','.DS_Store']):continue
 rel=str(p.relative_to(T))
 if rel.startswith(('downloads/','staging/','sealed/','rendered/','tmp/')):continue
 if rel=='outputs/artifact_manifest.csv':continue
 entries.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p),role='deliverable' if rel.startswith('outputs/') else 'code_config_run_or_note'))
with (O/'artifact_manifest.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=entries[0]);w.writeheader();w.writerows(entries)
idx=[]
for p in sorted((T/'runs').glob('*')):
 if not p.is_dir():continue
 idx.append(dict(module=p.name.split('_')[0],run_id=p.name,status='complete' if (p/'COMPLETED').exists() else 'incomplete',
  config_path='configs/freeze_manifest.json' if p.name.startswith(('N5','N6','N8','N9')) else 'configs/protocol_v1.json',
  input_hash_manifest='manifests/input_code_config_sha256.csv',code_path='scripts/',
  output_path=str((p/'result.json').relative_to(T)) if (p/'result.json').exists() else '',
  notes='task_only; see run result, freeze and audit notes'))
with (T/'notes/EXPERIMENT_INDEX.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=idx[0]);w.writeheader();w.writerows(idx)
print(json.dumps({'required_outputs':len(required),'artifact_rows':len(entries),'runs':len(idx),
 'research_status':'complete','official_capacity_performance':'not_testable'},ensure_ascii=False))
