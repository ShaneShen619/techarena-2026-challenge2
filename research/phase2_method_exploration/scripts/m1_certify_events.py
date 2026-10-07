"""Certify official 20 A diagnostic episodes from raw rows, without capacity labels.

Thresholds below are fixed before inspecting candidate-level errors. They test
the published roughly 30-minute pulse after a full CCCV charge. Named charge/
discharge counters are audited but not assumed to encode current sign correctly.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M1_certification_v2'
OUT.mkdir(parents=True,exist_ok=False)
CAND=TASK/'runs/M0_pulse_replay_v1/pulse_candidates.csv'
candidate=pd.read_csv(CAND,parse_dates=['start','end'])
rows=[]

def contiguous_rest(f:pd.DataFrame,index:int,step:int)->pd.DataFrame:
    gathered=[]
    last=index-step
    while 0<=index<len(f):
        if abs(float(f.current_A.iat[index]))>0.5:
            break
        if gathered:
            dt=abs((f.timestamp.iat[index]-f.timestamp.iat[last]).total_seconds())
            if dt<=0 or dt>20: break
        gathered.append(index)
        last=index
        index+=step
    return f.iloc[sorted(gathered)]

def contiguous_charge(f:pd.DataFrame,index:int)->pd.DataFrame:
    gathered=[]
    last=index+1
    while 0<=index<len(f):
        if float(f.current_A.iat[index])<5.0: break
        if gathered:
            dt=(f.timestamp.iat[last]-f.timestamp.iat[index]).total_seconds()
            if dt<0 or dt>20: break
        gathered.append(index)
        last=index
        index-=1
    return f.iloc[sorted(gathered)]

for filename,group in candidate.groupby('file',sort=True):
    f=pd.read_csv(ROOT/'data/operation'/filename,parse_dates=['timestamp'])
    for item in group.itertuples(index=False):
        starts=np.flatnonzero((f.timestamp==item.start)&f.current_A.between(-20.5,-19.5))
        ends=np.flatnonzero((f.timestamp==item.end)&f.current_A.between(-20.5,-19.5))
        if not len(starts) or not len(ends): raise RuntimeError(f'missing raw pulse {filename} {item.start}')
        first=int(starts[0]); last=int(ends[-1])
        pulse=f.iloc[first:last+1].copy()
        pre=contiguous_rest(f,first-1,-1)
        post=contiguous_rest(f,last+1,1)
        charge=contiguous_charge(f,int(pre.index[0])-1) if len(pre) else f.iloc[0:0]
        dt=pulse.timestamp.diff().dt.total_seconds().iloc[1:].to_numpy(float)
        current=pulse.current_A.to_numpy(float)
        duration=float((pulse.timestamp.iat[-1]-pulse.timestamp.iat[0]).total_seconds())
        q_integral=float(np.trapezoid(-current,pulse.timestamp.astype('int64').to_numpy()/1e9)/3600)
        counter_charge=float(pulse.charge_Ah_cum.iat[-1]-pulse.charge_Ah_cum.iat[0])
        counter_discharge=float(pulse.discharge_Ah_cum.iat[-1]-pulse.discharge_Ah_cum.iat[0])
        counter_total=counter_charge+counter_discharge
        cell_sum=pulse[[f'cell{i}_V' for i in range(1,5)]].sum(axis=1)
        residual=(pulse.pack_voltage_V-cell_sum).abs()
        pre_duration=float((pre.timestamp.iat[-1]-pre.timestamp.iat[0]).total_seconds()) if len(pre)>1 else 0.
        post_duration=float((post.timestamp.iat[-1]-post.timestamp.iat[0]).total_seconds()) if len(post)>1 else 0.
        charge_duration=float((charge.timestamp.iat[-1]-charge.timestamp.iat[0]).total_seconds()) if len(charge)>1 else 0.
        gates={
            'duration_1700_1900s':1700<=duration<=1900,
            'all_samples_minus20p5_to_minus19p5A':bool(pulse.current_A.between(-20.5,-19.5).all()),
            'positive_dt_le20s':bool(len(dt)>0 and np.isfinite(dt).all() and (dt>0).all() and (dt<=20).all()),
            'current_stable_0p25A':bool(np.max(np.abs(current-np.median(current)))<=0.25),
            'prior_charge_ge60min_and_13p95V':bool(charge_duration>=3600 and len(charge) and charge.pack_voltage_V.max()>=13.95),
            'pre_rest_ge25min':pre_duration>=1500,
            'temperature_span_le2C':float(pulse.temp_mean_C.max()-pulse.temp_mean_C.min())<=2.0,
            'counter_sum_matches_integral_0p2Ah':abs(counter_total-q_integral)<=0.2,
            'pack_cell_median_residual_le0p05V':float(residual.median())<=0.05,
        }
        rows.append({'file':filename,'start':item.start.isoformat(),'end':item.end.isoformat(),
                     'before_CK7':bool(item.before_CK7),'chamber_C':item.chamber_C,
                     'duration_s':duration,'n_samples':len(pulse),'median_dt_s':float(np.median(dt)),
                     'q_integral_Ah':q_integral,'charge_counter_delta_Ah':counter_charge,
                     'discharge_counter_delta_Ah':counter_discharge,'counter_sum_delta_Ah':counter_total,
                     'counter_named_discharge_matches':abs(counter_discharge-q_integral)<=0.2,
                     'pre_rest_s':pre_duration,'post_rest_s':post_duration,
                     'prior_charge_s':charge_duration,
                     'prior_charge_max_pack_V':float(charge.pack_voltage_V.max()) if len(charge) else None,
                     'prior_charge_end':charge.timestamp.iat[-1].isoformat() if len(charge) else '',
                     'pre_rest_start':pre.timestamp.iat[0].isoformat() if len(pre) else '',
                     'post_rest_end':post.timestamp.iat[-1].isoformat() if len(post) else '',
                     'temp_span_C':float(pulse.temp_mean_C.max()-pulse.temp_mean_C.min()),
                     'pack_cell_median_abs_residual_V':float(residual.median()),
                     'pack_cell_p95_abs_residual_V':float(residual.quantile(.95)),
                     'v_start_pack_V':float(pulse.pack_voltage_V.iat[0]),
                     'v_end_pack_V':float(pulse.pack_voltage_V.iat[-1]),
                     'accepted':all(gates.values()),
                     'reject_reasons':';'.join(k for k,v in gates.items() if not v),
                     **{f'gate_{k}':bool(v) for k,v in gates.items()}})
    print(filename,'certified_so_far',sum(x['accepted'] for x in rows),'of',len(rows),flush=True)

frame=pd.DataFrame(rows)
frame.to_csv(OUT/'event_certification.csv',index=False)
summary={'candidate_count':len(frame),'accepted':int(frame.accepted.sum()),
         'rejected':int((~frame.accepted).sum()),
         'accepted_before_CK7':int((frame.accepted&frame.before_CK7).sum()),
         'gate_failure_counts':{c.removeprefix('gate_'):int((~frame[c]).sum()) for c in frame if c.startswith('gate_')},
         'named_discharge_counter_matches_count':int(frame.counter_named_discharge_matches.sum()),
         'pulse_integral_Ah_median':float(frame.q_integral_Ah.median()),
         'pre_rest_s_median':float(frame.pre_rest_s.median()),
         'post_rest_s_median':float(frame.post_rest_s.median()),
         'note':'Certification based only on official input rows; no hidden capacity truth. Charge/discharge named counter inconsistency is separately audited.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
