"""Compile the frozen prior state-identifiability results into a new decision gate."""
from pathlib import Path
import hashlib,json
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OLD=ROOT/'research/phase2_method_exploration/runs'
conf=json.loads((OLD/'M4_confounds_v2/summary.json').read_text())
ident=json.loads((OLD/'M4_state_identifiability_v4/summary.json').read_text())
pack=json.loads((OLD/'M5_pack_v1/summary.json').read_text())
quality=json.loads((OLD/'M5_state_quality_v1/summary.json').read_text())
shrink=json.loads((OLD/'M5_shrinkage_v1/summary.json').read_text())
perm=json.loads((OLD/'M5_permutation_recheck_v1/summary.json').read_text())
source_names=['M4_confounds_v2','M4_state_identifiability_v4','M5_pack_v1',
              'M5_state_quality_v1','M5_shrinkage_v1','M5_permutation_recheck_v1']
pd.DataFrame([{'upstream_run':name,
               'summary_path':str((OLD/name/'summary.json').relative_to(ROOT)),
               'summary_sha256':hashlib.sha256((OLD/name/'summary.json').read_bytes()).hexdigest()}
              for name in source_names]).to_csv(TASK/'outputs/r4_upstream_sources.csv',index=False)

rows=[]
for r in quality['scores']:
    if r['method'] in ('explicit_four_cell','uniform_mean_cell','minimum_cell_usable_Ah'):
        rows.append({'experiment':'state_quality','quality':r['quality'],'method':r['method'],
                     'MAE_Ah':r['MAE_Ah'],'MAE_pp':r['MAE_Ah']*100/102,
                     'P95_abs_Ah':r['P95_abs_Ah'],'max_abs_Ah':r['max_abs_Ah']})
for r in shrink['scores']:
    if r['method'] in ('explicit_four_cell','noise_aware_shrunk_four_cell','uniform_mean_cell'):
        rows.append({'experiment':'noise_aware_shrinkage','quality':r['quality'],'method':r['method'],
                     'MAE_Ah':r['MAE_Ah'],'MAE_pp':r['MAE_Ah']*100/102,
                     'P95_abs_Ah':r['P95_abs_Ah'],'max_abs_Ah':r['max_abs_Ah']})
table=pd.DataFrame(rows)
wide=table.loc[table.experiment.eq('state_quality')].pivot(index='quality',columns='method',values='MAE_Ah')
wide['explicit_advantage_vs_uniform_Ah']=wide['uniform_mean_cell']-wide['explicit_four_cell']
shrink_wide=table.loc[table.experiment.eq('noise_aware_shrinkage')].pivot(index='quality',columns='method',values='MAE_Ah')
shrink_wide['explicit_advantage_vs_uniform_Ah']=shrink_wide['uniform_mean_cell']-shrink_wide['explicit_four_cell']
shrink_wide['shrunk_advantage_vs_uniform_Ah']=shrink_wide['uniform_mean_cell']-shrink_wide['noise_aware_shrunk_four_cell']
table.to_csv(TASK/'outputs/r4_pack_quality_scores.csv',index=False)
wide.reset_index().to_csv(TASK/'outputs/r4_pack_quality_decision.csv',index=False)
shrink_wide.reset_index().to_csv(TASK/'outputs/r4_pack_shrinkage_decision.csv',index=False)

multi=pd.DataFrame(conf['multi_start_Q_range_by_window_case'])
multi['Q_profile_width_Ah']=multi.Q_max_Ah-multi.Q_min_Ah
multi.to_csv(TASK/'outputs/r4_identifiability_profiles.csv',index=False)
summary={
 'official_forward_cell_events':ident['official_forward_cell_events'],
 'official_capacity_updates_accepted':ident['official_gate_accepted'],
 'official_median_capacity_profile_width_Ah':ident['official_median_profile_width_Ah'],
 'synthetic_median_Q_error_by_window_Ah':ident['synthetic_median_Q_error_by_window_Ah'],
 'capacity_profile_width_by_window_case':multi[['window_Ah','case','Q_profile_width_Ah','best_voltage_RMSE_mV']].to_dict('records'),
 'CK0_rebuilt_capacity_Ah':pack['CK0_rebuilt_capacity_Ah'],
 'CK0_reference_capacity_Ah':pack['CK0_reference_capacity_Ah'],
 'permutation_passed':bool(perm['passed']),
 'explicit_advantage_vs_uniform_by_quality_Ah':{k:float(v) for k,v in wide.explicit_advantage_vs_uniform_Ah.items()},
 'shrinkage_advantage_vs_uniform_by_quality_Ah':{k:float(v) for k,v in shrink_wide.shrunk_advantage_vs_uniform_Ah.items()},
 'decision':'keep official capacity-update gate closed; use explicit four-cell cutoff only when independently calibrated per-cell state quality reaches the synthetic ultra/oracle regime',
 'source_status':'compiled from frozen phase2_method_exploration runs; upstream hashes are in r4_upstream_sources.csv',
 'capacity_validation':'not testable on CK1-CK7; all quality thresholds are synthetic mechanism evidence'}
(TASK/'outputs/r4_state_pack_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
