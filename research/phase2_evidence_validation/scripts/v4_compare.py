"""Independent recomputation of D1 scalar results, nested selection and tails."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1]
IN=TASK/'runs/V3_R05_D1_20260929_v1';OUT=TASK/'runs/V4_comparison_20260929_v1';OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'COMPLETED').exists()
d=pd.read_csv(IN/'per_target_predictions.csv');s=pd.read_csv(IN/'inner_selections.csv');m=pd.read_csv(IN/'metrics.csv')
assert all(d.groupby(['arm','selection_objective']).size()==180)
for r in m.itertuples():
    z=d[(d.arm==r.arm)&(d.selection_objective==r.objective)]
    by=z.groupby('cell_id').error_pp.apply(lambda x:np.mean(np.abs(x)))
    assert abs(by.mean()-r.macro_mae_pp)<1e-9
    assert abs(by.max()-r.worst_cell_mae_pp)<1e-9
    assert abs(z.error_pp.abs().max()-r.max_abs_error_pp)<1e-9
selected=d.merge(s,left_on=['cell_id','selection_objective'],right_on=['held_cell','objective'])
selected=selected[selected.arm==selected.selected_arm].copy()
assert all(selected.groupby('selection_objective').size()==180)
selected.to_csv(OUT/'nested_selected_predictions.csv',index=False)
metrics=[]
for objective,z in selected.groupby('selection_objective'):
    by=z.groupby('cell_id').error_pp.apply(lambda x:float(np.abs(x).mean()))
    tail=z[z.late];late_by=tail.groupby('cell_id').error_pp.apply(lambda x:float(np.abs(x).mean()))
    metrics.append({'objective':objective,'arm':'nested_selected', 'n_targets':len(z),
     'macro_mae_pp':float(by.mean()),'worst_cell_mae_pp':float(by.max()),'worst_cell':by.idxmax(),
     'max_abs_error_pp':float(z.error_pp.abs().max()),'late_mae_pp':float(tail.error_pp.abs().mean()),
     'late_worst_cell_mae_pp':float(late_by.max()),'late_bias_pp':float(tail.error_pp.mean()),
     'late_overestimate_rate':float((tail.error_pp>0).mean())})
pd.DataFrame(metrics).to_csv(OUT/'nested_selected_metrics.csv',index=False)
paired=[]
for objective in ['average','tail']:
    base=d[(d.arm=='matched_no_T')&(d.selection_objective==objective)].set_index(['cell_id','target_ordinal'])
    for arm in ['time','count_time','instant_T','sampled_T']:
        z=d[(d.arm==arm)&(d.selection_objective==objective)].set_index(['cell_id','target_ordinal'])
        assert z.index.equals(base.index)
        for cell in z.index.get_level_values(0).unique():
            a=z.loc[cell];b=base.loc[cell]
            paired.append({'objective':objective,'arm':arm,'comparator':'matched_no_T','cell_id':cell,
             'delta_cell_mae_pp':float(a.error_pp.abs().mean()-b.error_pp.abs().mean()),
             'delta_late_mae_pp':float(a.loc[a.late,'error_pp'].abs().mean()-b.loc[b.late,'error_pp'].abs().mean())})
pd.DataFrame(paired).to_csv(OUT/'paired_cell_deltas.csv',index=False)
# Entity bootstrap expresses instability across these six reused development cells, not confirmation.
boot=[];r=np.random.default_rng(290929)
for objective in ['average','tail']:
    z=pd.DataFrame(paired)
    z=z[(z.objective==objective)&(z.arm=='sampled_T')]
    a=z.delta_cell_mae_pp.to_numpy(float);b=z.delta_late_mae_pp.to_numpy(float)
    idx=r.integers(0,len(a),(10000,len(a)))
    for name,v in [('macro',a),('late_macro',b)]:
        means=v[idx].mean(axis=1)
        boot.append({'objective':objective,'contrast':'sampled_T_minus_matched_no_T','metric':name,
         'point_delta_pp':float(v.mean()),'entity_bootstrap_q025':float(np.quantile(means,.025)),
         'entity_bootstrap_q975':float(np.quantile(means,.975)),
         'interpretation':'six reused development cells; descriptive instability only'})
pd.DataFrame(boot).to_csv(OUT/'entity_bootstrap.csv',index=False)
hist={'historical_frozen_TCN_macro_pp':2.8506935812720986,'historical_frozen_TCN_worst_pp':5.571703597785854,
      'historical_frozen_TCN_max_pp':17.174684187624337,'historical_postaudit_noT_macro_pp':2.478567178327022,
      'historical_best_status':'same six cells, old evaluation; not present in this run per-target table'}
(OUT/'result.json').write_text(json.dumps({'nested_selected':metrics,'historical':hist,
 'new_capacity_signal_supported':False,'reason':'sampled temperature loses to matched no-temperature feature basis; no D2 group capacity labels'},indent=2,ensure_ascii=False)+'\n')
(OUT/'COMPLETED').write_text('immutable run completed\n')
print(pd.DataFrame(metrics).to_string(index=False));print(pd.DataFrame(boot).to_string(index=False))
