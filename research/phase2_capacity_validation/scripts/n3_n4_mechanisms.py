"""Reconstruct official event context and current-counter behavior; no capacity labels."""
import csv,json,sys,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework.data import load_dataset

op=load_dataset(ROOT/'data').operation
ev=pd.read_csv(ROOT/'research/phase2_baseline_repair/outputs/event_audit.csv')
out=[];sensitivity=[]
for r in ev.itertuples():
    a,b=int(r.start_index),int(r.end_index)
    first=max(0,a-1)
    past=op.iloc[max(0,a-180):a]
    same=past[past.segment==r.segment]
    w=op.iloc[a:b+1]
    pre=op.iloc[a-1] if a else None
    cell=np.array([op.iloc[a][f'cell{k}_V'] for k in range(1,5)],float)
    before_delta=np.nan if pre is None else (op.timestamp.iloc[a]-pre.timestamp).total_seconds()
    tail_rest=0
    for x in same.iloc[::-1].itertuples():
        if abs(x.current_A)<0.5:tail_rest+=1
        else:break
    t=w.timestamp.astype('int64').to_numpy()/1e9
    i=w.current_A.to_numpy(float)
    dt=np.diff(t)
    left=float(np.sum(i[:-1]*dt)/3600)
    right=float(np.sum(i[1:]*dt)/3600)
    trap=(left+right)/2
    # The historical selector sums current at sample k times incoming dt.
    original=float(r.Q_partial_Ah)
    out.append(dict(event_id=r.event_id,segment=r.segment,source='official_operation',evidence_tier='unlabeled_mechanism',
      start_timestamp=r.t_start,end_timestamp=r.t_end,first_event_in_segment=int(not (ev[(ev.segment==r.segment)&(ev.event_id<r.event_id)].shape[0])),
      start_current_A=r.current_start_A,prestart_current_A=r.prestart_current_A,start_pack_V=r.pack_start_V,
      prestart_pack_V=r.prestart_pack_V,cell_spread_start_V=float(cell.max()-cell.min()),
      temperature_start_C=float(op.iloc[a].temp_mean_C),temperature_mean_C=r.temp_mean_C,
      previous_same_segment_rows=len(same),previous_30min_mean_current_A=float(same.current_A.mean()) if len(same) else np.nan,
      trailing_rest_samples=tail_rest,prestart_gap_s=before_delta,
      start_class='loaded_20A' if r.current_start_A>5 else 'idle_0A',
      Q_partial_Ah=original,Q_trap_Ah=trap,charge_counter_delta_Ah=r.charge_counter_delta_Ah,
      end_current_A=r.current_end_A,max_gap_s=r.max_gap_s,
      interpretation='start_class_is_selector_boundary_not_SOC_measurement'))
    sensitivity.append(dict(event_id=r.event_id,source='official_operation',kind='charge_event',
      left_Ah=left,right_Ah=right,trapezoid_Ah=trap,historical_Ah=original,
      left_minus_right_Ah=left-right,zero_offset_0p05A_assumed_delta_Ah=0.05*(t[-1]-t[0])/3600,
      gain_1pct_assumed_delta_Ah=0.01*trap,max_gap_s=float(max(dt)),
      gap_gt_60_count=int((dt>60).sum()),evidence='integration_rule_sensitivity_not_meter_calibration'))

