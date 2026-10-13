"""Real single-cell labels, same-cycle pairing, no discharge label-tail features."""
from common import *
import re
from scipy.integrate import cumulative_trapezoid

def p1():
 rows=[];inventory=[];phases=[]
 for folder in sorted((SOURCE/'dataset original').glob('102Ah*')):
  files=sorted(folder.glob('*.csv'));parts=[pd.read_csv(f,parse_dates=['absolute_time']) for f in files];raw=pd.concat(parts,ignore_index=True)
  name=folder.name;T=int(re.search(r'_(\d+)degC',name).group(1));rate=.5 if '0p5C' in name else 1.
  phases.append(dict(entity=name,source='P1',stages=raw.step_type.value_counts().to_dict(),cycles=raw.cycle_number.nunique()))
  charge_exposure=raw[raw.step_type=='cccv_charge'].groupby('cycle_number').step_capacity_Ah.max()
  origin=raw.absolute_time.min();cycles=sorted(raw.cycle_number.unique());selected=[c for c in cycles if c==cycles[0] or c%25==0 or c==cycles[-1]]
  for c in selected:
   g=raw[raw.cycle_number==c].sort_values('absolute_time',kind='stable')
   charge=g[g.step_type=='cccv_charge'].drop_duplicates('absolute_time',keep='last');dis=g[g.step_type=='cc_discharge'].drop_duplicates('absolute_time',keep='last')
   if len(charge)<15 or len(dis)<15:continue
   # True capacity label = independent observed CC discharge to cutoff.
   if not 2.45<=dis.voltage_V.iat[-1]<=2.55:continue
   end=charge.absolute_time.max();dstart=dis.absolute_time.min();dend=dis.absolute_time.max()
   before=g[(g.step_type=='rest')&(g.absolute_time>=end)&(g.absolute_time<=dstart)].drop_duplicates('absolute_time',keep='last')
   after=g[(g.step_type=='rest')&(g.absolute_time>=dend)].drop_duplicates('absolute_time',keep='last')
   t=ns(charge.absolute_time);t-=t[0];dt=ns(dis.absolute_time);dt-=dt[0]
   cq=charge.step_capacity_Ah.to_numpy(float);dq=dis.step_capacity_Ah.to_numpy(float)
   pt=(ns(before.absolute_time)-ns(pd.Series([end]))[0]) if len(before) else np.array([])
   at=(ns(after.absolute_time)-ns(pd.Series([dend]))[0]) if len(after) else np.array([])
   r=dict(source='P1',entity=name,event_id=f'{name}_{c}',cycle=int(c),nominal_Ah=102,label_Ah=float(dis.step_capacity_Ah.max()),
    chemistry='LFP',label_rate_C=rate,label_cutoff_V=2.5,label_temperature_C=T,
    charge_end=end.isoformat(),label_time=dend.isoformat(),pre_available_after=dstart.isoformat(),post_available_after=after.absolute_time.max().isoformat() if len(after) else None,
    m_cumulative_charge_Ah=float(charge_exposure[charge_exposure.index<c].sum()+cq.max()),m_age_days=float((end-origin).total_seconds()/86400),m_chamber_T=T,m_actual_T=float(before.temperature_C.mean()) if len(before) else float(charge.temperature_C.iat[-1]),m_charge_C=rate,
    m_charge_duration_s=float(t[-1]),m_charge_start_V=float(charge.voltage_V.iat[0]),m_charge_end_V=float(charge.voltage_V.iat[-1]),m_pre_rest_s=float(pt.max()) if len(pt) else 0,
    m_post_rest_s=float(at.max()) if len(at) else 0,exposure='Six previously exposed single-cell lifecycles; new features, not new blind entities')
   for duration in [300,900,1800]:
    visible=before[pt<=duration] if len(before) else before
    r[f'm_actual_T{duration}']=float(visible.temperature_C.mean()) if len(visible) else float(charge.temperature_C.iat[-1])
   r.update(charge_features(t,charge.voltage_V.to_numpy(),charge.current_A.to_numpy(),cq,102))
   if len(before)>=3:r.update(stage_features(pt,before.voltage_V.to_numpy(),'f2'))
   if len(after)>=3:r.update(stage_features(at,after.voltage_V.to_numpy(),'f4'))
   r.update(discharge_features(dt,dis.voltage_V.to_numpy(),-dis.current_A.to_numpy(),dq,102,temperature=dis.temperature_C.to_numpy()))
   # A signal from separate past charge windows, not from this target's future.
   rows.append(r)
  inventory.append(dict(source='P1',entity=name,chemistry='LFP',nominal_Ah=102,label_protocol=f'{rate}C discharge to 2.5V, chamber {T}C',paired_stages='CCCV, charge-rest, discharge-prefix, discharge-rest',full_discharge_tail_as_feature=False,previously_exposed=True,path=str(folder)))
  print('P1',name,'rows',sum(r['entity']==name for r in rows),flush=True)
 f=pd.DataFrame(rows).sort_values(['entity','cycle'])
 for entity,g in f.groupby('entity'):
  # Local Ah windows alone; no known capacity denominator.
  x=g.f1_dAh_3_35_3_4.to_numpy() if 'f1_dAh_3_35_3_4' in g else g.get('f1_dAh_3.35_3.4',pd.Series(np.nan,index=g.index)).to_numpy()
  past=[]
  for k,(idx,row) in enumerate(g.iterrows()):
   history=g.iloc[:k];history=history[history.m_age_days<row.m_age_days].tail(5)
   good=history[['m_age_days','f1_dAh_3.35_3.4']].dropna() if 'f1_dAh_3.35_3.4' in history else history.iloc[0:0]
   if len(good)>=3 and np.ptp(good.m_age_days)>0:
    slope=np.polyfit(good.m_age_days,np.log(good['f1_dAh_3.35_3.4']),1)[0];f.loc[idx,'A_past_log_window_slope']=slope
 f.to_csv(TASK/'P1_features.csv',index=False)
 save('P1_stage_inventory.json',phases)
 pd.DataFrame(inventory).to_csv(TASK/'label_inventory_P1.csv',index=False)

