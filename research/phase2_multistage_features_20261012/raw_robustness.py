"""Raw waveform perturbation on metadata-selected held-cell representative events."""
from source_benchmarks import *

def main():
 f=pd.read_csv(TASK/'P1_features.csv');g=f[f[['f2_1800_Var','f4_1800_Var']].notna().all(axis=1)].reset_index(drop=True);cols=families(g)['joint'];tunes=json.loads((TASK/'tuning_P1_main.json').read_text());out=[];rng=np.random.default_rng(42)
 for entity,gg in g.groupby('entity'):
  row=gg.sort_values('cycle').iloc[len(gg)//2];train=g[g.entity!=entity];cfg=next(x['config'] for x in tunes if x['family']=='joint' and x['test_entities']==[entity]);m=make(cfg);m.fit(train[cols],train.label_Ah/102)
  raw=pd.concat([pd.read_csv(p,parse_dates=['absolute_time']) for p in sorted((SOURCE/'dataset original'/entity).glob('*.csv'))],ignore_index=True);raw=raw[raw.cycle_number==row.cycle].sort_values('absolute_time',kind='stable')
  charge=raw[raw.step_type=='cccv_charge'].drop_duplicates('absolute_time',keep='last');dis=raw[raw.step_type=='cc_discharge'].drop_duplicates('absolute_time',keep='last');before=raw[(raw.step_type=='rest')&(raw.absolute_time>=charge.absolute_time.max())&(raw.absolute_time<=dis.absolute_time.min())].drop_duplicates('absolute_time',keep='last');after=raw[(raw.step_type=='rest')&(raw.absolute_time>=dis.absolute_time.max())].drop_duplicates('absolute_time',keep='last')
  cv=charge.voltage_V.to_numpy();dv=dis.voltage_V.to_numpy();pv=before.voltage_V.to_numpy();av=after.voltage_V.to_numpy();ct=ns(charge.absolute_time);ct-=ct[0];dt=ns(dis.absolute_time);dt-=dt[0];pt=ns(before.absolute_time)-ns(pd.Series([charge.absolute_time.max()]))[0];at=ns(after.absolute_time)-ns(pd.Series([dis.absolute_time.max()]))[0]
  variants=['unchanged','offset_minus5mV','offset_plus5mV','quantization1mV','noise1mV','rest_sample60s']
  base=None
  for name in variants:
   arrays=[x.copy() for x in [cv,pv,dv,av]]
   if name.startswith('offset'):
    shift=-.005 if 'minus' in name else .005;arrays=[x+shift for x in arrays]
   elif name=='quantization1mV':arrays=[np.round(x*1000)/1000 for x in arrays]
   elif name=='noise1mV':arrays=[x+rng.normal(0,.001,len(x)) for x in arrays]
   r=row.to_dict();r['m_charge_start_V']=float(arrays[0][0]);r['m_charge_end_V']=float(arrays[0][-1]);r.update(charge_features(ct,arrays[0],charge.current_A.to_numpy(),charge.step_capacity_Ah.to_numpy(),102))
   step=60 if name=='rest_sample60s' else 30
   r.update(stage_features(pt,arrays[1],'f2',step,45));r.update(stage_features(at,arrays[3],'f4',step,45));r.update(discharge_features(dt,arrays[2],-dis.current_A.to_numpy(),dis.step_capacity_Ah.to_numpy(),102))
   p=float(m.predict(pd.DataFrame([r])[cols])[0]*102)
   if base is None:base=p
   out.append(dict(entity=entity,event_id=row.event_id,cycle=int(row.cycle),variant=name,label_Ah=float(row.label_Ah),pred_Ah=p,prediction_change_Ah=p-base,abs_error_Ah=abs(p-row.label_Ah),selection='median cycle within predeclared complete-chain panel, no target-value selection'))
  print('raw robustness',entity,flush=True)
 r=pd.DataFrame(out);r.to_csv(TASK/'raw_waveform_robustness.csv',index=False)
 save('raw_waveform_robustness_summary.json',{name:{'mean_abs_change_Ah':float(abs(gg.prediction_change_Ah).mean()),'max_abs_change_Ah':float(abs(gg.prediction_change_Ah).max()),'entities':len(gg)} for name,gg in r.groupby('variant')})
if __name__=='__main__':main()
