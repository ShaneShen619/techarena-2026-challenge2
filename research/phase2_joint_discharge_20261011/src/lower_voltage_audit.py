"""Exploratory wider-discharge trend audit, not a capacity/SOC fit."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid

TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1];OUT=TASK/'outputs'

def main():
 catalog=pd.read_csv(ROOT/'research/charge_capacity_review_20261006/operating_events.csv',parse_dates=['t_start','t_end'])
 # Fixed descriptive selection: a repeated ~33 Ah discharge program, CK7 prefix.
 candidate=catalog[catalog.kind.eq('long_dynamic_discharge')&catalog.Q_Ah.between(32.7,33)&(catalog.t_end<pd.Timestamp('2025-08-28'))]
 events=[];waves=[];qgrid=np.arange(0,32.801,.2)
 for file,group in candidate.groupby('file'):
  raw=pd.read_csv(ROOT/'data/operation'/file,parse_dates=['timestamp'])
  for row in group.itertuples(index=False):
   p=raw.iloc[row.start_index_in_file:row.end_index_in_file+1]
   assert p.timestamp.iloc[0]==row.t_start and p.timestamp.iloc[-1]==row.t_end
   t=(p.timestamp-p.timestamp.iloc[0]).dt.total_seconds().to_numpy(float);j=-p.current_A.to_numpy(float)
   q=cumulative_trapezoid(j,t,initial=0)/3600
   assert (j>.5).all() and (np.diff(t)>0).all() and (np.diff(t)<=20).all()
   assert abs(q[-1]-row.Q_Ah)<1e-7 and q[-1]>=qgrid[-1]
   pack=p.pack_voltage_V.to_numpy(float);cells=p[[f'cell{i}_V' for i in range(1,5)]].to_numpy(float)
   record=dict(start=row.t_start.isoformat(),end=row.t_end.isoformat(),T=int(row.setpoint_C),q_Ah=float(q[-1]),start_pack_V=float(pack[0]),end_pack_V=float(pack[-1]),
    mean_T_C=float(p.temp_mean_C.mean()),start_current_A=float(j[0]),end_current_A=float(j[-1]),max_gap_s=float(np.diff(t).max()),
    cell_mean_end_V=float(cells[-1].mean()),pack_drop_V=float(pack[0]-pack[-1]))
   events.append(record)
   waves.append(dict(**record,q=qgrid,pack=np.interp(qgrid,q,pack),current=np.interp(qgrid,q,j),cells=np.stack([np.interp(qgrid,q,cells[:,i]) for i in range(4)],axis=1)))
 events=pd.DataFrame(events).sort_values('start');events.to_csv(OUT/'wider_discharge_events.csv',index=False)
 result=[];overlay=[]
 for T in [25,45]:
  part=sorted([w for w in waves if w['T']==T],key=lambda w:w['start']);early=part[:3];late=part[-3:]
  e=np.mean([w['pack'] for w in early],axis=0);l=np.mean([w['pack'] for w in late],axis=0)
  ei=np.mean([w['current'] for w in early],axis=0);li=np.mean([w['current'] for w in late],axis=0)
  change_end=(np.mean([w['end_pack_V'] for w in late])-np.mean([w['end_pack_V'] for w in early]))*1000
  change_start=(np.mean([w['start_pack_V'] for w in late])-np.mean([w['start_pack_V'] for w in early]))*1000
  result.append(dict(T=T,n_events=len(part),early_dates=[w['start'] for w in early],late_dates=[w['start'] for w in late],early_start_V=float(e[0]),late_start_V=float(l[0]),
   early_end_V=float(np.mean([w['end_pack_V'] for w in early])),late_end_V=float(np.mean([w['end_pack_V'] for w in late])),end_change_pack_mV=float(change_end),start_change_pack_mV=float(change_start),
   additional_drop_pack_mV=float(change_start-change_end),end_change_cell_mean_mV=float(change_end/4),
   mean_abs_current_profile_difference_A=float(np.mean(np.abs(ei-li))),early_mean_T_C=float(np.mean([w['mean_T_C'] for w in early])),late_mean_T_C=float(np.mean([w['mean_T_C'] for w in late])),
   q_span_Ah=[float(min(w['q_Ah'] for w in part)),float(max(w['q_Ah'] for w in part))]))
  overlay.append(dict(T=T,q=qgrid.round(1).tolist(),early_pack=e.round(5).tolist(),late_pack=l.round(5).tolist(),
   early_relative_mV=((e-e[0])*1000).round(3).tolist(),late_relative_mV=((l-l[0])*1000).round(3).tolist()))
 payload=dict(scope='Exploratory raw audit of repeated ~33 Ah dynamic discharges before CK7; no new capacity or calibrated SOC estimate',selection='existing sign-run catalog: long_dynamic_discharge and Q 32.7–33 Ah; current >0.5 A in magnitude; revalidated raw boundaries and integration',
  physical_packs=1,total_events=len(events),temperature_results=result,overlays=overlay)
 (OUT/'wider_discharge_trend.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in payload.items() if k!='overlays'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