events=pd.DataFrame(out);events.to_csv(T/'outputs/event_state_comparison.csv',index=False)
count=[]
for s,g in op.groupby('segment',sort=True):
    # Contiguous 10-30 minute current regimes, calculated only within segment.
    i=g.current_A.to_numpy(float);ts=g.timestamp.astype('int64').to_numpy()/1e9
    ch=g.charge_Ah_cum.to_numpy(float);dis=g.discharge_Ah_cum.to_numpy(float)
    states=np.where(i>0.5,'charge',np.where(i< -0.5,'discharge','idle'))
    breaks=np.flatnonzero((states[1:]!=states[:-1]) | (np.diff(ts)>120)) + 1
    edges=np.r_[0,breaks,len(g)]
    for k,(a,b) in enumerate(zip(edges[:-1],edges[1:])):
      if b-a<20:continue
      dt=np.diff(ts[a:b]);ii=i[a:b]
      if len(dt)==0:continue
      left=float(np.dot(ii[:-1],dt)/3600);right=float(np.dot(ii[1:],dt)/3600);trap=(left+right)/2
      cc=float(ch[b-1]-ch[a]);dc=float(dis[b-1]-dis[a])
      count.append(dict(segment=int(s),piece_id=k,start=str(g.timestamp.iloc[a]),end=str(g.timestamp.iloc[b-1]),
        state=states[a],n_rows=b-a,duration_s=float(ts[b-1]-ts[a]),max_gap_s=float(max(dt)),
        current_left_signed_Ah=left,current_right_signed_Ah=right,current_trap_signed_Ah=trap,
        charge_counter_delta_Ah=cc,discharge_counter_delta_Ah=dc,
        charge_minus_abs_integral_Ah=cc-abs(trap),discharge_minus_abs_integral_Ah=dc-abs(trap),
        charge_counter_negative_step_count=int(np.sum(np.diff(ch[a:b])< -0.01)),
        discharge_counter_negative_step_count=int(np.sum(np.diff(dis[a:b])< -0.01)),
        data_role='time_late_validation' if ts[a]>=np.quantile(ts,.7) else 'time_early_development',
        interpretation='counter_not_assumed_ground_truth'))
pd.DataFrame(count).to_csv(T/'outputs/counter_semantics.csv',index=False)
for row in count:
 if row['state']=='discharge' and row['n_rows']>=100:
  sensitivity.append(dict(event_id=f"segment{row['segment']}_piece{row['piece_id']}",source='official_operation',kind='discharge_piece',
    left_Ah=row['current_left_signed_Ah'],right_Ah=row['current_right_signed_Ah'],trapezoid_Ah=row['current_trap_signed_Ah'],historical_Ah=np.nan,
    left_minus_right_Ah=row['current_left_signed_Ah']-row['current_right_signed_Ah'],
    zero_offset_0p05A_assumed_delta_Ah=0.05*row['duration_s']/3600,
    gain_1pct_assumed_delta_Ah=0.01*row['current_trap_signed_Ah'],
    max_gap_s=row['max_gap_s'],gap_gt_60_count=int(row['max_gap_s']>60),
    evidence='integration_rule_sensitivity_not_meter_calibration'))
pd.DataFrame(sensitivity).to_csv(T/'outputs/integration_sensitivity.csv',index=False)
def summary(df):
 return dict(n=int(len(df)),q_min=float(df.Q_partial_Ah.min()),q_median=float(df.Q_partial_Ah.median()),
  q_max=float(df.Q_partial_Ah.max()),temp_min=float(df.temperature_start_C.min()),temp_max=float(df.temperature_start_C.max()),
  first_segment=int(df.first_event_in_segment.sum()),mean_start_current=float(df.start_current_A.mean()))
res=dict(event_classes={key:summary(g) for key,g in events.groupby('start_class')},
  n_counter_pieces=len(count),discharge_pieces=int(sum(x['state']=='discharge' for x in count)),
  long_event_selector_boundary_all_first=bool((events[events.Q_partial_Ah>40].first_event_in_segment==1).all()),
  source_sha256=hashlib.sha256((ROOT/'research/phase2_baseline_repair/outputs/event_audit.csv').read_bytes()).hexdigest())
run=T/'runs/N3_N4_mechanisms_20260930_v1';run.mkdir(exist_ok=True)
(run/'result.json').write_text(json.dumps(res,indent=2,ensure_ascii=False));(run/'COMPLETED').write_text('complete\n')
print(json.dumps(res,indent=2,ensure_ascii=False))
