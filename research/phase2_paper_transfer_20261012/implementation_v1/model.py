"""Paper-inspired loaded-curve registration. LAD solved by an epigraph LP.

Current and CK0 reference polarization are separate unknowns. The constant
CK0 ohmic voltage is absorbed into b; no independent OCV is fabricated.
Step R is an effective sampling-scale constraint, never certified R0.
"""
import numpy as np
from scipy.optimize import linprog,lsq_linear,minimize_scalar
from scipy.sparse import csr_matrix,hstack,vstack,eye
from common import *
from audit_stage import restfit

def bounds_for(e,tau,mode,pulses=None):
    lo=np.array([-.05,0,0,0,-.10]);hi=np.array([.05,.3,.3,.3,.10])
    low=np.tile(lo,(4,1));high=np.tile(hi,(4,1));flags=[]
    if mode=='independent':
        # Own in-event/boundary voltages allowed only in OFFLINE registration.
        # Forecasts use completed historical fits, never this target's fit.
        if pulses is not None:
            r=pulses[(pulses['T']==e['T']) & (pulses.panel==e['panel']) & pulses.qualified &
                (pulses.available_after<=e['available_after'])].drop_duplicates('pulse_uid').tail(8)
            if len(r)>=CFG['step_min_evidence']:
                for c in range(4):
                    vals=r[f'R{c+1}_ohm'].to_numpy();med=np.median(vals)
                    width=max(CFG['r_inflation_floor_ohm'],3*np.median(abs(vals-med)))
                    low[c,1]=max(0,med-width)*20;high[c,1]=min(.015,med+width)*20
                flags.append('sampling_scale_R_app')
        if e.get('synthetic_R_app') is not None:
            for c,med in enumerate(e['synthetic_R_app']):
                w=CFG['r_inflation_floor_ohm']
                low[c,1]=max(0,med-w)*20;high[c,1]=min(.015,med+w)*20
            flags.append('independent_synthetic_pulse')
        rr=restfit(e,tau)
        if rr['valid'] and not rr['amplitude_over_bound'] and rr['condition']<1e4 and rr['heldout_mae_mV']<rr['last_value_mae_mV']:
            # Approximate relative initial correction; allow fixed floor and
            # tau sensitivity, not a claim of exact initial polarization.
            alternatives=[restfit(e,tt) for tt in [tau/2,tau,tau*2]]
            amps=np.array([r['amp_V'] for r in alternatives if r['valid']])
            for c in range(4):
                low[c,4]=max(-.1,float(amps[:,c].min())-.003)
                high[c,4]=min(.1,float(amps[:,c].max())+.003)
            if np.any(high[:,4]<low[:,4]):low[:,4]=-.1;high[:,4]=.1
            else:flags.append('rest_amplitude_range')
    return low,high,flags

def design(p,s,d,tau):
    x=p['q']/s+d
    href=5.1*(-np.expm1(-3600*x/(5.1*tau)))
    a=np.c_[np.ones(len(x)),-p['j']/20,-p['h']/20,href/20,np.exp(-p['t']/tau)]
    return a,x

