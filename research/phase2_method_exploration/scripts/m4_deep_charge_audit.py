"""Exploratory audit of deep charges under strict official checkup cutoffs.

The deep-charge Ah are observed charge throughput, not hidden checkup labels.
Every row used by a checkpoint is earlier than that checkpoint. Thresholds
were chosen after retrospective support inspection and cannot be confirmation.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M4_deep_charge_audit_v1'
OUT.mkdir(parents=True,exist_ok=False)
events=pd.read_csv(TASK/'data_manifests/official_charge_support.csv',parse_dates=['event_end','cc_end'])
ck=pd.read_csv(ROOT/'data/checkups/evaluation_points.csv',parse_dates=['date'])
print(ck.to_string(index=False),flush=True)
assert 'checkup' in ck and 'date' in ck
for i in range(1,5):
    events[f'cell{i}_start_V']=events[f'cell{i}_v_start_V']
events['min_start_cell_V']=events[[f'cell{i}_start_V' for i in range(1,5)]].min(axis=1)
events['max_start_cell_V']=events[[f'cell{i}_start_V' for i in range(1,5)]].max(axis=1)
events['deep_candidate']=events.cc_Ah.ge(80)&events.max_start_cell_V.lt(3.1)
deep=events.loc[events.deep_candidate].copy()
deep['previous_CK']=None;deep['next_CK']=None
for j,row in deep.iterrows():
    past=ck.loc[ck.date<row.event_end];future=ck.loc[ck.date>row.event_end]
    deep.at[j,'previous_CK']=past.iloc[-1]['checkup'] if len(past) else None
    deep.at[j,'next_CK']=future.iloc[0]['checkup'] if len(future) else None
deep.to_csv(OUT/'deep_charge_events.csv',index=False)

bol=float(deep.iloc[0].cc_Ah);calibration_offset=100.41-bol
rows=[]
for row in ck.itertuples(index=False):
    prior=deep.loc[deep.event_end<row.date]
    latest=prior.iloc[-1] if len(prior) else None
    if latest is None:
        rows.append({'checkup':row.checkup,'date':row.date.isoformat(),
                     'latest_deep_event':None,'lag_days':None,'deep_charge_Ah':None,
                     'CK0_calibrated_charge_proxy_Ah':100.41,'proxy_SOH_pct':100*100.41/102,
                     'new_deep_since_previous_CK':False,'status':'CK0_anchor_only'})
        continue
    prev=ck.loc[ck.date<row.date]
    previous_ck_date=prev.date.max() if len(prev) else pd.Timestamp.min
    is_new=bool(latest.event_end>previous_ck_date)
    # This is a transparent delayed charge-throughput proxy. No per-Ck
    # hidden truth is used; the offset only calibrates the first public CK0.
    qhat=float(latest.cc_Ah+calibration_offset)
    rows.append({'checkup':row.checkup,'date':row.date.isoformat(),
                 'latest_deep_event':latest.event_end.isoformat(),
                 'lag_days':float((row.date-latest.event_end).total_seconds()/86400),
                 'deep_charge_Ah':float(latest.cc_Ah),
                 'CK0_calibrated_charge_proxy_Ah':qhat,
                 'proxy_SOH_pct':float(100*qhat/102),
                 'new_deep_since_previous_CK':is_new,
                 'status':'delayed_observed_charge_proxy_not_capacity_label'})
out=pd.DataFrame(rows)
assert all(pd.Timestamp(t)<pd.Timestamp(d) for t,d in zip(out.latest_deep_event.dropna(),out.loc[out.latest_deep_event.notna(),'date']))
out.to_csv(OUT/'strict_prefix_deep_charge_proxy.csv',index=False)
summary={'deep_candidate_count_all_time':len(deep),
         'first_deep_charge_Ah':bol,'public_CK0_capacity_Ah':100.41,
         'CK0_offset_Ah':calibration_offset,
         'deep_candidate_after_CK7_excluded_from_CK7':int(((deep.event_end>ck.date.max())&(deep.next_CK.isna())).sum()),
         'uncertainty_note':'Charge Ah from unknown initial SOC at 20.4A and terminal CV is not 5.1A discharge capacity. A prior checkup may have set initial SOC but checkup process is hidden; bias/efficiency, depth, temperature and month lag remain.',
         'selection_notice':'80Ah and <3.1V thresholds chosen after retrospective audit, so diagnostic only and not blind validation.',
         'capacity_validation':'CK1-CK7 labels hidden; no official error computed'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
