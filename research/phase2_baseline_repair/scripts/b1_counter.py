"""Independent raw-row check of current integration versus operating Ah counters."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework.data import load_operation
op=load_operation(ROOT/'data')
old=pd.read_csv(ROOT/'research/phase2_evidence_validation/outputs/event_eligibility.csv')
p=old[old.event_class=='pulse_20A']
rows=[]
for r in p.itertuples():
    w=op[(op.segment==r.segment)&(op.timestamp>=pd.Timestamp(r.start))&(op.timestamp<=pd.Timestamp(r.end))]
    ts=w.timestamp.values.astype('datetime64[s]').astype('int64')
    dt=np.diff(ts,prepend=ts[0]);i=w.current_A.to_numpy(float)
    rows.append(dict(segment=r.segment,start=r.start,end=r.end,n_rows=len(w),
        integrated_discharge_Ah=float((-np.minimum(i,0)*dt/3600).sum()),
        charge_counter_delta_Ah=float(w.charge_Ah_cum.iloc[-1]-w.charge_Ah_cum.iloc[0]),
        discharge_counter_delta_Ah=float(w.discharge_Ah_cum.iloc[-1]-w.discharge_Ah_cum.iloc[0]),
        max_gap_s=float(dt.max()),negative_current_rows=int((i<0).sum()),
        evidence_level='direct_raw_operation_rows'))
out=pd.DataFrame(rows);out.to_csv(TASK/'outputs/counter_audit.csv',index=False)
assert len(out)==len(p)
print(out[['integrated_discharge_Ah','charge_counter_delta_Ah','discharge_counter_delta_Ah']].median().to_string())
