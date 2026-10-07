"""M4 counterfactual: multi-start state fits and nuisance-parameter confounding."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.signal import savgol_filter

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M4_confounds_v1'
OUT.mkdir(parents=True,exist_ok=False)
ref=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
x=ref.discharged_Ah.to_numpy(float);qgrid=np.arange(0,100.401,.1)
cells=np.array([savgol_filter(np.interp(qgrid,x,ref[f'cell{i}_V']),101,3) for i in range(1,5)])
model=np.median(cells,axis=0);truth_grid=cells[1]
def v(q,Q,z,grid=model):return np.interp(np.clip(100.41*(1-z+q/Q),0,100.4),qgrid,grid)

trueQ=94.0;truez=.98;I=20.4
rows=[]
for horizon in (1.,10.,30.,90.):
 q=np.arange(0,horizon+.001,.25)
 truth=v(q,trueQ,truez,truth_grid)-.0017*I-.003*(1-np.exp(-q/2))+.0015*np.sin(2*np.pi*q/30)+.004
 for case in ('Q_only_known_SOC_and_offset','Q_SOC_free_offset','Q_SOC_offset_and_R'):
  for Qinit in (72.,85.,100.,116.):
   for zinit in (.90,.95,.99):
    if case=='Q_only_known_SOC_and_offset':
     # Even knowing SOC and constant offset does not remove curve mismatch.
     residual=lambda p:v(q,p[0],truez)-.0017*I+.004-truth
     x0=[Qinit];bounds=([70.],[120.])
    elif case=='Q_SOC_free_offset':
     residual=lambda p:v(q,p[0],p[1])+p[2]-truth
     x0=[Qinit,zinit,float(np.mean(truth-v(q,Qinit,zinit)))];bounds=([70.,.88,-.1],[120.,1.,.1])
    else:
     # A constant-current pulse makes free bias and R structurally identical.
     residual=lambda p:v(q,p[0],p[1])+p[2]-I*p[3]-truth
     x0=[Qinit,zinit,float(np.mean(truth-v(q,Qinit,zinit))),.0017]
     bounds=([70.,.88,-.1,0.],[120.,1.,.1,.005])
    fit=least_squares(residual,x0,bounds=bounds,max_nfev=300,xtol=1e-11,ftol=1e-11,gtol=1e-11)
    row={'window_Ah':horizon,'case':case,'Q_init_Ah':Qinit,'z_init':zinit,
         'Q_fit_Ah':float(fit.x[0]),'z_fit':float(fit.x[1]) if len(fit.x)>1 else truez,
         'voltage_RMSE_mV':float(1000*np.sqrt(np.mean(fit.fun**2))),
         'Q_abs_error_Ah':float(abs(fit.x[0]-trueQ)),'at_Q_bound':bool(fit.x[0]<70.01 or fit.x[0]>119.99)}
    if len(fit.x)>2:row['bias_fit_mV']=float(fit.x[2]*1000)
    if len(fit.x)>3:row['R_fit_mOhm']=float(fit.x[3]*1000)
    rows.append(row)
pd.DataFrame(rows).to_csv(OUT/'multi_start_parameter_fits.csv',index=False)

# Sensitivity before and after removing SOC, voltage offset and polarization.
sens=[]
for horizon in (1.,10.,30.,90.):
 q=np.arange(0,horizon+.001,.25)
 Q=trueQ;z=truez
 dQ=(v(q,Q+.1,z)-v(q,Q-.1,z))/.2*10
 dz=(v(q,Q,z+.0005)-v(q,Q,z-.0005))/.001*.01
 db=np.full(len(q),.01);dR=np.full(len(q),I*.0005)
 dp=.005*(1-np.exp(-q/2))
 for names,nu in [('none',np.empty((len(q),0))),('SOC',dz[:,None]),
                  ('SOC_bias',np.column_stack([dz,db])),('SOC_bias_polarization',np.column_stack([dz,db,dp]))]:
  if nu.shape[1]:
   u,s,_=np.linalg.svd(nu,full_matrices=False)
   rank=int(np.sum(s>1e-10));res=dQ-u[:,:rank]@(u[:,:rank].T@dQ)
  else:res=dQ
  sens.append({'window_Ah':horizon,'nuisance':names,
               'Q_unique_signal_mV_for_10Ah':float(1000*np.sqrt(np.mean(res**2))),
               'effective_noise_assumption_mV':5,
               'signal_over_noise':float(np.sqrt(min(len(q),15))*np.sqrt(np.mean(res**2))/.005)})
 # Full Jacobian has exact bias/R collinearity at fixed current.
 J=np.column_stack([dQ,dz,db,dR,dp]);s=np.linalg.svd(J,compute_uv=False)
 sens.append({'window_Ah':horizon,'nuisance':'full_J_min_singular',
              'Q_unique_signal_mV_for_10Ah':float(s[-1]*1000),
              'effective_noise_assumption_mV':5,'signal_over_noise':float(s[-1]/.005)})
pd.DataFrame(sens).to_csv(OUT/'sensitivity_nuisance.csv',index=False)
fits=pd.DataFrame(rows);ss=pd.DataFrame(sens)
summary={'multi_start_Q_range_by_window_case':[
    {'window_Ah':float(h),'case':str(c),'Q_min_Ah':float(g.Q_fit_Ah.min()),
     'Q_max_Ah':float(g.Q_fit_Ah.max()),'best_voltage_RMSE_mV':float(g.voltage_RMSE_mV.min()),
     'worst_Q_abs_error_Ah':float(g.Q_abs_error_Ah.max())}
    for (h,c),g in fits.groupby(['window_Ah','case'])],
 'sensitivity_after_all_nuisance_mV_for_10Ah':{str(h):float(g.Q_unique_signal_mV_for_10Ah.iloc[0])
     for h,g in ss.loc[ss.nuisance=='SOC_bias_polarization'].groupby('window_Ah')},
 'bias_R_identification':'exactly rank deficient for a single constant-current pulse; only bias - I*R is identified',
 'truth_model_limit':'synthetic CK0 cell2 shape plus dynamic polarization differs from fitted median-cell static quasi-OCV; no real capacity confirmation'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'fit_rows':len(fits),'sensitivity_rows':len(ss)},ensure_ascii=False),flush=True)
