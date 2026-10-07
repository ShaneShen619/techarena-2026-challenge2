"""R05 training-only within-cell temperature permutation and fixed-model perturbation."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
RUN=TASK/'runs/V3_R05_controls_20260929_v2';RUN.mkdir(parents=True,exist_ok=True)
assert not (RUN/'COMPLETED').exists()
src=TASK/'runs/V3_R05_D1_20260929_v1'
f=pd.read_csv(src/'features.csv');pred=pd.read_csv(src/'per_target_predictions.csv');sel=pd.read_csv(src/'inner_selections.csv')
panel=pd.read_csv(ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv').sort_values(['cell_id','target_ordinal'])
assert np.array_equal(f.cell_id.to_numpy(str),panel.cell_id.to_numpy(str))
ids=f.cell_id.to_numpy(str);ordinal=f.target_ordinal.to_numpy(int)
anchor=np.load(ROOT/'research/phase2_method_exploration/runs/M9_D1_v15_target_map_v1/target_inputs.npz')['metadata'][:,0]
truth=panel.target_soh_pp.to_numpy(float);y=truth-anchor
cols=['age_days','age_log1p','last_gap_days','history_count','prefix_prequalified_charge_count','current_A','current_temp_C','selected_T_mean','selected_T_recent','selected_T_change','selected_T_coverage','selected_T_hot_fraction']
tcols=['current_temp_C','selected_T_mean','selected_T_recent','selected_T_change','selected_T_hot_fraction']
def fit_predict(train,test,alpha,train_frame,test_frame):
    tr=train_frame[cols].to_numpy(float);te=test_frame[cols].to_numpy(float)
    med=np.array([np.nanmedian(tr[:,j]) if np.isfinite(tr[:,j]).any() else 0 for j in range(tr.shape[1])])
    mt=~np.isfinite(tr);mv=~np.isfinite(te);use=mt.any(axis=0)
    tr=np.column_stack([np.where(mt,med,tr),mt[:,use].astype(float)])
    te=np.column_stack([np.where(mv,med,te),mv[:,use].astype(float)])
    mu=tr.mean(axis=0);sd=np.where(tr.std(axis=0)<1e-9,1.,tr.std(axis=0))
    tr=(tr-mu)/sd;te=(te-mu)/sd
    slope=np.linalg.solve(tr.T@tr+alpha*np.eye(tr.shape[1]),tr.T@(y[train]-np.mean(y[train])))
    return np.mean(y[train])+te@slope

cells=np.unique(ids);rng=np.random.default_rng(290930);records=[]
for held in cells:
    tr=np.flatnonzero(ids!=held);te=np.flatnonzero(ids==held)
    chosen=pred[(pred.arm=='sampled_T')&(pred.selection_objective=='average')&(pred.cell_id==held)]
    alpha=float(chosen.selected_alpha.iloc[0]);base=anchor[te]+fit_predict(tr,te,alpha,f.iloc[tr],f.iloc[te])
    assert np.allclose(base,chosen.sort_values('target_ordinal').prediction_pp.to_numpy(float),atol=1e-8), (held,float(np.max(np.abs(base-chosen.sort_values('target_ordinal').prediction_pp.to_numpy(float)))))
    for condition,p in [('true',base)]:
        records.extend({'cell_id':held,'target_ordinal':int(ordinal[j]),'condition':condition,'seed':-1,'prediction_pp':float(v),'target_pp':float(truth[j]),'error_pp':float(v-truth[j])} for j,v in zip(te,p))
    for shift in [-5,5]:
        modified=f.iloc[te].copy();modified['current_temp_C']=modified.current_temp_C+shift
        p=anchor[te]+fit_predict(tr,te,alpha,f.iloc[tr],modified)
        records.extend({'cell_id':held,'target_ordinal':int(ordinal[j]),'condition':f'current_T_{shift:+d}C','seed':-1,'prediction_pp':float(v),'target_pp':float(truth[j]),'error_pp':float(v-truth[j])} for j,v in zip(te,p))
    for seed in range(20):
        altered=f.iloc[tr].copy()
        for cell in np.unique(ids[tr]):
            local=np.flatnonzero(altered.cell_id.to_numpy(str)==cell)
            # Frozen age quartiles within each training physical cell.
            ranks=pd.qcut(altered.iloc[local].age_days.rank(method='first'),4,labels=False)
            for binid in range(4):
                group=local[np.asarray(ranks)==binid]
                if len(group)<2:continue
                shuffled=group[rng.permutation(len(group))]
                altered.iloc[group,altered.columns.get_indexer(tcols)]=altered.iloc[shuffled][tcols].to_numpy()
        p=anchor[te]+fit_predict(tr,te,alpha,altered,f.iloc[te])
        records.extend({'cell_id':held,'target_ordinal':int(ordinal[j]),'condition':'train_T_permuted_within_cell_age_quartile','seed':seed,'prediction_pp':float(v),'target_pp':float(truth[j]),'error_pp':float(v-truth[j])} for j,v in zip(te,p))
out=pd.DataFrame(records);out.to_csv(RUN/'control_predictions.csv',index=False)
rows=[]
for (condition,seed),g in out.groupby(['condition','seed']):
    by=g.groupby('cell_id').error_pp.apply(lambda x:float(np.abs(x).mean()));late=g[g.target_ordinal>=21]
    rows.append({'condition':condition,'seed':seed,'macro_mae_pp':float(by.mean()),'worst_cell_mae_pp':float(by.max()),
                 'late_mae_pp':float(late.error_pp.abs().mean()),'late_bias_pp':float(late.error_pp.mean())})
pd.DataFrame(rows).to_csv(RUN/'control_metrics.csv',index=False)
result={'true_macro_mae_pp':float(next(r['macro_mae_pp'] for r in rows if r['condition']=='true')),
 'permuted_macro_mean_pp':float(np.mean([r['macro_mae_pp'] for r in rows if r['condition'].startswith('train_T_permuted')])),
 'permute_scope':'training cells only; within cell and age quartile, 20 seeds; fixed true-data inner alpha',
 'temperature_perturbation':'held cell current event measured temperature +/-5C; fixed fitted model',
 'causal_status':'D1 physical-cell split; sampled source events strictly pre-target in source builder'}
(RUN/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');(RUN/'COMPLETED').write_text('immutable run completed\n')
print(json.dumps(result,ensure_ascii=False))