def zhu():
 rows=[]
 for file in sorted((TASK/'public_data').glob('CY*.csv')):
  raw=pd.read_csv(file);print('Zhu columns',file.name,raw.columns.tolist()[:15],flush=True)
  # BioLogic files use recorded elapsed time, preserve physical filename IDs.
  timecol=next((c for c in raw.columns if c.lower() in ['time/s','time/s.1','time']),None)
  if timecol is None:raise RuntimeError('No validated time column '+file.name)
  T=int(file.name[2:4]);entity='Zhu_NCA_'+file.stem
  cycles=sorted(raw['cycle number'].unique());selected=[c for c in cycles if c%10==0 or c==cycles[0] or c==cycles[-1]]
  for c in selected:
   g=raw[raw['cycle number']==c].sort_values(timecol);v=g['Ecell/V'].to_numpy();I=g['<I>/mA'].to_numpy()/1000;t=g[timecol].to_numpy(float)
   control=g['control/V/mA'].to_numpy();zero=np.flatnonzero((abs(control)<1e-8)&(v>4))
   if len(zero)<3:continue
   blocks=np.split(zero,np.flatnonzero(np.diff(zero)>1)+1);rest=max(blocks,key=len)
   # Require a charge before this exact rest and discharge after it in same cycle.
   if rest[0]==0 or np.max(I[:rest[0]])<=0 or not np.any(I[rest[-1]+1:]<0):continue
   rt=t[rest]-t[rest[0]];r=dict(source='Zhu_NCA',entity=entity,event_id=f'{entity}_{c}',cycle=int(c),nominal_Ah=3.5,label_Ah=float(g['Q discharge/mA.h'].max()/1000),chemistry='NCA',
    m_age_days=float((t[rest[0]]-raw[timecol].min())/86400),m_chamber_T=T,m_actual_T=T,m_charge_C=float(g['control/mA'].iloc[1]/3500),m_charge_duration_s=float(t[rest[0]]-t[0]),m_charge_start_V=float(v[0]),m_charge_end_V=float(v[rest[0]]),m_pre_rest_s=float(rt[-1]),
    pre_available_after=float(t[rest[-1]]),label_time=float(t[-1]),paper_capacity_filter=bool(2.5<=g['Q discharge/mA.h'].max()/1000<=3.5))
   r.update(stage_features(rt,v[rest],'f2',dt=120,max_gap=180))
   charge=np.flatnonzero(I[:rest[0]]>0)
   if len(charge)>5:
    qq=g['Q charge/mA.h'].to_numpy()[charge]/1000;r.update(charge_features(t[charge]-t[charge[0]],v[charge],I[charge],qq,3.5))
   rows.append(r)
  print('Zhu extracted',entity,sum(r['entity']==entity for r in rows),flush=True)
 pd.DataFrame(rows).to_csv(TASK/'Zhu_features.csv',index=False)

if __name__=='__main__':p1();zhu()
