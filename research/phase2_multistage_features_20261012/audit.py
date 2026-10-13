from common import *
from public_benchmarks import stable_PI
from source_benchmarks import families,score,make
from scipy.integrate import cumulative_trapezoid
from xgboost import XGBRegressor
import platform,sys,importlib.metadata

def main():
 checks=[]
 def ck(name,ok,detail=''):checks.append(dict(check=name,pass_=bool(ok),detail=detail))
 v=np.array([3.6,3.5,3.45,3.42]);s=stats(v);mean=sum(v)/len(v);var=sum((v-mean)**2)/(len(v)-1)
 ck('Zhu_sample_variance',np.isclose(s['Var'],var));ck('Zhu_skew_sample_std_population_numerator',np.isclose(s['Ske'],sum(((v-mean)/np.sqrt(var))**3)/len(v)));ck('Zhu_excess_kurtosis',np.isclose(s['Kur'],sum(((v-mean)/np.sqrt(var))**4)/len(v)-3));ck('zero_variance_defined_and_masked',stats(np.repeat(3.5,20))['zero_var']==1)
 a,m=stable_PI(np.array([.1,.2]),np.array([0.,2.]));ck('zero_current_PI_mask',a[0]==0 and m[0]==1 and a[1]==.1 and np.isfinite(a).all())
 pulse=discharge_features(np.array([0,30,60,120,300]),np.array([3.4,3.38,3.37,3.36,3.35]),np.repeat(20.,5),np.array([0,.166,.333,.666,1.666]),102,temperature=np.repeat(25.,5))
 ck('raw_current_preserves_actual_discharge_sign',np.isclose(pulse['raw_I_C_30']*102,-20.))
 ck('raw_PI_defined_from_actual_current',np.isclose(pulse['raw_PI_30'],.001) and pulse['raw_zeroI_30']==0.)
 ck('raw_T_observed_grid',pulse['raw_T_30']==25.)
 ck('missing_grid_not_extrapolated',grid([0,10,20],[1,2,3],300,10,20) is None);ck('large_gap_rejected',grid([0,10,200,300],[1,2,3,4],300,10,20) is None)
 t=np.arange(0,1801,10);v=3.3+.1*np.exp(-t/300);a=stage_features(t[t<=300],v[t<=300],'f2',10,20);b=stage_features(t,np.where(t>300,99,v),'f2',10,20)
 ck('300s_prefix_future_voltage_invariance',all(np.isclose(a[k],b[k],equal_nan=True) for k in a if k.startswith('f2_300')))
 ck('unobserved_900_1800_missing',not np.isfinite(a['f2_900_Var']) and not np.isfinite(a['f2_1800_Var']))
 dt=ns(pd.Series(pd.to_datetime(['2025-01-01','2025-01-01 00:00:10'],format='mixed')));ck('datetime_unit_seconds',dt[1]-dt[0]==10)
 f=pd.read_csv(TASK/'P1_features.csv');features=families(f)['joint'];forbidden=['label_Ah','cycle','entity','label_time','m_post_rest_s','m_pre_rest_s']
 pairing=pd.read_csv(TASK/'P1_pairing_audit.csv');legal_ids=set(pairing[pairing.pairing_legal].event_id)
 scored=pd.read_csv(TASK/'predictions_P1_all_fallback.csv')
 ck('all_scored_capacity_labels_follow_charge',set(scored.event_id)<=legal_ids,f'{len(legal_ids)}/{len(pairing)} raw pairs legal')
 fs=json.loads((TASK/'P1_forward_split.json').read_text());ix=f.set_index('event_id');forward_ok=True
 for entity in f.entity.unique():
  tr=ix.loc[[e for e in fs['train_events'] if ix.loc[e,'entity']==entity]];te=ix.loc[[e for e in fs['test_events'] if ix.loc[e,'entity']==entity]]
  forward_ok &= bool(tr.cycle.max()<te.cycle.min() and pd.to_datetime(tr.label_time).max()<pd.to_datetime(te.charge_end).min())
 ck('forward_labels_before_future_inputs_and_physical_cycles',forward_ok)
 ck('capacity_tail_not_in_model',not any(c in features for c in forbidden));ck('known_nominal_current_denominator',all('true' not in c and 'label' not in c for c in features))
 tunes=json.loads((TASK/'tuning_P1_main.json').read_text());ck('outer_physical_entity_disjoint',all(not(set(x['train_entities'])&set(x['test_entities'])) for x in tunes));ck('candidate_budget_8_plus_2_aux_under12',len(json.loads((TASK/'protocol.json').read_text())['project_configs'])+2<=12)
 pf=json.loads((TASK/'protocol_freeze.json').read_text());ck('protocol_unmodified_after_freeze',sha(TASK/'protocol.json')==pf['protocol_sha256'])
 official=pd.read_csv(TASK/'official_features.csv');prefix=json.loads((TASK/'official_prefix_availability.json').read_text());ck('CK0_no_paired_feature',prefix[0]['available_feature_rows']==0)
 ck('pre_rest_excludes_discharge_features',official[official.budget.str.startswith('pre')].filter(regex='c[1-5]_f3_').isna().all().all())
 ck('pre_rest_excludes_post_rest',official[official.budget.str.startswith('pre')].filter(regex='c[1-5]_f4_').isna().all().all())
 ck('pre300_no_full_future_rest',official[official.budget=='pre300'].filter(regex='c[1-5]_f2_1800').isna().all().all())
 ck('feature_available_after_charge_end',all(pd.Timestamp(r.available_after)>=pd.Timestamp(r.charge_end) for r in official.itertuples() if pd.notna(r.charge_end)))
 # Rebuild official pre300 solely from raw prefix. No future waveform values are read into computation.
 coarse=[];cache={};registry=pd.read_csv(TASK/'official_registry.csv');comparisons=[]
 for row in official[official.budget.str.startswith('pre')].itertuples():
  file=registry.set_index('event_id').loc[row.event_id,'file']
  if file not in cache:cache[file]=pd.read_csv(SOURCE/'data/operation'/file,parse_dates=['timestamp']).sort_values('timestamp',kind='stable')
  raw=cache[file];observed=raw[raw.timestamp<=row.available_after].copy();charge=observed[observed.timestamp.between(row.charge_start,row.charge_end)];end=pd.Timestamp(row.charge_end)
  # Includes zero-current step markers at the charge boundary; these are real recorded samples.
  rest=observed[(observed.timestamp>=end)&(abs(observed.current_A)<=.5)];rest=rest[rest.timestamp<=row.available_after]
  if rest.empty:continue
  # Exact first rest sample is the same anchor used by extractor.
  duration=int(row.budget[3:]);rt=ns(rest.timestamp);rt-=rt[0];rv=rest.pack_voltage_V.to_numpy()/4
  one=stage_features(rt,rv,'f2',10,20)
  comparisons.append(np.isclose(one[f'f2_{duration}_Var'],getattr(row,f'c5_f2_{duration}_Var'),equal_nan=True))
  if duration==1800:
   g10=grid(rt,rv,1800,10,20);g30=grid(rt,rv,1800,30,20)
   if g10 is not None and g30 is not None:
    s10=stats(g10);s30=stats(g30);coarse.append(dict(event_id=row.event_id,available_after=row.available_after,Var_10s=s10['Var'],Var_30s=s30['Var'],Ske_10s=s10['Ske'],Ske_30s=s30['Ske'],Max_10s=s10['Max'],Max_30s=s30['Max']))
 ck('raw_prefix_rest_reconstruction',len(comparisons)>0 and all(comparisons),f'{sum(comparisons)}/{len(comparisons)}')
 # Visible-temperature calculation can be reconstructed with no future samples.
 vals=[]
 for row in official[official.budget=='pre300'].itertuples():
  file=registry.set_index('event_id').loc[row.event_id,'file'];raw=cache[file];visible=raw[(raw.timestamp>=row.charge_start)&(raw.timestamp<=row.available_after)]
  vals.append(np.isclose(visible.temp_mean_C.mean(),row.m_actual_T))
 ck('raw_prefix_temperature_reconstruction',all(vals),f'{sum(vals)}/{len(vals)}')
 pred=pd.read_csv(TASK/'official_auxiliary_predictions.csv');ck('next_event_aux_causal',all(pred.features_available_after<pred.target_start))
 out=pd.read_csv(TASK/'official_support_by_event.csv');ck('unverified_pack_capacity_left_empty',out[['Qpack_Ah','SOH_percent']].isna().all().all())
 ck('four_channels_are_one_physical_group',official.entity.nunique()==1)
 pd.DataFrame(coarse).to_csv(TASK/'sampling_10s_30s.csv',index=False)
 # Every input read into training/prefix features hashed, plus exact old read-only source locations.
 paths=list((SOURCE/'dataset original').glob('102Ah*/*.csv'))+list((SOURCE/'data/operation').glob('*.csv.gz'))
 documents=[SOURCE/'submission_instructions_2026.md',SOURCE/'data/DATA_DESCRIPTION.md',SOURCE/'research/phase2_routes23_prompts_20261012/方案3_CCCV静置脉冲联合特征_执行Prompt.md']
 paths+=documents+list((SOURCE/'research/phase2_routes23_prompts_20261012/paper_code_snapshot').glob('*'))
 manifest=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),read_only=True) for p in paths if p.is_file()]
 save('source_input_manifest.json',manifest)
 protected=list((WORK/'framework').rglob('*.py'))+list((WORK/'my_model').rglob('*.py'))+[WORK/'run_model.py']
 ck('protected_files_identical_to_original',all(p.read_bytes()==(SOURCE/p.relative_to(WORK)).read_bytes() for p in protected if p.is_file()))
 save('protected_files.json',[dict(path=str(p.relative_to(WORK)),sha256=sha(p)) for p in protected if p.is_file()])
 if (TASK/'raw_waveform_robustness.csv').exists():
  r=pd.read_csv(TASK/'raw_waveform_robustness.csv');b=r[r.variant=='unchanged'].merge(pd.read_csv(TASK/'predictions_P1_main.csv').query("family=='joint'") [['event_id','pred_Ah']],on='event_id',suffixes=('_raw','_saved'))
  ck('raw_unmodified_reextraction_matches_saved_prediction',np.allclose(b.pred_Ah_raw,b.pred_Ah_saved,atol=1e-4),f'max difference {abs(b.pred_Ah_raw-b.pred_Ah_saved).max()} Ah')
 af=pd.read_csv(TASK/'A_registered_features.csv').merge(f[['event_id','charge_end']],on='event_id');ck('A_history_date_strictly_prior',all(pd.Timestamp(r.A_history_max_time)<pd.Timestamp(r.charge_end) for r in af.itertuples() if pd.notna(r.A_history_max_time)))
 if (TASK/'causal_prefix_replay_audit.json').exists():
  replay=json.loads((TASK/'causal_prefix_replay_audit.json').read_text())
  ck('stage_identified_after_raw_query_cutoff_without_future_catalog',replay['query_inputs_truncated_before_stage_identification'] and not replay['uses_future_event_ids_or_catalog'])
  ck('independent_causal_replay_matches_registered_rest_features',replay['matched_inventory_rows']>0 and replay['all_matched_variances_equal'],f"{replay['matched_inventory_rows']} matched records")
 save('audit_checks.json',checks)
 # Save fully expanded locked-version default params from a parameter-only toy smoke fit, never paper performance.
 model=XGBRegressor(n_jobs=1);model.fit(np.arange(40).reshape(20,2),np.arange(20));(TASK/'Gasper_library_defaults_expanded_smoke_only.json').write_text(model.get_booster().save_config())
 save('environment.json',{'python':sys.version,'platform':platform.platform(),'packages':{k:importlib.metadata.version(k) for k in ['numpy','pandas','scipy','scikit-learn','xgboost','requests','matplotlib','tables']},'defaults_smoke_is_scientific_validation':False})
 print('checks',sum(x['pass_'] for x in checks),'/',len(checks),flush=True)
 for x in checks:
  if not x['pass_']:print('FAILED',x,flush=True)
if __name__=='__main__':main()
