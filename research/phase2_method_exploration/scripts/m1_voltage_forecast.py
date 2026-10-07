"""Forward pulse-voltage tests with equal 1 Ah target-event input budgets.

All parameters come from previous same-temperature events. The 2--10 Ah
portion of each target pulse is held out from prediction features. The output
is a voltage test; there is no CK1--CK7 capacity label in this experiment.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M1_voltage_forecast_v1'
OUT.mkdir(parents=True,exist_ok=False)
cert=pd.read_csv(TASK/'runs/M1_certification_v2/event_certification.csv',parse_dates=['start','end'])
cert=cert.loc[cert.accepted].sort_values('start')
qgrid=np.round(np.arange(0,10.001,0.1),3)
observe=(qgrid>=.2)&(qgrid<=1.0)
held=(qgrid>=2.0)&(qgrid<=10.0)
wave=[]
features=[]
for filename, group in cert.groupby('file',sort=True):
    raw=pd.read_csv(ROOT/'data/operation'/filename,parse_dates=['timestamp'])
    for item in group.itertuples(index=False):
        starts=np.flatnonzero((raw.timestamp==item.start)&raw.current_A.between(-20.5,-19.5))
        ends=np.flatnonzero((raw.timestamp==item.end)&raw.current_A.between(-20.5,-19.5))
        first=int(starts[0]);last=int(ends[-1]);pulse=raw.iloc[first:last+1]
        pre=raw.iloc[first-1]
        post=raw.iloc[last+1:last+8]
        assert abs(float(pre.current_A))<.5
        t=(pulse.timestamp.astype('int64').to_numpy()/1e9)
        dt=np.diff(t)
        current=-pulse.current_A.to_numpy(float)
        q=np.r_[0,np.cumsum((current[1:]+current[:-1])*dt/7200)]
        assert q[-1]>=10 and np.diff(q).min()>0
        for cell in range(1,5):
            name=f'cell{cell}_V'
            v=pulse[name].to_numpy(float)
            curve=np.interp(qgrid,q,v)
            pre_v=float(pre[name])
            at10=float(np.interp(10,t-t[0],v))
            at30=float(np.interp(30,t-t[0],v))
            at60=float(np.interp(60,t-t[0],v))
            current_A=float(np.median(current))
            recovery={}
            if len(post) and abs(float(post.current_A.iat[0]))<.5:
                tp=(post.timestamp.astype('int64').to_numpy()/1e9)-t[-1]
                vp=post[name].to_numpy(float)
                for sec in (10,30,60):
                    recovery[f'recovery_{sec}s_V']=float(np.interp(sec,tp,vp)-v[-1]) if tp[-1]>=sec else None
            else:
                recovery={f'recovery_{sec}s_V':None for sec in (10,30,60)}
            wave.append({'file':filename,'start':item.start.isoformat(),'cell':cell,
                         'chamber_C':int(item.chamber_C),'pre_rest_v_V':pre_v,'curve':curve})
            features.append({'file':filename,'start':item.start.isoformat(),'cell':cell,
                             'chamber_C':int(item.chamber_C),'pulse_Ah':float(q[-1]),
                             'pre_rest_v_V':pre_v,'v_10s_V':at10,'v_30s_V':at30,'v_60s_V':at60,
                             'apparent_R_10s_mOhm':(pre_v-at10)/current_A*1000,
                             'apparent_R_30s_mOhm':(pre_v-at30)/current_A*1000,
                             'apparent_R_60s_mOhm':(pre_v-at60)/current_A*1000,
                             'v_q2_V':float(np.interp(2,q,v)),'v_q5_V':float(np.interp(5,q,v)),
                             'v_q10_V':float(np.interp(10,q,v)),
                             'v_q2_q10_slope_V_per_Ah':float((np.interp(10,q,v)-np.interp(2,q,v))/8),
                             **recovery})

feature_frame=pd.DataFrame(features).sort_values(['start','cell'])
feature_frame.to_csv(OUT/'pulse_features.csv',index=False)

# One-step-forward by physical pack, temperature group and cell. Each target's
# first 1 Ah is shared across all methods; full target curve is score-only.
forecasts=[]
wave=sorted(wave,key=lambda x:x['start'])
for target in wave:
    history=[x for x in wave if x['cell']==target['cell'] and
             x['chamber_C']==target['chamber_C'] and x['start']<target['start']]
    if len(history)<2: continue
    last,prev=history[-1],history[-2]
    y=target['curve']; old=last['curve']
    delta=y[observe]-old[observe]
    shift=float(np.median(delta))
    base=old+shift
    # Fixed ECM surrogate with a 1 Ah polarization scale (~176 s at 20.4 A).
    design=np.column_stack([np.ones(len(qgrid)),qgrid,1-np.exp(-qgrid/1.0)])
    recent=history[-3:]
    curve_rel=np.mean([x['curve']-x['pre_rest_v_V'] for x in recent],axis=0)
    coef=np.linalg.lstsq(design,curve_rel,rcond=None)[0]
    ecm=target['pre_rest_v_V']+design@coef
    ecm+=np.median(y[observe]-ecm[observe])
    # Early target polarization difference, capped at 50 mV per cell.
    slope=float(np.polyfit(qgrid[observe],delta,1)[0])
    dynamic=old+shift+np.clip(slope*(qgrid-.6),-.05,.05)
    trend=last['curve']+np.clip(last['curve']-prev['curve'],-.05,.05)
    trend+=np.median(y[observe]-trend[observe])
    for method,pred in [('matched_last_shift',base),('fixed_ECM',ecm),
                        ('early_dynamic_slope',dynamic),('last_two_calendar_trend',trend)]:
        for qi in np.flatnonzero(held):
            forecasts.append({'file':target['file'],'start':target['start'],'cell':target['cell'],
                              'chamber_C':target['chamber_C'],'history_count':len(history),
                              'method':method,'q_Ah':float(qgrid[qi]),'actual_V':float(y[qi]),
                              'predicted_V':float(pred[qi]),'error_mV':float(1000*(pred[qi]-y[qi]))})
pred=pd.DataFrame(forecasts)
pred.to_csv(OUT/'forward_voltage_predictions.csv',index=False)
event=pred.assign(abs_mV=pred.error_mV.abs()).groupby(['start','cell','chamber_C','method'],as_index=False).abs_mV.mean()
event.to_csv(OUT/'event_method_mae.csv',index=False)

# Negative control: same pack, nearest opposite chamber setting within 21 days.
# Calendar, SOC and temperature remain coupled, so these are descriptive.
pair=[]
for cell,part in feature_frame.groupby('cell'):
    part=part.copy();part['t']=pd.to_datetime(part.start)
    for record in part.itertuples(index=False):
        later=part.loc[(part.t>record.t)&(part.chamber_C!=record.chamber_C)&
                       ((part.t-record.t).dt.total_seconds()<=21*86400)]
        if len(later)==0:continue
        nextrow=later.sort_values('t').iloc[0]
        if int(record.chamber_C)==25:
            r25=float(record.apparent_R_10s_mOhm);r45=float(nextrow.apparent_R_10s_mOhm)
        else:
            r25=float(nextrow.apparent_R_10s_mOhm);r45=float(record.apparent_R_10s_mOhm)
        pair.append({'cell':cell,'early_start':record.start,'later_start':nextrow.start,
                     'gap_days':float((nextrow.t-record.t).total_seconds()/86400),
                     'R25_10s_mOhm':r25,'R45_10s_mOhm':r45,'R25_minus_R45_mOhm':r25-r45})
pairs=pd.DataFrame(pair)
pairs.to_csv(OUT/'temperature_switch_resistance_pairs.csv',index=False)
summary={'certified_events':len(cert),'features_cell_events':len(feature_frame),
         'forward_test_cell_events':int(event[['start','cell']].drop_duplicates().shape[0]),
         'target_early_input_Ah':1.0,'score_interval_Ah':[2.0,10.0],
         'mae_mV_by_method':{k:float(v) for k,v in event.groupby('method').abs_mV.mean().items()},
         'mae_mV_by_temp_method':{f'{t}C_{m}':float(v) for (t,m),v in event.groupby(['chamber_C','method']).abs_mV.mean().items()},
         'opposite_temp_pair_count':len(pairs),
         'R25_minus_R45_10s_mOhm_median':float(pairs.R25_minus_R45_mOhm.median()) if len(pairs) else None,
         'interpretation_limit':'Voltage forecast and apparent resistance only; no CK1–CK7 capacity label or causal temperature isolation.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
