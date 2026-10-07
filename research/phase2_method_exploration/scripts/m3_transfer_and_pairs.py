"""Thermal-surface transfer check and actual temperature-pair inventory."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M3_transfer_pairs_v1'
OUT.mkdir(parents=True,exist_ok=False)
cfg=json.loads((TASK/'configs/m3_validation.json').read_text())
provenance=ROOT/'research/phase2_temperature_improvement/outputs/thermal_provenance.json'
first=json.loads(provenance.read_text())
theta=np.asarray(first['full_six_cell_theta_diagnostic_only'],float)
def t_eff(t,c):
    floor,k,sigma=theta
    u=t+k*c*c
    return .5*(u+floor+np.sqrt((u-floor)**2+sigma**2))

official=pd.read_csv(TASK/'data_manifests/official_charge_support.csv')
official=official.loc[official.cc_Ah<50].copy()
official['chamber_C']=official.file.str.extract(r'_(25|45)degC').astype(float)
official['nominal_charge_c_rate']=official.current_A/102
official['first_phase_pred_C']=[t_eff(t,c) for t,c in zip(official.chamber_C,official.nominal_charge_c_rate)]
official['transfer_error_C']=official.first_phase_pred_C-official.temp_C
official.to_csv(OUT/'official_charge_transfer.csv',index=False)
perT=official.groupby('chamber_C').transfer_error_C.agg(['size','median',lambda x:x.abs().mean()])
perT.columns=['n','median_error_C','mae_C']

p1=pd.read_csv(TASK/'data_manifests/d1_cropped_events.csv')
p1=p1.loc[p1.budget_Ah==20].dropna(subset=['temperature_C','current_A']).copy()
p1['t']=pd.to_datetime(p1.fragment_end)
pairs=[]
for cell,part in p1.groupby('cell_id'):
    part=part.sort_values('t').reset_index(drop=True)
    for i in range(1,len(part)):
        prev=part.iloc[i-1];now=part.iloc[i]
        hours=(now.t-prev.t).total_seconds()/3600
        dt=float(now.temperature_C-prev.temperature_C)
        di=float(now.current_A-prev.current_A)
        if not 0<hours<=cfg['matched_P1_event_pairs']['max_gap_hours']:continue
        if abs(dt)<cfg['matched_P1_event_pairs']['minimum_measured_temperature_difference_C']:continue
        if abs(di)>cfg['matched_P1_event_pairs']['maximum_current_difference_A']:continue
        pairs.append({'cell_id':cell,'earlier_event_id':prev.event_id,'later_event_id':now.event_id,
                      'gap_h':hours,'delta_temp_C':dt,'delta_current_A':di,
                      'earlier_w03_Ah':prev.w03_Ah,'later_w03_Ah':now.w03_Ah,
                      'delta_w03_Ah':float(now.w03_Ah-prev.w03_Ah) if pd.notna(prev.w03_Ah) and pd.notna(now.w03_Ah) else None,
                      'earlier_vend_V':prev.v_end_V,'later_vend_V':now.v_end_V})
pd.DataFrame(pairs).to_csv(OUT/'P1_near_age_temperature_pairs.csv',index=False)

pulses=pd.read_csv(TASK/'runs/M1_voltage_forecast_v1/pulse_features.csv')
pulses['t']=pd.to_datetime(pulses.start)
brackets=[]
for cell,part in pulses.groupby('cell'):
    part=part.sort_values('t')
    for center in part.itertuples(index=False):
        opposite=part.loc[part.chamber_C!=center.chamber_C]
        before=opposite.loc[opposite.t<center.t]
        after=opposite.loc[opposite.t>center.t]
        if len(before)==0 or len(after)==0:continue
        earlier=before.iloc[-1];later=after.iloc[0]
        days_before=(center.t-earlier.t).total_seconds()/86400
        days_after=(later.t-center.t).total_seconds()/86400
        if max(days_before,days_after)>cfg['official_temperature_pairs']['bracket_opposite_temperature_before_after_days']:continue
        w=days_before/(days_before+days_after)
        interpolated=(1-w)*earlier.apparent_R_10s_mOhm+w*later.apparent_R_10s_mOhm
        brackets.append({'cell':cell,'center_start':center.start,'center_chamber_C':center.chamber_C,
                         'opposite_before_start':earlier.start,'opposite_after_start':later.start,
                         'days_before':days_before,'days_after':days_after,
                         'center_R10_mOhm':center.apparent_R_10s_mOhm,
                         'bracketed_opposite_R10_mOhm':interpolated,
                         'center_minus_bracket_mOhm':center.apparent_R_10s_mOhm-interpolated})
pd.DataFrame(brackets).to_csv(OUT/'official_bracket_temperature_pairs.csv',index=False)
summary={'first_phase_surface_theta_diagnostic_only':theta.tolist(),
         'first_phase_source_sha256':hashlib.sha256((ROOT/'research/phase2_temperature_improvement/src/thermal_surface.py').read_bytes()).hexdigest(),
         'official_shallow_charge_count':len(official),
         'official_transfer_mae_C':float(official.transfer_error_C.abs().mean()),
         'official_transfer_by_chamber_C':{str(k):{a:float(v) for a,v in row.items()} for k,row in perT.to_dict(orient='index').items()},
         'first_phase_surface_portable_under_2C_rule':bool(official.transfer_error_C.abs().mean()<=2),
         'P1_adjacent_matched_temp_pairs':len(pairs),
         'P1_minimum_pairs_for_causal_claim':cfg['matched_P1_event_pairs']['minimum_independent_pairs_for_claim'],
         'official_bracket_cell_rows':len(brackets),
         'official_bracket_physical_pulses':len(set(x['center_start'] for x in brackets)),
         'official_center_minus_bracket_R10_mOhm_median':float(np.median([x['center_minus_bracket_mOhm'] for x in brackets])) if brackets else None,
         'claim_limit':'Equipment surface is not transferred if official error >2C; bracketed resistance is descriptive, not capacity truth or causal temperature isolation.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
