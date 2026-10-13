"""Final reference-pack capacity profiles; nuisance refitted at every candidate."""
from __future__ import annotations
import numpy as np
from scipy.optimize import least_squares
from common import CFG
from ecm import design
from joint_estimation import Window

def capacity_grid(q0=None):
    q0=CFG['q0_Ah'] if q0 is None else q0
    low,high=np.array(CFG['alpha_bounds'])*q0
    return np.unique(np.r_[low,np.arange(np.ceil(low*2)/2,high,.5),high,80.,100.])

def profile(window,delta=1.0,fine=True):
    q0=window.ref.capacity(1.)
    grid=capacity_grid(q0)
    # Additional 80/100 only apply when within this reference's capacity bounds.
    grid=grid[(grid>=q0*CFG['alpha_bounds'][0])&(grid<=q0*CFG['alpha_bounds'][1])]
    vals=np.array([window.at(c/q0)['rms_mV'] for c in grid])
    if not np.isfinite(vals).any():return dict(capacity=grid,rms=vals,best=None,accepted=False,width_Ah=np.inf,reason='no_domain_supported_candidate')
    best=int(np.nanargmin(vals));minimum=float(vals[best]);allow=vals<=minimum+delta
    if fine:
        add=[]
        for k in range(len(grid)-1):
            if allow[k]!=allow[k+1] and np.isfinite(vals[k]) and np.isfinite(vals[k+1]):
                add.extend(np.arange(grid[k],grid[k+1]+.00001,CFG['profile_boundary_step_Ah']).tolist())
        if add:
            grid=np.unique(np.r_[grid,add]);vals=np.array([window.at(c/q0)['rms_mV'] for c in grid]);best=int(vals.argmin());minimum=float(vals[best]);allow=vals<=minimum+delta
    subset=grid[allow]
    width=float(subset.max()-subset.min())
    touched=bool(allow[0] or allow[-1])
    unsupported=bool(np.any(~np.isfinite(vals)))
    boundary_best=bool(best in [0,len(grid)-1])
    fit=window.at(grid[best]/q0)
    accepted=bool(width<=CFG['profile_width_gate_Ah'] and not touched and not unsupported and not boundary_best)
    return dict(capacity=grid,rms=vals,best=fit,best_capacity_Ah=float(grid[best]),minimum_rms_mV=minimum,delta_mV=float(delta),
        lower_Ah=float(subset.min()),upper_Ah=float(subset.max()),width_Ah=width,touches_scan_boundary=touched,
        unsupported_candidate_count=int(np.sum(~np.isfinite(vals))),accepted=accepted,reference='fixed CK0 initial condition; only common alpha projected; not a confidence interval')

def diagnostics(window,fit):
    # Dimensionless scaling exposes local correlations; profiles remain primary.
    parameter=np.r_[fit['alpha'],fit['params'].ravel()]
    npar=fit['params'].shape[1]
    scale=np.r_[.10,np.tile([5.,.01,.10,.10,.001][:npar],4)]
    def residual(vec):
        alpha=vec[0];par=vec[1:].reshape(4,npar);rr=[]
        for c in range(4):
            x,a=design(window.net,window.j,window.h,alpha,par[c,0],window.tau,window.temp_delta)
            try:pred=window.ref.values(x,c)+a@par[c,1:]
            except ValueError:return None
            rr.append((pred-window.y[:,c])*window.w/2)
        return np.concatenate(rr)
    base=residual(parameter);cols=[]
    for k in range(len(parameter)):
        eps=1e-3*scale[k];vec=parameter.copy();vec[k]+=eps;r=residual(vec)
        if r is None:vec[k]-=2*eps;r=residual(vec);eps=-eps
        cols.append((r-base)/eps*scale[k] if r is not None else np.zeros_like(base))
    jac=np.stack(cols,axis=1);sv=np.linalg.svd(jac,compute_uv=False)
    normalized=jac/(np.linalg.norm(jac,axis=0)+1e-15)
    corr=normalized.T@normalized
    pairs=[]
    for k in range(1,len(parameter)):
        if abs(corr[0,k])>=.80:pairs.append(dict(parameter_index=k,capacity_column_correlation=float(corr[0,k])))
    return dict(singular_values=sv.tolist(),condition_number=float(sv[0]/max(sv[-1],1e-15)),capacity_high_correlation_pairs=pairs,
        interpretation='Local normalized sensitivity only; weak rank plus global refitted profile are both reported')

def numerical_refit_witness(window,C):
    """Independent full nonlinear optimizer checks the variable-projection result."""
    fit=window.at(C/window.ref.capacity(1.));alpha=fit['alpha'];par=fit['params'];npar=par.shape[1]
    if not np.isfinite(fit['loss']):return dict(capacity_Ah=C,available=False,reason='domain_unsupported')
    low_d=max(0.,-window.net.min()/alpha);high_d=min(window.dmax,window.ref.maximum-window.net.max()/alpha)
    lower=np.tile([low_d,-window.bias,0,0,-.002][:npar],4)
    upper=np.tile([high_d,window.bias,.30,.30,.002][:npar],4)
    def fun(vec):
        pp=vec.reshape(4,npar);res=[]
        for c in range(4):
            x,a=design(window.net,window.j,window.h,alpha,pp[c,0],window.tau,window.temp_delta)
            res.append((window.ref.values(x,c)+a@pp[c,1:]-window.y[:,c])*window.w/2)
        return np.concatenate(res)
    initial=np.clip(par.ravel(),lower+1e-9,upper-1e-9)
    opt=least_squares(fun,initial,bounds=(lower,upper),x_scale='jac',max_nfev=100,ftol=1e-9,xtol=1e-9)
    return dict(capacity_Ah=float(C),available=True,variable_projection_rms_mV=fit['rms_mV'],independent_optimizer_rms_mV=float(np.linalg.norm(opt.fun)*1000),
        optimizer_success=bool(opt.success),optimizer_calls=int(opt.nfev),parameters=opt.x.reshape(4,npar).tolist())
