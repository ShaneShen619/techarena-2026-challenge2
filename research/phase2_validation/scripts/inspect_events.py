from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(TASK/'src'))
from framework.data import load_dataset
from event_core import extract_charge_events,partial_ah
import pandas as pd

d=load_dataset(ROOT/'data')
rows=[]
for e in extract_charge_events(d.operation):
    for i in range(4):
        qs=[partial_ah(e,i,*w) for w in ((3.33,3.40),(3.36,3.43))]
        if any(q is not None for q in qs):
            rows.append(dict(end=e.end,segment=e.segment,cell=i+1,temp=e.median_temp,current=e.median_current,
                             total_Ah=e.ah,start_v=e.voltages[0,i],end_v=e.voltages[-1,i],
                             q1=qs[0],q2=qs[1],counter_delta=e.counter_delta_ah))
out=TASK/'runs'/'official_window_events.csv'
pd.DataFrame(rows).to_csv(out,index=False)
print(out,len(rows))
print(pd.DataFrame(rows).query('cell==1').head(30).to_string(index=False))
