"""Exact historical A nine windows/threshold crossing and matching; no prior B labels."""
from source_benchmarks import *
import importlib.util,sys
from dataclasses import replace

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
 ec=module('route3_legacy_event',SOURCE/'research/phase1_transfer_ab/src/event_core.py');trend=module('route3_legacy_trend',SOURCE/'research/phase1_pack_trend_20261011/src/trend.py');obs=module('route3_legacy_observation',SOURCE/'research/phase1_transfer_ab/src/observation_a.py')
 windows=json.loads((SOURCE/'research/phase1_transfer_ab/configs/experiment.json').read_text())['a_windows_V'];f=pd.read_csv(TASK/'P1_features.csv');rows=[]
 for entity,g in f.groupby('entity'):
  folder=SOURCE/'dataset original'/entity;raw=pd.concat([pd.read_csv(p,parse_dates=['absolute_time']).assign(source_part=i) for i,p in enumerate(sorted(folder.glob('*.csv')))],ignore_index=True)
  for row in g.itertuples():
   gg=raw[(raw.cycle_number==row.cycle)&(raw.absolute_time<=pd.Timestamp(row.charge_end))].copy();gg['segment']=gg.source_part
   events=ec.extract_charge_events(gg,time_col='absolute_time',voltage_cols=('voltage_V',),temp_col='temperature_C',segment_col='segment',counter_col=None,min_current=5)
   # Finished stable positive run before charge ends; choose by temporal CC run length, never label capacity.
   r=dict(entity=entity,event_id=row.event_id,cycle=int(row.cycle),fragment_end=row.charge_end,temperature_C=np.nan,current_A=np.nan)
   if events:
    event=max(events,key=lambda e:e.duration_s)
    cross=np.flatnonzero((event.voltages[:-1,0]<3.50)&(event.voltages[1:,0]>=3.50))
    if len(cross):
     stop=int(cross[0]+1);qq=event.q_ah[:stop+1];vv=event.voltages[:stop+1];tt=event.times_s[:stop+1]
     mask=qq>=qq[-1]-20;qq=qq[mask];vv=vv[mask];tt=tt[mask]
     current=np.interp(tt,ns(gg.absolute_time),gg.current_A);temperature=np.interp(tt,ns(gg.absolute_time),gg.temperature_C)
     if len(qq)>=10 and event.q_ah[stop]>=20 and np.std(current)/np.mean(current)<=.08:
      crop=replace(event,q_ah=qq-qq[0],voltages=vv,times_s=tt,counter_q_ah=None)
      r.update(fragment_end=pd.Timestamp(tt[-1],unit='s').isoformat(),temperature_C=float(np.median(temperature)),current_A=float(np.median(current)))
      for j,(lo,hi) in enumerate(windows):r[f'w{j:02d}_Ah']=ec.partial_ah(crop,0,lo,hi)
    for j in range(9):r.setdefault(f'w{j:02d}_Ah',np.nan)
   else:
    for j in range(9):r[f'w{j:02d}_Ah']=np.nan
   rows.append(r)
  print('registered A',entity,flush=True)
 fragments=pd.DataFrame(rows);features=[]
 for entity,g in f.groupby('entity'):
  history=fragments[fragments.entity==entity].sort_values('fragment_end')
  for row in g.itertuples():
   past=history[(pd.to_datetime(history.fragment_end)<pd.Timestamp(row.charge_end))&(history.event_id!=row.event_id)&(history.cycle<row.cycle)].tail(5)
   a=trend.summarize_trend(past,row.charge_end);b=obs.summarize(past)
   out={'event_id':row.event_id,'A_history_max_time':past.fragment_end.max() if len(past) else None}
   for key,val in a.items():
    if key.startswith(('slope','median_slope')) or key in ['valid_windows','matched_events','eligible']:out['A_registered_'+key]=val
   for key,val in b.items():
    if key.startswith('logratio'):out['A_registered_'+key]=val
   current=history[history.event_id==row.event_id].iloc[0]
   for j in range(9):out[f'A_registered_current_w{j:02d}_Ah']=current[f'w{j:02d}_Ah']
   features.append(out)
 af=pd.DataFrame(features);af.to_csv(TASK/'A_registered_features.csv',index=False);fragments.to_csv(TASK/'A_registered_fragments.csv',index=False)
 g=f.merge(af,on='event_id');g=g[g[['f2_1800_Var','f4_1800_Var']].notna().all(axis=1)].reset_index(drop=True)
 a=[c for c in g if c.startswith('A_registered_') and c!='A_registered_eligible'];joint=families(g)['joint'];f0=families(g)['F0']
 # Original A positive rate means declining window; normalized sign for existing residual code.
 g['A_past_log_window_slope']=-g.A_registered_median_slope_per_day
 run(g,{'A_original_windows':[c for c in a if 'current_w' in c],'A_original_history':a,'F0_A_original':f0+a,'joint':joint+a},'P1_registered_A',do_A=True)
 save('A_registered_provenance.json',{'original_windows':windows,'original_code_sha256':{str(p):sha(p) for p in [SOURCE/'research/phase1_transfer_ab/src/event_core.py',SOURCE/'research/phase1_pack_trend_20261011/src/trend.py',SOURCE/'research/phase1_transfer_ab/src/observation_a.py']},'history_limit':5,'source_events':'new fixed cycle25 panel; original20Ah crop ending at first3.50V upward crossing, stable-current CV<.08, original9 windows/median3/interpolated q crossings; not original older panel','rate_sign':'original positive means local Ah window shrinking; negated for residual covariate','coverage_events':int(g.A_registered_median_slope_per_day.notna().sum()),'all_events':len(g),'no_B_labels':True,'scope':'supplemental original-A algorithm check requested after non-A baseline, no performance-based window selection'})
if __name__=='__main__':main()
