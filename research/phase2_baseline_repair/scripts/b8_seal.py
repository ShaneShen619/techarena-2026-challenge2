"""Seal final acceptance, experiment index and artifact hashes after reader QA."""
import csv
import hashlib
import json
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
p=TASK/'outputs/acceptance_results.json'
a=json.loads(p.read_text())
a['research_completion_status']='complete_B0_B8'
a['B8']='passed_docx_pdf_3_pages_visual_QA_reader_12_of_12'
a['independent_reader_status']='passed_12_questions_with_navigation_edits'
a['document_visual_status']='passed_Word_native_PDF_all_3_pages'
p.write_text(json.dumps(a,indent=2,ensure_ascii=False))
index=TASK/'notes/EXPERIMENT_INDEX.csv'
rows=list(csv.DictReader(index.open()))
new=[
 ('B1','B1_event_causality_20260930_v1','D3_official_unlabeled','outputs/event_audit.csv','41 exact original windows and per-CK future leak'),
 ('B2','B2_candidate_comparison_20260930_v4','D3_official_unlabeled','outputs/per_ck_predictions.csv','5 candidates by 8 CK; 35 future mutation groups pass'),
 ('B3','B3_mechanism_stress_20260930_v3','synthetic_mechanism','outputs/stress_results.csv','voltage/current/gap/counter/temperature controls'),
 ('B4','B4_same_condition_matrix_20260930_v1','D3_official_unlabeled','outputs/baseline_comparison_matrix.csv','original constant causal and quality gates; no MAE'),
 ('B5','B5_clean_extract_20260930_v2','official_interface','runs/B5_clean_extract_20260930_v2/official_full/output.csv','fresh venv validator and eight CK'),
 ('B6','B6_decision_20260930_v1','decision','outputs/acceptance_results.json','causal/interface GO; capacity superiority not testable'),
 ('B7','B7_independent_audit_20260930_v1','independent_read_only','notes/INDEPENDENT_AUDIT.md','CK1 CK2 raw recheck and caveats'),
 ('B8','B8_report_reader_20260930_v1','report_and_reader','outputs/LFP_SOH_官方基线修复与下一步决策报告.pdf','Word native render 3 pages; reader 12 of 12')]
keys=rows[0].keys()
for module,run,level,out,notes in new:
    rows.append(dict(module=module,run_id=run,status='complete',evidence_level=level,
        config_path='configs/protocol.json',input_manifest='data_manifests/input_manifest.csv',
        code_path='scripts/',output_path=out,notes=notes))
with index.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
paths=[
 'START_PROMPT.md','configs/protocol.json','configs/acceptance.json','configs/event_rules.json','configs/event_rules_v2.json','configs/frozen_manifest.json',
 'data_manifests/input_manifest.csv','data_manifests/external_inventory.csv',
 'outputs/EXECUTIVE_SUMMARY.md','outputs/NEXT_STEPS.md','outputs/REPRODUCE.md','outputs/acceptance_results.json',
 'outputs/LFP_SOH_官方基线修复与下一步决策报告.md','outputs/LFP_SOH_官方基线修复与下一步决策报告.docx','outputs/LFP_SOH_官方基线修复与下一步决策报告.pdf',
 'outputs/event_audit.csv','outputs/anomaly_raw_rows.csv','outputs/counter_audit.csv','outputs/per_ck_reference_audit.csv',
 'outputs/per_ck_predictions.csv','outputs/candidate_comparison.csv','outputs/baseline_comparison_matrix.csv',
 'outputs/stress_results.csv','outputs/stress_gate_cross.csv','outputs/data_eligibility.csv','outputs/information_budget.csv',
 'outputs/predictions_official_unlabeled.csv',
 'notes/B1_FINDINGS.md','notes/INDEPENDENT_AUDIT.md','notes/READER_TEST.md','notes/STATUS.md','notes/RESUME.md','notes/FAILURES.md','notes/EXPERIMENT_INDEX.csv',
 'candidates/causal_baseline_research_only_v2.zip','runs/B5_official_candidate_20260930_v2/package_manifest.json',
 'runs/B5_clean_extract_20260930_v2/validation_report.txt','runs/B5_clean_extract_20260930_v2/official_full/output.csv']
with (TASK/'outputs/artifact_manifest.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['relative_path','bytes','sha256','exists']);w.writeheader()
    for rel in paths:
        file=TASK/rel
        exists=file.is_file()
        w.writerow(dict(relative_path=rel,bytes=file.stat().st_size if exists else '',
            sha256=hashlib.sha256(file.read_bytes()).hexdigest() if exists else '',exists=exists))
assert all((TASK/rel).is_file() for rel in paths)
print('sealed',len(paths),'artifacts')
