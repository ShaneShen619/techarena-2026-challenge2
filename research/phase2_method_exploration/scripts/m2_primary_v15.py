"""Nested physical-cell validation of budget-matched D1 baselines/candidates."""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m2_features import AGE,frame_for_condition

parser=argparse.ArgumentParser()
parser.add_argument('--budget',type=int,choices=[15,20,30],default=20)
parser.add_argument('--mode',choices=['cold','persistent'],default='persistent')
arg=parser.parse_args()
OUT=TASK/f'runs/M9_D1_v15_M2_{arg.budget}Ah_{arg.mode}_v1'
OUT.mkdir(parents=True,exist_ok=False)
CONFIG=TASK/'configs/m2_primary_v15.json'
cfg=json.loads(CONFIG.read_text())
assert cfg['protocol']=='v1.5'
cfg['condition']['budget_Ah']=arg.budget
cfg['condition']['history_mode']=arg.mode
panel_path=ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv'
assert hashlib.sha256(panel_path.read_bytes()).hexdigest()=='7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c'
X=frame_for_condition(cfg['condition']['budget_Ah'],cfg['condition']['history_mode'],
    TASK/'data_manifests/d1_v15_target_visibility.csv', TASK/'data_manifests/d1_v15_cropped_events.csv')
label=pd.read_csv(panel_path,usecols=['cell_id','target_ordinal','target_soh_pp'])
keys=pd.MultiIndex.from_frame(X[['cell_id','target_ordinal']])
truth=label.set_index(['cell_id','target_ordinal']).loc[keys,'target_soh_pp'].to_numpy(float)
cells=X.cell_id.to_numpy(str)
anchor=X.anchor_pp.to_numpy(float)
assert len(truth)==180 and len(np.unique(cells))==6

ALPHA=cfg['ridge_alpha_grid']
W=cfg['current_window_candidates']
methods={
 'age_ridge':[{'alpha':a} for a in ALPHA],
 'fixed_window_ridge':[{'alpha':a,'window':w} for w,a in itertools.product(W,ALPHA)],
 'mask_ridge':[{'alpha':a} for a in ALPHA],
 'within_cell_ratio_ridge':[{'alpha':a,'window':w} for w,a in itertools.product(W,ALPHA)],
 'rbf_residual':[{'alpha':a,'lengthscale':l} for l,a in itertools.product(cfg['rbf_lengthscale_grid'],cfg['rbf_alpha_grid'])],
}

def columns(method:str,param:dict)->list[str]:
    if method=='age_ridge':return AGE
    if method=='fixed_window_ridge':
        w=param['window'];return AGE+[f'w{w:02d}_Ah',f'w{w:02d}_mask']
    if method=='within_cell_ratio_ridge':
        w=param['window'];return AGE+[f'w{w:02d}_ratio',f'w{w:02d}_mask']
    if method in ('mask_ridge','rbf_residual'):
        cols=AGE+[f'w{w:02d}_{suffix}' for w in range(9) for suffix in ('Ah','mask')]
        if method=='rbf_residual':cols+=['v_start_V','v_end_V','current_A','observed_span_Ah']
        return cols
    raise KeyError(method)

def matrices(train:pd.DataFrame,test:pd.DataFrame,cols:list[str])->tuple[np.ndarray,np.ndarray]:
    a=train[cols].to_numpy(float);b=test[cols].to_numpy(float)
    median=np.array([np.nanmedian(col) if np.isfinite(col).any() else 0. for col in a.T])
    a=np.where(np.isfinite(a),a,median)
    b=np.where(np.isfinite(b),b,median)
    mean=a.mean(axis=0);scale=a.std(axis=0)
    scale=np.where(scale>=1e-10,scale,1.)
    return (a-mean)/scale,(b-mean)/scale

def ridge_fit(a:np.ndarray,y:np.ndarray,b:np.ndarray,alpha:float)->np.ndarray:
    aa=np.column_stack([np.ones(len(a)),a])
    bb=np.column_stack([np.ones(len(b)),b])
    penalty=np.diag([0.]+[alpha]*a.shape[1])
    coef=np.linalg.solve(aa.T@aa+penalty+np.eye(aa.shape[1])*1e-10,aa.T@y)
    return bb@coef

