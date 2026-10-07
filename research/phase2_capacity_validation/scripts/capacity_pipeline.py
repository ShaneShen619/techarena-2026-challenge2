"""Reproducible, fail-closed official and different-protocol capacity pipeline."""
import argparse,csv,hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
T=Path(__file__).resolve().parents[1];ROOT=T.parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(T/'src'))
from framework.data import load_dataset
from rpt import extract_reference_capacity

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readcsv(p):return list(csv.DictReader(Path(p).open()))
def writecsv(p,rows,fields=None):
 with Path(p).open('w',newline='') as f:
  cols=fields or list(rows[0]);w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
def require(cond,msg):
 if not cond:raise RuntimeError(msg)

def inventory():
 required=[ROOT/'data/checkups/CK0_reference_discharge.csv.gz',T/'downloads/SLBs_LFP_charging_data.zip',
  T/'outputs/split_manifest.csv',T/'outputs/transfer_features_v2.csv',T/'candidates/model_candidate_v1.py']
 for p in required:require(p.exists(),f'missing:{p}')
 return {'source_files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in required]}

def qualify():
 ds=load_dataset(ROOT/'data')
 assert len(ds.eval_points)==8
 p={'series_count':4,'nominal_Ah':102,'reference_current_A':5.1,'cutoff_pack_V':11.2,'full_charge_confirmed':True}
 x=extract_reference_capacity(pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz'),p)
 require(x.status=='accepted' and abs(x.capacity_Ah-100.412)<0.002,'CK0 RPT extraction mismatch')
 return {'official_CK0_reintegrated_Ah':x.capacity_Ah,'official_CK1_CK7_capacity':'hidden',
  'independent_same_protocol_D2':'absent','Ji_capacity':'different_protocol_author_reported_prior_three_test_mean'}

def freeze():
 dest=T/'configs/freeze_manifest.json'
 require(not dest.exists(),'freeze already exists; do not overwrite after evaluation')
 cfg=json.loads((T/'configs/transfer_final_freeze_v2.json').read_text())
 require(cfg['selected_candidate']=='q_window','unsafe transfer candidate')
 manifest={'version':'2026-09-30-N5-final-v1','official_cutoff':'each CK timestamp inclusive',
  'source_eligibility':'D2 absent; Ji only single-cell different-protocol',
  'official_candidates':{'C0':'CK0 constant','C1':'causal none','C2':'start','C3':'start_gap','C4':'range'},
  'official_thresholds':{'start_current_A_max':5,'max_gap_s_max':60,'Ah_range_multipliers':[0.5,1.5]},
  'official_reference':'fit uses only public CK0; q_ref recalculated at prediction prefix',
  'transfer_selected':'q_window','transfer_voltage_window_V':[3.35,3.50],
  'transfer_comparator':'development median','split_sha256':sha(T/'outputs/split_manifest.csv'),
  'feature_sha256':sha(T/'outputs/transfer_features_v2.csv'),
  'candidate_sha256':sha(T/'candidates/model_candidate_v1.py'),
  'rpt_extractor_sha256':sha(T/'src/rpt.py'),
  'pipeline_sha256':sha(__file__),'initial_config_sha256':sha(T/'configs/transfer_initial_v1.json'),
  'transfer_final_config_sha256':sha(T/'configs/transfer_final_freeze_v2.json'),
  'seed':20260930,'holdout_score_limit':1,'researcher_blinding':'nonblind_source_filenames',
  'target_protocol':'Ji reported prior capacity Ah; no verified nominal denominator',
  'missing_metric_rule':'null; never convert to zero','stopping':'one holdout score, no retuning',
  'high_goals_official_pp':{'macro_MAE':1,'worst_entity_MAE':2,'max_single_AE':5,'relative_simple_improvement_fraction':0.2}}
 dest.write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
 return {'freeze_sha256':sha(dest),'selected_transfer':cfg['selected_candidate']}

def extract():
 f=readcsv(T/'outputs/transfer_features_v2.csv');s=readcsv(T/'outputs/split_manifest.csv')
 require(len(f)==len(s)==23,'unexpected transfer entities')
 require({x['entity_id'] for x in f}=={x['entity_id'] for x in s},'split/feature ID mismatch')
 require(all(float(x['max_gap_s'])<=10 for x in f),'source sampling gap')
 return {'transfer_single_cell_features':len(f),'official_event_rows':len(readcsv(T/'outputs/event_state_comparison.csv')),
  'forbidden_source_columns_consumed':False}

def _model():
 spec=importlib.util.spec_from_file_location('frozen_candidate',T/'candidates/model_candidate_v1.py')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def predict():
 manifest=json.loads((T/'configs/freeze_manifest.json').read_text())
 require(sha(T/'candidates/model_candidate_v1.py')==manifest['candidate_sha256'],'candidate changed after freeze')
 require(sha(T/'outputs/transfer_features_v2.csv')==manifest['feature_sha256'],'features changed after freeze')
 mod=_model();ds=load_dataset(ROOT/'data');rows=[]
 for ck in ds.eval_points.itertuples():
  prefix=ds.operation.loc[ds.operation.timestamp<=pd.Timestamp(ck.date)].reset_index(drop=True)
  sub=ds.__class__(**{k:getattr(ds,k) for k in ds.__dataclass_fields__}) if hasattr(ds,'__dataclass_fields__') else None
  if sub is None:
   import copy
   sub=copy.copy(ds)
  sub.operation=prefix
  for name,gate in [('C0',None),('C1','none'),('C2','start'),('C3','start_gap'),('C4','range')]:
   if gate is None:p=float(ds.checkups_released.SOH_pct.iloc[0]);q=None
   else:
    m=mod.ActiveModel(gate);m.fit(sub);p=float(m.estimate_soh(sub,ck.date));q=m.last_q_ref
   rows.append(dict(source_id='official',entity_id='official_4S_one_pack',series_count=4,
    target_id=ck.checkup,checkpoint_date=str(ck.date),candidate=name,prediction_SOH_pct=p,
    reference_q_Ah=q,target_capacity_Ah=None,target_SOH_pct=None,abs_error_pp=None,
    capacity_status='hidden' if ck.checkup!='CK0' else 'released_anchor_not_independent_test',
    evidence_tier='unlabeled_official_inference',split='official_hidden',fallback=int(q is None)))
 writecsv(T/'outputs/official_predictions.csv',rows)
 feats=readcsv(T/'outputs/transfer_features_v2.csv');split={x['entity_id']:x for x in readcsv(T/'outputs/split_manifest.csv')}
 labels={x['entity_id']:x for x in readcsv(T/'sealed/ji_23_private_label_map.csv') if x['split']=='development'}
 dev=[x for x in feats if split[x['entity_id']]['split']=='development']
 hold=[x for x in feats if split[x['entity_id']]['split']=='sealed_holdout']
 require(len(labels)==15 and len(hold)==8,'split labels invalid')
 x=np.array([float(r['q_335_350_Ah']) for r in dev]);y=np.array([float(labels[r['entity_id']]['capacity_Ah_author_mean_3']) for r in dev])
 slope=float(np.dot(x-x.mean(),y-y.mean())/max(np.dot(x-x.mean(),x-x.mean()),1e-12))
 out=[]
 for r in hold:
  for cand,p in [('median',float(np.median(y))),('q_window',float(y.mean()+slope*(float(r['q_335_350_Ah'])-x.mean())) )]:
   out.append(dict(source_id='Ji_second_life_23',entity_id=r['entity_id'],series_count=1,
    candidate=cand,prediction_capacity_Ah=p,target_capacity_Ah=None,abs_error_Ah=None,
    evidence_tier='different_protocol_single_cell',split='sealed_holdout',
    label_status='sealed_prediction_before_target_access'))
 writecsv(T/'outputs/transfer_holdout_predictions_pre_score.csv',out)
 return {'official_predictions':len(rows),'transfer_holdout_prelabel_predictions':len(out)}

def score():
 require((T/'configs/freeze_manifest.json').exists(),'must freeze before score')
 flag=T/'sealed/HOLDOUT_SCORED_ONCE'
 require(not flag.exists(),'holdout already scored; no repeated tuning')
 m=json.loads((T/'configs/freeze_manifest.json').read_text())
 require(sha(T/'outputs/transfer_features_v2.csv')==m['feature_sha256'],'feature hash mismatch')
 require(sha(T/'candidates/model_candidate_v1.py')==m['candidate_sha256'],'candidate hash mismatch')
 rows=readcsv(T/'outputs/transfer_holdout_predictions_pre_score.csv')
 labels={x['entity_id']:x for x in readcsv(T/'sealed/ji_23_private_label_map.csv') if x['split']=='sealed_holdout'}
 require(len(labels)==8 and len(rows)==16,'holdout dimensions')
 scored=[]
 for r in rows:
  y=float(labels[r['entity_id']]['capacity_Ah_author_mean_3']);p=float(r['prediction_capacity_Ah'])
  scored.append({**r,'target_capacity_Ah':y,'abs_error_Ah':abs(p-y),'signed_error_Ah':p-y,
   'label_status':'author_prior_three_test_mean_not_raw_RPT_verified'})
 writecsv(T/'outputs/transfer_holdout_scored.csv',scored)
 flag.write_text(json.dumps({'freeze_sha256':sha(T/'configs/freeze_manifest.json'),
  'prediction_sha256':sha(T/'outputs/transfer_holdout_predictions_pre_score.csv'),
  'score_sha256':sha(T/'outputs/transfer_holdout_scored.csv')},indent=2))
 return {'holdout_cells':8,'scored_rows':16,'score_sha256':sha(T/'outputs/transfer_holdout_scored.csv')}

def report():
 rows=readcsv(T/'outputs/transfer_holdout_scored.csv');official=readcsv(T/'outputs/official_predictions.csv')
 comparisons=[];entities=[]
 for cand in ['median','q_window']:
  r=[x for x in rows if x['candidate']==cand];e=np.array([float(x['signed_error_Ah']) for x in r]);a=np.abs(e)
  comparisons.append(dict(source_id='Ji_second_life_23',tier='different_protocol_single_cell',candidate=cand,
   n_entities=len(r),n_targets=len(r),macro_MAE_Ah=float(a.mean()),point_MAE_Ah=float(a.mean()),
   worst_entity_MAE_Ah=float(a.max()),max_absolute_error_Ah=float(a.max()),signed_bias_Ah=float(e.mean()),
   overestimate_fraction=float((e>0).mean()),late_MAE_Ah=None,SOH_MAE_pp=None,
   reject_fraction=0,fallback_fraction=0,performance_scope='exploratory_nonblind_author_labels_one_stage'))
  for x in r:
   entities.append(dict(source_id='Ji_second_life_23',entity_id=x['entity_id'],candidate=cand,
    target_Ah=x['target_capacity_Ah'],prediction_Ah=x['prediction_capacity_Ah'],
    signed_error_Ah=x['signed_error_Ah'],MAE_Ah=x['abs_error_Ah'],SOH_error_pp=None,
    temperature_C=25,stage='one_second_life_snapshot_late_unavailable'))
 writecsv(T/'outputs/candidate_comparison.csv',comparisons)
 writecsv(T/'outputs/per_entity_metrics.csv',entities)
 per=[]
 for x in official:
  per.append(dict(source_id='official',entity_id=x['entity_id'],target_id=x['target_id'],candidate=x['candidate'],
   prediction_SOH_pct=x['prediction_SOH_pct'],target_SOH_pct=None,error_pp=None,
   prediction_capacity_Ah=None,target_capacity_Ah=None,error_Ah=None,
   split='official_hidden',tier='unlabeled_official_inference',status=x['capacity_status']))
 for x in rows:
  per.append(dict(source_id=x['source_id'],entity_id=x['entity_id'],target_id='one_second_life_snapshot',candidate=x['candidate'],
   prediction_SOH_pct=None,target_SOH_pct=None,error_pp=None,
   prediction_capacity_Ah=x['prediction_capacity_Ah'],target_capacity_Ah=x['target_capacity_Ah'],error_Ah=x['signed_error_Ah'],
   split='sealed_holdout',tier='different_protocol_single_cell',status=x['label_status']))
 writecsv(T/'outputs/per_target_predictions.csv',per)
 result={'official_hidden_targets':sum(x['target_id']!='CK0' for x in official),
  'official_MAE_pp':None,'same_protocol_independent_MAE_pp':None,'late_MAE':None,
  'transfer_comparison':comparisons,
  'selected_transfer_improvement_fraction_vs_median':1-comparisons[1]['macro_MAE_Ah']/comparisons[0]['macro_MAE_Ah']}
 (T/'outputs/pipeline_result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
 return result

steps={'inventory':inventory,'qualify':qualify,'freeze':freeze,'extract':extract,'predict':predict,'score':score,'report':report}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('stage',choices=[*steps,'all']);a=ap.parse_args()
 names=list(steps) if a.stage=='all' else [a.stage]
 for name in names:print(name,json.dumps(steps[name](),ensure_ascii=False))
