"""Loaded-curve registration and reference-charge EKF, with explicit domains."""
from __future__ import annotations
import copy, sys
import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear, minimize_scalar
from audit import ROOT, CFG
sys.path.insert(0,str(ROOT/'research/phase1_pack_trend_20261011/src'))
from pack import PackPrototype

class Template:
    def __init__(self, x=None, y=None, q0=100.41):
        if x is None:
            ref=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
            self.pack=PackPrototype(ref)
            ref['bin']=(ref.discharged_Ah/self.pack.axis_factor/.10).round().astype(int)
            f=ref.groupby('bin',sort=True)[[f'cell{i}_V' for i in range(1,5)]].median()
            self.x=f.index.to_numpy(float)*.10;self.y=f.to_numpy(float)
        else:self.x=np.asarray(x);self.y=np.asarray(y);self.pack=None
        self.q0=q0
        self.slope=(self.y[-1]-self.y[-3])/(self.x[-1]-self.x[-3])
    def values(self,x,cell):
        x=np.asarray(x,float)
        if np.any(x<0) or np.any(x>self.x[-1]+2+1e-9):raise ValueError('template_domain')
        out=np.interp(x,self.x,self.y[:,cell])
        return np.where(x>self.x[-1],self.y[-1,cell]+self.slope[cell]*(x-self.x[-1]),out)
    def derivative(self,x,cell):
        lo=max(0,float(x)-.1);hi=min(self.x[-1]+2,float(x)+.1)
        return float((self.values(hi,cell)-self.values(lo,cell))/(hi-lo)) if hi>lo else 0
    def capacity(self,s):
        s=np.broadcast_to(np.asarray(s,float),(4,))
        if self.pack is not None:return self.pack.capacity(s)
        upper=float(np.min(s*(self.x[-1]+2)))
        grid=np.unique(np.r_[0,upper,*[s[c]*self.x for c in range(4)]])
        grid=grid[(grid>=0)&(grid<=upper)]
        v=sum(self.values(grid/s[c],c) for c in range(4))
        idx=np.flatnonzero(v<=11.2)
        if not len(idx):raise ValueError('reference_cutoff_outside_domain')
        k=idx[0]
        return float(grid[0] if k==0 else np.interp(11.2,v[k-1:k+1][::-1],grid[k-1:k+1][::-1]))

def filtered(t,j,tau,initial=0):
    out=np.zeros(len(t));out[0]=initial
    for k in range(1,len(t)):
        a=np.exp(-(t[k]-t[k-1])/tau)
        out[k]=a*out[k-1]+(1-a)*j[k-1]
    return out

def restore(e,tau,budget=1800,endpoint=False,default=None):
    t=np.asarray(e['pre_t']);y=np.asarray(e['pre_y'])
    if len(t)<5:return np.zeros(4), False, np.zeros(4)
    # A waiting budget means the FIRST observed rest prefix, not its last window.
    use=t<=t[0]+budget;t=t[use];y=y[use]
    if len(t)<5:return np.zeros(4),False,np.zeros(4)
    if t[-1]-t[0]<.9*budget:return np.zeros(4),False,np.zeros(4)
    if endpoint:
        return (np.zeros(4) if default is None else np.asarray(default)),True,y[-1]
    # No SOC map: unknown asymptote + one recovery term only.
    a=np.column_stack([np.ones(len(t)),np.exp(-(t-t[0])/tau)])
    coef=np.linalg.lstsq(a,y,rcond=None)[0]
    residual=coef[1]*np.exp(-(0-t[0])/tau)
    ok=bool(np.max(np.abs(residual))<=.1)
    return residual,ok,coef[0]

def prepare(e,tau,mask=None):
    use=(e['t']>=20) if mask is None else mask&(e['t']>=20)
    return dict(q=e['q'][use],t=e['t'][use],j=e['j'][use],y=e['y'][use],h=filtered(e['t'],e['j'],tau)[use])

def design(p,s,d,tau):
    x=p['q']/s+d
    href=5.1*(-np.expm1(-3600*x/(5.1*tau)))
    a=np.column_stack([np.ones(len(x)),-(p['j']-5.1)/20,-(p['h']-href)/20,np.exp(-p['t']/tau)])
    return a,x

