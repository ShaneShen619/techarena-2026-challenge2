"""Walk-forward test of official apparent-R increments beyond matched pulse waveform."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M6_official_R_aux_v1';OUT.mkdir(parents=True,exist_ok=False)
cfg=json.loads((TASK/'configs/m6_official_R_aux.json').read_text())
feat=pd.read_csv(TASK/'runs/M1_voltage_forecast_v1/pulse_features.csv')
base=pd.read_csv(TASK/'runs/M1_voltage_forecast_v1/forward_voltage_predictions.csv')
base=base.loc[base.method.eq('matched_last_shift')].copy()
feat=feat.sort_values('start')
events=[]
for row in base[['start','cell','chamber_C']].drop_duplicates().itertuples(index=False):
    target=feat.loc[feat.start.eq(row.start)&feat.cell.eq(row.cell)].iloc[0]
    prior=feat.loc[feat.start.lt(row.start)&feat.cell.eq(row.cell)&feat.chamber_C.eq(row.chamber_C)]
    assert len(prior)>=2
    last=prior.iloc[-1]
    events.append({'start':row.start,'cell':row.cell,'chamber_C':row.chamber_C,
                   'delta_R10_mOhm':float(target.apparent_R_10s_mOhm-last.apparent_R_10s_mOhm)})
event=pd.DataFrame(events).sort_values(['start','cell'])
rot=event.copy();rot['cell']=rot.cell.map({1:2,2:3,3:4,4:1})
rot=rot.rename(columns={'delta_R10_mOhm':'wrong_cell_delta_R10_mOhm'})
event=event.merge(rot,on=['start','cell','chamber_C'],validate='one_to_one')
base=base.merge(event,on=['start','cell','chamber_C'],validate='many_to_one')
base['shape']=1-np.exp(-np.maximum(base.q_Ah-1,0)/2)
base['baseline_error_mV']=base.error_mV
records=[]
for start,part in base.groupby('start',sort=True):
    past=base.loc[base.start.lt(start)]
    if len(past):
        # Each physical cell event contributes one average residual, so 81
        # samples from one pulse are not falsely treated as independent.
        pe=past.groupby(['start','cell']).agg(x=('delta_R10_mOhm','first'),
                y=('baseline_error_mV','mean'),f=('shape','mean'))
        x=pe.x.to_numpy()*pe.f.to_numpy();y=pe.y.to_numpy()
        beta=float(np.clip(-np.dot(x,y)/(np.dot(x,x)+cfg['ridge_penalty']),
                           *cfg['coefficient_bound_mV_per_mOhm']))
    else:beta=0.
    for r in part.itertuples(index=False):
        # Saved error = baseline prediction - actual. Correcting forecast by
        # +beta*deltaR*shape adds that amount to the error.
        for method,dR in [('matched_last_shift',0.),('R10_delta_walkforward',r.delta_R10_mOhm),
                          ('wrong_cell_R10_control',r.wrong_cell_delta_R10_mOhm)]:
            err=r.baseline_error_mV+beta*dR*r.shape
            records.append({'start':r.start,'cell':r.cell,'chamber_C':r.chamber_C,'q_Ah':r.q_Ah,
                            'method':method,'actual_V':r.actual_V,
                            'predicted_V':r.actual_V+err/1000,'error_mV':err,
                            'delta_R10_mOhm':dR,'walkforward_beta_mV_per_mOhm':beta,
                            'earlier_pulse_cell_events':int(past[['start','cell']].drop_duplicates().shape[0])})
out=pd.DataFrame(records);out.to_csv(OUT/'forward_predictions.csv',index=False)
event_scores=out.assign(abs_mV=out.error_mV.abs()).groupby(['start','cell','method'],as_index=False).abs_mV.mean()
event_scores.to_csv(OUT/'event_scores.csv',index=False)
summary={'cell_events':len(event),'future_voltage_MAE_mV':{str(k):float(v) for k,v in event_scores.groupby('method').abs_mV.mean().items()},
         'walkforward_beta_last_mV_per_mOhm':float(out.walkforward_beta_mV_per_mOhm.iloc[-1]),
         'mean_abs_delta_R10_mOhm':float(event.delta_R10_mOhm.abs().mean()),
         'claim_limit':cfg['claim'],'TU_transfer_limit':cfg['selection_limit']}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
