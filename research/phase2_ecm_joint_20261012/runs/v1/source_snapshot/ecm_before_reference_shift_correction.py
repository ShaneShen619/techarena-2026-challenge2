"""Shared loaded-reference ECM and explicit official first-pack-cutoff projection."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.signal import lfilter
from scipy.optimize import brentq
from common import ROOT,CFG,CELLS

class Reference:
    def __init__(self,x=None,v=None,pack=None,q0=None):
        self.q0=float(CFG['q0_Ah'] if q0 is None else q0)
        if x is None:
            f=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz').sort_values('discharged_Ah').groupby('discharged_Ah',sort=True).last()
            raw_x=f.index.to_numpy(float);v=f[CELLS].to_numpy(float);pack=f.voltage_V.to_numpy(float)
            hit=np.flatnonzero(pack<=CFG['cutoff_pack_V'])[0]
            raw_root=float(np.interp(CFG['cutoff_pack_V'],pack[hit-1:hit+1][::-1],raw_x[hit-1:hit+1][::-1]))
            self.axis_factor=raw_root/self.q0;x=raw_x/self.axis_factor
        else:self.axis_factor=1.0
        self.raw_x=np.asarray(x,float);self.raw_v=np.asarray(v,float)
        self.residual=np.asarray(pack,float)-self.raw_v.sum(axis=1) if pack is not None else np.zeros(len(x))
        # Fit table is a declared median reduction; original table is retained for cutoff.
        f=pd.DataFrame(self.raw_v);f['bin']=np.round(self.raw_x/.05).astype(int)
        smooth=f.groupby('bin').median();self.x=smooth.index.to_numpy(float)*.05;self.v=smooth.iloc[:,:4].to_numpy(float)
        # Keep exact domain endpoints, never invent negative coordinates/tail.
        self.x=np.r_[self.raw_x[0],self.x[(self.x>self.raw_x[0])&(self.x<self.raw_x[-1])],self.raw_x[-1]]
        self.v=np.stack([np.interp(self.x,smooth.index.to_numpy(float)*.05,smooth[c]) for c in range(4)],axis=1)
        self.v[0]=self.raw_v[0];self.v[-1]=self.raw_v[-1]
        self.maximum=float(self.raw_x[-1])
        self.smoothing_rms_mV=float(np.sqrt(np.mean((self.values(self.raw_x)-self.raw_v)**2))*1000)

    def values(self,x,cell=None,raw=False):
        x=np.asarray(x,float)
        if np.any(~np.isfinite(x)) or np.any(x<self.raw_x[0]-1e-8) or np.any(x>self.maximum+1e-8):raise ValueError('reference_coordinate_outside_observed_domain')
        xx,vv=(self.raw_x,self.raw_v) if raw else (self.x,self.v)
        if cell is not None:return np.interp(x,xx,vv[:,cell])
        return np.stack([np.interp(x,xx,vv[:,c]) for c in range(4)],axis=-1)

    def derivative(self,x,cell):
        x=float(x);lo=max(self.raw_x[0],x-.10);hi=min(self.maximum,x+.10)
        if hi<=lo:return 0.0
        return float((self.values(hi,cell)-self.values(lo,cell))/(hi-lo))

    def pack_voltage(self,q,alpha=1.0,reference_shift=None,aging_R=None,residual_delta_V=0):
        aa=np.broadcast_to(np.asarray(alpha,float),(4,))
        shifts=np.zeros(4) if reference_shift is None else np.asarray(reference_shift,float)
        rr=np.zeros(4) if aging_R is None else np.asarray(aging_R,float)
        if np.any(aa<=0) or np.any(shifts<0):raise ValueError('unavailable_reference_initial_state')
        coords=np.asarray(q)[...,None]/aa+shifts
        cells=np.stack([self.values(coords[...,c],c,raw=True) for c in range(4)],axis=-1)-5.1*rr
        chain_coord=np.asarray(q)/aa.mean()
        if np.any(chain_coord>self.maximum+1e-8):raise ValueError('reference_residual_domain')
        return cells.sum(axis=-1)+np.interp(chain_coord,self.raw_x,self.residual)+residual_delta_V

    def capacity(self,alpha=1.0,reference_shift=None,aging_R=None,residual_delta_V=0):
        aa=np.broadcast_to(np.asarray(alpha,float),(4,));shift=np.zeros(4) if reference_shift is None else np.asarray(reference_shift,float)
        upper=float(min(np.min(aa*(self.maximum-shift)),aa.mean()*self.maximum))
        if upper<=0:raise ValueError('reference_no_supported_domain')
        knots=np.unique(np.r_[0,upper,*[aa[c]*(self.raw_x-shift[c]) for c in range(4)],aa.mean()*self.raw_x])
        knots=knots[(knots>=0)&(knots<=upper)]
        v=self.pack_voltage(knots,aa,shift,aging_R,residual_delta_V)
        hit=np.flatnonzero(v<=CFG['cutoff_pack_V']+1e-10)
        if not len(hit):raise ValueError('reference_cutoff_not_observed_no_tail_extrapolation')
        k=int(hit[0])
        if k==0:return 0.0
        if abs(v[k]-CFG['cutoff_pack_V'])<1e-10:return float(knots[k])
        return float(brentq(lambda q:float(self.pack_voltage(q,aa,shift,aging_R,residual_delta_V))-CFG['cutoff_pack_V'],knots[k-1],knots[k],xtol=1e-9))

def filtered(t,j,tau,initial=0.0):
    t=np.asarray(t,float);j=np.asarray(j,float)
    if len(t)==1:return np.array([initial])
    dt=np.diff(t)
    if np.any(dt<=0) or np.any(dt>CFG['maximum_gap_s']+1e-6):raise ValueError('unobserved_dynamic_gap')
    if np.ptp(dt)<1e-8:
        a=float(np.exp(-dt[0]/tau))
        return lfilter([0,1-a],[1,-a],j,zi=[initial])[0]
    out=np.empty(len(t));out[0]=initial
    for k in range(1,len(t)):
        a=np.exp(-dt[k-1]/tau);out[k]=a*out[k-1]+(1-a)*j[k-1]
    return out

def actual_response(e,tau,charge_history=True):
    if charge_history:return filtered(e['htime'],e['hj'],tau)[e['hobs']]
    # Ablation: reset at discharge, no inherited charge/daily-current polarization.
    use=e['t']>=0;out=np.zeros(len(e['t']))
    if use.any():
        start=int(e['hobs'][np.flatnonzero(use)[0]])
        response=filtered(e['htime'][start:],e['hj'][start:],tau)
        out[use]=response[e['hobs'][use]-start]
    return out

def make_points(e,tau,rests=True,charge_history=True,mean_cells=False):
    h=actual_response(e,tau,charge_history)
    use=np.ones(len(e['t']),bool) if rests else e['phase']==1
    # 10s sampling cannot resolve the first two transition samples.
    use &= ~((e['t']>=0)&(e['t']<20))
    use &= ~((e['phase']==2)&(e['t']<np.max(e['t'][e['phase']==1])+20))
    ids=np.flatnonzero(use)[::CFG['fit_stride']]
    phase=e['phase'][ids];counts=np.bincount(phase,minlength=3);npresent=int((counts>0).sum())
    w=np.array([1/np.sqrt(npresent*counts[p]) for p in phase])
    y=e['y'][ids]
    if mean_cells:y=np.repeat(y.mean(axis=1)[:,None],4,axis=1)
    return dict(net=e['net'][ids],j=e['j'][ids],h=h[ids],phase=phase,w=w,y=y,event=e,indices=ids,temp_delta=e['temp'][ids]-e['T'])

def design(net,j,h,alpha,d,tau,temp_delta=None):
    x=net/alpha+d
    href=5.1*(-np.expm1(-3600*x/(5.1*tau)))
    a=np.column_stack([np.ones(len(x)),-(j-5.1)/20,-(h-href)/20])
    if temp_delta is not None:a=np.column_stack([a,temp_delta])
    return x,a

def predict(ref,e,fit):
    h=actual_response(e,fit['tau'],fit.get('charge_history',True))
    out=[]
    for c in range(4):
        d=fit['params'][c,0];coef=fit['params'][c,1:]
        x,a=design(e['net'],e['j'],h,fit['alpha'],d,fit['tau'],e['temp']-e['T'] if fit.get('temperature',True) else None)
        out.append(ref.values(x,c)+a@coef)
    return np.stack(out,axis=1)
