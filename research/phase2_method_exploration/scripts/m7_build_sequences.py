"""Rebuild D1 20Ah native P1 sequences from original rows, without labels."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M7_sequences_v1';OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(ROOT/'research/phase2_temperature_improvement/src'))
from event_core import extract_charge_events
from route_a_repaired import stable_cc_prefix
cfg=json.loads((TASK/'configs/m7_representation.json').read_text())
view=pd.read_csv(TASK/'data_manifests/d1_target_visibility.csv')
view=view.loc[view.budget_Ah.eq(20)&view.history_mode.eq('persistent')]
assert len(view)==180
wanted={e for field in view.allowed_event_ids_json for e in json.loads(field)}
crop=pd.read_csv(TASK/'data_manifests/d1_cropped_events.csv')
crop=crop.loc[crop.budget_Ah.eq(20)].set_index('event_id',verify_integrity=True)
L=cfg['max_native_samples'];ids=[];cells=[];array=[];lengths=[];records=[]
for cell in sorted(view.cell_id.unique()):
    needed={e for e in wanted if e.startswith(cell+'|')}
    cycles={int(e.split('|')[1]) for e in needed};parts=[]
    for path in sorted((ROOT/'dataset original'/cell).glob('*.csv')):
        for chunk in pd.read_csv(path,usecols=['absolute_time','cycle_number','step_type','voltage_V','current_A','temperature_C'],chunksize=100000):
            q=chunk.loc[chunk.cycle_number.isin(cycles)&~chunk.step_type.eq('cc_discharge')]
            if len(q):parts.append(q.drop(columns='step_type'))
    raw=pd.concat(parts,ignore_index=True)
    raw['absolute_time']=pd.to_datetime(raw.absolute_time)
    raw=raw.sort_values('absolute_time',kind='stable').reset_index(drop=True)
    events=extract_charge_events(raw,time_col='absolute_time',voltage_cols=('voltage_V',),
                                 temp_col='temperature_C',segment_col='cycle_number',counter_col=None)
    found=set()
    for ev in events:
        eid=f'{cell}|{ev.segment}|{ev.start.isoformat()}|{ev.end.isoformat()}'
        if eid not in needed:continue
        found.add(eid)
        cc,status=stable_cc_prefix(ev);assert status=='pass' and cc is not None
        v=cc.voltages[:,0]
        crossing=np.flatnonzero((v[:-1]<3.50)&(v[1:]>=3.50));assert len(crossing)
        stop=int(crossing[0]+1);qstart=float(cc.q_ah[stop]-20)
        assert qstart>=0
        mask=(cc.q_ah>=qstart)&(np.arange(len(cc.q_ah))<=stop)
        time=cc.times_s[mask].astype(float);q=cc.q_ah[mask]-cc.q_ah[mask][0];V=v[mask]
        assert len(V)<=L,(eid,len(V))
        current=np.empty(len(V));current[1:]=3600*np.diff(q)/np.diff(time);current[0]=current[1]
        meta=crop.loc[eid]
        start=pd.Timestamp(int(time[0]),unit='s');end=pd.Timestamp(int(time[-1]),unit='s')
        assert start==pd.Timestamp(meta.fragment_start) and end==pd.Timestamp(meta.fragment_end)
        assert len(V)==int(meta.n_samples)
        assert abs(float(V[0])-float(meta.v_start_V))<1e-6
        assert abs(float(V[-1])-float(meta.v_end_V))<1e-6
        assert abs(float(q[-1])-float(meta.observed_span_Ah))<1e-6
        temp=float(meta.temperature_C) if pd.notna(meta.temperature_C) else np.nan
        out=np.zeros((L,5),np.float32);offset=L-len(V)
        out[offset:,0]=(V-3.45)/.1
        out[offset:,1]=current/100
        out[offset:,2]=temp/50 if np.isfinite(temp) else 0
        out[offset:,3]=q/20
        out[offset:,4]=1
        ids.append(eid);cells.append(cell);array.append(out);lengths.append(len(V))
        records.append({'event_id':eid,'cell_id':cell,'fragment_start':start.isoformat(),
                        'fragment_end':end.isoformat(),'n_native_samples':len(V),
                        'span_Ah':float(q[-1]),'native_median_dt_s':float(np.median(np.diff(time))),
                        'source_voltage_first_V':float(V[0]),'source_voltage_last_V':float(V[-1]),
                        'source_temperature_C':temp})
    assert found==needed,(cell,len(found),len(needed),list(needed-found)[:3])
    print(cell,'sequences',len(needed),flush=True)
assert len(ids)==len(wanted)==910
np.savez_compressed(OUT/'native_sequences.npz',event_ids=np.array(ids),cell_ids=np.array(cells),
                    X=np.stack(array),length=np.array(lengths,dtype=np.int16))
pd.DataFrame(records).to_csv(OUT/'sequence_manifest.csv',index=False)
summary={'events':len(ids),'physical_cells':len(set(cells)),'min_native_samples':min(lengths),
         'max_native_samples':max(lengths),'max_length_allocated':L,
         'data_sha256':hashlib.sha256((OUT/'native_sequences.npz').read_bytes()).hexdigest(),
         'label_columns_in_sequence_file':False,'no_upsampling':True,
         'source':'first raw 3.50V crossing; only native 30s points in trailing 20Ah'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
