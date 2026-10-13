"""Outcome-free raw-event and operating-anchor audit; never opens hidden labels."""
from __future__ import annotations
import hashlib, json, pickle
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
RUN = TASK / 'runs/v1'
CELLS = [f'cell{i}_V' for i in range(1, 5)]
CFG = json.loads((TASK/'configs/frozen_protocol.json').read_text())

def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):h.update(block)
    return h.hexdigest()

def rest(raw, idx, step):
    ids=[]; previous=None
    while 0<=idx<len(raw) and abs(raw.current_A.iat[idx])<=0.5:
        if previous is not None:
            dt=abs((raw.timestamp.iat[idx]-raw.timestamp.iat[previous]).total_seconds())
            if dt>20:break
        ids.append(idx);previous=idx;idx+=step
    return sorted(ids)

def clean(df):
    return df.sort_values('timestamp',kind='stable').drop_duplicates('timestamp',keep='last')

def audit():
    RUN.mkdir(parents=True, exist_ok=True)
    short=pd.read_csv(ROOT/'research/phase2_method_exploration/outputs/event_catalog.csv',parse_dates=['event_start','event_end'])
    op=pd.read_csv(ROOT/'research/charge_capacity_review_20261006/operating_events.csv',parse_dates=['t_start','t_end'])
    candidates=[]
    for r in short[short.quality_status.eq('certified') & short.before_CK7].itertuples():
        candidates.append(dict(file=r.source_file,start=r.event_start,end=r.event_end,panel='short',T=int(r.temperature_C)))
    for r in op[op.kind.eq('long_dynamic_discharge') & op.Q_Ah.between(32.7,33) & (op.t_end<pd.Timestamp('2025-08-28'))].itertuples():
        candidates.append(dict(file=r.file,start=r.t_start,end=r.t_end,panel='wide',T=int(r.setpoint_C)))
    events=[]; ledger=[];anchors=[];gaps=[];counter=[]
    for file in sorted({c['file'] for c in candidates}):
        raw=pd.read_csv(ROOT/'data/operation'/file,parse_dates=['timestamp'])
        full=op[op.file.eq(file)&op.kind.eq('full_charge')].sort_values('t_end')
        anchor_info=[]
        for a in full.itertuples():
            p=clean(raw.iloc[a.start_index_in_file:a.end_index_in_file+1])
            cv=p[(p.pack_voltage_V>=13.95)&(p.current_A>0.5)]
            cv_s=float((cv.timestamp.iat[-1]-cv.timestamp.iat[0]).total_seconds()) if len(cv)>1 else 0
            dt=np.diff(p.timestamp.astype('int64').to_numpy()/1e9)
            ok=bool(p.current_A.ge(0.5).all() and (dt<=20).all() and float(p.pack_voltage_V.iat[-1])>=13.95 and float(p.current_A.iat[-1])<=5.5 and cv_s>=60)
            rec=dict(file=file,start=a.t_start.isoformat(),end=a.t_end.isoformat(),tail_A=float(p.current_A.iat[-1]),end_pack_V=float(p.pack_voltage_V.iat[-1]),cv_s=cv_s,cell_spread_mV=float(p[CELLS].iloc[-1].max()-p[CELLS].iloc[-1].min())*1000,qualified=ok,end_index=int(a.end_index_in_file))
            anchors.append(rec);anchor_info.append(rec)
        tsec=raw.timestamp.astype('int64').to_numpy()/1e9
        for idx in np.flatnonzero(np.diff(tsec)>20):
            gaps.append(dict(file=file,from_time=raw.timestamp.iat[idx].isoformat(),to_time=raw.timestamp.iat[idx+1].isoformat(),gap_s=float(tsec[idx+1]-tsec[idx])))
        for c in [c for c in candidates if c['file']==file]:
            valid=raw.current_A.lt(-.5)
            ix0=np.flatnonzero(raw.timestamp.eq(c['start']) & valid)
            ix1=np.flatnonzero(raw.timestamp.eq(c['end']) & valid)
            if not len(ix0) or not len(ix1):
                ledger.append(dict(**{k:str(v) for k,v in c.items()},qualified=False,reason='raw_boundary_absent'));continue
            first=int(ix0[0]);last=int(ix1[-1]);p=clean(raw.iloc[first:last+1])
            t=(p.timestamp-c['start']).dt.total_seconds().to_numpy(float);j=-p.current_A.to_numpy(float)
            q=cumulative_trapezoid(j,t,initial=0)/3600
            pre=clean(raw.iloc[rest(raw,first-1,-1)]);post=clean(raw.iloc[rest(raw,last+1,1)])
            pre_t=(pre.timestamp-c['start']).dt.total_seconds().to_numpy(float)
            post_t=(post.timestamp-c['end']).dt.total_seconds().to_numpy(float)
            prev=[a for a in anchor_info if a['qualified'] and pd.Timestamp(a['end'])<=c['start']]
            anchor=prev[-1] if prev else None
            net=np.nan;age=np.nan;chain_ok=False;chain_id='unknown';dqprev=np.nan
            if anchor:
                chain=clean(raw.iloc[anchor['end_index']:first+1]);ct=(chain.timestamp-chain.timestamp.iat[0]).dt.total_seconds().to_numpy(float)
                age=(c['start']-pd.Timestamp(anchor['end'])).total_seconds()/3600
                chain_ok=bool((np.diff(ct)<=20).all() and age<=168)
                chain_id=file+'|'+anchor['end']
                if chain_ok:net=float(np.trapezoid(-chain.current_A.to_numpy(float),ct)/3600)
            delta= p[['charge_Ah_cum','discharge_Ah_cum']].iloc[-1]-p[['charge_Ah_cum','discharge_Ah_cum']].iloc[0]
            counter.append(dict(start=c['start'].isoformat(),panel=c['panel'],integrated_discharge_Ah=float(q[-1]),charge_counter_delta=float(delta.iloc[0]),discharge_counter_delta=float(delta.iloc[1]),sum_residual_Ah=float(delta.sum()-q[-1]),counter_direction_supported=bool(delta.iloc[1]>.9*q[-1])))
            ok=bool((j>.5).all() and (np.diff(t)>0).all() and (np.diff(t)<=20).all() and q[-1]>=9 and len(p)>20)
            keep=np.unique(np.r_[0,np.arange(0,len(t),3),len(t)-1])
            e=dict(id=c['panel']+'_'+c['start'].isoformat(),file=file,panel=c['panel'],T=c['T'],start=c['start'].isoformat(),end=c['end'].isoformat(),available_after=(post.timestamp.iat[-1].isoformat() if len(post) else c['end'].isoformat()),
                   t=t[keep],q=q[keep],j=j[keep],y=p[CELLS].to_numpy(float)[keep],pack=p.pack_voltage_V.to_numpy(float)[keep],temperature=p.temp_mean_C.to_numpy(float)[keep],
                   pre_t=pre_t,pre_y=pre[CELLS].to_numpy(float),post_t=post_t,post_y=post[CELLS].to_numpy(float),
                   q_total=float(q[-1]),net_since_anchor_Ah=net,anchor_age_h=age,chain_ok=chain_ok,chain_id=chain_id,anchor_end=anchor['end'] if anchor else None,raw_start_index=first,raw_end_index=last,
                   anchor_tail_A=anchor['tail_A'] if anchor else None,anchor_cell_spread_mV=anchor['cell_spread_mV'] if anchor else None,
                   temp_mean=float(p.temp_mean_C.mean()),temp_span=float(p.temp_mean_C.max()-p.temp_mean_C.min()),max_gap_s=float(np.diff(t).max()),raw_rows=len(p))
            ledger.append({k:e[k] for k in ['id','file','panel','T','start','end','available_after','q_total','net_since_anchor_Ah','anchor_age_h','chain_ok','chain_id','anchor_end','anchor_tail_A','anchor_cell_spread_mV','temp_mean','temp_span','max_gap_s','raw_rows']}|dict(qualified=ok,reason='accepted_raw_sign_time_span' if ok else 'raw_quality_failure',pre_rest_s=float(pre_t[-1]-pre_t[0]) if len(pre_t)>1 else 0,post_rest_s=float(post_t[-1]-post_t[0]) if len(post_t)>1 else 0))
            if ok:events.append(e)
        print('audit',file,flush=True)
    events.sort(key=lambda e:e['start'])
    # Whole anchor chains stay on one side of each panel/T split.
    for panel in ['short','wide']:
        for T in [25,45]:
            group=[e for e in events if e['panel']==panel and e['T']==T];n=max(2,int(.4*len(group)))
            devchains={e['chain_id'] for e in group[:n] if e['chain_id']!='unknown'}
            for k,e in enumerate(group):e['split']='development' if k<n or e['chain_id'] in devchains else 'evaluation'
    # Any cross-panel chain exposed in development is also development everywhere.
    exposed={e['chain_id'] for e in events if e['split']=='development' and e['chain_id']!='unknown'}
    for e in events:
        if e['chain_id'] in exposed:e['split']='development'
    mapping={e['id']:e['split'] for e in events}
    for row in ledger:row['split']=mapping.get(row.get('id'),'rejected')
    pd.DataFrame(ledger).to_csv(RUN/'event_ledger.csv',index=False)
    pd.DataFrame(anchors).to_csv(RUN/'charge_anchors.csv',index=False)
    pd.DataFrame(counter).to_csv(RUN/'counter_audit.csv',index=False)
    pd.DataFrame(gaps).to_csv(RUN/'gaps.csv',index=False)
    with open(RUN/'events.pkl','wb') as f:pickle.dump(events,f)
    registry=[dict(source='official',tier='O',entities=1,SOC_truth='absent',capacity_truth='CK0_only',accepted_use='raw_voltage_dynamics_and_reference_position',gap='hidden_followup_capacity_no_absolute_cell_OCV_SOC'),
              dict(source='synthetic_two_RC',tier='S',entities='20_fixed_seeds_per_scenario',SOC_truth='generator',capacity_truth='independent_reference_simulation',accepted_use='mechanism_only',gap='not_real_accuracy')]
    old=pd.read_csv(ROOT/'research/phase2_capacity_validation/outputs/data_eligibility.csv')
    for r in old.itertuples():
        if r.source_id.startswith('official'):continue
        registry.append(dict(source=r.source_id,tier='R_candidate',entities=r.physical_entities,SOC_truth='not_qualified',capacity_truth=r.capacity_label,accepted_use='inventory_only',gap=r.qualification_gap+'; no_independent_SOC_endpoint_and_OCV_calibration_in_registered_local_evidence'))
    pd.DataFrame(registry).to_csv(TASK/'data_registry.csv',index=False)
    paths=[TASK/'START_PROMPT.md',TASK/'protocol.md',TASK/'configs/frozen_protocol.json',Path(__file__),ROOT/'data/DATA_DESCRIPTION.md',ROOT/'data/checkups/CK0_reference_discharge.csv.gz',ROOT/'data/checkups/checkup_capacities_released.csv',ROOT/'research/phase2_method_exploration/outputs/event_catalog.csv',ROOT/'research/charge_capacity_review_20261006/operating_events.csv',*sorted((ROOT/'data/operation').glob('*.csv.gz'))]
    (RUN/'source_manifest.json').write_text(json.dumps([dict(path=str(p.relative_to(ROOT)),sha256=digest(p),bytes=p.stat().st_size) for p in paths],indent=2))
    print(pd.DataFrame(ledger).groupby(['panel','T','split']).size().to_string(),flush=True)
    return events

if __name__=='__main__':audit()