def predict(method:str,param:dict,train_idx:np.ndarray,test_idx:np.ndarray)->np.ndarray:
    train=X.iloc[train_idx];test=X.iloc[test_idx]
    y=truth[train_idx]-anchor[train_idx]
    a,b=matrices(train,test,columns(method,param))
    if method!='rbf_residual':
        delta=ridge_fit(a,y,b,float(param['alpha']))
    else:
        # Kernel learns only the age-baseline residual. All transforms and
        # intercept are fitted on training physical cells within each fold.
        age_a,age_b=matrices(train,test,AGE)
        baseline_train=ridge_fit(age_a,y,age_a,10.)
        baseline_test=ridge_fit(age_a,y,age_b,10.)
        length=float(param['lengthscale'])
        sq=((a[:,None,:]-a[None,:,:])**2).mean(axis=2)
        cross=((b[:,None,:]-a[None,:,:])**2).mean(axis=2)
        kernel=np.exp(-sq/(2*length**2))
        weights=np.linalg.solve(kernel+np.eye(len(a))*float(param['alpha']),y-baseline_train)
        delta=baseline_test+np.exp(-cross/(2*length**2))@weights
    return anchor[test_idx]+delta

def inner_score(method:str,param:dict,outer_train:np.ndarray)->float:
    errs=[]
    for cell in np.unique(cells[outer_train]):
        validation=outer_train[cells[outer_train]==cell]
        fitting=outer_train[cells[outer_train]!=cell]
        p=predict(method,param,fitting,validation)
        errs.append(float(np.mean(np.abs(p-truth[validation]))))
    return float(np.mean(errs))

rows=[];selected=[]
for held_cell in np.unique(cells):
    outer_test=np.flatnonzero(cells==held_cell)
    outer_train=np.flatnonzero(cells!=held_cell)
    chosen={}
    for method,grid in methods.items():
        scored=[(inner_score(method,p,outer_train),i,p) for i,p in enumerate(grid)]
        score,_,param=min(scored,key=lambda item:(item[0],item[1]))
        chosen[method]=(param,score)
        selected.append({'held_cell':held_cell,'method':method,'inner_macro_mae_pp':score,
                         'selected_json':json.dumps(param,sort_keys=True)})
    predictions={'anchor_constant':anchor[outer_test]}
    for method,(param,_) in chosen.items():
        predictions[method]=predict(method,param,outer_train,outer_test)
    for local,index in enumerate(outer_test):
        for method,p in predictions.items():
            rows.append({'cell_id':cells[index],'target_ordinal':int(X.target_ordinal.iat[index]),
                         'method':method,'target_soh_pp':float(truth[index]),
                         'anchor_soh_pp':float(anchor[index]),'pred_soh_pp':float(p[local]),
                         'error_pp':float(p[local]-truth[index]),'budget_Ah':arg.budget,
                         'history_mode':arg.mode,'held_cell':held_cell,
                         'w01_visible':int(X.w01_mask.iat[index]),
                         'w03_visible':int(X.w03_mask.iat[index])})
    print('held',held_cell,'selected',{m:(p,round(s,3)) for m,(p,s) in chosen.items()},flush=True)

pred=pd.DataFrame(rows)
pred.to_csv(OUT/'predictions.csv',index=False)
pd.DataFrame(selected).to_csv(OUT/'inner_selections.csv',index=False)
assert pred.groupby('method').size().eq(180).all()
metrics=[]
for method,part in pred.groupby('method'):
    per=part.assign(abs_pp=part.error_pp.abs()).groupby('cell_id').abs_pp.mean()
    metrics.append({'method':method,'macro_mae_pp':float(per.mean()),
                    'worst_cell_mae_pp':float(per.max()),
                    'max_absolute_error_pp':float(part.error_pp.abs().max()),
                    'p95_absolute_error_pp':float(part.error_pp.abs().quantile(.95)),
                    'per_cell_mae_pp':{k:float(v) for k,v in per.items()},
                    'w01_visible_target_count':int(part.w01_visible.sum()),
                    'w03_visible_target_count':int(part.w03_visible.sum())})
summary={'protocol':'v1.5','condition':cfg['condition'],'n_targets':180,
         'n_physical_cells':6,'metrics':metrics,
         'note':'Same six P1 cells used in development; cropped deep-charge proxy, not official 4S C/20 or independent D2.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'metrics':{x['method']:x['macro_mae_pp'] for x in metrics}},ensure_ascii=False),flush=True)
