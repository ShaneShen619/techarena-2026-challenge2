"""Rebuild baseline event windows and audit checkpoint causality; writes only TASK."""
import csv
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from framework.data import load_dataset
from my_model.model_example import ExampleModel, full_charge_events, I_END, MAX_BACK, V_FULL, V_LO


def audit_events(op):
    ts = op.timestamp.values.astype('datetime64[s]').astype('int64')
    I = op.current_A.to_numpy(float)
    U = op.pack_voltage_V.to_numpy(float)
    seg = op.segment.to_numpy()
    dt_raw = np.diff(ts, prepend=ts[0]).astype(float)
    dt = dt_raw.copy()
    dt[(dt > 600) | (dt < 0)] = 0
    ah = np.maximum(I * dt / 3600, 0)
    hi = U >= V_FULL
    ends = np.where(hi & (I < I_END) & (np.r_[False, I[:-1] >= 5] | np.r_[False, hi[:-1]]))[0]
    ends = ends[np.r_[True, np.diff(ends) > 60]] if len(ends) else ends
    rows = []
    for e in ends:
        j = e
        while j > 0 and I[j] > -0.5 and U[j] >= V_LO and seg[j] == seg[e] and e-j < MAX_BACK:
            j -= 1
        if e-j < 30 or U[j] > V_LO+0.05:
            continue
        w = op.iloc[j:e+1]
        d = dt_raw[j:e+1]
        positive = I[j:e+1] > 0
        rows.append(dict(event_id=len(rows), segment=int(seg[e]), start_index=int(j), end_index=int(e),
            t_start=str(op.timestamp.iloc[j]), t_end=str(op.timestamp.iloc[e]), n_rows=int(e-j+1),
            Q_partial_Ah=float(ah[j:e+1].sum()), pack_start_V=float(U[j]), pack_end_V=float(U[e]),
            current_start_A=float(I[j]), current_end_A=float(I[e]), negative_rows=int((I[j:e+1]<0).sum()),
            below_13p4_rows=int((U[j:e+1]<V_LO).sum()), positive_charge_Ah=float(ah[j:e+1][positive].sum()),
            max_gap_s=float(np.max(d)), gap_gt_60_count=int((d>60).sum()), gap_gt_600_count=int((d>600).sum()),
            repeated_timestamp_count=int((d==0).sum()), negative_dt_count=int((d<0).sum()),
            segment_count=int(w.segment.nunique()), temp_mean_C=float(w.temp_mean_C.mean()),
            temp_min_C=float(w.temp_mean_C.min()), temp_max_C=float(w.temp_mean_C.max()),
            pack_cell_sum_residual_max_V=float(np.abs(w[[f'cell{k}_V' for k in range(1,5)]].sum(axis=1)-w.pack_voltage_V).max()),
            charge_counter_delta_Ah=float(w.charge_Ah_cum.iloc[-1]-w.charge_Ah_cum.iloc[0]),
            discharge_counter_delta_Ah=float(w.discharge_Ah_cum.iloc[-1]-w.discharge_Ah_cum.iloc[0]),
            end_CV_evidence=bool(U[e]>=V_FULL and I[e]<I_END),
            prestart_index=int(j-1) if j>0 else None,
            prestart_pack_V=float(U[j-1]) if j>0 else None,
            prestart_current_A=float(I[j-1]) if j>0 else None,
            prestart_segment=int(seg[j-1]) if j>0 else None))
    out=pd.DataFrame(rows)
    ref=full_charge_events(op)
    assert len(out)==len(ref)
    assert np.allclose(out.Q_partial_Ah,ref.Q_partial_Ah,atol=1e-9)
    assert (pd.to_datetime(out.t_end).reset_index(drop=True)==ref.t_end.reset_index(drop=True)).all()
    return out


