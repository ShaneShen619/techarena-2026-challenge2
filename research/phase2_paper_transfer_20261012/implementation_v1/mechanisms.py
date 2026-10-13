"""Independent 2RC generator reused read-only, new observed pulse constraints.
Truth is kept in generator/reporting only; model sees synthetic_R_app observations.
"""
import argparse
import numpy as np
import pandas as pd
import model
from common import *

def generate(seed,scenario,extra_deficit=0):
    source='capacity_and_start' if scenario=='outliers' else scenario
    template,e=generator.generate(seed,source,extra_deficit)
    e['id']=f'S_{scenario}_{seed}_{extra_deficit}';e['scenario']=scenario
    strict=StrictTemplate(template.x,template.y,template.q0)
    rng=np.random.default_rng(seed)
    r=np.vstack([rng.uniform(.0007,.0013,4),rng.uniform(.0003,.0006,4),rng.uniform(.0004,.0008,4)])
    if scenario=='temperature_45C':r*=.78
    if scenario=='resistance_growth':r*=np.array([1.7,1.2,1.4])[:,None]
    Q=102*e['truth_s'];pulse_rng=np.random.default_rng(seed+887)
    samples=[];observations=[]
    for j in [5.1,10.2,20.4]:
        z=np.full(4,.55);p=np.zeros((2,4));h=np.zeros(4)
        v0=generator.ocv(z,e['T'])
        z,p,h=generator.step(z,p,h,j,10,Q,r,e['T'])
        v1=generator.ocv(z,e['T'])-j*r[0]-p.sum(axis=0)+h
        v0=np.round((v0+pulse_rng.normal(0,.0002,4))/.001)*.001
        v1=np.round((v1+pulse_rng.normal(0,.0002,4))/.001)*.001
        samples.append(-(v1-v0)/j)
        observations.append(dict(current_A=j,dt_s=10,before_V=v0.tolist(),after_V=v1.tolist()))
    e['synthetic_R_app']=np.median(samples,axis=0)
    e['pulse_observations']=observations
    if scenario=='outliers':e['y']=e['y'].copy();e['y'][::17]+=.05
    return strict,e

def metrics(template,e,profiles,loss,mode):
    rows=[];diag,curve=model.diagnosis([profiles],loss,template.q0)
    for kind in ['fixed','common','shrunk4','free4_diagnostic']:
        s,params,_=model.select([profiles],kind='free4' if '4' in kind else 'common',
            fixed=kind=='fixed',shrink=kind=='shrunk4',loss=loss)
        p=prepare(e,600)
        try:pred=model.predict(template,p,s,params,600);vmae=float(abs(pred-p['y']).mean()*1000)
        except ValueError:vmae=np.nan
        caps={}
        for tail in [0,2]:
            if template.pack is not None:raise RuntimeError('synthetic pack unexpectedly real')
            maximum=float(np.min(s*(template.x[-1]+tail)))
            knots=np.unique(np.r_[0,maximum,*[s[c]*template.x for c in range(4)]])
            knots=knots[(knots>=0)&(knots<=maximum)]
            try:
                # Use the original explicit bounded-tail implementation only
                # for the labelled sensitivity. Strict default is no tail.
                if tail==2:cap=legacy.Template(template.x,template.y,template.q0).capacity(s)
                else:
                    v=sum(template.values(knots/s[c],c) for c in range(4));hit=np.flatnonzero(v<=11.2)
                    if not len(hit):raise ValueError('strict_cutoff_outside_domain')
                    k=int(hit[0]);cap=0. if k==0 else float(np.interp(11.2,v[k-1:k+1][::-1],knots[k-1:k+1][::-1]))
            except ValueError:cap=np.nan
            caps[tail]=cap
        quality=bool(np.max(np.diff(e['t']))<=45)
        accepted=bool(kind=='common' and diag['gate'] and quality)
        err=abs(s-e['truth_s'])
        rows.append(dict(scenario=e['scenario'],seed=e['seed'],loss=loss,mode=mode,kind=kind,
            s_mae=float(err.mean()),s_max_error=float(err.max()),s1=float(s[0]),s2=float(s[1]),s3=float(s[2]),s4=float(s[3]),
            truth_s_mean=float(e['truth_s'].mean()),constant_capacity=bool(np.all(e['truth_s']==1)),
            d_mae_reference_Ah=float(abs(params[:,0]-e['truth_d']).mean()),voltage_mae_mV=vmae,
            profile_width_Ah=diag['width_Ah'],boundary=diag['boundary'],accepted_update=accepted,
            false_accepted_scale=bool(accepted and err.mean()>.02),gap_quality_ok=quality,
            capacity_est_Ah=caps[0],capacity_valid=bool(np.isfinite(caps[0])),
            capacity_tail2_Ah=caps[2],capacity_true_Ah=e['truth_capacity'],
            capacity_error_Ah=float(abs(caps[0]-e['truth_capacity'])),
            reference_step_error_Ah=e['reference_step_error'],direct_constraints=int(profiles['direct_constraints'])))
    return rows

def main(phase):
    if phase=='evaluation':
        from run import verify_freeze
        verify_freeze()
        if (TASK/'SYNTHETIC_STARTED').exists():raise RuntimeError('synthetic evaluation already started')
        (TASK/'SYNTHETIC_STARTED').write_text('2026-10-13\n')
    seeds=CFG[phase+'_seeds'];rows=[];curves=[];observed=[]
    for scenario in CFG['synthetic_scenarios']:
        for seed in seeds:
            template,e=generate(seed,scenario)
            for loss in ['L2','LAD']:
                for mode in ['free','independent']:
                    pr=model.profile(template,e,600,loss,mode,cache=True)
                    rows.extend(metrics(template,e,pr,loss,mode))
                    if seed==seeds[0]:
                        d,curve=model.diagnosis([pr],loss,template.q0)
                        curves.extend(dict(scenario=scenario,seed=seed,loss=loss,mode=mode,s=float(s),loss_mV=float(v)) for s,v in zip(pr['sgrid'],curve))
            if seed==seeds[0]:observed.append(dict(scenario=scenario,seed=seed,pulses=e['pulse_observations']))
        print('mechanism',phase,scenario,flush=True)
        pd.DataFrame(rows).to_csv(TASK/f'synthetic_{phase}_metrics.csv',index=False)
    pd.DataFrame(curves).to_csv(TASK/f'synthetic_{phase}_profiles.csv',index=False)
    savejson(f'synthetic_{phase}_pulse_observations.json',observed)
    if phase=='evaluation':
        verify_freeze();(TASK/'SYNTHETIC_COMPLETE').write_text('2026-10-13\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['development','evaluation']);main(p.parse_args().phase)
