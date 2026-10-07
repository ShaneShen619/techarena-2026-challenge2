"""LOSO TU step-response benchmark with causal per-cell time filtering."""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M6_workpoint_time_v2';OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(TASK/'src'))
from m6_models import features,centers_farthest,rbf,ridge_fit,WienerResidual
cfg=json.loads((TASK/'configs/m6_model.json').read_text())
source=TASK/'runs/M6_TU_steps_v1'
inventory=pd.read_csv(source/'extraction_summary_by_system.csv')
eligible_systems=inventory.loc[inventory.selected_3h_ge10A.ge(100),'system'].tolist()
def load(sysid):
    path=source/f'system_{sysid:02d}_events.csv'
    if path.stat().st_size==0:return pd.DataFrame()
    x=pd.read_csv(path,parse_dates=['timestamp'])
    return x.loc[x.threshold_A.eq(10)&x.R_plausible].copy()
cache={int(s):load(int(s)) for s in inventory.system}
assert len(eligible_systems)>=4,eligible_systems
all_predictions=[];folds=[]
for held in eligible_systems:
    train=[]
    for sid,frame in cache.items():
        if sid==held or len(frame)==0:continue
        event_times=frame.timestamp.drop_duplicates().sort_values().to_numpy()
        ix=np.unique(np.linspace(0,len(event_times)-1,min(cfg['train_cap_events_per_system'],len(event_times))).astype(int))
        keep=pd.Index(event_times[ix]);train.append(frame.loc[frame.timestamp.isin(keep)])
    train=pd.concat(train,ignore_index=True)
    train=train.loc[train.R_step_mOhm.between(*cfg['outlier_target_range_mOhm'])]
    y=train.R_step_mOhm.to_numpy(float)
    X=features(train)
    center=centers_farthest(X,cfg['spatial_kernel']['n_fixed_centers'],seed=20260928+int(held))
    Plinear=np.column_stack([np.ones(len(X)),X]);blinear,_=ridge_fit(Plinear,y,cfg['linear_ridge_alpha'])
    Prbf=np.column_stack([np.ones(len(X)),rbf(X,center)]);brbf,A= ridge_fit(Prbf,y,cfg['spatial_kernel']['ridge_alpha'])
    median=float(np.median(y));resid=y-Prbf@brbf
    noise=float(max(.1,1.4826*np.median(np.abs(resid-np.median(resid)))))
    cov=noise**2*np.linalg.inv(A)
    target=cache[held].sort_values(['cell','timestamp'])
    warm=0;score_count=0
    for cell,part in target.groupby('cell'):
        if len(part)<80:continue
        part=part.sort_values('timestamp')
        n_warm=max(20,int(np.floor(.2*len(part))))
        x=features(part);px=np.column_stack([np.ones(len(x)),x]);pr=np.column_stack([np.ones(len(x)),rbf(x,center)])
        linear=px@blinear;spatial=pr@brbf
        spatial_var=np.maximum(noise**2,np.einsum('ij,jk,ik->i',pr,cov,pr)+noise**2)
        filter=WienerResidual(noise,
            cfg['time_filter']['process_std_mOhm_per_sqrt_day'],
            cfg['time_filter']['initial_std_mOhm'],
            cfg['time_filter']['max_filter_abs_state_mOhm'])
        prev_R=None
        for j,(row,lin,sp,var) in enumerate(zip(part.itertuples(index=False),linear,spatial,spatial_var)):
            m,p=filter.predict(row.timestamp)
            ytrue=float(row.R_step_mOhm)
            if j>=n_warm:
                pred={'global_median':median,'workpoint_linear_ridge':float(lin),
                      'workpoint_RBF_approx':float(sp),
                      'RBF_plus_causal_Wiener_time':float(sp+m),
                      'last_same_cell_step':float(prev_R)}
                sigma={'global_median':noise,'workpoint_linear_ridge':noise,
                       'workpoint_RBF_approx':np.sqrt(var),
                       'RBF_plus_causal_Wiener_time':np.sqrt(var+p),
                       'last_same_cell_step':noise}
                for method,yp in pred.items():
                    all_predictions.append({'held_system':held,'cell':cell,'timestamp':row.timestamp.isoformat(),
                        'I_after_A':row.I_after_A,'SOC_BMS_pct':row.SOC_BMS_pct,'temperature_C':row.temperature_C,
                        'delta_I_A':row.delta_I_A,'method':method,
                        'actual_R_mOhm':ytrue,'pred_R_mOhm':yp,'error_mOhm':yp-ytrue,
                        'interval90_low_mOhm':yp-1.645*sigma[method],
                        'interval90_high_mOhm':yp+1.645*sigma[method],
                        'warmup_rows_same_cell':n_warm,'train_other_system_rows':len(train)})
                score_count+=1
            else:warm+=1
            # Observations update state only after any prediction at this time.
            filter.update(ytrue-float(sp))
            prev_R=ytrue
    folds.append({'held_system':held,'train_other_system_rows':len(train),
                  'target_cell_rows_scored':score_count,'target_cell_rows_warmup':warm,
                  'training_R_median_mOhm':median,'training_R_residual_robust_std_mOhm':noise})
    print(f'held {held:02d} train {len(train)} scored {score_count}',flush=True)
pred=pd.DataFrame(all_predictions);pred.to_csv(OUT/'LOSO_online_predictions.csv',index=False)
pd.DataFrame(folds).to_csv(OUT/'folds.csv',index=False)
pred['abs_error_mOhm']=pred.error_mOhm.abs()
pred['covered90']=(pred.actual_R_mOhm>=pred.interval90_low_mOhm)&(pred.actual_R_mOhm<=pred.interval90_high_mOhm)
per=pred.groupby(['held_system','method'],as_index=False).agg(
    MAE_mOhm=('abs_error_mOhm','mean'),RMSE_mOhm=('error_mOhm',lambda s:float(np.sqrt(np.mean(s**2)))),
    P95_abs_mOhm=('abs_error_mOhm',lambda s:float(np.quantile(s,.95))),
    coverage90=('covered90','mean'),n=('error_mOhm','size'))
per.to_csv(OUT/'per_system_scores.csv',index=False)
summary={'eligible_held_systems':eligible_systems,'held_system_count':len(eligible_systems),
         'scored_cell_events':int(pred[['held_system','cell','timestamp']].drop_duplicates().shape[0]),
         'system_macro_MAE_mOhm':{str(k):float(v) for k,v in per.groupby('method').MAE_mOhm.mean().items()},
         'system_macro_RMSE_mOhm':{str(k):float(v) for k,v in per.groupby('method').RMSE_mOhm.mean().items()},
         'worst_system_MAE_mOhm':{str(k):float(v) for k,v in per.groupby('method').MAE_mOhm.max().items()},
         'system_macro_coverage90':{str(k):float(v) for k,v in per.groupby('method').coverage90.mean().items()},
         'label_limit':'step-response mOhm only, no independent capacity labels',
         'method_limit':cfg['claim_limit']}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
