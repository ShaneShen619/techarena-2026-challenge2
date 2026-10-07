"""Seal unlabeled predictions, information budget and factual acceptance state."""
import hashlib
import json
from pathlib import Path
import pandas as pd
TASK=Path(__file__).resolve().parents[1]
source=TASK/'runs/B5_clean_extract_20260930_v2/official_full/output.csv'
raw=pd.read_csv(source)
assert len(raw)==8 and raw.checkup.tolist()==[f'CK{i}' for i in range(8)]
out=raw.rename(columns={'SOH_est':'SOH_est_pct'})
out['capacity_truth_Ah']=pd.NA;out['capacity_truth_pct']=pd.NA;out['capacity_error_pp']=pd.NA
out['label_status']=['released_anchor_only']+['hidden']*7
out['evidence_level']='official_unlabeled_prefix'
out['protocol']='official_four_series_operating_prefix'
out['candidate']='causal_equivalent_none_v2_zip'
out.to_csv(TASK/'outputs/predictions_official_unlabeled.csv',index=False)
assert source.read_bytes()==(TASK/'runs/B5_official_candidate_20260930_v1/output.csv').read_bytes()
original=pd.read_csv(TASK/'runs/B0_example_20260930_v1/output.csv').rename(columns={'SOH_est':'original_pct'})[['checkup','original_pct']]
constant=pd.read_csv(TASK/'runs/B0_ck0_constant_20260930_v1/output.csv').rename(columns={'SOH_est':'CK0_constant_pct'})[['checkup','CK0_constant_pct']]
matrix=out[['checkup','date','SOH_est_pct']].merge(original,on='checkup').merge(constant,on='checkup')
detail=pd.read_csv(TASK/'outputs/per_ck_predictions.csv')
for name in ['range','gap','combined','start']:
    matrix=matrix.merge(detail[detail.candidate==name][['checkup','prediction_pct']].rename(columns={'prediction_pct':name+'_pct'}),on='checkup')
matrix['truth_pct']=pd.NA;matrix['error_pp']=pd.NA;matrix['evidence_level']='official_unlabeled'
matrix.to_csv(TASK/'outputs/baseline_comparison_matrix.csv',index=False)
budget=pd.DataFrame([
 dict(item='official_CK0_capacity',available=True,scope='one_4S_pack_one_anchor',value='100.41 Ah',capacity_accuracy_test=False),
 dict(item='official_CK1_CK7_capacity',available=False,scope='seven_hidden_targets',value='',capacity_accuracy_test=False),
 dict(item='official_operation',available=True,scope='one_4S_pack_8_checkpoints',value='1572894 rows; 41 extracted windows',capacity_accuracy_test=False),
 dict(item='D1_six_cell_proxy',available=True,scope='6_reused_single_cells_180_targets',value='different protocol, no direct 13.4 V 4S mapping',capacity_accuracy_test=False),
 dict(item='TU_8S_field',available=True,scope='28_8S_systems',value='no paired reference capacity',capacity_accuracy_test=False),
 dict(item='Che_single_cell',available=True,scope='11_cells',value='normalized full-charge labels, different protocol',capacity_accuracy_test=False),
 dict(item='independent_four_series_D2',available=False,scope='none_qualified_local',value='',capacity_accuracy_test=False)])
budget.to_csv(TASK/'outputs/information_budget.csv',index=False)
accept={
 'version':'2026-09-30-final-v1',
 'research_completion_status':'pending_B8_document_reader_test',
 'B0':'passed','B1':'passed','B2':'passed_35_future_mutations','B3':'passed_mechanism_stress_not_capacity','B4':'passed_unlabeled_fair_comparison',
 'B5':'passed_clean_extraction_fresh_venv_official_validator_and_all_8_CK',
 'B6':'no_go_for_capacity_superiority_claim; go_for_causal_repair_research_candidate',
 'B7':'passed_independent_read_only_audit','B8':'pending',
 'official_capacity_MAE_pp':None,'D1_capacity_MAE_pp':None,'independent_D2_capacity_MAE_pp':None,
 'performance_target_status':'not_testable_without_CK1_CK7_or_matched_independent_D2',
 'competition_upload_status':'not_authorized_not_done'}
(TASK/'outputs/acceptance_results.json').write_text(json.dumps(accept,indent=2,ensure_ascii=False))
print(json.dumps(accept,indent=2,ensure_ascii=False))
