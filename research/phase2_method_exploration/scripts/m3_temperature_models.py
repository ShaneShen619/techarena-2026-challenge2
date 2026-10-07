"""Separate current-T, cropped-history-T and weak Arrhenius exposure channels."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m2_features import AGE,frame_for_condition
OUT=TASK/'runs/M3_temperature_models_v1'
OUT.mkdir(parents=True,exist_ok=False)
cfg=json.loads((TASK/'configs/m3_validation.json').read_text())
X=frame_for_condition(20,'persistent')
labels=pd.read_csv(ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv',
                   usecols=['cell_id','target_ordinal','target_soh_pp'])
keys=pd.MultiIndex.from_frame(X[['cell_id','target_ordinal']])
y=labels.set_index(['cell_id','target_ordinal']).loc[keys,'target_soh_pp'].to_numpy(float)
cell=X.cell_id.to_numpy(str);anchor=X.anchor_pp.to_numpy(float)
group=np.array([int(re.search(r'_(\d+)degC_',s).group(1)) for s in cell])
methods=['age_rate_noT','current_T','history_T','both_T','history_arrhenius','temperature_age_interaction']
alphas=[.1,1,10,100,1000]
EA=37300.;RGAS=8.314

def raw_design(frame,method):
    a=frame[AGE+['current_A']].to_numpy(float)
    if method=='age_rate_noT':return a
    cur=frame.current_temp_C.to_numpy(float)
    hist=frame.history_temp_C.to_numpy(float)
    cmiss=(~np.isfinite(cur)).astype(float)
    hmiss=(~np.isfinite(hist)).astype(float)
    if method=='current_T':
        return np.column_stack([a,cur,cmiss])
    if method=='history_T':
        return np.column_stack([a,hist,hmiss])
    if method=='both_T':
        return np.column_stack([a,cur,hist,cur-hist,cmiss,hmiss])
    if method=='history_arrhenius':
        # External 37.3 kJ/mol weak prior, converted to J/mol explicitly.
        # A current 15-fragment temperature summary is NOT full lifetime exposure.
        acceleration=np.exp(np.clip(EA/RGAS*(1/298.15-1/(hist+273.15)),-3,3))
        exposure=frame.prefix_prequalified_charge_count.to_numpy(float)/1000*acceleration
        return np.column_stack([a,exposure,hmiss])
    if method=='temperature_age_interaction':
        count=frame.prefix_prequalified_charge_count.to_numpy(float)/1000
        return np.column_stack([a,cur,hist,(cur-37)*count,(hist-37)*count,cmiss,hmiss])
    raise KeyError(method)

def normalize(train_raw,test_raw):
    med=np.array([np.nanmedian(col) if np.isfinite(col).any() else 0. for col in train_raw.T])
    a=np.where(np.isfinite(train_raw),train_raw,med)
    b=np.where(np.isfinite(test_raw),test_raw,med)
    mean=a.mean(axis=0);scale=a.std(axis=0)
    scale=np.where(scale>=1e-10,scale,1.)
    return (a-mean)/scale,(b-mean)/scale

def fit_predict(train,test,method,alpha,test_frame=None):
    train_frame=X.iloc[train]
    test_frame=X.iloc[test] if test_frame is None else test_frame
    a,b=normalize(raw_design(train_frame,method),raw_design(test_frame,method))
    aa=np.column_stack([np.ones(len(a)),a]);bb=np.column_stack([np.ones(len(b)),b])
    penalty=np.diag([1e-10]+[alpha+1e-10]*a.shape[1])
    coef=np.linalg.solve(aa.T@aa+penalty,aa.T@(y[train]-anchor[train]))
    return test_frame.anchor_pp.to_numpy(float)+bb@coef

def choose(train,method):
    scores=[]
    for alpha in alphas:
        errs=[]
        for held in np.unique(cell[train]):
            val=train[cell[train]==held];fit=train[cell[train]!=held]
            errs.append(float(np.abs(fit_predict(fit,val,method,alpha)-y[val]).mean()))
        scores.append((float(np.mean(errs)),alpha))
    return min(scores)

rows=[];selection=[];bias=[]
for held in np.unique(cell):
    train=np.flatnonzero(cell!=held);test=np.flatnonzero(cell==held)
    for method in methods:
        score,alpha=choose(train,method)
        selection.append({'held_cell':held,'method':method,'alpha':alpha,'inner_macro_mae_pp':score})
        base=fit_predict(train,test,method,alpha)
        for i,index in enumerate(test):
            rows.append({'cell_id':held,'target_ordinal':int(X.target_ordinal.iat[index]),
                         'nominal_group_C_split_only':int(group[index]),
                         'method':method,'actual_pp':float(y[index]),'pred_pp':float(base[i]),
                         'error_pp':float(base[i]-y[index])})
        for channel in ['current','history']:
            for signed in cfg['sensor_bias_C']:
                changed=X.iloc[test].copy()
                col='current_temp_C' if channel=='current' else 'history_temp_C'
                changed[col]=changed[col]+signed
                modified=fit_predict(train,test,method,alpha,changed)
                for i,index in enumerate(test):
                    bias.append({'cell_id':held,'target_ordinal':int(X.target_ordinal.iat[index]),
                                 'method':method,'channel':channel,'bias_C':signed,
                                 'base_pp':float(base[i]),'biased_pp':float(modified[i]),
                                 'delta_pp':float(modified[i]-base[i])})
    print('held',held,flush=True)
pred=pd.DataFrame(rows);pred.to_csv(OUT/'LOCO_predictions.csv',index=False)
pd.DataFrame(selection).to_csv(OUT/'inner_selections.csv',index=False)
pd.DataFrame(bias).to_csv(OUT/'sensor_bias_predictions.csv',index=False)
metrics=[]
for method,part in pred.groupby('method'):
    per=part.assign(ae=part.error_pp.abs()).groupby('cell_id').ae.mean()
    metrics.append({'method':method,'macro_mae_pp':float(per.mean()),
                    'worst_cell_mae_pp':float(per.max()),
                    'max_abs_error_pp':float(part.error_pp.abs().max()),
                    'per_cell_mae_pp':{k:float(v) for k,v in per.items()}})

# Temperature-group holdout is a harder, descriptive extrapolation check.
group_rows=[]
for heldT in np.unique(group):
    train=np.flatnonzero(group!=heldT);test=np.flatnonzero(group==heldT)
    for method in methods:
        score,alpha=choose(train,method)
        out=fit_predict(train,test,method,alpha)
        for i,index in enumerate(test):
            group_rows.append({'held_temperature_group_C':int(heldT),'cell_id':cell[index],
                               'target_ordinal':int(X.target_ordinal.iat[index]),
                               'method':method,'pred_pp':float(out[i]),
                               'actual_pp':float(y[index]),'error_pp':float(out[i]-y[index]),
                               'inner_macro_mae_pp':score,'selected_alpha':alpha})
g=pd.DataFrame(group_rows);g.to_csv(OUT/'held_temperature_group_predictions.csv',index=False)
group_score=g.assign(ae=g.error_pp.abs()).groupby(['held_temperature_group_C','method'],as_index=False).ae.mean()
group_score.to_csv(OUT/'held_temperature_group_scores.csv',index=False)
b=pd.DataFrame(bias)
bs=[]
for (method,channel,signed),part in b.loc[b.bias_C!=0].groupby(['method','channel','bias_C']):
    bs.append({'method':method,'channel':channel,'bias_C':signed,
               'median_abs_prediction_shift_pp':float(part.delta_pp.abs().median()),
               'p95_abs_prediction_shift_pp':float(part.delta_pp.abs().quantile(.95)),
               'max_abs_prediction_shift_pp':float(part.delta_pp.abs().max()),
               'shift_gt0p5pp_targets':int(part.delta_pp.abs().gt(.5).sum())})
pd.DataFrame(bs).to_csv(OUT/'sensor_bias_summary.csv',index=False)
summary={'protocol':'v1.4','evidence':'P1 six-cell development proxy',
         'observed_current_temperature_missing_targets':int(X.current_temp_C.isna().sum()),
         'observed_cropped_history_temperature_missing_targets':int(X.history_temp_C.isna().sum()),
         'external_Ea_kJ_per_mol_weak_prior':EA/1000,
         'metrics':metrics,'temperature_group_holdout':group_score.to_dict(orient='records'),
         'sensor_bias_summary':bs,
         'causal_temperature_coefficient_identifiable':False,
         'reason':'Only 6 near-age P1 temperature pairs met the frozen matching rule; chamber/cell/age remain confounded.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({m['method']:m['macro_mae_pp'] for m in metrics},ensure_ascii=False),flush=True)
