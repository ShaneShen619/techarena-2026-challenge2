"""Prespecified nested entity capacity tests; transformations fitted inside each fold."""
from common import *
from sklearn.model_selection import GroupKFold,LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet,Ridge
from xgboost import XGBRegressor
import warnings,joblib
warnings.filterwarnings('ignore',category=RuntimeWarning)
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings('ignore',category=ConvergenceWarning)
CONFIG=json.loads((TASK/'protocol.json').read_text())['project_configs']
METADATA=['m_cumulative_charge_Ah','m_age_days','m_chamber_T','m_actual_T','m_charge_C','m_charge_duration_s','m_charge_start_V','m_charge_end_V']

def make(c):
 if c['kind']=='EN':reg=ElasticNet(alpha=c['alpha'],l1_ratio=c['l1_ratio'],max_iter=3000,tol=1e-4)
 elif c['kind']=='Ridge':reg=Ridge(alpha=c['alpha'])
 else:reg=XGBRegressor(n_estimators=c['n_estimators'],max_depth=c['max_depth'],learning_rate=c['learning_rate'],reg_lambda=1,reg_alpha=0,subsample=1,colsample_bytree=1,n_jobs=1,random_state=42,objective='reg:squarederror',verbosity=0)
 return make_pipeline(SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True),StandardScaler(),reg)

def score(f,p):
 e=f[['entity','label_Ah','nominal_Ah']].copy();e['pred']=p;e['abs']=abs(e.label_Ah-e.pred);e['square']=(e.label_Ah-e.pred)**2;e['relative']=e['abs']/e.label_Ah;e['pp']=100*e['abs']/e.nominal_Ah
 g=e.groupby('entity').agg(mae=('abs','mean'),mse=('square','mean'),relative=('relative','mean'),pp=('pp','mean'))
 return dict(MAE_Ah=float(g.mae.mean()),RMSE_Ah=float(np.sqrt(g.mse.mean())),relative_error=float(g.relative.mean()),SOH_MAE_pp=float(g.pp.mean()),worst_entity_MAE_Ah=float(g.mae.max()),entities=len(g),events=len(e))

def tune(f,cols):
 groups=f.entity;unique=groups.nunique();splits=list(GroupKFold(min(3,unique)).split(f,groups=groups));loss=[]
 for c in CONFIG:
  ps=np.full(len(f),np.nan)
  for tr,te in splits:
   m=make(c);m.fit(f.iloc[tr][cols],f.iloc[tr].label_Ah/f.iloc[tr].nominal_Ah);ps[te]=m.predict(f.iloc[te][cols])*f.iloc[te].nominal_Ah
  loss.append(score(f,ps)['SOH_MAE_pp'])
 k=int(np.argmin(loss));return CONFIG[k],loss

def families(f,duration=1800,budget='post'):
 cols=f.columns;f0=[c for c in METADATA if c in cols]
 f1=[c for c in cols if c.startswith('f1_')]
 f2_duration=duration if budget=='pre' else 1800
 f2=[c for c in cols if c.startswith(f'f2_{f2_duration}_') and not c.endswith(('zero_var','tau_boundary'))]
 f4=[c for c in cols if c.startswith(f'f4_{duration}_') and not c.endswith(('zero_var','tau_boundary'))]
 f3=[c for c in cols if c.startswith('f3_')];raw=[c for c in cols if c.startswith('raw_')]
 stages={'F1_CCCV':f1,'F2_rest':f2}
 if budget!='pre':stages['F3_dynamic']=f3
 if budget=='post':stages['F4_recovery']=f4
 out={'F0':f0,'NT_only':[c for c in f0 if c in ['m_age_days','m_chamber_T']], 'V0_T':[c for c in f0 if c in ['m_actual_T','m_charge_start_V','m_charge_end_V']]}
 out.update({'F0_'+k:f0+v for k,v in stages.items()})
 three=[f'f2_{duration}_{c}' for c in ['Var','Ske','Max'] if f'f2_{duration}_{c}' in cols];six=[f'f2_{duration}_{c}' for c in ['Var','Ske','Max','Min','Mean','Kur'] if f'f2_{duration}_{c}' in cols]
 out.update(Zhu_three=three,Zhu_six=six,F0_Zhu_three=f0+three)
 if raw and budget!='pre':out['F0_raw']=f0+raw
 joint=f0+sum(stages.values(),[]);out['joint']=joint
 out['joint_no_full_charge']=[c for c in joint if c not in ['f1_Qcharge','m_charge_duration_s','f1_cv_Ah']]
 out['shape_only']=[c for c in joint if c not in f0 and not c.endswith(('Max','Min','Mean')) and 'Qcharge' not in c]
 out['A_window_only']=[c for c in f1 if 'dAh_' in c]
 if 'A_past_log_window_slope' in cols:out['joint_plus_A']=joint+['A_past_log_window_slope']
 for k,v in stages.items():out['joint_without_'+k]=[c for c in joint if c not in v]
 return {k:list(dict.fromkeys(v)) for k,v in out.items() if v}

