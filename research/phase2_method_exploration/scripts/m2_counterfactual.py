"""Freeze primary-trained models, vary only the crop of the same P1 events.

The true capacity for a target is unchanged across crop positions. A large
prediction change therefore falsifies invariance to observation position.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m2_features import AGE,frame_for_condition

OUT=TASK/'runs/M2_crop_counterfactual_v1'
OUT.mkdir(parents=True,exist_ok=False)
primary=frame_for_condition(20,'persistent')
variants={'3p45':'M2_crop_3p45_v1','3p55':'M2_crop_3p55_v1',
          'full_tail':'M2_crop_full_tail_v1','mid_event':'M2_crop_mid_event_v1'}
frames={'primary':primary}
for name,dirname in variants.items():
    path=TASK/'runs'/dirname
    frames[name]=frame_for_condition(20,'persistent',path/'visibility.csv',path/'cropped_events.csv')
    assert frames[name][['cell_id','target_ordinal']].equals(primary[['cell_id','target_ordinal']])
panel=pd.read_csv(ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv',
                  usecols=['cell_id','target_ordinal','target_soh_pp'])
keys=pd.MultiIndex.from_frame(primary[['cell_id','target_ordinal']])
truth=panel.set_index(['cell_id','target_ordinal']).loc[keys,'target_soh_pp'].to_numpy(float)
cell=primary.cell_id.to_numpy(str)
selection=pd.read_csv(TASK/'runs/M2_primary_v2/inner_selections.csv')
saved=pd.read_csv(TASK/'runs/M2_primary_v2/predictions.csv')

def cols(method,param):
    if method=='age_ridge':return AGE
    if method=='fixed_window_ridge':
        w=param['window'];return AGE+[f'w{w:02d}_Ah',f'w{w:02d}_mask']
    if method=='within_cell_ratio_ridge':
        w=param['window'];return AGE+[f'w{w:02d}_ratio',f'w{w:02d}_mask']
    names=AGE+[f'w{w:02d}_{suffix}' for w in range(9) for suffix in ('Ah','mask')]
    return names+(['v_start_V','v_end_V','current_A','observed_span_Ah'] if method=='rbf_residual' else [])

def matrices(train,test,columns):
    a=train[columns].to_numpy(float);b=test[columns].to_numpy(float)
    med=np.array([np.nanmedian(c) if np.isfinite(c).any() else 0. for c in a.T])
    a=np.where(np.isfinite(a),a,med);b=np.where(np.isfinite(b),b,med)
    mean=a.mean(axis=0);scale=a.std(axis=0);scale=np.where(scale>=1e-10,scale,1.)
    return (a-mean)/scale,(b-mean)/scale

def ridge(a,y,b,alpha):
    aa=np.column_stack([np.ones(len(a)),a]);bb=np.column_stack([np.ones(len(b)),b])
    penalty=np.diag([0.]+[float(alpha)]*a.shape[1])
    coef=np.linalg.solve(aa.T@aa+penalty+np.eye(aa.shape[1])*1e-10,aa.T@y)
    return bb@coef

def predict(method,param,train_idx,test_idx,test_frame):
    train=primary.iloc[train_idx];test=test_frame.iloc[test_idx]
    y=truth[train_idx]-train.anchor_pp.to_numpy(float)
    a,b=matrices(train,test,cols(method,param))
    if method!='rbf_residual':
        delta=ridge(a,y,b,param['alpha'])
    else:
        age_a,age_b=matrices(train,test,AGE)
        base_train=ridge(age_a,y,age_a,10.)
        base_test=ridge(age_a,y,age_b,10.)
        length=float(param['lengthscale'])
        kernel=np.exp(-((a[:,None,:]-a[None,:,:])**2).mean(axis=2)/(2*length**2))
        cross=np.exp(-((b[:,None,:]-a[None,:,:])**2).mean(axis=2)/(2*length**2))
        weights=np.linalg.solve(kernel+np.eye(len(a))*float(param['alpha']),y-base_train)
        delta=base_test+cross@weights
    return test.anchor_pp.to_numpy(float)+delta

rows=[]
for held in np.unique(cell):
    train_idx=np.flatnonzero(cell!=held);test_idx=np.flatnonzero(cell==held)
    for method in ['age_ridge','fixed_window_ridge','mask_ridge',
                   'within_cell_ratio_ridge','rbf_residual']:
        select=selection.loc[(selection.held_cell==held)&(selection.method==method)]
        assert len(select)==1
        param=json.loads(select.selected_json.iloc[0])
        base=predict(method,param,train_idx,test_idx,primary)
        reference=saved.loc[(saved.held_cell==held)&(saved.method==method)].sort_values('target_ordinal').pred_soh_pp.to_numpy()
        assert np.max(np.abs(base-reference))<1e-8
        for name,frame in frames.items():
            if name=='primary':continue
            changed=predict(method,param,train_idx,test_idx,frame)
            for k,index in enumerate(test_idx):
                rows.append({'cell_id':held,'target_ordinal':int(primary.target_ordinal.iat[index]),
                             'method':method,'alternate_crop':name,
                             'primary_prediction_pp':float(base[k]),
                             'alternate_prediction_pp':float(changed[k]),
                             'shift_pp':float(changed[k]-base[k]),
                             'abs_shift_pp':float(abs(changed[k]-base[k])),
                             'primary_current_w01':int(primary.w01_mask.iat[index]),
                             'alternate_current_w01':int(frame.w01_mask.iat[index]),
                             'alternate_current_w03':int(frame.w03_mask.iat[index])})
result=pd.DataFrame(rows)
result.to_csv(OUT/'same_capacity_crop_shifts.csv',index=False)
summ=[]
for (crop,method),part in result.groupby(['alternate_crop','method']):
    summ.append({'alternate_crop':crop,'method':method,'n_targets':len(part),
                 'median_abs_shift_pp':float(part.abs_shift_pp.median()),
                 'p95_abs_shift_pp':float(part.abs_shift_pp.quantile(.95)),
                 'max_abs_shift_pp':float(part.abs_shift_pp.max()),
                 'targets_shift_gt2pp':int(part.abs_shift_pp.gt(2).sum())})
pd.DataFrame(summ).to_csv(OUT/'summary.csv',index=False)
(OUT/'summary.json').write_text(json.dumps(summ,ensure_ascii=False,indent=2)+'\n')
print(pd.DataFrame(summ).to_string(index=False),flush=True)
