"""M4: finite-rate CK0 sensitivity, profile identifiability and causal pulse forecast.

No CK1--CK7 capacity label is accessed. Synthetic truth has unmodelled dynamic
polarization and smooth shape mismatch, making fitted voltage non-equivalent to Q.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares, minimize_scalar
from scipy.signal import savgol_filter

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M4_state_identifiability_v1'
OUT.mkdir(parents=True,exist_ok=False)
cfg=json.loads((TASK/'configs/m4_state.json').read_text())
ref=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
qref=ref.discharged_Ah.to_numpy(float)
Q0=100.41
q_grid=np.arange(0,100.401,.1)
v_cells={}
for k in range(1,5):
    v=np.interp(q_grid,qref,ref[f'cell{k}_V'].to_numpy(float))
    v_cells[k]=savgol_filter(v,101,3)
v_median=np.median(np.array(list(v_cells.values())),axis=0)

def curve(q,Q,z0,grid=v_median):
    """Finite-rate reference reparameterization, not a thermodynamic OCV."""
    q_equiv=Q0*(1-z0+np.asarray(q)/Q)
    return np.interp(np.clip(q_equiv,0,100.4),q_grid,grid)

def profile(q,y,sigma_V):
    """Profile Q with z0 and free constant offset, using effective mV noise."""
    qvals=np.arange(70.0,120.001,1.0)
    losses=[];zbest=[];bias=[]
    for Q in qvals:
        def score(z):
            p=curve(q,Q,z);return float(np.mean(((y-y.mean())-(p-p.mean()))**2))
        # Global scan is necessary because plateau kinks give local minima.
        zs=np.linspace(.88,1.0,49)
        ss=np.array([score(z) for z in zs]);j=int(np.argmin(ss))
        lo=zs[max(0,j-1)];hi=zs[min(len(zs)-1,j+1)]
        opt=minimize_scalar(score,bounds=(lo,hi),method='bounded',options={'xatol':1e-7})
        z=float(opt.x);p=curve(q,Q,z)
        zbest.append(z);bias.append(float(np.mean(y-p)))
        # Number of effective observations capped at 15 to avoid 0.25Ah
        # serial samples manufacturing false precision.
        losses.append(float(score(z)*min(len(q),15)/(sigma_V**2)))
    losses=np.asarray(losses);ix=int(np.argmin(losses));inside=qvals[losses<=losses[ix]+3.841459]
    return {'Q_fit_Ah':float(qvals[ix]),'z0_fit':zbest[ix],'bias_fit_V':bias[ix],
            'profile_low_Ah':float(inside.min()),'profile_high_Ah':float(inside.max()),
            'profile_width_Ah':float(inside.max()-inside.min()),
            'min_at_interior':bool(0<ix<len(qvals)-1),
            'rmse_V':float(np.sqrt(np.mean((y-curve(q,qvals[ix],zbest[ix])-bias[ix])**2))),
            'Q_profile':qvals,'loss_profile':losses}

def jacobian_svd(q,Q,z0,sigma_V):
    base=curve(q,Q,z0)
    # Scaled physical perturbations: Q 10Ah, SOC 0.01, bias 10mV,
    # R 0.5mOhm at constant 20.4A, polarization 5mV with q/2Ah dynamic.
    dQ=(curve(q,Q+.05,z0)-curve(q,Q-.05,z0))/.1*10
    dz=(curve(q,Q,z0+.0001)-curve(q,Q,z0-.0001))/.0002*.01
    db=np.full_like(q,.01)
    dR=np.full_like(q,20.4*.0005)
    dp=.005*(1-np.exp(-q/2))
    cols=np.column_stack([dQ,dz,db,dR,dp])/(sigma_V*np.sqrt(min(len(q),15)))
    s=np.linalg.svd(cols,compute_uv=False)
    # Remove free bias and SOC via orthogonal projection to measure Q-only info.
    nuisance=np.column_stack([dz,db,dp]);Qb,_=np.linalg.qr(nuisance)
    q_res=dQ-Qb@(Qb.T@dQ)
    return {'capacity_signal_mV_for_10Ah':float(np.linalg.norm(dQ)/np.sqrt(len(q))*1000),
            'capacity_unique_signal_mV_for_10Ah':float(np.linalg.norm(q_res)/np.sqrt(len(q))*1000),
            'scaled_singular_values':s.tolist(),
            'bias_R_column_correlation':float(np.corrcoef(db,dR)[0,1]) if np.std(db)*np.std(dR)>0 else 1.0}

# CK0 cell-specific slope catalog. This is a finite-rate shape description.
slope_rows=[]
for cell,v in v_cells.items():
    slope=np.gradient(v,q_grid)
    for lo,hi in ((0,1),(1,10),(10,20),(20,40),(40,60),(60,80),(80,90),(90,100)):
        sel=(q_grid>=lo)&(q_grid<hi)
        slope_rows.append({'cell':cell,'q_from_Ah':lo,'q_to_Ah':hi,
                           'median_abs_dV_dAh_mV_per_Ah':float(1000*np.median(np.abs(slope[sel]))),
                           'mean_abs_dV_dAh_mV_per_Ah':float(1000*np.mean(np.abs(slope[sel])))})
pd.DataFrame(slope_rows).to_csv(OUT/'CK0_slope_by_cell.csv',index=False)

sim=[];selected_profiles=[]
for Qtrue in cfg['synthetic_protocol']['truth_Q_Ah']:
  for ztrue in cfg['synthetic_protocol']['truth_initial_SOC']:
    for horizon in cfg['synthetic_protocol']['windows_Ah']:
      if horizon>=Qtrue*ztrue-1: continue
      q=np.arange(0,horizon+.001,.25)
      # Truth shape differs from estimator: CK0 cell 2 (not median), one
      # smooth morphology term, current drop, dynamic polarization, bias.
      truth=curve(q,Qtrue,ztrue,v_cells[2])-.0017*20.4 \
          -.003*(1-np.exp(-q/2))+.0015*np.sin(2*np.pi*q/30)+.004
      for sigma in cfg['synthetic_protocol']['voltage_noise_sensitivity_mV']:
        pr=profile(q,truth,sigma/1000)
        j=jacobian_svd(q,Qtrue,ztrue,sigma/1000)
        accept=pr['profile_width_Ah']<=20 and pr['min_at_interior']
        sim.append({'truth_Q_Ah':Qtrue,'truth_z0':ztrue,'window_Ah':horizon,
                    'assumed_effective_sigma_mV':sigma,**{k:v for k,v in pr.items() if k not in ('Q_profile','loss_profile')},
                    'Q_abs_error_Ah':abs(pr['Q_fit_Ah']-Qtrue),'gate_accept':accept,
                    'gate_Q_after_Ah':float(Q0+np.clip(pr['Q_fit_Ah']-Q0,-.02*Q0,.02*Q0)) if accept else Q0,
                    'uncertainty_halfwidth_after_Ah':10.0 if accept else 10.5,
                    'capacity_signal_mV_for_10Ah':j['capacity_signal_mV_for_10Ah'],
                    'capacity_unique_signal_mV_for_10Ah':j['capacity_unique_signal_mV_for_10Ah'],
                    'minimum_scaled_singular_value':min(j['scaled_singular_values'])})
        if Qtrue==94 and ztrue==.98 and sigma==5:
            selected_profiles.extend({'truth_Q_Ah':Qtrue,'window_Ah':horizon,'Q_candidate_Ah':float(Qc),
                                      'delta_profile_loss':float(loss-min(pr['loss_profile']))}
                                     for Qc,loss in zip(pr['Q_profile'],pr['loss_profile']))
pd.DataFrame(sim).to_csv(OUT/'synthetic_identifiability.csv',index=False)
pd.DataFrame(selected_profiles).to_csv(OUT/'selected_capacity_profiles.csv',index=False)

# Independent official forward-voltage test. Every model sees only target's
# first 1Ah plus past same-temperature pulses; future 2--10Ah is score-only.
cert=pd.read_csv(TASK/'runs/M1_certification_v2/event_certification.csv',parse_dates=['start','end'])
cert=cert.loc[cert.accepted].sort_values('start')
qg=np.round(np.arange(0,10.001,.1),3);early=(qg>=.2)&(qg<=1);held=qg>=2
waves=[]
for filename,group in cert.groupby('file',sort=True):
  raw=pd.read_csv(ROOT/'data/operation'/filename,parse_dates=['timestamp'])
  for item in group.itertuples(index=False):
    st=np.flatnonzero((raw.timestamp==item.start)&raw.current_A.between(-20.5,-19.5));
    en=np.flatnonzero((raw.timestamp==item.end)&raw.current_A.between(-20.5,-19.5))
    pulse=raw.iloc[int(st[0]):int(en[-1])+1]
    t=pulse.timestamp.astype('int64').to_numpy()/1e9
    I=-pulse.current_A.to_numpy(float)
    q=np.r_[0,np.cumsum((I[1:]+I[:-1])*np.diff(t)/7200)]
    for cell in range(1,5):
      waves.append({'start':item.start.isoformat(),'cell':cell,'temp':int(item.chamber_C),
                    'file':filename,'curve':np.interp(qg,q,pulse[f'cell{cell}_V'].to_numpy(float))})

fore=[];updates=[]
for target in sorted(waves,key=lambda x:x['start']):
  history=[w for w in waves if w['cell']==target['cell'] and w['temp']==target['temp'] and w['start']<target['start']]
  if len(history)<2:continue
  y=target['curve'];refcell=v_cells[target['cell']]
  # Fixed CK0 EC shape: constant ohmic/hysteresis term profiled by early
  # alignment. The prior same-condition event supplies empirical polarization.
  base=curve(qg,Q0,1,refcell)
  ck=base+np.median(y[early]-base[early])
  old=history[-1]['curve'];match=old+np.median(y[early]-old[early])
  # Capacity-SOC joint fit on early interval, deliberately ungated as a
  # falsification. Later score cannot influence this fit.
  p=profile(qg[early],y[early],.005)
  qfit=p['Q_fit_Ah'];zfit=p['z0_fit']
  ungated=curve(qg,qfit,zfit,refcell)
  ungated+=np.median(y[early]-ungated[early])
  accepted=p['profile_width_Ah']<=20 and p['min_at_interior']
  qgated=Q0+np.clip(qfit-Q0,-.02*Q0,.02*Q0) if accepted else Q0
  gated=curve(qg,qgated,1,refcell)
  gated+=np.median(y[early]-gated[early])
  updates.append({'start':target['start'],'cell':target['cell'],'chamber_C':target['temp'],
                  'Q_ungated_Ah':qfit,'z0_ungated':zfit,
                  'profile_low_Ah':p['profile_low_Ah'],'profile_high_Ah':p['profile_high_Ah'],
                  'profile_width_Ah':p['profile_width_Ah'],'gate_accept':accepted,
                  'Q_gated_Ah':qgated,'uncertainty_halfwidth_Ah':10 if accepted else 10.5,
                  'early_fit_rmse_mV':1000*p['rmse_V']})
  for name,pred in [('CK0_fixed_shape',ck),('last_same_temp_shift',match),
                    ('early_ungated_Q_SOC',ungated),('early_gated_Q_fixed_SOC',gated)]:
    for ii in np.flatnonzero(held):
      fore.append({'start':target['start'],'cell':target['cell'],'chamber_C':target['temp'],
                   'method':name,'q_Ah':float(qg[ii]),'actual_V':float(y[ii]),
                   'predicted_V':float(pred[ii]),'error_mV':float(1000*(pred[ii]-y[ii]))})
pd.DataFrame(updates).to_csv(OUT/'official_gate_diagnostics.csv',index=False)
fore=pd.DataFrame(fore);fore.to_csv(OUT/'official_forward_predictions.csv',index=False)
events=fore.assign(abs_mV=fore.error_mV.abs()).groupby(['start','cell','chamber_C','method'],as_index=False).abs_mV.mean()
events.to_csv(OUT/'official_event_voltage_mae.csv',index=False)
simdf=pd.DataFrame(sim);update=pd.DataFrame(updates)
summary={'synthetic_scenarios':len(simdf),'synthetic_gate_accept_by_window_sigma':simdf.groupby(['window_Ah','assumed_effective_sigma_mV']).gate_accept.mean().rename(lambda x:x).reset_index().to_dict('records'),
         'synthetic_median_Q_error_by_window_Ah':{str(k):float(v) for k,v in simdf.loc[simdf.assumed_effective_sigma_mV==5].groupby('window_Ah').Q_abs_error_Ah.median().items()},
         'official_forward_cell_events':len(update),'official_gate_accepted':int(update.gate_accept.sum()),
         'official_median_profile_width_Ah':float(update.profile_width_Ah.median()),
         'official_voltage_MAE_mV_by_method':{str(k):float(v) for k,v in events.groupby('method').abs_mV.mean().items()},
         'capacity_validation':'not_testable: CK1-CK7 capacity labels hidden; synthetic truth is mechanism test only',
         'reference_limit':'CK0 is 5.1A finite-rate 4S discharge; not equilibrium OCV or unique cell Q; 20.4A pulses have rate/thermal mismatch'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