def run(f,fams,tag,outer=None,do_A=False):
 outer=list(outer if outer is not None else LeaveOneGroupOut().split(f,groups=f.entity));records=[];tunes=[]
 for name,cols in fams.items():
  p=np.full(len(f),np.nan)
  for fold,(tr,te) in enumerate(outer):
   train=f.iloc[tr];test=f.iloc[te];cfg,loss=tune(train,cols);m=make(cfg);m.fit(train[cols],train.label_Ah/train.nominal_Ah);pr=m.predict(test[cols])*test.nominal_Ah;p[te]=pr
   tunes.append(dict(family=name,fold=fold,train_entities=sorted(train.entity.unique()),test_entities=sorted(test.entity.unique()),config=cfg,inner_losses=loss))
   for idx,pred in zip(te,pr):records.append(dict(dataset=tag,family=name,fold=fold,event_id=f.iloc[idx].event_id,entity=f.iloc[idx].entity,cycle=f.iloc[idx].get('cycle',np.nan),label_Ah=float(f.iloc[idx].label_Ah),pred_Ah=float(pred),abs_error_Ah=float(abs(pred-f.iloc[idx].label_Ah)),SOH_error_pp=float(100*(pred-f.iloc[idx].label_Ah)/f.iloc[idx].nominal_Ah)))
   if do_A and name=='joint':
    # Cross-fit base prediction inside the outer-training entities only.
    oof=np.full(len(train),np.nan)
    for a,b in GroupKFold(min(3,train.entity.nunique())).split(train,groups=train.entity):
     inner=make(cfg);inner.fit(train.iloc[a][cols],train.iloc[a].label_Ah/train.iloc[a].nominal_Ah);oof[b]=inner.predict(train.iloc[b][cols])
    acols=['A_past_log_window_slope','m_age_days','m_chamber_T'];resid=train.label_Ah/train.nominal_Ah-oof
    residual=make({'kind':'Ridge','alpha':10});residual.fit(train[acols],resid)
    pr2=pr+residual.predict(test[acols])*test.nominal_Ah
    for idx,pred in zip(te,pr2):records.append(dict(dataset=tag,family='joint_A_OOF_residual',fold=fold,event_id=f.iloc[idx].event_id,entity=f.iloc[idx].entity,cycle=f.iloc[idx].get('cycle',np.nan),label_Ah=float(f.iloc[idx].label_Ah),pred_Ah=float(pred),abs_error_Ah=float(abs(pred-f.iloc[idx].label_Ah)),SOH_error_pp=float(100*(pred-f.iloc[idx].label_Ah)/f.iloc[idx].nominal_Ah)))
  print(tag,name,score(f.iloc[np.flatnonzero(np.isfinite(p))],p[np.isfinite(p)])['MAE_Ah'],flush=True)
 pd.DataFrame(records).to_csv(TASK/f'predictions_{tag}.csv',index=False);save(f'tuning_{tag}.json',tunes)
 out=[]
 for name,g in pd.DataFrame(records).groupby('family'):
  truth=f.set_index('event_id').loc[g.event_id].reset_index();out.append({'dataset':tag,'family':name,**score(truth,g.pred_Ah.to_numpy())})
 pd.DataFrame(out).to_csv(TASK/f'metrics_{tag}.csv',index=False)
 # Entity/late/worst scores and fold-preserved predictions are saved.
 r=pd.DataFrame(records);r['sq']=(r.pred_Ah-r.label_Ah)**2
 entity=r.groupby(['family','entity']).agg(events=('event_id','size'),MAE_Ah=('abs_error_Ah','mean'),MSE_Ah=('sq','mean'),worst_abs_Ah=('abs_error_Ah','max')).reset_index()
 late=r[r.cycle>=r.groupby(['family','entity']).cycle.transform(lambda x:x.quantile(.8))].groupby(['family','entity']).abs_error_Ah.mean().rename('late_MAE_Ah').reset_index()
 entity.merge(late,on=['family','entity'],how='left').to_csv(TASK/f'entity_errors_{tag}.csv',index=False)
 return pd.DataFrame(out)

