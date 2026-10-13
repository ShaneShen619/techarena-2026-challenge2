"""Re-certify raw events, charge/CV anchors, direction-aware charge ledger."""
from __future__ import annotations
import json, pickle
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid
from common import TASK,ROOT,OUT,CFG,CELLS,digest,json_dump,environment,seconds,protected_paths

def clean(df):
    return df.sort_values('timestamp',kind='stable').drop_duplicates('timestamp',keep='last').reset_index(drop=True)

def rest_ids(raw,idx,step):
    ids=[]; previous=None
    while 0<=idx<len(raw) and abs(raw.current_A.iat[idx])<=CFG['current_active_A']:
        if previous is not None and not 0<abs((raw.timestamp.iat[idx]-raw.timestamp.iat[previous]).total_seconds())<=CFG['maximum_gap_s']:break
        ids.append(idx);previous=idx;idx+=step
    return sorted(ids)

def integrate(df):
    return cumulative_trapezoid(-df.current_A.to_numpy(float),seconds(df.timestamp),initial=0)/3600

def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'EVALUATION_COMPLETE').exists():raise RuntimeError('Completed run is immutable. Set ECM_RUN_ID to a new run.')
    catalog=ROOT/'research/phase2_method_exploration/outputs/event_catalog.csv'
    source=ROOT/'research/charge_capacity_review_20261006/operating_events.csv'
    old=pd.read_csv(catalog,parse_dates=['event_start','event_end'])
    op=pd.read_csv(source,parse_dates=['t_start','t_end'])
    candidates=[dict(file=r.source_file,start=r.event_start,end=r.event_end,panel='short',T=int(r.temperature_C))
        for r in old[old.quality_status.eq('certified')&old.before_CK7].itertuples()]
    candidates += [dict(file=r.file,start=r.t_start,end=r.t_end,panel='wide',T=int(r.setpoint_C))
        for r in op[op.kind.eq('long_dynamic_discharge')&op.Q_Ah.between(32.7,33)&(op.t_end<pd.Timestamp(CFG['operation_end']))].itertuples()]
    events=[];audit=[];anchors=[];gaps=[];stages=[];counter=[];charge_trend=[]
    manifests=[catalog,source,ROOT/'data/DATA_DESCRIPTION.md',ROOT/'data/checkups/CK0_reference_discharge.csv.gz',ROOT/'data/checkups/checkup_capacities_released.csv',
        ROOT/'data/checkups/evaluation_points.csv',TASK/'configs/protocol.json',ROOT/'research/phase2_routes23_prompts_20261012/方案2_四串动态模型与容量联合估计_执行Prompt.md']
    json_dump(OUT/'protected_before.json',[dict(path=str(p.relative_to(ROOT)),sha256=digest(p)) for p in protected_paths() if p.is_file()])
    for file in sorted({c['file'] for c in candidates}):
        path=ROOT/'data/operation'/file; manifests.append(path)
        original=pd.read_csv(path,parse_dates=['timestamp'])
        # Preserve transition duplicates until the physical stage is selected.
        # A global keep-last would erase the last charged/discharged sample.
        raw=original[original.timestamp<=pd.Timestamp(CFG['operation_end'])].sort_values('timestamp',kind='stable').reset_index(drop=True)
        tt=seconds(raw.timestamp)
        for k in np.flatnonzero(np.diff(tt)>CFG['maximum_gap_s']):gaps.append(dict(file=file,start=str(raw.timestamp.iat[k]),end=str(raw.timestamp.iat[k+1]),gap_s=float(tt[k+1]-tt[k])))
        aa=[]
        for a in op[op.file.eq(file)&op.kind.eq('full_charge')&(op.t_end<pd.Timestamp(CFG['operation_end']))].itertuples():
            charge=clean(original.iloc[int(a.start_index_in_file):int(a.end_index_in_file)+1])
            cv=charge[(charge.pack_voltage_V>=CFG['anchor_pack_min_V'])&(charge.current_A>CFG['current_active_A'])]
            duration=float((cv.timestamp.iat[-1]-cv.timestamp.iat[0]).total_seconds()) if len(cv)>1 else 0
            continuous=bool(len(charge)>1 and (np.diff(seconds(charge.timestamp))<=CFG['maximum_gap_s']).all())
            qualified=bool(continuous and charge.current_A.ge(CFG['current_active_A']).all() and charge.pack_voltage_V.iat[-1]>=CFG['anchor_pack_min_V'] and charge.current_A.iat[-1]<=CFG['anchor_tail_max_A'] and duration>=CFG['anchor_min_cv_s'])
            at=int(raw.index[raw.timestamp.eq(a.t_end)&raw.current_A.gt(.5)][-1])
            anchor=dict(file=file,start=a.t_start.isoformat(),end=a.t_end.isoformat(),qualified=qualified,end_index=at,
                cv_s=duration,tail_A=float(charge.current_A.iat[-1]),spread_mV=float(charge[CELLS].iloc[-1].max()-charge[CELLS].iloc[-1].min())*1000)
            anchors.append(anchor);aa.append(anchor)
            if len(cv):stages.append(dict(file=file,phase='CV',start=cv.timestamp.iat[0].isoformat(),end=cv.timestamp.iat[-1].isoformat(),rows=len(cv),Ah=float(-integrate(cv)[-1]),qualified=qualified))
            cc=charge[charge.timestamp<(cv.timestamp.iat[0] if len(cv) else a.t_end)]
            if len(cc)>1:stages.append(dict(file=file,phase='CC',start=cc.timestamp.iat[0].isoformat(),end=cc.timestamp.iat[-1].isoformat(),rows=len(cc),Ah=float(-integrate(cc)[-1]),qualified=continuous))
            cq=-integrate(charge)
            record=dict(anchor_id=file+'|'+a.t_end.isoformat(),end=a.t_end.isoformat(),T=int(a.setpoint_C),qualified=qualified,cv_s=duration,tail_A=anchor['tail_A'])
            for c in range(4):
                # Predetermined A-like charging windows, not tuned by target trends.
                vals=[];v=charge[CELLS[c]].to_numpy(float)
                for center in [3.36,3.40,3.44,3.48]:
                    idx=np.flatnonzero((v>=center-.005)&(v<=center+.005)&(charge.current_A.to_numpy()>0.5))
                    if len(idx)>=3 and (np.diff(seconds(charge.timestamp)[idx])<=20).all():vals.append(float(cq[idx[-1]]-cq[idx[0]]))
                record[f'A_cell{c+1}_Ah']=float(np.mean(vals)) if vals else None
                record[f'A_cell{c+1}_window_count']=len(vals)
            charge_trend.append(record)
        for c in [c for c in candidates if c['file']==file]:
            iz0=np.flatnonzero(raw.timestamp.eq(c['start'])&raw.current_A.lt(-.5));iz1=np.flatnonzero(raw.timestamp.eq(c['end'])&raw.current_A.lt(-.5))
            if not len(iz0) or not len(iz1):audit.append(dict(id=c['panel']+'_'+c['start'].isoformat(),qualified=False,reason='raw_boundary_absent'));continue
            first,last=int(iz0[0]),int(iz1[-1]);p=clean(raw.iloc[first:last+1])
            t=seconds(p.timestamp);q=integrate(p)
            pre_ids=rest_ids(raw,first-1,-1);post_ids=rest_ids(raw,last+1,1)
            pre_ids=[k for k in pre_ids if raw.timestamp.iat[k]<c['start']]
            post_ids=[k for k in post_ids if raw.timestamp.iat[k]>c['end']]
            pre=clean(raw.iloc[pre_ids]);post=clean(raw.iloc[post_ids])
            previous=[a for a in aa if a['qualified'] and pd.Timestamp(a['end'])<=c['start']]
            anchor=previous[-1] if previous else None
            chain_ok=False;net=np.nan;history_begin=first;offsets=None
            if anchor:
                chain=clean(raw.iloc[anchor['end_index']:first+1])
                age_h=(c['start']-pd.Timestamp(anchor['end'])).total_seconds()/3600
                chain_ok=bool((np.diff(seconds(chain.timestamp))<=20).all() and age_h<=CFG['anchor_max_age_h'])
                if chain_ok:
                    net=float(integrate(chain)[-1])
                    history_begin=int(raw.timestamp.searchsorted(pd.Timestamp(anchor['end'])-pd.Timedelta(seconds=CFG['history_burn_in_s'])))
                    # Burn-in cannot cross recording gaps.
                    bad=np.flatnonzero(np.diff(seconds(raw.timestamp.iloc[history_begin:anchor['end_index']+1]))>20)
                    if len(bad):history_begin+=int(bad[-1])+1
            obs_ids=np.r_[pre_ids,np.arange(first,last+1),post_ids].astype(int)
            obs_phase=np.where(obs_ids<first,0,np.where(obs_ids<=last,1,2))
            selected=[]
            for phase in range(3):
                ids=obs_ids[obs_phase==phase]
                if phase!=1 and len(ids):
                    st=raw.timestamp.iat[ids[0]];en=raw.timestamp.iat[ids[-1]]
                    if phase==0:ids=ids[raw.timestamp.iloc[ids]>=en-pd.Timedelta(seconds=CFG['fit_rest_budget_s'])]
                    else:ids=ids[raw.timestamp.iloc[ids]<=st+pd.Timedelta(seconds=CFG['fit_rest_budget_s'])]
                selected.extend(ids[::CFG['observation_stride']].tolist())
            obs_ids=np.unique(np.r_[selected,first,last]);obs=clean(raw.iloc[obs_ids])
            hist_end=int(obs_ids[-1]);history_begin=min(history_begin,int(obs_ids[0]))
            hist=clean(pd.concat([raw.iloc[history_begin:hist_end+1],obs],ignore_index=True))
            htime=seconds(hist.timestamp)
            hobs=np.searchsorted(hist.timestamp.to_numpy(),obs.timestamp.to_numpy())
            hnet=integrate(hist)
            if chain_ok:
                anchor_offset=int(hist.timestamp.searchsorted(pd.Timestamp(anchor['end'])));hnet-=hnet[anchor_offset]
            else:hnet-=hnet[int(hist.timestamp.searchsorted(c['start']))]
            phase=np.where(obs.timestamp<c['start'],0,np.where(obs.timestamp<=c['end'],1,2))
            qobs=np.interp(seconds(obs.timestamp,c['start']),t,q,left=0,right=q[-1])
            phase=phase.astype(int)
            signed_good=bool(p.current_A.lt(-.5).all());times_good=bool((np.diff(t)>0).all() and (np.diff(t)<=20).all())
            ok=bool(signed_good and times_good and q[-1]>9 and len(p)>20)
            e=dict(id=c['panel']+'_'+c['start'].isoformat(),file=file,panel=c['panel'],T=c['T'],start=c['start'].isoformat(),end=c['end'].isoformat(),
                available_after=obs.timestamp.iat[-1].isoformat(),qualified=ok,chain_ok=chain_ok,anchor_end=anchor['end'] if anchor else None,
                chain_id=file+'|'+anchor['end'] if anchor and chain_ok else 'unknown_'+c['start'].isoformat(),net_since_anchor_Ah=net,
                q_total=float(q[-1]),t=seconds(obs.timestamp,c['start']),q=qobs,j=-obs.current_A.to_numpy(float),phase=phase,
                y=obs[CELLS].to_numpy(float),pack=obs.pack_voltage_V.to_numpy(float),temp=obs.temp_mean_C.to_numpy(float),
                htime=htime,hj=-hist.current_A.to_numpy(float),hobs=hobs,net=hnet[hobs],history_timestamp_start=hist.timestamp.iat[0].isoformat(),
                pre_duration_s=float((pre.timestamp.iat[-1]-pre.timestamp.iat[0]).total_seconds()) if len(pre)>1 else 0,
                post_duration_s=float((post.timestamp.iat[-1]-post.timestamp.iat[0]).total_seconds()) if len(post)>1 else 0,
                raw_rows=len(p),raw_max_gap_s=float(np.diff(t).max()),actual_T=float(p.temp_mean_C.mean()),
                anchor_burn_in_s=float((pd.Timestamp(anchor['end'])-hist.timestamp.iat[0]).total_seconds()) if anchor and chain_ok else 0)
            e['split']='development' if pd.Timestamp(e['available_after'])<pd.Timestamp(CFG['development_until']) else 'evaluation'
            e['daily_link_status']='continuous' if chain_ok else 'unqualified_anchor_or_gap'
            row={k:v for k,v in e.items() if not isinstance(v,np.ndarray)}
            row['reason']='accepted_raw_sign_time_span' if ok else 'raw_quality_failure'
            row['pack_sum_median_mV']=float((p.pack_voltage_V-p[CELLS].sum(axis=1)).median()*1000)
            audit.append(row)
            d=p[['charge_Ah_cum','discharge_Ah_cum']].iloc[-1]-p[['charge_Ah_cum','discharge_Ah_cum']].iloc[0]
            counter.append(dict(id=e['id'],integral_Ah=float(q[-1]),charge_delta_Ah=float(d.iloc[0]),discharge_delta_Ah=float(d.iloc[1]),sum_residual_Ah=float(d.sum()-q[-1])))
            for ph,name in [(0,'pre_rest'),(1,'discharge'),(2,'post_rest')]:
                use=phase==ph
                if use.any():stages.append(dict(file=file,event_id=e['id'],phase=name,start=(pd.Timestamp(e['start'])+pd.Timedelta(seconds=float(e['t'][use][0]))).isoformat(),end=(pd.Timestamp(e['start'])+pd.Timedelta(seconds=float(e['t'][use][-1]))).isoformat(),rows=int(use.sum()),Ah=float(q[-1]) if ph==1 else 0,qualified=ok))
            if ok:events.append(e)
        print('certified raw',file,flush=True)
    events.sort(key=lambda e:e['start'])
    # Prevent development/evaluation chains crossing the fixed calendar boundary.
    dev_chains={e['chain_id'] for e in events if e['split']=='development'}
    for e in events:
        if e['split']=='evaluation' and e['chain_id'] in dev_chains:e['split']='boundary_buffer'
    mapping={e['id']:e['split'] for e in events}
    for row in audit:row['split']=mapping.get(row['id'],'rejected')
    pd.DataFrame(audit).to_csv(OUT/'event_ledger.csv',index=False)
    pd.DataFrame(anchors).to_csv(OUT/'charge_anchors.csv',index=False)
    pd.DataFrame(stages).to_csv(OUT/'stages.csv',index=False)
    pd.DataFrame(counter).to_csv(OUT/'counter_audit.csv',index=False)
    pd.DataFrame(gaps).to_csv(OUT/'gaps.csv',index=False)
    pd.DataFrame(charge_trend).to_csv(OUT/'A_charge_windows.csv',index=False)
    pd.DataFrame([dict(id=e['id'],start=e['start'],available_after=e['available_after'],split=e['split'],chain_id=e['chain_id']) for e in events]).to_csv(OUT/'split_manifest.csv',index=False)
    with (OUT/'events.pkl').open('wb') as f:pickle.dump(events,f)
    json_dump(OUT/'data_manifest.json',[dict(path=str(p.relative_to(ROOT)),sha256=digest(p),bytes=p.stat().st_size) for p in manifests])
    json_dump(OUT/'environment.json',environment())
    summary=dict(events=len(events),continuous_anchor_events=sum(e['chain_ok'] for e in events),physical_packs=1,
        split_counts=pd.DataFrame(audit).groupby(['panel','T','split']).size().to_dict())
    summary['split_counts']={str(k):v for k,v in summary['split_counts'].items()}
    json_dump(OUT/'audit_summary.json',summary)
    print(summary,flush=True)
    return events

def load():
    with (OUT/'events.pkl').open('rb') as f:return pickle.load(f)

if __name__=='__main__':prepare()
