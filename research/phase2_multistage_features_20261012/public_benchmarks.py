"""Executable once verified author CSV members are available. No fabricated paper metrics."""
from source_benchmarks import *
from sklearn.model_selection import GroupShuffleSplit
import re

def stable_PI(p,I):
 valid=np.isfinite(I)&(np.abs(I)>1e-6);out=np.zeros_like(p,dtype=float);np.divide(p,I,out=out,where=valid);return out,(~valid).astype(float)

def gasper():
 required=['features_pulse_hppc.csv','features_pulse_rapid.csv','targets_soh.csv']
 if not all((TASK/'public_data'/n).exists() for n in required):
  return {'status':'UNVERIFIED','reason':'Required verified ZIP members unavailable; HTTP range requests timed out; only metadata/index and author code audited','missing':[n for n in required if not (TASK/'public_data'/n).exists()]}
 targets=pd.read_csv(TASK/'public_data/targets_soh.csv');records=[];splits=[]
 for filename in required[:2]:
  raw=pd.read_csv(TASK/'public_data'/filename);f=raw.merge(targets,on='measurement_id',how='left',validate='many_to_one',suffixes=('_pulse',''))
  f=f[f.cell_id.str.startswith('D')&f['C/3 discharge capacity'].notna()].reset_index(drop=True)
  # Exact actual-second grid like author's join helper; no SOC or capacity-other-rate columns in X.
  vc=[c for c in raw.columns if c.startswith('voltage_') and '.0s' in c];ic=[c for c in raw.columns if c.startswith('current_') and '.0s' in c];temp=[c for c in raw.columns if c.startswith('temperature')]
  for v in vc:
   suffix=v.split('_',1)[1];p=f[v]-f[vc[0]];f['polarization_'+suffix]=p
   key='current_'+suffix
   if key in f:
    ratio,mask=stable_PI(p.to_numpy(),f[key].to_numpy());f['PI_'+suffix]=ratio;f['zeroI_'+suffix]=mask
  full=vc+ic+temp+[c for c in f if c.startswith(('polarization_','PI_','zeroI_'))];baseline=[vc[0]]+temp
  views={'V0_T':baseline,'raw_masked_PI':full,'raw_without_PI':vc+ic+temp+[c for c in f if c.startswith('polarization_')]}
  degraded=[c for c in full if c in temp or bool(re.search(r'_(0|10|20|30|40|50|60)\.0s$',c))];views['raw_10s_grid']=degraded
  for protocol,outer in [('author_measurement',GroupShuffleSplit(50,test_size=.2,random_state=42).split(f,groups=f.measurement_id)),('strict_cell',GroupKFold(5).split(f,groups=f.cell_id))]:
   for fold,(tr,te) in enumerate(outer):
    overlap=sorted(set(f.cell_id.iloc[tr])&set(f.cell_id.iloc[te]));splits.append(dict(pulse=filename,protocol=protocol,fold=fold,train_cells=sorted(f.cell_id.iloc[tr].unique()),test_cells=sorted(f.cell_id.iloc[te].unique()),overlap=overlap,train_measurements=sorted(f.measurement_id.iloc[tr].unique().tolist()),test_measurements=sorted(f.measurement_id.iloc[te].unique().tolist())))
    for name,cols in views.items():
     m=make_pipeline(SimpleImputer(strategy='median',keep_empty_features=True),XGBRegressor(n_jobs=1));m.fit(f.iloc[tr][cols],f['C/3 discharge capacity'].iloc[tr]);p=m.predict(f.iloc[te][cols])
     if fold==0 and name=='raw_masked_PI':(TASK/f'Gasper_expanded_{filename}_{protocol}.json').write_text(m[-1].get_booster().save_config())
     for idx,pred in zip(te,p):records.append(dict(pulse=filename,protocol=protocol,fold=fold,family=name,entity=f.cell_id.iloc[idx],measurement_id=f.measurement_id.iloc[idx],label_Ah=float(f['C/3 discharge capacity'].iloc[idx]),pred_Ah=float(pred),nominal_Ah=2.3))
  print('Gasper',filename,len(f),f.cell_id.nunique(),flush=True)
 r=pd.DataFrame(records);r.to_csv(TASK/'Gasper_predictions.csv',index=False);save('Gasper_splits.json',splits)
 metrics=[]
 for key,g in r.groupby(['pulse','protocol','family']):metrics.append(dict(zip(['pulse','protocol','family'],key),**score(g,g.pred_Ah.to_numpy())))
 pd.DataFrame(metrics).to_csv(TASK/'Gasper_metrics.csv',index=False)
 return {'status':'RUN','physical_cell_scores_separate_from_author_protocol':True}

def zhu():
 path=TASK/'Zhu_features.csv'
 if not path.exists():return {'status':'UNVERIFIED','reason':'No verified NCA raw CSV downloaded; strict waveform/capacity pairing not yet executable; no complete paper reproduction claimed'}
 f=pd.read_csv(path);f=f[f[['f2_1800_Var','f2_1800_Ske','f2_1800_Max']].notna().all(axis=1)].reset_index(drop=True)
 if f.entity.nunique()<4:return {'status':'UNVERIFIED','reason':'Insufficient independent physical cells for declared grouped validation'}
 family=families(f,1800,'pre');family={k:v for k,v in family.items() if k in ['F0','F0_F1_CCCV','Zhu_three','Zhu_six','F0_F2_rest','joint']};outer=list(GroupKFold(min(5,f.entity.nunique())).split(f,groups=f.entity));run(f,family,'Zhu_subset',outer)
 records=[]
 for fold,(tr,te) in enumerate(outer):
  cols=['f2_1800_Var','f2_1800_Ske','f2_1800_Max'];m=make({'kind':'XGB','n_estimators':6,'max_depth':6,'learning_rate':.8});m.fit(f.iloc[tr][cols],f.label_Ah.iloc[tr]/3.5);p=m.predict(f.iloc[te][cols])*3.5
  for idx,pred in zip(te,p):records.append(dict(fold=fold,entity=f.entity.iloc[idx],event_id=f.event_id.iloc[idx],label_Ah=float(f.label_Ah.iloc[idx]),pred_Ah=float(pred),nominal_Ah=3.5))
 pd.DataFrame(records).to_csv(TASK/'Zhu_fixed_Table11_predictions.csv',index=False)
 return {'status':'RUN','scope':'limited dataset1 subset, not original130cells or original stratum4:1 reproduction'}
if __name__=='__main__':save('public_benchmark_status.json',{'Gasper':gasper(),'Zhu':zhu()})
