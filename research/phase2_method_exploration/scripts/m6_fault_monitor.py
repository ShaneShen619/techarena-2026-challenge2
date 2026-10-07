"""TU relative-resistance anomaly signal and synthetic persistent-fault injection."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M6_fault_monitor_v1';OUT.mkdir(parents=True,exist_ok=False)
cfg=json.loads((TASK/'configs/m6_fault.json').read_text())
source=TASK/'runs/M6_TU_steps_v1'
inv=pd.read_csv(source/'extraction_summary_by_system.csv')
systems=inv.loc[inv.selected_3h_ge10A.ge(100),'system'].astype(int).tolist()
all=[]
for sid in systems:
    d=pd.read_csv(source/f'system_{sid:02d}_events.csv',parse_dates=['timestamp'])
    d=d.loc[d.threshold_A.eq(10)&d.R_plausible].copy()
    # Each event has eight cells except when a cell-specific response fails
    # plausibility; other-cell median remains robust with >=6 valid cells.
    for time,g in d.groupby('timestamp'):
        rr=g.R_step_mOhm.to_numpy(float);cells=g.cell.to_numpy(int)
        for row,r,cell in zip(g.itertuples(index=False),rr,cells):
            other=np.median(rr[cells!=cell])
            all.append({'system':sid,'timestamp':time,'cell':cell,'R_step_mOhm':r,
                        'relative_R_mOhm':r-other,'valid_cells_at_step':len(g)})
signal=pd.DataFrame(all).sort_values(['system','cell','timestamp'])
signal.to_csv(OUT/'relative_step_signals.csv',index=False)
flags=[];injections=[]
for held in systems:
    training=signal.loc[signal.system.ne(held)]
    threshold=float(max(.3,training.relative_R_mOhm.quantile(.99)))
    target=signal.loc[signal.system.eq(held)]
    for cell,part in target.groupby('cell'):
        part=part.sort_values('timestamp').reset_index(drop=True)
        if len(part)<80:continue
        original=part.relative_R_mOhm.to_numpy(float)
        def alerts(values):
            med=pd.Series(values).rolling(5,min_periods=5).median().to_numpy()
            return np.isfinite(med)&(med>threshold)
        clean=alerts(original)
        for j,row in part.iterrows():
            flags.append({'system':held,'cell':cell,'timestamp':row.timestamp.isoformat(),
                          'relative_R_mOhm':original[j],'threshold_mOhm':threshold,
                          'alert':bool(clean[j]),'causal_prefix_events':j+1})
        onset=max(5,int(np.floor(cfg['injection_start_fraction']*len(part))))
        for amplitude in cfg['synthetic_injections_mOhm']:
            changed=original.copy();changed[onset:]+=amplitude
            injected=alerts(changed)
            later=np.flatnonzero(injected[onset:])
            first=int(onset+later[0]) if len(later) else None
            injections.append({'system':held,'cell':cell,'n':len(part),'threshold_mOhm':threshold,
                               'injection_mOhm':amplitude,'start_index':onset,
                               'detected_after_injection':first is not None,
                               'delay_events':first-onset if first is not None else None,
                               'clean_alert_fraction':float(clean.mean()),
                               'clean_alert_fraction_before_onset':float(clean[:onset].mean()),
                               'injected_alert_fraction_after_onset':float(injected[onset:].mean()),
                               'incremental_alert_fraction_after_onset':float(injected[onset:].mean()-clean[onset:].mean())})
f=pd.DataFrame(flags);f.to_csv(OUT/'causal_alerts.csv',index=False)
inj=pd.DataFrame(injections);inj.to_csv(OUT/'synthetic_injection_results.csv',index=False)
summary={'systems':len(systems),'cell_streams':int(f[['system','cell']].drop_duplicates().shape[0]),
         'unmodified_alert_fraction_unverified':float(f.alert.mean()),
         'injection_results':[
             {'amplitude_mOhm':float(a),'streams':len(g),
              'detected_fraction':float(g.detected_after_injection.mean()),
              'median_delay_events_when_detected':float(g.delay_events.median()),
              'mean_incremental_alert_fraction':float(g.incremental_alert_fraction_after_onset.mean())}
             for a,g in inj.groupby('injection_mOhm')],
         'truth_limit':'Original TU anomalies are not labeled; unmodified alerts are not verified false/true positives. Injected effects are synthetic.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
