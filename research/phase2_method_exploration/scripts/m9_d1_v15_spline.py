"""Fold-fitted piecewise-linear ageing curves, with rate/temperature ablations."""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m2_features import frame_for_condition

OUT=TASK/'runs/M9_D1_v15_spline_v1'
OUT.mkdir(parents=True,exist_ok=False)
cfg=json.loads((TASK/'configs/m2_spline.json').read_text())
X=frame_for_condition(20,'persistent',TASK/'data_manifests/d1_v15_target_visibility.csv',
                      TASK/'data_manifests/d1_v15_cropped_events.csv')
panel=pd.read_csv(ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv',
                  usecols=['cell_id','target_ordinal','target_soh_pp'])
keys=pd.MultiIndex.from_frame(X[['cell_id','target_ordinal']])
y=panel.set_index(['cell_id','target_ordinal']).loc[keys,'target_soh_pp'].to_numpy(float)
anchor=X.anchor_pp.to_numpy(float)
cell=X.cell_id.to_numpy(str)

def matrices(train_idx,test_idx,method):
    tr=X.iloc[train_idx];te=X.iloc[test_idx]
    count_tr=tr.prefix_prequalified_charge_count.to_numpy(float)/1000
    count_te=te.prefix_prequalified_charge_count.to_numpy(float)/1000
    knots=np.quantile(count_tr,[.25,.5,.75])
    def make(frame,z):
        basis=np.column_stack([z]+[np.maximum(z-k,0) for k in knots])
        age=frame.age_days.to_numpy(float)/365
        gap=frame.last_gap_days.to_numpy(float)
        blocks=[basis,age[:,None],gap[:,None]]
        if method in ('spline_age_rate','spline_age_temp_rate'):
            rate=frame.current_A.to_numpy(float)
            indicator=(rate>=75).astype(float)
            blocks.extend([indicator[:,None],basis*indicator[:,None]])
        if method=='spline_age_temp_rate':
            temp=frame.current_temp_C.to_numpy(float)
            blocks.extend([temp[:,None],basis*temp[:,None]/20])
        return np.column_stack([b if np.ndim(b)>1 else b[:,None] for b in blocks])
    a=make(tr,count_tr);b=make(te,count_te)
    med=np.array([np.nanmedian(c) if np.isfinite(c).any() else 0. for c in a.T])
    a=np.where(np.isfinite(a),a,med);b=np.where(np.isfinite(b),b,med)
    mean=a.mean(axis=0);scale=a.std(axis=0);scale=np.where(scale>=1e-10,scale,1.)
    return (a-mean)/scale,(b-mean)/scale

def fit_predict(train_idx,test_idx,method,alpha):
    a,b=matrices(train_idx,test_idx,method)
    tr_y=y[train_idx]-anchor[train_idx]
    aa=np.column_stack([np.ones(len(a)),a]);bb=np.column_stack([np.ones(len(b)),b])
    penalty=np.diag([0.]+[float(alpha)]*a.shape[1])
    coef=np.linalg.solve(aa.T@aa+penalty+np.eye(aa.shape[1])*1e-10,aa.T@tr_y)
    return anchor[test_idx]+bb@coef

rows=[];select=[]
for held in np.unique(cell):
    train=np.flatnonzero(cell!=held);test=np.flatnonzero(cell==held)
    for method in cfg['models']:
        scores=[]
        for alpha in cfg['ridge_alpha']:
            errs=[]
            for inner in np.unique(cell[train]):
                valid=train[cell[train]==inner]
                fit=train[cell[train]!=inner]
                pred=fit_predict(fit,valid,method,alpha)
                errs.append(float(np.abs(pred-y[valid]).mean()))
            scores.append((float(np.mean(errs)),alpha))
        score,chosen=min(scores)
        select.append({'held_cell':held,'method':method,'alpha':chosen,'inner_macro_mae_pp':score})
        pred=fit_predict(train,test,method,chosen)
        for i,index in enumerate(test):
            rows.append({'cell_id':held,'target_ordinal':int(X.target_ordinal.iat[index]),
                         'method':method,'actual_pp':float(y[index]),'pred_pp':float(pred[i]),
                         'error_pp':float(pred[i]-y[index]),'outer_held_cell':held})
    print('held',held,flush=True)
pred=pd.DataFrame(rows)
pred.to_csv(OUT/'predictions.csv',index=False)
pd.DataFrame(select).to_csv(OUT/'inner_selections.csv',index=False)
metrics=[]
for method,part in pred.groupby('method'):
    per=part.assign(ae=part.error_pp.abs()).groupby('cell_id').ae.mean()
    metrics.append({'method':method,'macro_mae_pp':float(per.mean()),
                    'worst_cell_mae_pp':float(per.max()),
                    'max_abs_error_pp':float(part.error_pp.abs().max()),
                    'per_cell_mae_pp':{k:float(v) for k,v in per.items()}})
(OUT/'summary.json').write_text(json.dumps({'protocol':'v1.5','n_targets':180,'metrics':metrics,
    'claim_limit':cfg['claim_limit']},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(metrics,ensure_ascii=False),flush=True)
