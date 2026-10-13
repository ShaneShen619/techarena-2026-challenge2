"""Distinguish documented pack cutoff from observable cell-protection evidence."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1];OUT=TASK/'outputs';CELLS=[f'cell{i}_V' for i in range(1,5)]

def main():
 stats=[];ends=[];inputs=[]
 for path in sorted((ROOT/'data/operation').glob('*.csv.gz')):
  f=pd.read_csv(path,parse_dates=['timestamp']);loaded=f.current_A.lt(-.5)
  d=f.loc[loaded]
  stats.append(dict(file=path.name,rows=len(f),loaded_discharge_rows=int(loaded.sum()),min_loaded_cell_V=float(d[CELLS].min().min()),min_loaded_pack_V=float(d.pack_voltage_V.min()),
   loaded_cell_le2p8_rows=int(d[CELLS].min(axis=1).le(2.8).sum()),loaded_pack_le11p2_rows=int(d.pack_voltage_V.le(11.2).sum()),
   lowest_any_state_cell_V=float(f[CELLS].min().min()),lowest_any_state_pack_V=float(f.pack_voltage_V.min())))
  t=(f.timestamp-f.timestamp.iloc[0]).dt.total_seconds().to_numpy(float);j=-f.current_A.to_numpy(float);mask=loaded.to_numpy()
  starts=np.flatnonzero(mask & np.r_[True,(~mask[:-1])|(np.diff(t)>20)|(np.diff(t)<0)])
  for a in starts:
   b=a
   while b+1<len(f) and mask[b+1] and 0<=t[b+1]-t[b]<=20:b+=1
   q=np.trapezoid(j[a:b+1],t[a:b+1])/3600
   if q<1 or b+1>=len(f):continue
   dt=float(t[b+1]-t[b])
   if not 0<=dt<=20 or mask[b+1]:continue
   row=f.iloc[b];nxt=f.iloc[b+1]
   ends.append(dict(file=path.name,start=f.timestamp.iloc[a].isoformat(),end=row.timestamp.isoformat(),q_Ah=float(q),duration_s=float(t[b]-t[a]),
    last_current_A=float(row.current_A),next_current_A=float(nxt.current_A),transition_gap_s=dt,last_pack_V=float(row.pack_voltage_V),last_min_cell_V=float(row[CELLS].min()),
    next_pack_V=float(nxt.pack_voltage_V),next_min_cell_V=float(nxt[CELLS].min()),
    **{name:float(row[name]) for name in CELLS}))
  inputs.append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 r=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz',parse_dates=['timestamp'])
 ck0=[]
 for name in CELLS:
  hit=r.index[r[name].le(2.8)].tolist()
  if hit:
   idx=hit[0];row=r.iloc[idx]
   ck0.append(dict(cell=name,first_reported_le2p8_time=row.timestamp.isoformat(),pack_V=float(row.voltage_V),current_A=float(row.current_A),q_Ah=float(row.discharged_Ah),
    remaining_reference_rows=len(r)-idx-1,time_to_last_s=float((r.timestamp.iloc[-1]-row.timestamp).total_seconds()),Ah_to_last=float(r.discharged_Ah.iloc[-1]-row.discharged_Ah)))
 s=pd.DataFrame(stats);e=pd.DataFrame(ends)
 s.to_csv(OUT/'cutoff_segment_audit.csv',index=False);e.to_csv(OUT/'observed_discharge_endpoints.csv',index=False)
 r.tail(15).to_csv(OUT/'CK0_cutoff_tail.csv',index=False)
 summary=dict(scope='Official four-series target pack; all 13 released operation files, Jan-Sep 2025; not phase-1 single-cell or external TU systems',
  protocol=dict(checkup='C/20 5.1 A to PACK 11.2 V after full charge',operation='PACK voltage window 11.1-14.1 V; application-program steps also end discharges',cell_protection_setting='not provided'),
  columns_have_cell_voltage=True,columns_have_trip_reason=False,segments=len(s),loaded_discharge_samples=int(s.loaded_discharge_rows.sum()),
  minimum_loaded_cell_V=float(s.min_loaded_cell_V.min()),minimum_loaded_pack_V=float(s.min_loaded_pack_V.min()),
  loaded_cell_le2p8_samples=int(s.loaded_cell_le2p8_rows.sum()),loaded_pack_le11p2_samples=int(s.loaded_pack_le11p2_rows.sum()),
  observed_discharge_to_non_discharge_transitions_ge1Ah=len(e),minimum_endpoint_cell_V=float(e.last_min_cell_V.min()),minimum_endpoint_pack_V=float(e.last_pack_V.min()),
  CK0_first_cell_threshold_reports=ck0,CK0_last_sample=dict(time=r.timestamp.iloc[-1].isoformat(),pack_V=float(r.voltage_V.iloc[-1]),current_A=float(r.current_A.iloc[-1]),cells_V=r[CELLS].iloc[-1].tolist()),
  interpretation=['Documented reference cutoff is pack voltage, not first individual cell threshold','CK0 reported cell2=2.800 V at pack=11.202 V while negative current continued through the remaining 3 seconds of the supplied trace','Rounding, debounce, unknown threshold and the missing post-cutoff trace prevent proof that cell protection is absent','Operation does not approach 2.8 V per cell and does not exercise that candidate protection threshold','Cell channels permit retrospective crossing detection; no controller configuration/trip logs reveal which condition actually commanded shutdown'],
  operation_input_sha256=inputs)
 (OUT/'cutoff_audit_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in summary.items() if k!='operation_input_sha256'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
