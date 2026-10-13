"""Exact earliest stage1 master N/T code, refit on training cells only; unanchored comparison."""
from common import *
from source_benchmarks import score
import sys
OLD=SOURCE/'research/phase1_transfer_ab';sys.path.insert(0,str(OLD/'src'))
from legacy.model_template import MyModel
from source_model import CachedCell

def main():
 metadata=json.loads((OLD/'artifacts/data_metadata.json').read_text());records=[];inputs=[OLD/'artifacts/data_metadata.json',OLD/'src/legacy/model_template.py',OLD/'src/legacy/collapse.py',OLD/'src/legacy/pretrained.json']
 for rec in metadata:
  p=OLD/'artifacts'/f"data_{rec['cell_id']}.npz";data=np.load(p);rec.update({k:data[k] for k in data.files});records.append(rec);inputs.append(p)
 f=pd.read_csv(TASK/'P1_features.csv');f=f[f[['f2_1800_Var','f4_1800_Var']].notna().all(axis=1)].reset_index(drop=True);out=[];splits=[]
 for entity,g in f.groupby('entity'):
  train=[CachedCell(r) for r in records if r['cell_id']!=entity];model=MyModel();model.fit(train)
  rec=next(r for r in records if r['cell_id']==entity);curve=model.predict_soh(rec['nominal_T'],rec['nominal_C'])
  for row in g.itertuples():
   # Source's current completed charge count; no FUTURE lifetime endpoint or held-cell anchor Q.
   pred=float(curve[row.cycle-1]*102/100);out.append(dict(entity=entity,event_id=row.event_id,cycle=row.cycle,label_Ah=row.label_Ah,pred_Ah=pred,nominal_Ah=102))
  splits.append(dict(test_entity=entity,training_entities=[r['cell_id'] for r in records if r['cell_id']!=entity],held_capacity_anchor_used=False));print('legacy N/T',entity,flush=True)
 r=pd.DataFrame(out);r.to_csv(TASK/'legacy_NT_predictions.csv',index=False);save('legacy_NT_metrics.json',score(r,r.pred_Ah.to_numpy()));save('legacy_NT_provenance.json',{'code':'exact original MyModel.fit and predict_soh from phase1_transfer_ab/src/legacy','protocol':'training five complete source-cell trajectories, test sixth, known nominal T/C and currently completed source charge cycle; unanchored initial level learned from training only','same_labels_as_other_models':True,'same_source_cells_but_full_training_curves':True,'held_true_initial_capacity_used':False,'scope':'historical N/T comparator, not equal training event count to small joint feature model, not in fair stage incremental gate','splits':splits,'input_manifest':[dict(path=str(p),sha256=sha(p)) for p in inputs]})
if __name__=='__main__':main()
