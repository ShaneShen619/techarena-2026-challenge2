"""Retrospective official charge-support audit; no capacity labels or tuning.

Reads one official segment at a time to measure observable voltage/depth
support. This audit may inspect full campaign; strict online feature selection
must later be constrained to each checkup prefix and external protocol.
"""
from pathlib import Path
import json
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OLD=ROOT/'research/phase2_temperature_improvement'
sys.path.insert(0,str(OLD/'src'))
from event_core import extract_charge_events,partial_ah
from route_a_repaired import stable_cc_prefix

rows=[]
for path in sorted((ROOT/'data/operation').glob('*.csv.gz')):
    f=pd.read_csv(path,parse_dates=['timestamp'])
    events=extract_charge_events(f,time_col='timestamp',voltage_cols=('cell1_V','cell2_V','cell3_V','cell4_V'),
                                 temp_col='temp_mean_C',segment_col='segment',counter_col='charge_Ah_cum')
    for e in events:
        cc,status=stable_cc_prefix(e)
        if status!='pass' or cc is None:continue
        rec={'file':path.name,'event_end':e.end.isoformat(),'cc_end':cc.end.isoformat(),
             'cc_Ah':float(cc.ah),'temp_C':float(cc.median_temp),
             'current_A':float(cc.median_current)}
        for ci in range(4):
            rec[f'cell{ci+1}_v_start_V']=float(cc.voltages[0,ci])
            rec[f'cell{ci+1}_v_end_V']=float(cc.voltages[-1,ci])
            q=partial_ah(cc,ci,3.38,3.42)
            rec[f'cell{ci+1}_w_3p38_3p42_Ah']=float(q) if q is not None else None
        rows.append(rec)
    print(path.name,'qualified_so_far',len(rows),flush=True)
out=pd.DataFrame(rows).sort_values('event_end')
out.to_csv(TASK/'data_manifests/official_charge_support.csv',index=False)
late=out[out.cc_Ah<50]
summary={'qualified_charge_events_all_time':len(out),'shallow_lt50_Ah_events_all_time':len(late),
         'shallow_cc_Ah_median':float(late.cc_Ah.median()),
         'shallow_cell_v_start_median_V':{f'cell{i}':float(late[f'cell{i}_v_start_V'].median()) for i in range(1,5)},
         'shallow_cell_v_end_median_V':{f'cell{i}':float(late[f'cell{i}_v_end_V'].median()) for i in range(1,5)},
         'shallow_window_3p38_3p42_support':{f'cell{i}':int(late[f'cell{i}_w_3p38_3p42_Ah'].notna().sum()) for i in range(1,5)},
         'note':'Retrospective input support only; later strict-online modeling cannot tune early predictions using future campaign distributions.'}
(TASK/'data_manifests/official_charge_support_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