def linfit(a,y,fixed_a=None,bias=.05):
    if fixed_a is not None:
        y=y-a[:,-1]*fixed_a;a=a[:,:-1]
    low=np.array([-bias,0,0,-.1])[:a.shape[1]];high=np.array([bias,.3,.3,.1])[:a.shape[1]]
    coef=np.linalg.lstsq(a,y,rcond=None)[0]
    if np.any(coef<low) or np.any(coef>high):
        coef=lsq_linear(a,y,bounds=(low,high),method='bvls',max_iter=25).x
    residual=a@coef-y
    if fixed_a is not None:coef=np.r_[coef,fixed_a]
    return float(np.mean(residual**2)),coef

def fit_cell(template,p,s,c,tau,d_fixed=None,prior=None,fixed_a=None,bias=.05):
    dmax=min(65,template.x[-1]+2-float(p['q'].max())/s)
    if dmax<0:raise ValueError('template_domain')
    def calc(d):
        a,x=design(p,s,d,tau)
        loss,coef=linfit(a,p['y'][:,c]-template.values(x,c),fixed_a,bias)
        if prior is not None:loss+=((d-prior)/5*.001)**2
        return loss,coef
    if d_fixed is not None:
        if d_fixed<0 or d_fixed>dmax:raise ValueError('anchor_outside_template')
        d=float(d_fixed);loss,coef=calc(d)
    else:
        grid=np.unique(np.minimum(np.r_[0,.1,.5,2,5,10,20,35,50,dmax],dmax))
        score=np.array([calc(d)[0] for d in grid]);idx=int(score.argmin());d=float(grid[idx]);loss=float(score[idx])
        for k in np.argsort(score)[:2]:
            lo=grid[max(0,k-1)];hi=grid[min(len(grid)-1,k+1)]
            if hi>lo+.001:
                r=minimize_scalar(lambda z:calc(z)[0],bounds=(lo,hi),method='bounded',options={'maxiter':18,'xatol':.01})
                if r.fun<loss:d=float(r.x);loss=float(r.fun)
        loss,coef=calc(d)
    return loss,np.r_[d,coef]

def predict(template,p,s,par,c,tau):
    a,x=design(p,s,par[0],tau)
    return template.values(x,c)+a@par[1:]

def profile(template,e,tau,prior=False,rest_mode='free',bias=.05,fixed_d=None):
    p=prepare(e,tau);sgrid=np.round(np.arange(.70,1.0501,.025),6)
    loss=np.full((len(sgrid),4),np.inf);params=np.zeros((len(sgrid),4,5))
    amp,ok,_=restore(e,tau)
    for k,s in enumerate(sgrid):
        for c in range(4):
            pr=e['net_since_anchor_Ah']/s if prior and np.isfinite(e.get('net_since_anchor_Ah',np.nan)) and e['net_since_anchor_Ah']>=0 else None
            fix=amp[c] if rest_mode=='shape' and ok else None
            fixed=0. if fixed_d=='zero' else e['net_since_anchor_Ah']/s if fixed_d=='anchor' and np.isfinite(e.get('net_since_anchor_Ah',np.nan)) and e['net_since_anchor_Ah']>=0 else None
            try:loss[k,c],params[k,c]=fit_cell(template,p,s,c,tau,d_fixed=fixed,prior=pr,fixed_a=fix,bias=bias)
            except ValueError:loss[k,c]=np.inf
    return dict(sgrid=sgrid,loss=loss,params=params)

def choose(pr,mode='joint'):
    if mode=='shift':idx=np.full(4,int(np.argmin(abs(pr['sgrid']-1))))
    elif mode=='free4':idx=np.argmin(pr['loss'],axis=0)
    else:idx=np.full(4,int(np.argmin(pr['loss'].mean(axis=1))))
    return pr['sgrid'][idx],np.stack([pr['params'][idx[c],c] for c in range(4)])

