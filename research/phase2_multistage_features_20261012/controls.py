from source_benchmarks import *
import joblib

def main():
 f=pd.read_csv(TASK/'P1_features.csv');f=f[f[['f2_1800_Var','f4_1800_Var']].notna().all(axis=1)].reset_index(drop=True);cols=families(f)['joint'];rng=np.random.default_rng(42);records=[];negative=[]
 for fold,(tr,te) in enumerate(LeaveOneGroupOut().split(f,groups=f.entity)):
  train=f.iloc[tr].copy();test=f.iloc[te].copy();cfg,_=tune(train,cols);m=make(cfg);m.fit(train[cols],train.label_Ah/train.nominal_Ah)
  variants={'unchanged':test.copy()}
  for shift in [-.005,.005]:
   h=test.copy()
   for c in cols:
    if c.startswith('raw_V_') or c.startswith('f1_V_') or c.endswith(('_Max','_Min','_Mean')) or c in ['m_charge_start_V','m_charge_end_V']:h[c]+=shift
   # Ah-crossing windows cannot be shifted exactly without raw re-extraction; not perturbed here.
   variants[f'absolute_voltage_shift_{shift}']=h
  h=test.copy()
  for c in cols:
   if c.startswith('raw_V_') or c.startswith('f1_V_') or c.endswith(('_Max','_Min','_Mean')):h[c]=np.round(h[c]*1000)/1000
  variants['1mV_summary_quantization']=h
  h=test.copy()
  for c in cols:
   if c.startswith('raw_V_') or c.startswith('f1_V_') or c.endswith(('_Max','_Min','_Mean')):h[c]+=rng.normal(0,.001,len(h))
  variants['1mV_summary_noise']=h
  for stage in ['f1_','f2_','f3_','f4_']:
   h=test.copy();h[[c for c in cols if c.startswith(stage)]]=np.nan;variants['missing_'+stage]=h
  base=m.predict(test[cols])*test.nominal_Ah
  for name,h in variants.items():
   p=m.predict(h[cols])*h.nominal_Ah
   for k,(idx,row) in enumerate(test.iterrows()):records.append(dict(variant=name,entity=row.entity,event_id=row.event_id,label_Ah=row.label_Ah,pred_Ah=float(p.iloc[k] if hasattr(p,'iloc') else p[k]),delta_Ah=float((p-base).iloc[k] if hasattr(p,'iloc') else (p-base)[k]),nominal_Ah=102))
  # Matched shuffle of shape/charge signal within physical cell and age quartile, not target-capacity bins.
  def shuffled(frame,labels=False):
   h=frame.copy();signal=[c for c in cols if c.startswith(('f1_','f2_','f3_','f4_','raw_'))]
   for _,g in h.groupby('entity'):
    b=pd.qcut(g.m_age_days,4,labels=False,duplicates='drop')
    for _,gg in g.groupby(b):
     ix=gg.index.to_numpy();per=rng.permutation(ix)
     if labels:h.loc[ix,'label_Ah']=h.loc[per,'label_Ah'].to_numpy()
     else:h.loc[ix,signal]=h.loc[per,signal].to_numpy()
   return h
  for name,tr2,te2 in [('label_shuffle_age_quartile',shuffled(train,True),test),('shape_shuffle_age_quartile',shuffled(train),shuffled(test))]:
   cm=make(cfg);cm.fit(tr2[cols],tr2.label_Ah/tr2.nominal_Ah);p=cm.predict(te2[cols])*te2.nominal_Ah
   for (_,row),pred in zip(te2.iterrows(),p):negative.append(dict(variant=name,entity=row.entity,event_id=row.event_id,label_Ah=row.label_Ah,pred_Ah=float(pred),nominal_Ah=102))
  print('controls fold',fold,flush=True)
 r=pd.DataFrame(records);r.to_csv(TASK/'robustness_predictions.csv',index=False)
 summary=[]
 for name,g in r.groupby('variant'):summary.append(dict(variant=name,**score(g,g.pred_Ah.to_numpy()),mean_abs_prediction_change_Ah=float(abs(g.delta_Ah).groupby(g.entity).mean().mean()),max_change_Ah=float(abs(g.delta_Ah).max())))
 pd.DataFrame(summary).to_csv(TASK/'robustness_metrics.csv',index=False)
 r=pd.DataFrame(negative);r.to_csv(TASK/'negative_control_predictions.csv',index=False)
 pd.DataFrame([dict(variant=name,**score(g,g.pred_Ah.to_numpy())) for name,g in r.groupby('variant')]).to_csv(TASK/'negative_control_metrics.csv',index=False)
 # A is a correlated direction/quality signal. No automatic adjustment.
 p=pd.read_csv(TASK/'predictions_P1_main.csv');p=p[p.family=='joint'].merge(f[['event_id','m_age_days','A_past_log_window_slope']],on='event_id').sort_values(['entity','m_age_days'])
 p['past_pred_slope']=p.groupby('entity').pred_Ah.diff()/p.groupby('entity').m_age_days.diff();p['A_direction_conflict']=(p.past_pred_slope*p.A_past_log_window_slope<0).where(p.A_past_log_window_slope.notna())
 p.to_csv(TASK/'A_conflict_flags.csv',index=False)
 # Independent analytic fixed-Q stress: RC relaxation, no parameters learned from the four-cell reference model.
 sr=[];time=np.arange(0,1801,10);Q=102
 for T in [25,45]:
  for soc in [.7,.9,1.]:
   for current in [10,20,40]:
    for offset in [-.005,0,.005]:
     equilibrium=3.32+.07*soc+.0002*(T-25)+offset;amp=.08*(current/20)*np.exp(-(T-25)/50);tau=300*np.exp(-(T-25)/60)
     vv=equilibrium+amp*np.exp(-time/tau);r=stats(vv);sr.append(dict(true_capacity_Ah=Q,T=T,SOC=soc,preceding_current_A=current,sensor_offset_V=offset,**r,drop_V=float(vv[-1]-vv[0])))
 pd.DataFrame(sr).to_csv(TASK/'constant_capacity_independent_RC_stress.csv',index=False)
 # Same real continuous rest sampled at10s vs30s from official waveforms, fixed geometry.
 of=pd.read_csv(TASK/'official_features.csv');rr=[]
 for row in of[of.budget=='pre1800'].itertuples():
  # The grid statistics can be checked on raw source indices in audit.py; this summary uses only observed features.
  rr.append(dict(event_id=row.event_id,available_after=row.available_after,Var10s=row.c5_f2_1800_Var,Max10s=row.c5_f2_1800_Max))
 pd.DataFrame(rr).to_csv(TASK/'official_full_rest_feature_index.csv',index=False)
if __name__=='__main__':main()
