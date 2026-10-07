"""Full 28-system chunked TU step-response extraction with active-balancing filter."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M6_TU_steps_v1';OUT.mkdir(parents=True,exist_ok=False)
cfg=json.loads((TASK/'configs/m6_step_extraction.json').read_text())
cols=['Timestamp','I_Battery','SOC_Battery',*[f'Temperature_{i}' for i in range(1,5)],
      *[f'I_CNV_Cell_{i}' for i in range(1,9)],*[f'U_Cell_{i}' for i in range(1,9)]]
thresholds=[5,10,20];summaries=[]
for sysid in range(1,29):
    path=ROOT/'TU Darmstadt'/f'data_sys_{sysid}.csv'
    seen={t:set() for t in thresholds};selected={t:[] for t in thresholds}
    counts={t:0 for t in thresholds};accepted={t:0 for t in thresholds}
    rows=0;dups=0;gaps=0;reversed_time=0;balanced_steps=0;unphysical=0
    last=None
    for chunk in pd.read_csv(path,usecols=cols,chunksize=250000):
        rows+=len(chunk)
        f=pd.concat([last,chunk],ignore_index=True) if last is not None else chunk
        last=f.tail(1).copy()
        ts=pd.to_datetime(f.Timestamp,errors='coerce').to_numpy(dtype='datetime64[s]').astype('int64')
        dt=np.diff(ts)
        dups+=int(np.sum(dt==0));gaps+=int(np.sum(dt>100));reversed_time+=int(np.sum(dt<0))
        I=f.I_Battery.to_numpy(float);dI=np.diff(I)
        soc=f.SOC_Battery.to_numpy(float)
        temp=f[[f'Temperature_{i}' for i in range(1,5)]].to_numpy(float).mean(axis=1)
        bal=np.nanmax(np.abs(f[[f'I_CNV_Cell_{i}' for i in range(1,9)]].to_numpy(float)),axis=1)>.05
        voltage=f[[f'U_Cell_{i}' for i in range(1,9)]].to_numpy(float)
        base=((dt>=1)&(dt<=10)&(I[1:]>-200)&(I[1:]<-5)&(I[:-1]<.5)&
             (soc[1:]>40)&(soc[1:]<94)&(temp[1:]>10)&(temp[1:]<100)&
             (~bal[1:])&(~bal[:-1])&(dI<=-5))
        # Adjacent voltage validity is checked before temporal thinning.
        index=np.flatnonzero(base)+1
        for j in index:
            step=float(dI[j-1]);v0=voltage[j-1];v1=voltage[j]
            if not np.isfinite(v0).all() or not np.isfinite(v1).all() or not np.all((v0>2)&(v0<3.7)&(v1>2)&(v1<3.7)):
                unphysical+=1;continue
            R=(v1-v0)/step*1000
            plausible=np.isfinite(R)&(R>0)&(R<10)
            if plausible.sum()<6:continue
            bucket=int(ts[j]//(3*3600))
            for threshold in thresholds:
                if step>-threshold:continue
                counts[threshold]+=1
                if bucket in seen[threshold]:continue
                seen[threshold].add(bucket);accepted[threshold]+=1
                for cell in range(8):
                    selected[threshold].append({'system':sysid,'threshold_A':threshold,
                        'timestamp':pd.Timestamp(ts[j],unit='s').isoformat(),
                        'cell':cell+1,'I_before_A':float(I[j-1]),'I_after_A':float(I[j]),
                        'delta_I_A':step,'SOC_BMS_pct':float(soc[j]),'temperature_C':float(temp[j]),
                        'v_before_V':float(v0[cell]),'v_after_V':float(v1[cell]),
                        'R_step_mOhm':float(R[cell]),'R_plausible':bool(plausible[cell]),
                        'step_interval_s':int(dt[j-1]),'sample_time_bin_3h':bucket})
    combined=[x for threshold in thresholds for x in selected[threshold]]
    out=pd.DataFrame(combined)
    out.to_csv(OUT/f'system_{sysid:02d}_events.csv',index=False)
    summaries.append({'system':sysid,'raw_rows':rows,'duplicate_timestamps':dups,
                      'gaps_gt100s':gaps,'negative_time_jumps':reversed_time,
                      'voltage_invalid_step_candidates':unphysical,
                      **{f'candidates_ge{t}A':counts[t] for t in thresholds},
                      **{f'selected_3h_ge{t}A':accepted[t] for t in thresholds},
                      **{f'plausible_cell_rows_ge{t}A':int(sum(x['R_plausible'] for x in selected[t])) for t in thresholds}})
    print(f'TU {sysid:02d} rows={rows} raw10={counts[10]} kept10={accepted[10]}',flush=True)
pd.DataFrame(summaries).to_csv(OUT/'extraction_summary_by_system.csv',index=False)
summary={'systems':28,'raw_rows':int(sum(x['raw_rows'] for x in summaries)),
         'selected_3h_10A_events':int(sum(x['selected_3h_ge10A'] for x in summaries)),
         'systems_with_at_least_100_10A_events':int(sum(x['selected_3h_ge10A']>=100 for x in summaries)),
         'selected_3h_5A_events':int(sum(x['selected_3h_ge5A'] for x in summaries)),
         'selected_3h_20A_events':int(sum(x['selected_3h_ge20A'] for x in summaries)),
         'duplicate_timestamps':int(sum(x['duplicate_timestamps'] for x in summaries)),
         'gaps_gt100s':int(sum(x['gaps_gt100s'] for x in summaries)),
         'negative_time_jumps':int(sum(x['negative_time_jumps'] for x in summaries)),
         'resistance_definition':cfg['cell_response'],'capacity_labels':False}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