def forecast(template,e,s,par,tau,budget,calibration='shift',rest_mode=None):
    par=np.array(par,copy=True);s=np.broadcast_to(s,(4,)).copy()
    full=prepare(e,tau, np.ones(len(e['t']),bool))
    if rest_mode:
        amp,ok,_=restore(e,tau,endpoint=rest_mode=='endpoint',default=par[:,-1])
        if ok:par[:,-1]=amp
    pre=(e['q']<=budget)&(e['t']>=20)
    if budget>0 and pre.sum()>=3:
        p=prepare(e,tau,pre)
        for c in range(4):
            if calibration=='d':
                center=par[c,0];lo=max(0,center-5);hi=min(65,center+5,template.x[-1]+2-e['q'][-1]/s[c])
                def fun(d):
                    pp=par[c].copy();pp[0]=d
                    res=predict(template,p,s[c],pp,c,tau)-p['y'][:,c]
                    return np.mean(res**2)+((d-center)/5*.001)**2
                if hi>lo:
                    opt=minimize_scalar(fun,bounds=(lo,hi),method='bounded',options={'xatol':.01,'maxiter':20});par[c,0]=opt.x
            # Equal target prefix budget; intercept correction follows d calibration.
            residual=p['y'][:,c]-predict(template,p,s[c],par[c],c,tau)
            correction=float(np.median(residual))
            par[c,1]+=correction
    out=np.stack([predict(template,full,s[c],par[c],c,tau) for c in range(4)],axis=1)
    return full,out,par

def ekf(template,e,s,par,tau,budget,rest_mode=True,observe_full=False,initial_error=0):
    """Charge x and relative polarization p. No observation in forecast suffix."""
    n=len(e['t']);out=np.full((n,4),np.nan);xtrace=np.full((n,4),np.nan);variance=np.full((n,4),np.nan)
    s=np.broadcast_to(s,(4,));par=np.array(par,copy=True)
    amp,ok,_=restore(e,tau)
    for c in range(4):
        b,r0,rp,a=par[c,1:];r0/=20;rp/=20
        if rest_mode and ok:a=amp[c]
        # y=B(x)-r0*(j-5.1)-p+rp*href(x)+b; p(0)=-a.
        state=np.array([par[c,0]+initial_error,-a],float);P=np.diag([25.,.01**2])
        for k in range(n):
            if k:
                dt=e['t'][k]-e['t'][k-1];decay=np.exp(-dt/tau)
                state[0]+=(e['q'][k]-e['q'][k-1])/s[c]
                state[1]=decay*state[1]+(1-decay)*rp*e['j'][k-1]
                F=np.diag([1.,decay]);P=F@P@F.T+np.diag([.003**2*dt,1e-7*dt])
            if not 0<=state[0]<=template.x[-1]+2:continue
            def obs(x,p):
                href=5.1*(-np.expm1(-3600*x/(5.1*tau)))
                return float(template.values(x,c)-r0*(e['j'][k]-5.1)-p+rp*href+b)
            pred=obs(*state)
            h=template.derivative(state[0],c)+rp*3600/tau*np.exp(-3600*state[0]/(5.1*tau))
            H=np.array([h,-1.])
            update=(e['t'][k]>=20) and (observe_full or e['q'][k]<=budget)
            if update:
                den=float(H@P@H+.003**2);K=P@H/den
                proposal=state+K*(e['y'][k,c]-pred)
                if 0<=proposal[0]<=template.x[-1]+2:
                    state=proposal;A=np.eye(2)-np.outer(K,H);P=A@P@A.T+np.outer(K,K)*.003**2
                    pred=obs(*state)
            out[k,c]=pred;xtrace[k,c]=state[0];variance[k,c]=P[0,0]
    return out,xtrace,variance

def last_curve(e,last,budget):
    if last is None:raise ValueError('no_same_program_history')
    if e['q'][-1]>last['q'][-1]+.1:raise ValueError('prior_curve_domain')
    pred=np.stack([np.interp(e['q'],last['q'],last['y'][:,c]) for c in range(4)],axis=1)
    pre=(e['q']>=.2)&(e['q']<=budget)
    if budget>0 and pre.any():pred+=np.median(e['y'][pre]-pred[pre],axis=0)
    return pred

def errors(y,pred,q,pack=None):
    use=(q>=2)&np.isfinite(pred).all(axis=1)
    if not use.any():raise ValueError('no_valid_score_samples')
    diff=(pred[use]-y[use])*1000
    return dict(mae_mV=float(np.abs(diff).mean()),rms_mV=float(np.sqrt(np.mean(diff**2))),pack_mae_mV=float(np.abs(diff.sum(axis=1)).mean()),n_score=int(use.sum()),max_cell_error_mV=float(np.abs(diff).max()),per_cell_mae_mV=np.abs(diff).mean(axis=0).tolist())
