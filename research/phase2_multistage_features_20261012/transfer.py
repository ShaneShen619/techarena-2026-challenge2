from common import *
from source_benchmarks import make,METADATA,families,tune
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error
import joblib

def main():
 source=pd.read_csv(TASK/'P1_features.csv');source=source[source[['f2_1800_Var','f4_1800_Var']].notna().all(axis=1)].reset_index(drop=True);models={};provenance=[]
 for budget in ['pre300','pre900','pre1800','dis_end','post300','post900','post1800']:
  duration=int(budget[3:]) if budget.startswith('pre') else int(budget[4:]) if budget.startswith('post') else 1800
  kind='pre' if budget.startswith('pre') else 'post' if budget.startswith('post') else 'dis';training=source.copy()
  if kind=='pre':training.m_actual_T=training[f'm_actual_T{duration}']
  cols=families(training,duration,kind)['joint'];cfg,_=tune(training,cols);model=make(cfg);model.fit(training[cols],training.label_Ah/102)
  support={c:{'low':float(training[c].quantile(.01)),'high':float(training[c].quantile(.99))} for c in cols if training[c].notna().any()}
  models[budget]={'model':model,'features':cols,'support':support,'config':cfg,'duration':duration,'kind':kind}
  provenance.append({'budget':budget,'features':cols,'config':cfg,'entities':sorted(training.entity.unique()),'rows':len(training),'official_rows_used':0})
 joblib.dump(models,TASK/'source_budget_models.joblib');save('source_budget_models_provenance.json',provenance)
 f=pd.read_csv(TASK/'official_features.csv');rows=[]
 # Conversion is deliberately absent: single-cell source label is not official group reference capacity.
 for _,row in f.iterrows():
  bundle=models[row.budget];cols=bundle['features'];support=bundle['support'];duration=bundle['duration'];kind=bundle['kind']
  for c in range(1,6):
   x={k:(row.get(k,np.nan) if k.startswith('m_') else row.get(f'c{c}_{k}',np.nan)) for k in cols}
   if c<5:
    x['m_charge_start_V']=row.get(f'quality_cell{c}_charge_start_V',np.nan);x['m_charge_end_V']=row.get(f'quality_cell{c}_charge_end_V',np.nan)
   reasons=['coupled_pack_CV_control_does_not_match_independent_source_cell_CV_control','source_rest_grid30s_vs_native_official10s_not_harmonized'];mandatory=['m_charge_end_V','m_charge_C','f1_Qcharge',f'f2_{duration if kind=="pre" else 1800}_Var']
   if kind=='post':mandatory.append(f'f4_{duration}_Var')
   if kind!='pre':mandatory.append('f3_dV_t30')
   if not all(np.isfinite(x.get(k,np.nan)) for k in mandatory):reasons.append('required_stage_missing_or_not_yet_available')
   for k in cols:
    if k not in support or not np.isfinite(x[k]):continue
    lo,hi=support[k]['low'],support[k]['high'];width=max(hi-lo,1e-6)
    if x[k]<lo-.25*width or x[k]>hi+.25*width:reasons.append('outside_source_support:'+k)
   # Recorded measurement/control incompatibilities are physical, not fitted threshold decisions.
   reasons.append('label_protocol_mismatch_P1_single_cell_0.5_or_1C_2.5V_vs_pack_C20_11.2V')
   mapped='single_cell' if c<5 else 'pack_voltage_div4_is_not_a_physical_cell'
   accepted=not reasons
   prediction=float(bundle['model'].predict(pd.DataFrame([x]))[0]*102) if accepted else None
   rows.append(dict(event_id=row.event_id,budget=row.budget,available_after=row.available_after,channel=f'cell{c}' if c<5 else 'pack_div4',input_scope=mapped,feature_support_pass=not any('support' in z or 'missing' in z for z in reasons),capacity_transfer_accepted=accepted,conditional_single_cell_Ah=prediction,Qpack_Ah=None,SOH_percent=None,status='UNVERIFIED',reasons=';'.join(reasons)))
 out=pd.DataFrame(rows);out.to_csv(TASK/'official_support_by_event.csv',index=False)
 ck=[]
 for point in pd.read_csv(SOURCE/'data/checkups/evaluation_points.csv').itertuples():
  p=f[f.available_after<=pd.Timestamp(point.date).isoformat()];po=out[out.available_after<=pd.Timestamp(point.date).isoformat()]
  perbudget=[]
  for budget,g in p.groupby('budget'):
   latest=g.sort_values('available_after').iloc[-1];perbudget.append(dict(budget=budget,latest_event=latest.event_id,available_after=latest.available_after,feature_rows=len(g)))
  ck.append(dict(checkup=point.checkup,date=point.date,available_events=int(p.event_id.nunique()),available_rows=len(p),feature_only_supported_rows=int(po.feature_support_pass.sum()),capacity_accepted_rows=int(po.capacity_transfer_accepted.sum()),capacity_accept_coverage=float(po.capacity_transfer_accepted.mean()) if len(po) else None,paired_CK0=False,Qpack_Ah=None,SOH_percent=None,real_error_Ah=None,status='UNVERIFIED',latest_by_budget=perbudget))
 save('official_checkpoint_support.json',ck)
 # Causal auxiliary task. Past COMPLETED event -> next event dV30, never capacity.
 complete=f[(f.type=='standard')&(f.budget=='post1800')].sort_values('available_after');pairs=[]
 for i in range(len(complete)-1):
  prev=complete.iloc[i];nxt=complete.iloc[i+1]
  if prev.available_after>=nxt.event_start:continue
  p=prev.to_dict();p['target_event']=nxt.event_id;p['target_start']=nxt.event_start;p['target_dV30']=nxt.c5_f3_dV_t30;p['target_temperature']=nxt.m_chamber_T
  pairs.append(p)
 p=pd.DataFrame(pairs).dropna(subset=['target_dV30']);cut=int(.6*len(p));tr=p.iloc[:cut];te=p.iloc[cut:]
 core=[c for c in METADATA if c in p.columns];stage=[c for c in p.columns if c.startswith('c5_') and c.split('_')[1] in ['f1','f2','f3','f4']];structure=[c for c in p.columns if c.startswith('f5_')]
 results=[];metrics=[]
 for name,features in [('metadata',core),('metadata_stages',core+stage),('metadata_stages_structure',core+stage+structure)]:
  # Tune ONLY chronological subfolds in training; avoid future data normalization.
  alphas=[1,10];loss=[]
  innercut=max(3,int(.6*len(tr)))
  for alpha in alphas:
   m=make({'kind':'Ridge','alpha':alpha});m.fit(tr.iloc[:innercut][features],tr.target_dV30.iloc[:innercut]);pr=m.predict(tr.iloc[innercut:][features]);loss.append(float(mean_absolute_error(tr.target_dV30.iloc[innercut:],pr)))
  alpha=alphas[int(np.argmin(loss))];m=make({'kind':'Ridge','alpha':alpha});m.fit(tr[features],tr.target_dV30);pred=m.predict(te[features]);error=abs(pred-te.target_dV30.to_numpy())*1000
  metrics.append(dict(family=name,train_events=len(tr),test_events=len(te),MAE_mV=float(error.mean()),worst_mV=float(error.max()),selected_alpha=alpha,target='NEXT standard event pack-average dV30, not capacity'))
  for (_,row),pr,e in zip(te.iterrows(),pred,error):results.append(dict(family=name,input_event=row.event_id,features_available_after=row.available_after,target_event=row.target_event,target_start=row.target_start,pred_V=float(pr),true_V=float(row.target_dV30),abs_error_mV=float(e),target_temperature=row.target_temperature))
 pd.DataFrame(metrics).to_csv(TASK/'official_auxiliary_metrics.csv',index=False);pd.DataFrame(results).to_csv(TASK/'official_auxiliary_predictions.csv',index=False)
 save('official_auxiliary_split.json',{'train_input_events':tr.event_id.tolist(),'test_input_events':te.event_id.tolist(),'training_fraction':.6,'target_is_capacity':False,'past_stages_only':True})
 # Visible matched conditions and repeated-temperature trajectories; no fixed-capacity claim.
 f.to_csv(TASK/'official_prefix_feature_trajectories.csv',index=False)
 summary=f[(f.type=='standard')&(f.budget=='post1800')].groupby('m_chamber_T').agg(events=('event_id','size'),median_rest_Max=('c5_f2_1800_Max','median'),std_rest_Max=('c5_f2_1800_Max','std'),median_dV30=('c5_f3_dV_t30','median'),std_dV30=('c5_f3_dV_t30','std'),median_cell_spread=('f5_f3_dV_t30_range','median'))
 summary.to_csv(TASK/'official_temperature_summary.csv')
if __name__=='__main__':main()
