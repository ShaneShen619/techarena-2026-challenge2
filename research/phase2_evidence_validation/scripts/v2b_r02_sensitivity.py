"""Versioned R02 sensitivity aligned to preregistered 70–105 Ah apparent axis.

The apparent Ah axis is CK0 Ah times dimensionless voltage-axis stretch;
neither is directly a future protocol capacity without known reference state.
"""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
sys.path.insert(0,str(TASK/'src'))
from r02 import LoadedTemplate,fit_profile
RUN=TASK/'runs/V2_R02_sensitivity_20260929_v3';RUN.mkdir(parents=True,exist_ok=True)
assert not (RUN/'COMPLETED').exists()
cfg=json.loads((TASK/'configs/r02.json').read_text())
t=LoadedTemplate.from_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
ck0=float(pd.read_csv(ROOT/'data/checkups/checkup_capacities_released.csv').loc[0,'capacity_Ah'])
mn,mx,step=cfg['C_scale_grid']['value']; apparent=np.arange(mn,mx+step/2,step);scales=apparent/ck0
assert len(apparent)==71 and abs(scales[-1]*ck0-105)<1e-9
rng=np.random.default_rng(290931)
rows=[];profile=[];held=[]
windows=[('plateau',20,10),('knee',85,8),('long',40,50)]
settings=[('free',np.arange(-3,3.01,.25),np.arange(-.010,.0101,.002)),
 ('start_fixed',[0.],np.arange(-.010,.0101,.002)),('bias_fixed',np.arange(-3,3.01,.25),[0.]),
 ('tight',np.arange(-.5,.51,.25),np.arange(-.002,.0021,.002)),
 ('wide',np.arange(-5,5.01,.5),np.arange(-.020,.0201,.004))]
cases=[('true_scale_change',.94,0.,0.,'stretch'),('same_capacity_start',1.,2.,0.,'stretch'),
 ('same_capacity_bias',1.,0.,.006,'stretch'),('same_capacity_hysteresis',1.,0.,0.,'sine'),
 ('same_capacity_polarization',1.,0.,0.,'exponential'),('mixed_wrong_shape',.96,1.,.004,'sine')]
for w,start,span in windows:
    x0=np.linspace(0,span,101)
    for case,c,s,b,kind in cases:
        q=(start+s+x0)/c
        if q.max()>t.q[-1]:continue
        clean=np.interp(q,t.q,t.pack_v)+b
        if kind=='sine':clean+=.008*np.sin(np.pi*x0/span)
        if kind=='exponential':clean-=.006*(1-np.exp(-x0/2))
        dense_noise=rng.normal(0,.001,len(x0))
        for obs,noise,selector in [('dense_1mV',.001,np.arange(101)),
                                   ('sparse_1mV',.001,np.arange(0,101,10)),
                                   ('dense_3mV',.003,np.arange(101))]:
            x=x0[selector]
            y=clean[selector]+(dense_noise[selector] if noise==.001 else rng.normal(0,noise,len(selector)))
            for setting,offsets,biases in settings:
                p=fit_profile(t,x,y,start,scales,offsets,biases,noise)
                p['apparent_axis_Ah']=apparent;p['window']=w;p['case']=case;p['observation']=obs;p['nuisance']=setting
                p['prior_free_mse_V2']=p.data_mse_V2
                # Deliberately assertive age prior: just a sensitivity contrast.
                p['prior_tight_objective_V2']=p.data_mse_V2+(.015*(p.C_scale-1))**2
                profile.append(p)
                best=p.loc[p.prior_free_mse_V2.idxmin()];prior=p.loc[p.prior_tight_objective_V2.idxmin()]
                delta=1000*(np.sqrt(p.prior_free_mse_V2)-np.sqrt(p.prior_free_mse_V2.min()))
                support=p.loc[delta<=1,'apparent_axis_Ah']
                rows.append({'window':w,'case':case,'generation_kind':kind,'observation':obs,'nuisance':setting,
                  'true_axis_Ah_if_same_template':c*ck0,'best_axis_Ah':float(best.apparent_axis_Ah),
                  'best_data_rmse_mV':float(best.data_rmse_mV),
                  'sensitivity_axis_min_Ah':float(support.min()),'sensitivity_axis_max_Ah':float(support.max()),
                  'tight_prior_best_axis_Ah':float(prior.apparent_axis_Ah),
                  'at_start_boundary':bool(abs(best.best_start_offset_Ah-min(offsets))<1e-9 or abs(best.best_start_offset_Ah-max(offsets))<1e-9),
                  'at_bias_boundary':bool(abs(best.best_voltage_bias_V-min(biases))<1e-9 or abs(best.best_voltage_bias_V-max(biases))<1e-9),
                  'official_capacity_valid':False})
            # Same generated event: fit first half, predict withheld second half.
            if obs=='dense_1mV':
                p=fit_profile(t,x[:51],y[:51],start,scales,settings[0][1],settings[0][2],noise)
                best=p.loc[p.data_mse_V2.idxmin()]
                future_q=(start+best.best_start_offset_Ah+x[51:])/best.C_scale
                if future_q.min()<t.q[0] or future_q.max()>t.q[-1]:
                    held.append({'window':w,'case':case,'fit_first_fraction':.5,'heldout_rmse_mV':np.nan,
                      'heldout_is_independent_capacity_label':False,'rejection_reason':'withheld_q_outside_CK0_template'})
                    continue
                pred=t.voltage(start+best.best_start_offset_Ah+x[51:],best.C_scale,best.best_voltage_bias_V)
                held.append({'window':w,'case':case,'fit_first_fraction':.5,
                  'heldout_rmse_mV':float(1000*np.sqrt(np.mean((pred-y[51:])**2))),
                  'heldout_is_independent_capacity_label':False,'rejection_reason':''})
pd.concat(profile,ignore_index=True).to_csv(RUN/'paired_profiles.csv',index=False)
pd.DataFrame(rows).to_csv(RUN/'sensitivity_summary.csv',index=False)
pd.DataFrame(held).to_csv(RUN/'same_event_heldout_voltage.csv',index=False)
result={'run_id':RUN.name,'supersedes':'V2_R02_sensitivity_20260929_v2 for paired sparse noise and no heldout extrapolation',
 'frozen_grid_Ah':[mn,mx,step],'dimensionless_scale':'apparent_axis_Ah / CK0 released 100.41 Ah',
 'profiles':len(rows),'synthetic_heldout_events':len(held),'heldout_rejected':int(pd.DataFrame(held).heldout_rmse_mV.isna().sum()),
 'official_capacity_identifiable':False,'interval_type':'illustrative 1mV RMSE sensitivity, not confidence interval'}
(RUN/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');(RUN/'COMPLETED').write_text('immutable run completed\n')
print(json.dumps(result))
