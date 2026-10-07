"""Charge/discharge shape-transfer falsification on completed deep CC charges.

Retrospective signal audit only. Hidden checkup capacities are never read.
"""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.signal import savgol_filter

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M4_deep_curve_profile_v1';OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(ROOT/'research/phase2_temperature_improvement/src'))
from event_core import extract_charge_events
from route_a_repaired import stable_cc_prefix
ref=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
grid_q=np.arange(0,100.401,.1);qq=ref.discharged_Ah.to_numpy(float)
curves={i:savgol_filter(np.interp(grid_q,qq,ref[f'cell{i}_V']),101,3) for i in range(1,5)}
manifest=pd.read_csv(TASK/'runs/M4_deep_charge_audit_v1/deep_charge_events.csv',parse_dates=['event_end'])
def shape(q,Q,z0,curve):
    equivalent_discharge_Ah=100.41*(1-z0-q/Q)
    return np.interp(np.clip(equivalent_discharge_Ah,0,100.4),grid_q,curve)
rows=[]
for filename,part in manifest.groupby('file'):
    frame=pd.read_csv(ROOT/'data/operation'/filename,parse_dates=['timestamp'])
    events=extract_charge_events(frame,time_col='timestamp',voltage_cols=('cell1_V','cell2_V','cell3_V','cell4_V'),temp_col='temp_mean_C',segment_col='segment',counter_col='charge_Ah_cum')
    for mr in part.itertuples(index=False):
        matching=[e for e in events if e.end==mr.event_end]
        assert len(matching)==1,(filename,mr.event_end,len(matching))
        cc,status=stable_cc_prefix(matching[0]);assert status=='pass'
        q=np.arange(0,min(85,cc.ah)+.001,.5)
        assert q[-1]<=cc.q_ah[-1]
        for cell in range(1,5):
            y=np.interp(q,cc.q_ah,cc.voltages[:,cell-1]);curve=curves[cell]
            Qs=np.arange(70.,120.001,1.)
            scores=[];zs=[];offsets=[]
            for Q in Qs:
                def score(z):
                    p=shape(q,Q,z,curve)
                    return float(np.mean(((y-y.mean())-(p-p.mean()))**2))
                zscan=np.linspace(0,.20,41);ss=np.array([score(z) for z in zscan]);j=int(np.argmin(ss))
                op=minimize_scalar(score,bounds=(zscan[max(0,j-1)],zscan[min(j+1,40)]),method='bounded')
                z=float(op.x);p=shape(q,Q,z,curve)
                scores.append(score(z));zs.append(z);offsets.append(float(np.mean(y-p)))
            j=int(np.argmin(scores));rmse=np.sqrt(scores[j])
            # Effective 15 samples, with 5mV or 20mV structural noise.
            row={'file':filename,'event_end':mr.event_end.isoformat(),'temp_C':float(mr.temp_C),
                 'cell':cell,'deep_CC_Ah':float(cc.ah),'fit_window_Ah':float(q[-1]),
                 'Q_fit_Ah':float(Qs[j]),'z0_fit':zs[j],'voltage_offset_mV':1000*offsets[j],
                 'voltage_RMSE_mV':1000*rmse,'Q_at_bound':bool(j==0 or j==len(Qs)-1)}
            for sigma in (5.,20.):
                loss=np.array(scores)*15/(sigma/1000)**2
                inside=Qs[loss<=loss[j]+3.841459]
                row[f'Q_profile_width_Ah_at_{int(sigma)}mV']=float(inside.max()-inside.min())
            rows.append(row)
out=pd.DataFrame(rows);out.to_csv(OUT/'deep_charge_shape_profiles.csv',index=False)
summary={'deep_events':len(manifest),'cell_event_fits':len(out),
         'fit_Q_median_Ah':float(out.Q_fit_Ah.median()),'fit_Q_at_bound_fraction':float(out.Q_at_bound.mean()),
         'voltage_RMSE_mV_median':float(out.voltage_RMSE_mV.median()),
         'voltage_offset_mV_median':float(out.voltage_offset_mV.median()),
         'charge_transfer_limit':'A 20.4A charge has direction/rate hysteresis relative to CK0 5.1A discharge. A narrow Q profile is not proof of true capacity if residual shape is wrong.',
         'truth':'CK1-CK7 hidden; deep CC Ah is observable but not a capacity label'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
