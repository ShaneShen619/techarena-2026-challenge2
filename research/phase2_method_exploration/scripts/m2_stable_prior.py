"""A fragment-independent prefix fallback with nested physical-cell tuning."""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m2_features import frame_for_condition
OUT=TASK/'runs/M2_stable_prefix_prior_v1'
OUT.mkdir(parents=True,exist_ok=False)
X=frame_for_condition(20,'persistent')
cols=['age_days','age_log1p','prefix_prequalified_charge_count']
panel=pd.read_csv(ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv',
                  usecols=['cell_id','target_ordinal','target_soh_pp'])
keys=pd.MultiIndex.from_frame(X[['cell_id','target_ordinal']])
y=panel.set_index(['cell_id','target_ordinal']).loc[keys,'target_soh_pp'].to_numpy(float)
cell=X.cell_id.to_numpy(str)
anchor=X.anchor_pp.to_numpy(float)
def predict(train,test,alpha):
    a=X.iloc[train][cols].to_numpy(float);b=X.iloc[test][cols].to_numpy(float)
    mean=a.mean(axis=0);scale=a.std(axis=0);scale=np.where(scale>=1e-10,scale,1.)
    a=(a-mean)/scale;b=(b-mean)/scale
    aa=np.column_stack([np.ones(len(a)),a]);bb=np.column_stack([np.ones(len(b)),b])
    coef=np.linalg.solve(aa.T@aa+np.diag([1e-10]+[alpha+1e-10]*a.shape[1]),aa.T@(y[train]-anchor[train]))
    return anchor[test]+bb@coef
rows=[];selection=[]
for held in np.unique(cell):
    train=np.flatnonzero(cell!=held);test=np.flatnonzero(cell==held)
    candidate=[]
    for alpha in [.1,1,10,100,1000]:
        errs=[]
        for inner in np.unique(cell[train]):
            valid=train[cell[train]==inner]
            fit=train[cell[train]!=inner]
            errs.append(float(np.abs(predict(fit,valid,alpha)-y[valid]).mean()))
        candidate.append((float(np.mean(errs)),alpha))
    score,alpha=min(candidate)
    selection.append({'held_cell':held,'alpha':alpha,'inner_macro_mae_pp':score})
    out=predict(train,test,alpha)
    for i,index in enumerate(test):
        rows.append({'cell_id':held,'target_ordinal':int(X.target_ordinal.iat[index]),
                     'actual_pp':float(y[index]),'pred_pp':float(out[i]),
                     'error_pp':float(out[i]-y[index])})
pred=pd.DataFrame(rows)
pred.to_csv(OUT/'predictions.csv',index=False)
pd.DataFrame(selection).to_csv(OUT/'inner_selections.csv',index=False)
per=pred.assign(ae=pred.error_pp.abs()).groupby('cell_id').ae.mean()
summary={'method':'stable_age_count_anchor','macro_mae_pp':float(per.mean()),
         'worst_cell_mae_pp':float(per.max()),'max_abs_error_pp':float(pred.error_pp.abs().max()),
         'per_cell_mae_pp':{k:float(v) for k,v in per.items()},
         'invariant_to_crop_position_by_construction':True,
         'claim_limit':'Same six P1 development cells; no official capacity verification.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