def linear(a,target,low,high,loss):
    if loss=='L2':
        coef=np.linalg.lstsq(a,target,rcond=None)[0]
        if np.any(coef<low) or np.any(coef>high):
            coef=lsq_linear(a,target,bounds=(low,high),method='bvls',max_iter=40).x
        objective=float(np.mean((a@coef-target)**2))
    else:
        n,m=a.shape
        sparse=csr_matrix(a);ident=eye(n,format='csr')
        constraints=vstack([hstack([sparse,-ident]),hstack([-sparse,-ident])],format='csr')
        fit=linprog(np.r_[np.zeros(m),np.ones(n)/n],A_ub=constraints,
            b_ub=np.r_[target,-target],bounds=list(zip(low,high))+[(0,None)]*n,
            method='highs',options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
        if not fit.success:raise RuntimeError('LAD LP: '+fit.message)
        coef=fit.x[:m];objective=float(np.abs(a@coef-target).mean())
    residual=a@coef-target
    return objective,coef,float(np.abs(residual).mean()),float(np.sqrt(np.mean(residual**2)))

def fit_cell(template,p,s,c,tau,loss,low,high,d_fixed=None):
    dmax=min(CFG['d_max_Ah'],template.x[-1]-p['q'].max()/s)
    if dmax<template.x[0]-1e-9:raise ValueError('strict_template_domain')
    def calc(d):
        a,x=design(p,s,d,tau)
        return linear(a,p['y'][:,c]-template.values(x,c),low,high,loss)
    if d_fixed is not None:
        if not template.x[0]<=d_fixed<=dmax:raise ValueError('fixed_d_domain')
        d=float(d_fixed);result=calc(d)
    else:
        grid=np.unique(np.minimum(np.array([0,.5,3,10,25,45,65,dmax]),dmax))
        values=[calc(d) for d in grid]
        best=int(np.argmin([v[0] for v in values]));d=float(grid[best]);result=values[best]
        for k in np.argsort([v[0] for v in values])[:2]:
            lo=grid[max(0,k-1)];hi=grid[min(len(grid)-1,k+1)]
            if hi>lo+.001:
                opt=minimize_scalar(lambda v:calc(v)[0],bounds=(lo,hi),method='bounded',
                    options={'maxiter':CFG['d_local_maxiter'],'xatol':.02})
                candidate=calc(opt.x)
                if candidate[0]<result[0]:d=float(opt.x);result=candidate
    objective,coef,mae,rms=result
    return objective,np.r_[d,coef],mae,rms

def profile(template,e,tau,loss='L2',mode='free',pulses=None,grid=None,cache=True,fit_points=None,tight_bias=False):
    path=profile_path(e,loss,mode)
    if cache and path.exists():
        z=np.load(path);return {k:z[k] for k in z.files}
    p=prepare(e,tau,CFG['fit_max_points'] if fit_points is None else fit_points);low,high,flags=bounds_for(e,tau,mode,pulses)
    if tight_bias:low[:,0]=-.01;high[:,0]=.01
    grid=np.array(CFG['s_grid'] if grid is None else grid,float)
    if mode=='independent' and not flags and cache:
        free=profile(template,e,tau,loss,'free',pulses,grid,cache)
        out={k:v.copy() for k,v in free.items()};out['direct_constraints']=np.array(0)
    else:
        obj=np.full((len(grid),4),np.inf);params=np.full((len(grid),4,6),np.nan)
        mae=np.full_like(obj,np.inf);rms=np.full_like(obj,np.inf)
        for k,s in enumerate(grid):
            for c in range(4):
                try:obj[k,c],params[k,c],mae[k,c],rms[k,c]=fit_cell(template,p,s,c,tau,loss,low[c],high[c])
                except ValueError:pass
        out=dict(sgrid=grid,objective=obj,params=params,mae=mae,rms=rms,
                 lower=low,upper=high,direct_constraints=np.array(len(flags)))
    if cache:
        path.parent.mkdir(exist_ok=True);np.savez_compressed(path,**out)
    return out

def select(profiles,kind='common',fixed=False,shrink=False,loss='L2'):
    grid=profiles[0]['sgrid']
    obj=np.mean([p['objective'] for p in profiles],axis=0)
    if fixed:ix=np.full(4,np.argmin(abs(grid-1)))
    elif kind=='common':ix=np.full(4,np.argmin(obj.mean(axis=1)))
    else:
        ix=np.argmin(obj,axis=0)
        if shrink:
            center=grid[np.argmin(obj.mean(axis=1))]
            # Fixed research shrinkage, explicitly a prior-like penalty.
            strength=CFG['smoothing_lambda'] if loss=='L2' else .002
            ix=np.argmin(obj+strength*(grid[:,None]-center)**2,axis=0)
    params=np.median([np.stack([p['params'][ix[c],c] for c in range(4)]) for p in profiles],axis=0)
    return grid[ix],params,obj

def predict(template,p,s,params,tau):
    s=np.broadcast_to(s,(4,))
    return np.stack([template.values(design(p,s[c],params[c,0],tau)[1],c)+
        design(p,s[c],params[c,0],tau)[0]@params[c,1:] for c in range(4)],axis=1)

def forecast(template,e,s,params,tau,budget):
    params=np.array(params,copy=True);p=prepare(e,tau)
    prefix=(e['q']<=budget)&(e['t']>=20)
    if budget>0 and prefix.sum()>=3:
        pp=legacy.prepare(e,tau,prefix)
        # Only an intercept update on the allowed prefix; start/capacity do not
        # use the target's eventual maximum Ah or future suffix voltages.
        pred=predict(template,pp,s,params,tau)
        params[:,1]+=np.median(pp['y']-pred,axis=0)
    return p,predict(template,p,s,params,tau),params

def diagnosis(profiles,loss,q0):
    objective=np.mean([p['objective'] for p in profiles],axis=(0,2))
    curve=np.sqrt(objective)*1000 if loss=='L2' else objective*1000
    grid=profiles[0]['sgrid'];best=int(np.argmin(curve))
    accepted=grid[curve<=curve[best]+CFG['profile_tolerance_mV']]
    width=float(np.ptp(accepted)*q0)
    gate=bool(width<=CFG['profile_width_gate_Ah'] and best not in [0,len(grid)-1])
    return dict(best_s=float(grid[best]),width_Ah=width,boundary=bool(best in [0,len(grid)-1]),
                gate=gate,accepted_s=accepted.tolist(),minimum_loss_mV=float(curve[best])),curve
