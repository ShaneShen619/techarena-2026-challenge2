import copy,csv,hashlib,json,sys
from pathlib import Path
import pandas as pd
T=Path(__file__).resolve().parents[1];ROOT=T.parents[1]
sys.path.insert(0,str(ROOT))
from framework.data import load_dataset
from my_model.model_example import ExampleModel
ds=load_dataset(ROOT/'data');src=ROOT/'my_model/model_example.py'
rows=[]
for ck in ds.eval_points.itertuples():
 prefix=copy.copy(ds);prefix.operation=ds.operation[ds.operation.timestamp<=ck.date].reset_index(drop=True)
 full_m=ExampleModel();full_m.fit(ds)
 prefix_m=ExampleModel();prefix_m.fit(prefix)
 yfull=full_m.estimate_soh(prefix,ck.date);yprefix=prefix_m.estimate_soh(prefix,ck.date)
 rows.append(dict(checkup=ck.checkup,q_ref_full_fit_Ah=full_m.q_ref,q_ref_prefix_fit_Ah=prefix_m.q_ref,
  prediction_full_fit_pct=yfull,prediction_prefix_fit_pct=yprefix,delta_full_minus_prefix_pp=yfull-yprefix,
  source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),evidence='original_full_fit_leak_positive_control'))
with (T/'outputs/original_leakage_control.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
assert abs(rows[1]['delta_full_minus_prefix_pp'])>0.01
run=T/'runs/N0_original_leak_20260930_v1';run.mkdir(exist_ok=True)
(run/'result.json').write_text(json.dumps({'CK1':rows[1],'n_checkpoints':len(rows)},indent=2));(run/'COMPLETED').write_text('complete\n')
print(json.dumps({'CK1':rows[1]},indent=2))
