"""Assemble cross-run tables without re-fitting or relabeling evidence tiers."""
from pathlib import Path
import json
import pandas as pd
TASK=Path(__file__).resolve().parents[1];OUT=TASK/'outputs'
v3=TASK/'runs/V3_R05_D1_20260929_v1'
d=pd.read_csv(v3/'per_target_predictions.csv')
assert len(d)==2160 and d.evidence_tier.eq('D1').all()
d.to_csv(OUT/'per_target_predictions.csv',index=False)
m=pd.read_csv(v3/'metrics.csv')
rows=[]
for r in m.itertuples():
    rows.append({'method':f'R05_{r.arm}_{r.objective}','evidence_tier':'D1','physical_entity':'P1_single_cell',
       'protocol':'20Ah_deep_charge_prefix_proxy_to_single_cell_high_rate_discharge',
       'n_entities':r.n_cells,'n_targets':r.n_targets,'macro_mae_pp':r.macro_mae_pp,
       'worst_entity_mae_pp':r.worst_cell_mae_pp,'max_abs_error_pp':r.max_abs_error_pp,
       'late_mae_pp':r.late_mae_pp,'late_bias_pp':r.late_signed_bias_pp,
       'official_capacity_valid':False,'capacity_status':'D1_proxy_measured'})
for r in pd.read_csv(TASK/'runs/V4_comparison_20260929_v1/nested_selected_metrics.csv').itertuples():
    rows.append({'method':f'R05_nested_selected_{r.objective}','evidence_tier':'D1','physical_entity':'P1_single_cell',
       'protocol':'20Ah_deep_charge_prefix_proxy_to_single_cell_high_rate_discharge','n_entities':6,'n_targets':180,
       'macro_mae_pp':r.macro_mae_pp,'worst_entity_mae_pp':r.worst_cell_mae_pp,'max_abs_error_pp':r.max_abs_error_pp,
       'late_mae_pp':r.late_mae_pp,'late_bias_pp':r.late_bias_pp,'official_capacity_valid':False,
       'capacity_status':'D1_proxy_measured'})
rows.append({'method':'R02_gated_R01_CK0_constant','evidence_tier':'D3','physical_entity':'one_official_4S_group',
 'protocol':'CK0_released_5p1A_pack_first_11p2V','n_entities':1,'n_targets':8,
 'macro_mae_pp':pd.NA,'worst_entity_mae_pp':pd.NA,'max_abs_error_pp':pd.NA,
 'late_mae_pp':pd.NA,'late_bias_pp':pd.NA,'official_capacity_valid':False,
 'capacity_status':'CK1_CK7_true_capacity_hidden'})
pd.DataFrame(rows).to_csv(OUT/'method_comparison.csv',index=False)
budget=[
 ('D3','CK0_capacity_Ah','released CK0 only','initial','R01/R02','allowed'),
 ('D3','CK0_loaded_pack_and_cell_voltage','CK0 reference curve','initial','R02','allowed_loaded_not_OCV'),
 ('D3','operation_voltage_current_temperature','timestamp <= until','per_checkup','R02/quality','allowed_but_unqualified_for_capacity'),
 ('D3','CK1_CK7_true_capacity','hidden','any','none','forbidden'),
 ('D1','anchor_SO H_pp'.replace(' ',''),'first P1 discharge anchor per cell','initial','R05','allowed'),
 ('D1','age_days_event_count','strict prefix','target','R05','allowed_not_true_Ah'),
 ('D1','selected_event_temperature','first/recent/current 20Ah cropped event','target','R05','allowed_sampled_not_continuous'),
 ('D1','cell_id_target_ordinal','grouping/scoring only','target','none','forbidden_as_predictor'),
 ('D1','target_capacity_and_future_source_rows','target or later','future','none','forbidden'),
 ('S','synthetic_capacity_and_voltage','generated','mechanism','R02','not_official_validation')]
pd.DataFrame(budget,columns=['evidence_tier','input','source_or_window','availability','consumer','decision']).to_csv(OUT/'information_budget.csv',index=False)
pd.read_csv(TASK/'runs/V2_R02_20260929_v1/predictions_official_unlabeled.csv').to_csv(OUT/'predictions_official_unlabeled.csv',index=False)
print({'d1_rows':len(d),'methods':len(rows),'information_budget_rows':len(budget)})