def main():
    run=TASK/'runs/B1_event_causality_20260930_v1';run.mkdir(exist_ok=True)
    ds=load_dataset(ROOT/'data')
    op=ds.operation
    ev=audit_events(op)
    ev.to_csv(TASK/'outputs/event_audit.csv',index=False)
    ev.to_csv(run/'event_audit.csv',index=False)
    full=ExampleModel();full.fit(ds)
    ckrows=[];future=[]
    for ck in ds.eval_points.itertuples():
        cutoff=pd.Timestamp(ck.date)
        prefix=op[op.timestamp<=cutoff].reset_index(drop=True)
        ds.operation=prefix
        pm=ExampleModel();pm.fit(ds)
        pe=full_charge_events(prefix)
        first=pe[pe.segment==pe.segment.min()] if len(pe) else pe
        latest=float(pe.tail(3).Q_partial_Ah.median()) if len(pe) else None
        ckrows.append(dict(checkup=ck.checkup,date=str(cutoff),n_operation_rows=len(prefix),n_events=len(pe),
            n_first_segment_events=len(first),q_ref_full_Ah=full.q_ref,q_ref_prefix_Ah=pm.q_ref,
            latest3_median_Ah=latest,SOH_full_fit_pct=full.estimate_soh(ds,cutoff),
            SOH_prefix_fit_pct=pm.estimate_soh(ds,cutoff),
            fit_future_leak=bool(pm.q_ref is not None and full.q_ref!=pm.q_ref)))
        # Re-fit with deletion, shuffle, and extreme corruption strictly after cutoff.
        if ck.checkup!='CK7':
            after=op[op.timestamp>cutoff]
            changed=op.copy()
            ix=changed.index[changed.timestamp>cutoff]
            changed.loc[ix,'current_A']=1e6
            changed.loc[ix,'pack_voltage_V']=14.1
            ds.operation=changed
            extreme=ExampleModel();extreme.fit(ds)
            ds.operation=prefix
            future.append(dict(checkup=ck.checkup,full_q_ref=full.q_ref,deleted_q_ref=pm.q_ref,
                extreme_q_ref=extreme.q_ref,full_prediction=full.estimate_soh(ds,cutoff),
                deleted_prediction=pm.estimate_soh(ds,cutoff),extreme_prediction=extreme.estimate_soh(ds,cutoff),
                n_future_rows=len(after)))
    pd.DataFrame(ckrows).to_csv(TASK/'outputs/per_ck_reference_audit.csv',index=False)
    pd.DataFrame(future).to_csv(run/'future_mutations.csv',index=False)
    # Probe raw start/end context for two anomalies and a normal event.
    exemplar=pd.concat([ev.iloc[[0,1,5,7,39]],ev.nlargest(2,'Q_partial_Ah')]).drop_duplicates('event_id')
    raw=[]
    for r in exemplar.itertuples():
        for idx in sorted(set([r.start_index-2,r.start_index-1,r.start_index,r.start_index+1,r.end_index-1,r.end_index,r.end_index+1])):
            if 0<=idx<len(op):
                q=op.iloc[idx]
                raw.append(dict(event_id=r.event_id,index=idx,timestamp=q.timestamp,segment=q.segment,current_A=q.current_A,
                    pack_voltage_V=q.pack_voltage_V,charge_Ah_cum=q.charge_Ah_cum,discharge_Ah_cum=q.discharge_Ah_cum,
                    temp_mean_C=q.temp_mean_C))
    pd.DataFrame(raw).to_csv(TASK/'outputs/anomaly_raw_rows.csv',index=False)
    result=dict(n_operation_rows=len(op),n_events=len(ev),q_ref_full_Ah=full.q_ref,
        anomalous=ev.nlargest(2,'Q_partial_Ah')[['event_id','t_start','t_end','Q_partial_Ah','n_rows','max_gap_s','segment_count','negative_rows','below_13p4_rows']].to_dict('records'))
    (run/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    (run/'COMPLETED').write_text('completed\n')
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__': main()