def main():
 f=pd.read_csv(TASK/'P1_features.csv').replace([np.inf,-np.inf],np.nan)
 legal=pd.to_datetime(f.label_time)>pd.to_datetime(f.charge_end)
 f.assign(pairing_legal=legal).to_csv(TASK/'P1_pairing_audit.csv',index=False)
 f=f[legal].reset_index(drop=True)
 # Common retrospective intersection; missing-stage population reported separately.
 keep=f[['f2_1800_Var','f4_1800_Var']].notna().all(axis=1);g=f[keep].reset_index(drop=True)
 save('P1_coverage.json',{'all_events':len(f),'intersection':len(g),'coverage':float(keep.mean()),'by_entity':f.assign(complete=keep).groupby('entity').complete.mean().to_dict(),'selection':'same complete chain intersection for main all-stage comparisons; all-event fallback separately'})
 fam=families(g);run(g,fam,'P1_main',do_A=True)
 # Prefix metadata actual T computed solely from that prefix; no full-rest T.
 for duration in [300,900,1800]:
  h=g.copy();h.m_actual_T=h[f'm_actual_T{duration}'];ff=families(h,duration,'pre');ff={k:v for k,v in ff.items() if k in ['F0','F0_F1_CCCV','F0_F2_rest','joint','Zhu_three','Zhu_six']};run(h,ff,f'P1_pre{duration}')
 for budget in ['dis','post']:
  ff=families(g,1800,budget);ff={k:v for k,v in ff.items() if k in ['F0','F0_F1_CCCV','F0_F2_rest','F0_F3_dynamic','F0_F4_recovery','joint']}
  if budget!='post':run(g,ff,'P1_dis_end')
 for duration in [300,900]:
  ff=families(g,duration,'post');ff={k:v for k,v in ff.items() if k in ['F0','F0_F4_recovery','joint']};run(g,ff,f'P1_post{duration}')
 core={k:v for k,v in fam.items() if k in ['F0','F0_F1_CCCV','F0_F2_rest','F0_F3_dynamic','F0_F4_recovery','joint','joint_no_full_charge']}
 tempouter=list(LeaveOneGroupOut().split(g,groups=g.m_chamber_T));run(g,core,'P1_cross_temperature',tempouter)
 tr=[];te=[]
 for _,gg in g.groupby('entity'):
  indices=gg.sort_values('cycle').index.to_numpy();cut=int(.7*len(indices));test_indices=indices[cut:];earliest_test=pd.to_datetime(g.loc[test_indices,'charge_end']).min();train_indices=[j for j in indices[:cut] if pd.Timestamp(g.loc[j,'label_time'])<earliest_test];tr.extend(train_indices);te.extend(test_indices)
 save('P1_forward_split.json',{'train_events':g.loc[tr,'event_id'].tolist(),'test_events':g.loc[te,'event_id'].tolist(),'rule':'physical-cycle70/30 with training label timestamp strictly before earliest future test charge_end per cell; clock-reset overlaps excluded'})
 run(g,core,'P1_forward',[(np.array(tr),np.array(te))])
 # All events impute absent features inside folds; masks-only tests missingness shortcuts.
 allfamilies={k:v for k,v in families(f).items() if k in ['F0','joint','joint_no_full_charge']};h=f.copy()
 maskcols=[]
 for c in allfamilies['joint']:
  mc='mask_'+c;h[mc]=h[c].isna().astype(float);maskcols.append(mc)
 allfamilies['mask_only']=maskcols;run(h,allfamilies,'P1_all_fallback')
 cfg,_=tune(g,fam['joint']);final=make(cfg);final.fit(g[fam['joint']],g.label_Ah/g.nominal_Ah);joblib.dump({'model':final,'features':fam['joint'],'config':cfg,'training_entities':sorted(g.entity.unique())},TASK/'P1_final.joblib')
 save('P1_final_support.json',{c:{'low':float(g[c].quantile(.01)),'high':float(g[c].quantile(.99))} for c in fam['joint'] if g[c].notna().any()})
 save('project_candidates.json',CONFIG)
if __name__=='__main__':main()
