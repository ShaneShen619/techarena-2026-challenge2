from pathlib import Path
import json
import pandas as pd
TASK=Path(__file__).resolve().parents[1];OUT=TASK/'outputs'
v1=TASK/'runs/V1_event_coverage_20260929_v2/result.json'
v2=TASK/'runs/V2_R02_sensitivity_20260929_v3/result.json'
v3=TASK/'runs/V3_R05_D1_20260929_v1/metrics.csv'
v4=TASK/'runs/V4_comparison_20260929_v1/nested_selected_metrics.csv'
v6=TASK/'runs/V6_hard_tests_20260929_v1/result.json'
for p in [v1,v2,v3,v4,v6,OUT/'LFP_SOH_文献驱动验证与双路线决策报告.docx',OUT/'LFP_SOH_文献驱动验证与双路线决策报告.pdf',TASK/'notes/INDEPENDENT_AUDIT.md',TASK/'notes/READER_TEST.md']:
    assert p.exists(),p
assert 'PASSED' in (TASK/'candidates/official_gated/validation_report.txt').read_text()
assert len(list((TASK/'rendered/final').glob('page-*.png')))==5
m=pd.read_csv(v3);q=m[(m.objective=='average')&(m.arm=='matched_no_T')].iloc[0]
chosen=pd.read_csv(v4);a=chosen[chosen.objective=='average'].iloc[0];tail=chosen[chosen.objective=='tail'].iloc[0]
assert q.macro_mae_pp>1 and a.macro_mae_pp>q.macro_mae_pp and tail.late_mae_pp>a.late_mae_pp
def detail(status,reason,tier,runs,refs):return {'status':status,'reason':reason,'evidence_level':tier,'run_ids':runs,'artifact_refs':refs}
details={
 'environment_smoke_pass':detail('passed','raw event, CK0, prefix, regression, serialization and Word smoke executed','V0',['V0_preflight_20260929'],['notes/READINESS.md']),
 'data_provenance_verified':detail('passed','input hashes and D1 deep-charge origin checked; D2-compatible absent','D0/D1/D3',['V0_preflight_20260929'],['data_manifests/input_manifest.csv','outputs/data_eligibility.csv']),
 'protocol_frozen':detail('passed','v1 configs before V1; R05 v2 before fitting; R02 v1 unit mismatch corrected in versioned sensitivity','D1/D3/S',['V2_R02_sensitivity_20260929_v3','V3_R05_D1_20260929_v1'],['configs/frozen_manifest.json','configs/r05_v2.json','notes/PREREGISTRATION.md']),
 'r02_implemented':detail('passed','loaded CK0 pack template, root, bounded profile, synthetic mismatch and gated official fallback','S/D3',['V2_R02_20260929_v1','V2_R02_sensitivity_20260929_v3'],['src/r02.py','runs/V2_R02_sensitivity_20260929_v3/sensitivity_summary.csv']),
 'r02_identifiability_status':detail('inconclusive','no qualified >=5Ah near-reference operating windows; reference state/T unknown; synthetic nuisance mimic scale','S/D3',['V1_event_coverage_20260929_v2','V2_R02_sensitivity_20260929_v3'],['outputs/event_eligibility.csv','runs/V2_R02_sensitivity_20260929_v3/paired_profiles.csv']),
 'r05_implemented':detail('passed','executable anchored ridge prototype, nested physical-cell LOCO and temperature controls; official group update unqualified','D1',['V3_R05_D1_20260929_v1','V3_R05_controls_20260929_v2'],['scripts/v3_r05_d1.py','runs/V3_R05_D1_20260929_v1/per_target_predictions.csv']),
 'r05_capacity_validation_status':detail('failed','D1 proxy sampled-temperature arm loses matched no-T basis and high target; D2/D3 capacity untestable','D1',['V3_R05_D1_20260929_v1','V4_comparison_20260929_v1'],['outputs/method_comparison.csv']),
 'r05_D1_proxy':detail('failed','sampled T macro 4.759 pp vs matched no-T 3.521 pp; six reused single cells','D1',['V3_R05_D1_20260929_v1'],['runs/V3_R05_D1_20260929_v1/metrics.csv']),
 'r05_D2_compatible':detail('not_testable','no independent new physical 4S group with official-matched capacity labels','D2-compatible',[],['outputs/data_eligibility.csv']),
 'r05_D3_official':detail('not_testable','CK1–CK7 capacity truth hidden; one CK0 anchor cannot fit group prior','D3',[],['data/checkups/checkup_capacities_released.csv']),
 'causal_hard_tests_pass':detail('passed','future deletion/refit, extreme operating mutation, serialization, all CK coverage and isolated clean-copy official validator','D3',['V6_official_candidate_20260929_v1','V6_hard_tests_20260929_v1','V6_clean_extract_20260929_v1'],['runs/V6_hard_tests_20260929_v1/result.json','runs/V6_clean_extract_20260929_v1/result.json']),
 'incremental_capacity_signal_status':detail('inconclusive','sampled temperature feature gain unsupported on D1; official increment untestable','D1/D3',['V3_R05_D1_20260929_v1','V3_R05_controls_20260929_v2'],['runs/V3_R05_controls_20260929_v2/control_metrics.csv']),
 'd1_high_targets_met':detail('failed','macro/worst/max exceed 1/2/5 pp and no 20% gain over strong simple baseline','D1',['V3_R05_D1_20260929_v1','V4_comparison_20260929_v1'],['outputs/method_comparison.csv']),
 'improvement_vs_previous_best':detail('failed','new nested R05 5.147 pp macro vs historical frozen TCN 2.851 pp on same developed cells','D1',['V4_comparison_20260929_v1'],['runs/V4_comparison_20260929_v1/result.json']),
 'tail_and_worst_entity_status':detail('failed','tail-priority selected late 9.385 vs average-priority 8.940 pp; worst remains >2 pp','D1',['V4_comparison_20260929_v1'],['runs/V4_comparison_20260929_v1/nested_selected_metrics.csv']),
 'external_transfer_confirmation':detail('not_testable','no eligible same-protocol new group; Che/TU do not meet reference protocol','D2-compatible',[],['outputs/data_eligibility.csv']),
 'compatible_independent_group_capacity_confirmation':detail('not_testable','new independent 4S RPT package absent','D2-compatible',[],['outputs/D2_MEASUREMENT_PROTOCOL.md']),
 'official_ck1_ck7_accuracy_verified':detail('not_testable','competition hides CK1–CK7 truth; D3 predictions are unlabeled','D3',['V6_official_candidate_20260929_v1'],['outputs/predictions_official_unlabeled.csv']),
 'independent_audit_status':detail('passed','independent raw/metric audit; R02 v1 issue corrected, v3 last small safeguard self-checked','D1/D3/S',['V1_event_coverage_20260929_v2','V3_R05_D1_20260929_v1','V2_R02_sensitivity_20260929_v3'],['notes/INDEPENDENT_AUDIT.md']),
 'reader_test_status':detail('passed','no-context reader answered 12/12; first D2 raw-field ambiguity revised and retested','document',[],['notes/READER_TEST.md']),
 'word_render_verified':detail('passed','5-page PDF rendered to PNG and all pages visually checked; split table repeats header','document',[],['rendered/final/page-1.png','rendered/final/page-5.png']),
 'research_complete':detail('passed','V0–V8 executable components, constrained module decisions, independent review and all documents delivered; capacity performance separate','D1/D3/S',['V0_preflight_20260929','V1_event_coverage_20260929_v2','V2_R02_sensitivity_20260929_v3','V3_R05_D1_20260929_v1','V4_comparison_20260929_v1','V6_hard_tests_20260929_v1'],['outputs/LFP_SOH_文献驱动验证与双路线决策报告.pdf'])
}
res={'version':'2026-09-29-final','environment_smoke_pass':True,'data_provenance_verified':True,'protocol_frozen':True,
 'r02_implemented':True,'r02_identifiability_status':'insufficient_current_D3',
 'r05_implemented':True,'r05_capacity_validation_status':'D1_proxy_failed_D2_D3_not_testable',
 'causal_hard_tests_pass':True,'incremental_capacity_signal_status':'not_supported_for_sampled_T_D1;official_not_testable',
 'd1_high_targets_met':False,'improvement_vs_previous_best':False,'tail_and_worst_entity_status':'worse_with_tail_priority',
 'external_transfer_confirmation':False,'compatible_independent_group_capacity_confirmation':False,
 'official_ck1_ck7_accuracy_verified':False,'independent_audit_status':'passed_with_versioned_R02_correction',
 'reader_test_status':'passed_12_of_12_after_revision','word_render_verified':True,'research_complete':True,
 'performance_target_met':False,'official_capacity_performance_status':'not_testable_hidden_truth',
 'acceptance_details':details}
(OUT/'acceptance_results.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in res.items() if k!='acceptance_details'},ensure_ascii=False))
