"""Independent score recomputation and condition inventory for M2."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M2_compiled_v1'
OUT.mkdir(parents=True,exist_ok=False)
cases=[
 ('M2_primary_v1','20Ah persistent, protocol v1.3'),
 ('M2_20Ah_no_count_v1','20Ah persistent, no prefix count'),
 ('M2_primary_v2','20Ah persistent, protocol v1.4 main'),
 ('M2_15Ah_persistent_v1','15Ah persistent'),
 ('M2_30Ah_persistent_v1','30Ah persistent'),
 ('M2_20Ah_cold_v1','20Ah cold'),
 ('M2_3p45_persistent_v1','20Ah endpoint 3.45V'),
 ('M2_3p55_persistent_v1','20Ah endpoint 3.55V'),
 ('M2_full_tail_persistent_v1','20Ah completed deep tail'),
 ('M2_mid_event_persistent_v1','20Ah fixed event middle'),
 ('M2_mid_rbf_age_only_v1','mid RBF age only'),
 ('M2_mid_rbf_age_voltage_v1','mid RBF age + voltage'),
 ('M2_mid_rbf_age_current_v1','mid RBF age + current'),
 ('M2_mid_rbf_age_voltage_current_v1','mid RBF age + voltage + current'),
 ('M2_mid_rbf_age_window_v1','mid RBF age + prescribed windows'),
 ('M2_primary_rbf_age_voltage_v1','main RBF age + voltage'),
 ('M2_primary_rbf_age_current_v1','main RBF age + current'),
 ('M2_primary_rbf_age_voltage_current_v1','main RBF age + voltage + current'),
]
rows=[]
for name,condition in cases:
    source=TASK/'runs'/name/'predictions.csv'
    df=pd.read_csv(source)
    assert len(df.groupby('method'))==6
    for method,part in df.groupby('method'):
        assert len(part)==180 and len(part[['cell_id','target_ordinal']].drop_duplicates())==180
        assert (part.pred_soh_pp-part.target_soh_pp-part.error_pp).abs().max()<1e-9
        per=part.assign(ae=part.error_pp.abs()).groupby('cell_id').ae.mean()
        rows.append({'run_id':name,'condition':condition,'method':method,
                     'macro_mae_pp':float(per.mean()),'worst_cell_mae_pp':float(per.max()),
                     'max_abs_error_pp':float(part.error_pp.abs().max()),
                     'p95_abs_error_pp':float(part.error_pp.abs().quantile(.95)),
                     'w01_visible_target_count':int(part.w01_visible.sum()),
                     'w03_visible_target_count':int(part.w03_visible.sum())})
out=pd.DataFrame(rows)
out.to_csv(OUT/'all_conditions_independent_scores.csv',index=False)
primary=out.loc[out.run_id=='M2_primary_v2'].set_index('method')
baselines=['anchor_constant','age_ridge','fixed_window_ridge','mask_ridge']
strongest=primary.loc[baselines,'macro_mae_pp'].idxmin()
best_baseline=float(primary.loc[strongest,'macro_mae_pp'])
spline=json.loads((TASK/'runs/M2_spline_v1/summary.json').read_text())
other_candidates=[(m['method'],m['macro_mae_pp']) for m in spline['metrics']]
for method in ['within_cell_ratio_ridge','rbf_residual']:
    other_candidates.append((method,float(primary.loc[method,'macro_mae_pp'])))
best_method,best_value=min(other_candidates,key=lambda z:z[1])
asp=json.loads((TASK/'configs/acceptance.json').read_text())['d1_aspirational_thresholds']
reduction=(best_baseline-best_value)/best_baseline
result={'protocol':'v1.4','evidence':'D1 P1 six-cell development proxy only',
        'strongest_eligible_primary_baseline':strongest,'baseline_macro_mae_pp':best_baseline,
        'best_exploratory_candidate':best_method,'candidate_macro_mae_pp':best_value,
        'candidate_relative_improvement':reduction,
        'required_relative_improvement':asp['relative_macro_mae_improvement_vs_strongest_eligible_baseline'],
        'd1_target_met':False,'official_capacity_accuracy_verified':False,
        'd2_confirmation_status':'not_available','research_closed':False,
        'basis':'Independent recomputation from 180 row predictions; candidate remains above macro/worst/max thresholds. More modules remain.'}
(OUT/'interim_acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False),flush=True)
