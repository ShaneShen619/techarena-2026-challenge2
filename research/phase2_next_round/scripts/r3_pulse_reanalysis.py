"""Independent pulse/recovery evidence audit from frozen certified events."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OLD=ROOT/'research/phase2_method_exploration/runs/M1_voltage_forecast_v1'
pred=pd.read_csv(OLD/'forward_voltage_predictions.csv')
feat=pd.read_csv(OLD/'pulse_features.csv',parse_dates=['start'])
assert feat['start'].nunique()==41 and len(feat)==164

# Recompute waveform forecast scores and paired event-cell advantage.
pred['abs_mV']=pred.error_mV.abs()
score=pred.groupby(['method','chamber_C'],as_index=False).agg(MAE_mV=('abs_mV','mean'),P95_mV=('abs_mV',lambda s:s.quantile(.95)),points=('abs_mV','size'))
all_score=pred.groupby('method',as_index=False).agg(MAE_mV=('abs_mV','mean'),P95_mV=('abs_mV',lambda s:s.quantile(.95)),points=('abs_mV','size'))
event=pred.groupby(['start','cell','method'],as_index=False).abs_mV.mean()
pivot=event.pivot(index=['start','cell'],columns='method',values='abs_mV')
paired=(pivot['fixed_ECM']-pivot['matched_last_shift']).dropna()

# Recovery coverage and within-temperature temporal trends. Trends are diagnostics only.
features=['apparent_R_10s_mOhm','apparent_R_30s_mOhm','apparent_R_60s_mOhm','recovery_10s_V','recovery_30s_V','recovery_60s_V','v_q2_q10_slope_V_per_Ah']
coverage=[]
for name in features:
    coverage.append({'feature':name,'available':int(feat[name].notna().sum()),'total':len(feat),'coverage':float(feat[name].notna().mean())})
trends=[]
for (cell,temp),g in feat.sort_values('start').groupby(['cell','chamber_C']):
    t=(g.start-g.start.min()).dt.total_seconds().to_numpy()/86400
    for name in features:
        ok=np.isfinite(g[name].to_numpy(float))
        if ok.sum()<4: continue
        rho=float(spearmanr(t[ok],g.loc[ok,name]).statistic)
        slope=float(np.polyfit(t[ok],g.loc[ok,name].to_numpy(float),1)[0]) if np.ptp(t[ok])>0 else np.nan
        med=float(np.median(g.loc[ok,name])); mad=float(np.median(np.abs(g.loc[ok,name]-med)))
        trends.append({'cell':int(cell),'chamber_C':int(temp),'feature':name,'events':int(ok.sum()),'spearman_time':rho,'linear_slope_per_day':slope,'median':med,'MAD':mad})

# Event-level block bootstrap: does simple curve reuse improve voltage prediction?
rng=np.random.default_rng(20260929); starts=np.array(sorted(pred.start.unique())); boots=[]
for _ in range(2000):
    take=rng.choice(starts,size=len(starts),replace=True)
    values=[]
    for s in take:
        idx=(event.start==s)
        p=event.loc[idx].pivot(index='cell',columns='method',values='abs_mV')
        if {'fixed_ECM','matched_last_shift'}.issubset(p.columns): values.extend((p.fixed_ECM-p.matched_last_shift).dropna())
    boots.append(float(np.mean(values)))

score.to_csv(TASK/'outputs/r3_voltage_scores_by_temperature.csv',index=False)
all_score.to_csv(TASK/'outputs/r3_voltage_scores_all.csv',index=False)
pd.DataFrame(coverage).to_csv(TASK/'outputs/r3_recovery_coverage.csv',index=False)
pd.DataFrame(trends).to_csv(TASK/'outputs/r3_pulse_feature_trends.csv',index=False)
summary={'certified_pulses':int(feat.start.nunique()),'cell_events':len(feat),'future_forecast_cell_events':int(event[['start','cell']].drop_duplicates().shape[0]),
         'matched_last_shift_MAE_mV':float(all_score.loc[all_score.method.eq('matched_last_shift'),'MAE_mV'].iloc[0]),
         'fixed_ECM_MAE_mV':float(all_score.loc[all_score.method.eq('fixed_ECM'),'MAE_mV'].iloc[0]),
         'paired_mean_advantage_mV':float(paired.mean()),'event_block_bootstrap_advantage_95pct':[float(np.quantile(boots,.025)),float(np.quantile(boots,.975))],
         'recovery_60s_coverage':float(feat.recovery_60s_V.notna().mean()),
         'capacity_label_available':False,'capacity_increment_supported':False,
         'information_budget':'observe 0.2-1.0Ah of the target pulse, then forecast 2-10Ah of the same pulse using a matched prior pulse',
         'interpretation':'early target-pulse voltage plus a matched prior pulse predicts the later segment of that same pulse; no compatible capacity label links that information to SOH'}
(TASK/'outputs/r3_pulse_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(all_score.to_string(index=False)); print(json.dumps(summary,ensure_ascii=False))
