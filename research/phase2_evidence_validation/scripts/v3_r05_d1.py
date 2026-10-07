"""Frozen D1 v1.5 sampled-temperature proxy, nested physical-cell validation."""
from __future__ import annotations
import csv, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/phase2_method_exploration'
RUN=TASK/'runs/V3_R05_D1_20260929_v1'
RUN.mkdir(parents=True,exist_ok=True)
assert not (RUN/'COMPLETED').exists(), 'Immutable completed run'
cfg=json.loads((TASK/'configs/r05_v2.json').read_text())
z=np.load(BASE/'runs/M9_D1_v15_target_map_v1/target_inputs.npz')
meta=z['metadata']; ids=z['cell_ids'].astype(str); ords=z['target_ordinals'].astype(int); slots=z['indices']
panel=pd.read_csv(ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv').sort_values(['cell_id','target_ordinal'])
assert len(panel)==180 and np.array_equal(panel.cell_id.to_numpy(str),ids) and np.array_equal(panel.target_ordinal.to_numpy(int),ords)
assert np.allclose(meta[:,0],panel.anchor_soh_pp.to_numpy(float),atol=1e-3)
man=pd.read_csv(BASE/'runs/M9_D1_v15_inputs_v1/sequence_manifest.csv')
t=man.source_temperature_C.to_numpy(float); spans=man.span_Ah.to_numpy(float); ns=man.n_native_samples.to_numpy(float)
st=pd.to_datetime(man.fragment_start); en=pd.to_datetime(man.fragment_end)
assert len(t)>np.max(slots)
cutoff=pd.to_datetime(panel.target_discharge_start)
histor=[]
for i,row in enumerate(slots):
    valid=[int(x) for x in row if x>=0]; unique=list(dict.fromkeys(valid))
    assert all(en.iloc[j]<cutoff.iloc[i] for j in unique)
    initial=list(dict.fromkeys(int(x) for x in row[1:11] if x>=0))
    recent=list(dict.fromkeys(int(x) for x in row[11:] if x>=0))
    def mean_temp(jj):
        a=t[jj] if len(jj) else np.array([])
        return float(np.nanmean(a)) if np.isfinite(a).any() else np.nan
    tt=t[unique]; fin=np.isfinite(tt)
    early=mean_temp(initial); late=mean_temp(recent)
    histor.append({
      'selected_T_mean':mean_temp(unique),'selected_T_recent':late,
      'selected_T_change':late-early if np.isfinite(late) and np.isfinite(early) else np.nan,
      'selected_T_coverage':float(fin.mean()),'selected_T_hot_fraction':float(np.mean(tt[fin]>=45)) if fin.any() else np.nan,
      'first_count':len(initial),'recent_count':len(recent),
      'selected_native_samples_mean':float(np.mean(ns[unique])),
      'selected_span_Ah_mean':float(np.mean(spans[unique])),
      'selected_span_Ah_sd':float(np.std(spans[unique])),
      'selected_fragment_duration_mean_h':float(np.mean((en.iloc[unique].to_numpy()-st.iloc[unique].to_numpy())/np.timedelta64(1,'h'))),
      'selected_event_age_span_days':float((en.iloc[unique].max()-en.iloc[unique].min()).total_seconds()/86400)
    })
h=pd.DataFrame(histor)
f=pd.DataFrame({'age_days':meta[:,1], 'age_log1p':meta[:,2], 'history_count':meta[:,3],
 'last_gap_days':meta[:,4], 'prefix_prequalified_charge_count':meta[:,5],
 'current_A':meta[:,6], 'current_temp_C':meta[:,7]})
f=pd.concat([f,h],axis=1)
arms={
 'anchor':[],
 'time':['age_days','age_log1p','last_gap_days'],
 'count_time':['age_days','age_log1p','last_gap_days','history_count','prefix_prequalified_charge_count'],
 'instant_T':['age_days','age_log1p','last_gap_days','history_count','prefix_prequalified_charge_count','current_A','current_temp_C'],
 'sampled_T':['age_days','age_log1p','last_gap_days','history_count','prefix_prequalified_charge_count','current_A','current_temp_C','selected_T_mean','selected_T_recent','selected_T_change','selected_T_coverage','selected_T_hot_fraction'],
 'matched_no_T':['age_days','age_log1p','last_gap_days','history_count','prefix_prequalified_charge_count','current_A','first_count','recent_count','selected_native_samples_mean','selected_span_Ah_mean','selected_span_Ah_sd','selected_fragment_duration_mean_h']
}
assert list(arms)==cfg['arms']
assert len(arms['sampled_T'])==len(arms['matched_no_T'])
y=panel.target_soh_pp.to_numpy(float)-meta[:,0]
cells=np.unique(ids); penalties=cfg['ridge_penalties']
def fit_predict(train,test,cols,alpha):
    if not cols: return np.zeros(len(test))
    x=f[cols].to_numpy(float)
    tr=x[train]; te=x[test]
    med=np.array([np.nanmedian(tr[:,j]) if np.isfinite(tr[:,j]).any() else 0. for j in range(tr.shape[1])])
    missing_tr=~np.isfinite(tr); missing_te=~np.isfinite(te)
    tr=np.where(missing_tr,med,tr); te=np.where(missing_te,med,te)
    # Include missing flags only where train actually exhibits missingness.
    use=missing_tr.any(axis=0)
    tr=np.column_stack([tr,missing_tr[:,use].astype(float)])
    te=np.column_stack([te,missing_te[:,use].astype(float)])
    mu=tr.mean(axis=0); sd=tr.std(axis=0); sd=np.where(sd<1e-9,1.,sd)
    tr=(tr-mu)/sd; te=(te-mu)/sd
    slope=np.linalg.solve(tr.T@tr+float(alpha)*np.eye(tr.shape[1]),tr.T@(y[train]-np.mean(y[train])))
    return np.mean(y[train])+te@slope

def inner_score(train_cells,arm,alpha):
    maes=[]; late=[]
    for cell in train_cells:
        it=np.flatnonzero(np.isin(ids,train_cells)&(ids!=cell)); iv=np.flatnonzero(ids==cell)
        p=meta[iv,0]+fit_predict(it,iv,arms[arm],alpha)
        err=p-panel.target_soh_pp.to_numpy(float)[iv]
        maes.append(float(np.mean(np.abs(err))))
        late.append(float(np.mean(np.abs(err[ords[iv]>=21]))))
    return float(np.mean(maes)),float(max(late))

records=[]; selections=[]
for held in cells:
    train_cells=[c for c in cells if c!=held]
    tr=np.flatnonzero(ids!=held); te=np.flatnonzero(ids==held)
    inner={}
    for arm in arms:
        if arm=='anchor': continue
        for alpha in penalties:
            inner[(arm,alpha)]=inner_score(train_cells,arm,alpha)
    for objective in ('average','tail'):
        def criterion(pair):
            a,w=inner[pair]
            return a if objective=='average' else .5*a+.5*w
        best_by_arm={arm:min(((arm,a) for a in penalties),key=lambda pair:(criterion(pair),pair[1])) for arm in arms if arm!='anchor'}
        selected=min(best_by_arm.values(),key=lambda pair:(criterion(pair),list(arms).index(pair[0]),pair[1]))
        for arm in arms:
            if arm=='anchor': alpha=np.nan; pred=meta[te,0]; score=np.nan
            else:
                pair=best_by_arm[arm]; alpha=pair[1]; score=criterion(pair)
                pred=meta[te,0]+fit_predict(tr,te,arms[arm],alpha)
            for j,p in zip(te,pred):
                records.append({'evidence_tier':'D1','protocol':'P1_deep_charge_prefix_20Ah_single_cell_proxy','version':cfg['version'],
                 'cell_id':ids[j],'target_ordinal':int(ords[j]),'target_cutoff':str(cutoff.iloc[j]),'arm':arm,'selection_objective':objective,
                 'selected_alpha':alpha,'prediction_pp':float(p),'target_pp':float(panel.target_soh_pp.iloc[j]),
                 'error_pp':float(p-panel.target_soh_pp.iloc[j]),'inner_objective_pp':score,'late':bool(ords[j]>=21),
                 'fallback':arm=='anchor'})
        selections.append({'held_cell':held,'objective':objective,'selected_arm':selected[0],'selected_alpha':selected[1],
          'selected_inner_objective_pp':criterion(selected)})
out=pd.DataFrame(records); out.to_csv(RUN/'per_target_predictions.csv',index=False)
pd.DataFrame(selections).to_csv(RUN/'inner_selections.csv',index=False)
f.insert(0,'target_ordinal',ords);f.insert(0,'cell_id',ids);f.to_csv(RUN/'features.csv',index=False)
rows=[]
for (objective,arm),g in out.groupby(['selection_objective','arm'],sort=False):
    g=g.sort_values(['cell_id','target_ordinal']); e=g.error_pp.to_numpy(float)
    by=g.groupby('cell_id').error_pp.apply(lambda z:float(np.abs(z).mean()))
    late=g[g.late]; le=late.error_pp.to_numpy(float)
    rows.append({'objective':objective,'arm':arm,'n_targets':len(g),'n_cells':len(by),
      'macro_mae_pp':float(by.mean()),'worst_cell_mae_pp':float(by.max()),'worst_cell':by.idxmax(),
      'max_abs_error_pp':float(np.max(np.abs(e))),'late_mae_pp':float(np.mean(np.abs(le))),
      'late_signed_bias_pp':float(np.mean(le)),'late_overestimate_rate':float(np.mean(le>0)),
      'all_signed_bias_pp':float(np.mean(e))})
metrics=pd.DataFrame(rows);metrics.to_csv(RUN/'metrics.csv',index=False)
summary={'run_id':RUN.name,'evidence':'D1 proxy same six reused P1 cells; not official pack capacity',
 'targets_per_arm':180,'cells':len(cells),'late_targets_per_arm':int(sum(ords>=21)),
 'feature_missing_current_T':int(f.current_temp_C.isna().sum()),
 'feature_missing_selected_T_mean':int(f.selected_T_mean.isna().sum()),
 'not_testable':cfg['not_testable'],
 'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [TASK/'configs/r05_v2.json',BASE/'runs/M9_D1_v15_target_map_v1/target_inputs.npz',BASE/'runs/M9_D1_v15_inputs_v1/sequence_manifest.csv',ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv',Path(__file__)]}}
(RUN/'result.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
(RUN/'COMPLETED').write_text('immutable run completed\n')
print(metrics.to_string(index=False));print(json.dumps(summary,ensure_ascii=False))
