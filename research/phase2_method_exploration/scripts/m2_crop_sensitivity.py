"""Create predeclared alternate D1 crop positions from native P1 rows.

Uses M2/M4 audited event IDs as event selection metadata, then reads original
source rows and recomputes all cropped window quantities. Model-facing output
does not contain full-charge Ah or target labels. This is still a deep-charge
crop proxy, not an observed shallow-cycle experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--mode',choices=['3p45','3p55','full_tail','mid_event'],required=True)
args=parser.parse_args()
OUT=TASK/'runs'/f'M2_crop_{args.mode}_v1'
OUT.mkdir(parents=True,exist_ok=False)
crop_name={'3p45':'first_3p45V_crossing_tail','3p55':'first_3p55V_crossing_tail',
           'full_tail':'completed_charge_tail','mid_event':'fixed_mid_event_capacity_coordinate'}[args.mode]
OLD = ROOT/'research/phase2_temperature_improvement'
sys.path.insert(0, str(OLD/'src'))
from event_core import extract_charge_events, partial_ah
from route_a_repaired import stable_cc_prefix

VIEW = TASK/'data_manifests/d1_target_visibility.v1.1.csv'
source = pd.read_csv(VIEW)
assert len(source) == 1080
wanted = {x for field in source.allowed_event_ids_json for x in json.loads(field)}
bycell: dict[str,set[str]] = {}
for event_id in wanted:
    cell = event_id.split('|',1)[0]
    bycell.setdefault(cell,set()).add(event_id)

windows = [(3.35,3.39),(3.38,3.42),(3.41,3.45),(3.44,3.48),
           (3.35,3.42),(3.38,3.45),(3.41,3.48),
           (3.35,3.45),(3.38,3.48)]
rows=[]
audit=[]
for cell, ids in sorted(bycell.items()):
    cycles = {int(x.split('|')[1]) for x in ids}
    pieces=[]
    for path in sorted((ROOT/'dataset original'/cell).glob('*.csv')):
        for chunk in pd.read_csv(path,usecols=['absolute_time','cycle_number','step_type','voltage_V',
                                               'current_A','temperature_C'],chunksize=100000):
            part=chunk.loc[chunk.cycle_number.isin(cycles) & ~chunk.step_type.eq('cc_discharge')]
            if len(part): pieces.append(part.drop(columns='step_type'))
    if not pieces:
        raise RuntimeError(f'no source rows for {cell}')
    raw=pd.concat(pieces,ignore_index=True)
    raw['absolute_time']=pd.to_datetime(raw.absolute_time)
    raw=raw.sort_values('absolute_time',kind='stable').reset_index(drop=True)
    events=extract_charge_events(raw,time_col='absolute_time',voltage_cols=('voltage_V',),
                                 temp_col='temperature_C',segment_col='cycle_number',counter_col=None)
    found=set()
    for event in events:
        eid=f'{cell}|{event.segment}|{event.start.isoformat()}|{event.end.isoformat()}'
        if eid not in ids: continue
        found.add(eid)
        cc,status=stable_cc_prefix(event)
        audit.append({'cell_id':cell,'event_id':eid,'source_event_end':event.end.isoformat(),
                      'old_qualifier_recomputed':status,'full_cc_Ah_audit_only':float(cc.ah) if cc is not None else None})
        if status!='pass' or cc is None: continue
        if args.mode in ('3p45','3p55'):
            threshold={'3p45':3.45,'3p55':3.55}[args.mode]
            measured=cc.voltages[:,0]
            crossing=np.flatnonzero((measured[:-1]<threshold)&(measured[1:]>=threshold))
            if not len(crossing):
                audit[-1]['endpoint_status']=f'no_{threshold:.2f}V_crossing'
                continue
            stop=int(crossing[0]+1)
        elif args.mode=='full_tail':
            stop=len(cc.q_ah)-1
        else:
            stop=int(np.argmin(np.abs(cc.q_ah-0.5*cc.ah)))
        audit[-1]['endpoint_status']='pass'
        for budget in (15,20,30):
            qstart=float(cc.q_ah[stop]-budget)
            if qstart<0:
                continue
            mask=(cc.q_ah>=qstart) & (np.arange(len(cc.q_ah))<=stop)
            if mask.sum()<3:
                continue
            times=cc.times_s[mask].copy()
            v=cc.voltages[mask].copy()
            q=cc.q_ah[mask].copy()
            q-=q[0]
            span=float(q[-1])
            if span<=0 or span>budget+1e-8:
                raise AssertionError('invalid cropped Ah span')
            begin=pd.Timestamp(int(times[0]),unit='s')
            end=pd.Timestamp(int(times[-1]),unit='s')
            frag=replace(cc,start=begin,end=end,duration_s=float(times[-1]-times[0]),
                         ah=span,times_s=times,q_ah=q,voltages=v,counter_q_ah=None)
            selected=raw.loc[(raw.cycle_number==event.segment) &
                             (raw.absolute_time>=begin) & (raw.absolute_time<=end) &
                             (raw.current_A>=5)]
            actual_dt=np.diff(times).astype(float)
            if len(actual_dt)==0 or (actual_dt<=0).any():
                raise AssertionError('invalid sampled event time')
            rec={'cell_id':cell,'event_id':eid,'budget_Ah':budget,
                 'crop_position':crop_name,'fragment_start':begin.isoformat(),
                 'fragment_end':end.isoformat(),'n_samples':len(times),
                 'observed_span_Ah':span,'median_dt_s':float(np.median(actual_dt)),
                 'max_dt_s':float(np.max(actual_dt)),
                 'temperature_C':float(selected.temperature_C.median()) if selected.temperature_C.notna().any() else None,
                 'current_A':float(selected.current_A.median()) if len(selected) else None,
                 'v_start_V':float(v[0,0]),'v_end_V':float(v[-1,0])}
            for idx,(lo,hi) in enumerate(windows):
                value=partial_ah(frag,0,lo,hi)
                rec[f'w{idx:02d}_Ah']=float(value) if value is not None else None
                rec[f'w{idx:02d}_visible']=int(value is not None)
            rows.append(rec)
    absent=ids-found
    if absent:
        raise RuntimeError(f'{cell}: {len(absent)} expected event IDs not reconstructed, examples {sorted(absent)[:3]}')
    print(cell,'wanted_events',len(ids),'cropped_rows_so_far',len(rows),flush=True)

eventview=pd.DataFrame(rows)
eventview.to_csv(OUT/'cropped_events.csv',index=False)
pd.DataFrame(audit).to_csv(OUT/'event_audit_restricted.csv',index=False)
assert len(eventview[['cell_id','event_id','budget_Ah']].drop_duplicates())==len(eventview)
assert not any(x in eventview.columns for x in ['full_cc_Ah_audit_only','target_capacity_Ah','target_soh_pp'])
assert eventview.max_dt_s.le(60).all()
summary={'mode':args.mode,'selected_unique_events':len(wanted),'reconstructed_unique_events':len(audit),
         'cropped_fragment_rows':len(eventview),
         'by_budget':{str(k):int(v) for k,v in eventview.groupby('budget_Ah').size().items()},
         'window_support_by_budget':{str(b):{f'w{i:02d}':int(s[f'w{i:02d}_visible'].sum()) for i in range(len(windows))}
                                     for b,s in eventview.groupby('budget_Ah')},
         'source_selection_note':'Audited full-event IDs and stable-CC gate choose completed charge; alternate endpoint is frozen in protocol v1.4. Only native cropped fragment signals enter model-facing file.',
         'label_columns_in_model_view':False,
         'model_view_sha256':hashlib.sha256((OUT/'cropped_events.csv').read_bytes()).hexdigest()}
final=[]
available={(str(r.event_id),int(r.budget_Ah)):r for r in eventview.itertuples(index=False)}
for row in source.to_dict(orient='records'):
    budget=int(row['budget_Ah'])
    old_allowed=json.loads(row['allowed_event_ids_json'])
    kept=[eid for eid in old_allowed if (eid,budget) in available]
    missing=[eid for eid in old_allowed if (eid,budget) not in available]
    current=row['current_event_id'] if isinstance(row['current_event_id'],str) else None
    if current not in kept: current=None
    row['allowed_event_ids_json']=json.dumps(kept)
    row['missing_qualified_event_ids_json']=json.dumps(missing)
    row['allowed_event_count']=len(kept)
    row['current_event_id']=current if current is not None else ''
    row['crop_position']=crop_name
    row['metadata_status']='native_fragment_verified'
    row['no_event_reason']='no_endpoint_or_budget_fragment' if not kept else ''
    row['allowed_fragment_end_max']=max((available[(eid,budget)].fragment_end for eid in kept),default='')
    if row['allowed_fragment_end_max'] and not pd.Timestamp(row['allowed_fragment_end_max'])<pd.Timestamp(row['target_discharge_start']):
        raise AssertionError('future fragment')
    final.append(row)
manifest=pd.DataFrame(final)
manifest.to_csv(OUT/'visibility.csv',index=False)
summary['target_rows']=len(manifest)
summary['zero_event_rows']=int(manifest.allowed_event_count.eq(0).sum())
summary['lost_old_prequalified_event_references']=int(sum(len(json.loads(x)) for x in manifest.missing_qualified_event_ids_json))
summary['visibility_sha256']=hashlib.sha256((OUT/'visibility.csv').read_bytes()).hexdigest()
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
