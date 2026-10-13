from common import *
from source_benchmarks import make,families,score

def main():
 f=pd.read_csv(TASK/'P1_features.csv');g=f[f[['f2_1800_Var','f4_1800_Var']].notna().all(axis=1)].reset_index(drop=True);fams=families(g);cols=fams['joint'];tunes=json.loads((TASK/'tuning_P1_main.json').read_text());out=[]
 for x in tunes:
  if x['family']!='joint':continue
  tr=g[g.entity.isin(x['train_entities'])];te=g[g.entity.isin(x['test_entities'])];m=make(x['config']);m.fit(tr[cols],tr.label_Ah/102)
  lo=tr[cols].quantile(.01);hi=tr[cols].quantile(.99);width=(hi-lo).clip(lower=1e-6);valid=te[cols].notna().all(axis=1)&((te[cols]>=lo-.25*width)&(te[cols]<=hi+.25*width)).all(axis=1);p=m.predict(te[cols])*102
  for (idx,row),pr,ok in zip(te.iterrows(),p,valid):out.append(dict(entity=row.entity,event_id=row.event_id,label_Ah=row.label_Ah,pred_Ah=float(pr),nominal_Ah=102,source_feature_support=bool(ok),outside_features=';'.join(c for c in cols if pd.isna(row[c]) or (pd.notna(lo[c]) and not(lo[c]-.25*width[c]<=row[c]<=hi[c]+.25*width[c])))))
 od=pd.DataFrame(out);od.to_csv(TASK/'P1_outer_support.csv',index=False);ret=od[od.source_feature_support];save('P1_outer_support_summary.json',{'coverage_events':float(od.source_feature_support.mean()),'coverage_entity_mean':float(od.groupby('entity').source_feature_support.mean().mean()),'retained_entities':ret.entity.nunique(),'total_entities':od.entity.nunique(),'all_intersection_metrics':score(od,od.pred_Ah.to_numpy()),'retained_metrics':score(ret,ret.pred_Ah.to_numpy()) if len(ret) else None,'gate':'ALL model features finite and outer-training1%-99% interval expanded25%; outlier rejections may be high; unconditional metrics remain primary'})
 # Label inventory per measured capacity, never fabricated target labels.
 labels=[]
 for r in f.itertuples():labels.append(dict(source='P1',physical_entity_id=r.entity,event_id=r.event_id,chemistry='LFP',nominal_Ah=102,label_Ah=r.label_Ah,label_temperature_C=r.label_temperature_C,label_rate_C=r.label_rate_C,label_cutoff='single cell 2.5V',capacity_measurement_time=r.label_time,waveform_charge_end=r.charge_end,pre_available_after=r.pre_available_after,post_available_after=r.post_available_after,pairing_legal=pd.Timestamp(r.label_time)>pd.Timestamp(r.charge_end),charge_rest30_complete=np.isfinite(r.f2_1800_Var),discharge_rest30_complete=np.isfinite(r.f4_1800_Var),previous_exposure=True,label_scope='real single-cell reference discharge; NOT pack label'))
 ck=pd.read_csv(SOURCE/'data/checkups/evaluation_points.csv')
 for r in ck.itertuples():labels.append(dict(source='official',physical_entity_id='one_official_pack',event_id=r.checkup,chemistry='LFP',nominal_Ah=102,label_Ah=100.41 if r.checkup=='CK0' else np.nan,label_temperature_C=np.nan,label_temperature_status='reference_temperature_not_released_or_specified',label_rate_C=.05,label_cutoff='four-cell pack first11.2V',capacity_measurement_time=r.date,waveform_charge_end=None,pre_available_after=None,post_available_after=None,charge_rest30_complete=False,discharge_rest30_complete=False,previous_exposure=True,label_scope='CK0 released; CK1-7 unreleased; CK0 input unpaired'))
 pd.DataFrame(labels).to_csv(TASK/'label_inventory.csv',index=False)
 # Missing-stage report over every candidate and checkpoint, including excluded short/unpaired stages.
 registry=pd.read_csv(TASK/'official_registry.csv');official=pd.read_csv(TASK/'official_features.csv');missing=[]
 for point in ck.itertuples():
  date=pd.Timestamp(point.date).isoformat()
  for r in registry.itertuples():
   for budget in ['pre300','pre900','pre1800','dis_end','post300','post900','post1800']:
    rr=official[(official.event_id==r.event_id)&(official.budget==budget)]
    if len(rr):status='available' if rr.available_after.iat[0]<=date else 'query_truncated';after=rr.available_after.iat[0]
    elif budget.startswith('pre') and not r.charge_paired:status='no_paired_full_charge_in_visible_chain';after=None
    elif budget.startswith('pre') and r.pre_rest_s<int(budget[3:]):status='not_recorded_continuously_to_required_duration';after=None
    elif budget.startswith('post') and r.post_rest_s<int(budget[4:]):status='not_recorded_continuously_to_required_duration';after=None
    else:status='event_not_qualified';after=None
    missing.append(dict(checkup=point.checkup,event_id=r.event_id,type=r.type,budget=budget,status=status,available_after=after))
 pd.DataFrame(missing).to_csv(TASK/'official_missingness_by_checkpoint.csv',index=False)
 dictionary=[]
 for c in sorted(set(f.columns)|set(official.columns)):
  base=c[3:] if c.startswith(tuple(f'c{i}_' for i in range(1,6))) else c
  if base.startswith('f1_'):family='F1';avail='completed CC/CV';definition='visible charge quantity/threshold crossing/CV taper grid fit; no extrapolation'
  elif base.startswith(('f2_','f4_')):
   family='F2' if base.startswith('f2_') else 'F4';avail=('charge' if family=='F2' else 'discharge')+' rest start + '+base.split('_')[1]+' s';definition='continuous rest on fixed time grid; ddof1 variance, sample-std skew/kurt, true extrema, relative end change, tail drift, candidate-tau exponential residual'
  elif base.startswith(('f3_','raw_')):family='F3';avail='early fixed 10/30/60/300s or <=10Ah observed; benchmark budget discharge end';definition='loaded relative V response, apparent30s response divided by preceding current, nominal-C current summaries; raw V/P/I_C grids; not instantaneous resistance'
  elif base.startswith('f5_'):family='F5';avail='max availability of constituent observed channels';definition='four channels within ONE physical group; shared current and temperature, mean/std/range'
  elif base.startswith('A_'):family='A';avail='past completed windows strictly before target';definition='local observed Ah window history; calendar-day log-slope, correlated with F1'
  elif base.startswith('m_'):family='F0';avail='observed metadata cutoff; T prefixes separate';definition='known operating conditions; full-discharge duration/Q excluded'
  else:family='audit_or_label';avail='per-row timestamp';definition='identity, label, availability, quality or audit annotation; not automatically a model input'
  unit='dimensionless'
  if base.endswith('_Var'):unit='V^2'
  elif base.startswith('raw_PI'):unit='ohm; masked apparent polarization/current'
  elif base.startswith('raw_T'):unit='degC, observed shared event temperature'
  elif 'Ah' in base or base.endswith('Qcharge'):unit='Ah'
  elif base.endswith(('_Max','_Min','_Mean','_drop','_exp_amp','_exp_rmse')) or base.startswith(('raw_V','raw_P','f1_V','f3_dV')):unit='V (CV amplitude/RMSE instead normalized C)'
  elif base.endswith(('_s','_seconds')):unit='s'
  elif base.endswith('_drift'):unit='V/s'
  elif base.endswith('Rapp_30'):unit='ohm, apparent30s response'
  elif 'temp' in base.lower() or base in ['m_chamber_T','m_actual_T']:unit='degC'
  elif base.endswith('_days'):unit='days'
  dictionary.append(dict(feature=c,family=family,unit=unit,available_after_rule=avail,definition=definition,failure='missing coverage/gap/zero variance/no threshold crossing recorded as missing or explicit mask; no outside-support extrapolation claimed'))
 pd.DataFrame(dictionary).to_csv(TASK/'feature_dictionary.csv',index=False)
 # Preserve actual historical registered-A official prefixes without carrying B predictions into labels.
 old=SOURCE/'research/phase1_pack_trend_20261011/outputs/official_cell_trends.json';a=json.loads(old.read_text());save('official_registered_A_prefix.json',[{k:r[k] for k in ['checkup','date','eligible_A_cells','cell_trends']} for r in a]);save('official_registered_A_provenance.json',{'path':str(old),'sha256':sha(old),'copied_fields_exclude_B':True,'not_a_capacity_label':True})
 main=pd.read_csv(TASK/'metrics_P1_main.csv').set_index('family');primary=float(main.loc['joint','MAE_Ah']);f0=float(main.loc['F0','MAE_Ah']);single=float(main.loc[['F0_F1_CCCV','F0_F2_rest','F0_F3_dynamic','F0_raw','F0_F4_recovery'],'MAE_Ah'].min());coverage=json.loads((TASK/'P1_coverage.json').read_text())['coverage']
 temperature=pd.read_csv(TASK/'entity_errors_P1_cross_temperature.csv');reference=pd.read_csv(TASK/'entity_errors_P1_main.csv');t=temperature[temperature.family=='joint'][['entity','MAE_Ah']].merge(reference[reference.family=='joint'][['entity','MAE_Ah']],on='entity',suffixes=('_temperature','_cell'));t['relative_worsening']=t.MAE_Ah_temperature/t.MAE_Ah_cell-1;t.to_csv(TASK/'temperature_layer_worsening.csv',index=False)
 save('acceptance.json',{'audits':'PASS','paper_code_and_formula_audit':'PASS','public_paper_capacity_benchmarks':'UNVERIFIED: verified waveform members unavailable due range download timeouts','P1_joint_vs_F0':'PASS' if primary<=.95*f0 else 'FAIL','P1_joint_vs_best_single':'PASS' if primary<=.95*single else 'FAIL','P1_direct_stage_coverage':'PASS' if coverage>=.9 else 'FAIL','improvement_vs_F0':1-primary/f0,'improvement_vs_best_single':1-primary/single,'direct_stage_coverage':coverage,'temperature_layer_gate':'FAIL' if (t.relative_worsening>.1).any() else 'PASS','source_joint_capacity_mainline':'FAIL','official_capacity_transfer_coverage':'FAIL: zero compatible accepted rows; rejection does not establish robustness','four_cell_structure_capacity_increment':'UNVERIFIED: no real group labels','real_group_Qpack_conversion':'UNVERIFIED','replace_current_B':False})
 save('execution_context.json',{'worktree':str(WORK),'source_read_only':str(SOURCE),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=WORK,text=True).strip(),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORK,text=True).strip(),'utc':pd.Timestamp.now(tz='UTC').isoformat(),'subagents_spawned':False})
 (TASK/'.gitignore').write_text('.venv/\n__pycache__/\n')
 print('output inventory and gates saved',flush=True)
if __name__=='__main__':main()
