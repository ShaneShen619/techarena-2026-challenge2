"""Replay the best M2 temperature spline under ±1 C current-sensor bias."""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m2_features import frame_for_condition
OUT=TASK/'runs/M3_spline_sensor_bias_v1'
OUT.mkdir(parents=True,exist_ok=False)
X=frame_for_condition(20,'persistent')
label=pd.read_csv(ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv',
                  usecols=['cell_id','target_ordinal','target_soh_pp'])
keys=pd.MultiIndex.from_frame(X[['cell_id','target_ordinal']])
y=label.set_index(['cell_id','target_ordinal']).loc[keys,'target_soh_pp'].to_numpy(float)
cell=X.cell_id.to_numpy(str)
anchor=X.anchor_pp.to_numpy(float)
selected=pd.read_csv(TASK/'runs/M2_spline_v1/inner_selections.csv')
old=pd.read_csv(TASK/'runs/M2_spline_v1/predictions.csv')
def design(frame,knots):
    count=frame.prefix_prequalified_charge_count.to_numpy(float)/1000
    basis=np.column_stack([count]+[np.maximum(count-k,0) for k in knots])
    age=frame.age_days.to_numpy(float)/365
    gap=frame.last_gap_days.to_numpy(float)
    rate=(frame.current_A.to_numpy(float)>=75).astype(float)
    temp=frame.current_temp_C.to_numpy(float)
    return np.column_stack([basis,age,gap,rate,basis*rate[:,None],temp,basis*temp[:,None]/20])
def predict(train,test,alpha,altered=None):
    tr=X.iloc[train];te=X.iloc[test] if altered is None else altered
    knots=np.quantile(tr.prefix_prequalified_charge_count.to_numpy(float)/1000,[.25,.5,.75])
    a=design(tr,knots);b=design(te,knots)
    med=np.array([np.nanmedian(c) if np.isfinite(c).any() else 0. for c in a.T])
    a=np.where(np.isfinite(a),a,med);b=np.where(np.isfinite(b),b,med)
    mean=a.mean(axis=0);scale=a.std(axis=0);scale=np.where(scale>=1e-10,scale,1.)
    a=(a-mean)/scale;b=(b-mean)/scale
    aa=np.column_stack([np.ones(len(a)),a]);bb=np.column_stack([np.ones(len(b)),b])
    coef=np.linalg.solve(aa.T@aa+np.diag([1e-10]+[alpha+1e-10]*a.shape[1]),
                         aa.T@(y[train]-anchor[train]))
    return te.anchor_pp.to_numpy(float)+bb@coef
rows=[]
for held in np.unique(cell):
    train=np.flatnonzero(cell!=held);test=np.flatnonzero(cell==held)
    match=selected.loc[(selected.held_cell==held)&(selected.method=='spline_age_temp_rate')]
    assert len(match)==1
    alpha=float(match.alpha.iloc[0])
    base=predict(train,test,alpha)
    saved=old.loc[(old.cell_id==held)&(old.method=='spline_age_temp_rate')].sort_values('target_ordinal').pred_pp.to_numpy(float)
    assert np.max(np.abs(base-saved))<1e-8
    for bias in (-1.,0.,1.):
        view=X.iloc[test].copy()
        view['current_temp_C']=view.current_temp_C+bias
        shifted=predict(train,test,alpha,view)
        for i,index in enumerate(test):
            rows.append({'cell_id':held,'target_ordinal':int(X.target_ordinal.iat[index]),
                         'bias_C':bias,'base_pp':float(base[i]),'biased_pp':float(shifted[i]),
                         'delta_pp':float(shifted[i]-base[i]),
                         'abs_shift_pp':float(abs(shifted[i]-base[i]))})
result=pd.DataFrame(rows)
result.to_csv(OUT/'predictions.csv',index=False)
summ=[]
for bias,part in result.loc[result.bias_C!=0].groupby('bias_C'):
    summ.append({'bias_C':bias,'median_abs_shift_pp':float(part.abs_shift_pp.median()),
                 'p95_abs_shift_pp':float(part.abs_shift_pp.quantile(.95)),
                 'max_abs_shift_pp':float(part.abs_shift_pp.max()),
                 'gt0p5pp_targets':int(part.abs_shift_pp.gt(.5).sum())})
(OUT/'summary.json').write_text(json.dumps(summ,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summ,ensure_ascii=False),flush=True)
