"""Separate truly hit event perturbations from inert historical controls."""
import csv,sys,json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(T/'candidates'))
from framework.data import load_dataset
from model_candidate_v1 import events,ActiveModel
d=load_dataset(ROOT/'data',until='2025-03-11');base=d.operation
assert 43400<len(base) and base.segment.iloc[43400]==1
cases={'unmodified':base,'remove_missing_segment3_zero_control':base[base.segment!=3].copy()}
x=base.copy();x.loc[43400,'timestamp']+=pd.Timedelta(seconds=90);cases['90s_inside_real_window']=x
x=base.copy();x.loc[43400,'timestamp']=x.loc[43399,'timestamp'];cases['duplicate_inside_real_window']=x
x=base.copy();x.loc[43395:43405,'current_A']=0;cases['eleven_current_rows_inside_real_window']=x
out=[];ev0=events(base)
for name,op in cases.items():
 d.operation=op;e=events(op);m=ActiveModel('none');m.fit(d);p=m.estimate_soh(d,'2025-03-11')
 hit=bool((e.t_end==pd.Timestamp('2025-01-24 20:40:13')).any())
 # Pair the original second event by event-end timestamp.
 q=float(e.loc[e.t_end==pd.Timestamp('2025-01-24 20:40:13'),'Q_partial_Ah'].iloc[0]) if hit else None
 out.append(dict(case=name,modified_row_43400=int(name not in ['unmodified','remove_missing_segment3_zero_control']),
  modified_row_within_original_event=int(43357<=43400<=43744),n_rows=len(op),n_events=len(e),
  event1_q_Ah=q,prediction_pct=p,q_ref_Ah=m.last_q_ref,
  interpretation='zero_control' if 'zero_control' in name else 'intervention_or_reference'))
with (T/'outputs/stress_hit_audit.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=out[0]);w.writeheader();w.writerows(out)
assert out[1]['event1_q_Ah']==out[0]['event1_q_Ah']
assert out[2]['event1_q_Ah']!=out[0]['event1_q_Ah']
assert out[4]['event1_q_Ah']!=out[0]['event1_q_Ah']
run=T/'runs/N0_stress_hit_20260930_v1';run.mkdir(exist_ok=True)
(run/'result.json').write_text(json.dumps(out,indent=2));(run/'COMPLETED').write_text('complete\n')
print(json.dumps(out,indent=2))
