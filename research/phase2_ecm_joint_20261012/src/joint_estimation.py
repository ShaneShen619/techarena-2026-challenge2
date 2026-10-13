"""Low-dimensional moving-window co-estimation, variable projection and causal initialization."""
from __future__ import annotations
import copy
import numpy as np
from scipy.optimize import lsq_linear,minimize_scalar
from common import CFG
from ecm import make_points,design,actual_response,predict

def linear_fit(a,y,w,bias=.05,temperature=True):
    aw=a*w[:,None];yw=y*w
    low=np.array([-bias,0,0,-CFG['actual_temperature_linear_bound_V_per_C']])[:a.shape[1]]
    high=np.array([bias,.30,.30,CFG['actual_temperature_linear_bound_V_per_C']])[:a.shape[1]]
    coef=np.linalg.lstsq(aw,yw,rcond=None)[0]
    if np.any(coef<low) or np.any(coef>high):coef=lsq_linear(aw,yw,bounds=(low,high),method='bvls',tol=1e-10,max_iter=60).x
    residual=a@coef-y
    return float(np.sum((residual*w)**2)),coef,residual

class Window:
    def __init__(self,ref,events,tau,rests=True,charge_history=True,bias=None,dmax=None,temperature=True,mean_cells=False):
        if not events:raise ValueError('empty_historical_window')
        self.ref=ref;self.events=events;self.tau=float(tau);self.rests=rests;self.charge_history=charge_history
        self.bias=CFG['bias_bound_V'] if bias is None else bias
        self.dmax=CFG['anchor_offset_bounds_Ah'][1] if dmax is None else dmax
        self.temperature=temperature;self.mean_cells=mean_cells
        self.points=[make_points(e,tau,rests,charge_history,mean_cells) for e in events]
        self.net=np.concatenate([p['net'] for p in self.points]);self.j=np.concatenate([p['j'] for p in self.points]);self.h=np.concatenate([p['h'] for p in self.points])
        self.y=np.concatenate([p['y'] for p in self.points]);self.w=np.concatenate([p['w']/np.sqrt(len(events)) for p in self.points])
        self.temp_delta=np.concatenate([p['temp_delta'] for p in self.points]) if temperature else None
        self.cached={}

    def cell(self,alpha,c):
        low=max(0.,-float(self.net.min())/alpha)
        high=min(self.dmax,self.ref.maximum-float(self.net.max())/alpha)
        if high<low:return np.inf,np.full(5 if self.temperature else 4,np.nan)
        def calc(d):
            x,a=design(self.net,self.j,self.h,alpha,d,self.tau,self.temp_delta)
            target=self.y[:,c]-self.ref.values(x,c)
            loss,coef,_=linear_fit(a,target,self.w,self.bias,self.temperature)
            return loss,coef
        grid=np.unique(np.clip(CFG['profile_multistart_offsets_Ah']+[low,high],low,high))
        scores=np.array([calc(d)[0] for d in grid]);idx=int(scores.argmin());best_d=float(grid[idx]);best_loss=float(scores[idx])
        for k in np.argsort(scores)[:2]:
            lo=grid[max(0,int(k)-1)];hi=grid[min(len(grid)-1,int(k)+1)]
            if hi-lo>1e-5:
                opt=minimize_scalar(lambda d:calc(d)[0],bounds=(lo,hi),method='bounded',options={'xatol':.01,'maxiter':18})
                if opt.fun<best_loss:best_d=float(opt.x);best_loss=float(opt.fun)
        loss,coef=calc(best_d)
        return loss,np.r_[best_d,coef]

    def at(self,alpha):
        key=round(float(alpha),10)
        if key in self.cached:return self.cached[key]
        fits=[self.cell(alpha,c) for c in range(4)]
        loss=float(np.mean([r[0] for r in fits]));params=np.stack([r[1] for r in fits])
        out=dict(alpha=float(alpha),loss=loss,rms_mV=float(np.sqrt(loss)*1000),params=params,tau=self.tau,
            rests=self.rests,charge_history=self.charge_history,temperature=self.temperature,
            history_ids=[e['id'] for e in self.events],available_after=max(e['available_after'] for e in self.events),
            parameterization='shared_anchor_offset_bias_R0_R1_temperature_per_cell')
        self.cached[key]=out
        return out

    def fit(self,free=False):
        if not free:return self.at(1.)
        grid=np.linspace(*CFG['alpha_bounds'],15)
        vals=np.array([self.at(a)['loss'] for a in grid]);best=int(vals.argmin())
        if not np.isfinite(vals[best]):raise ValueError('all_historical_parameters_outside_domain')
        out=self.at(grid[best])
        for k in np.argsort(vals)[:2]:
            lo=grid[max(0,int(k)-1)];hi=grid[min(len(grid)-1,int(k)+1)]
            opt=minimize_scalar(lambda a:self.at(a)['loss'],bounds=(lo,hi),method='bounded',options={'xatol':.001,'maxiter':15})
            if opt.fun<out['loss']:out=self.at(opt.x)
        return out

def initialized(ref,e,fit,budget=0,use_rest=True):
    result=copy.deepcopy(fit)
    params=result['params'].copy()
    h=actual_response(e,result['tau'],result.get('charge_history',True))
    pre=(e['phase']==0)&(e['t']>=-300)
    if use_rest and pre.sum()>=5:
        for c in range(4):
            x,a=design(e['net'][pre],e['j'][pre],h[pre],result['alpha'],params[c,0],result['tau'],e['temp'][pre]-e['T'] if result.get('temperature',True) else None)
            pred=ref.values(x,c)+a@params[c,1:]
            params[c,1]=np.clip(params[c,1]+np.median(e['y'][pre,c]-pred),-CFG['bias_bound_V'],CFG['bias_bound_V'])
    prefix=(e['phase']==1)&(e['q']<=budget)&(e['t']>=20)
    if budget>0 and prefix.sum()>=3:
        for c in range(4):
            center=params[c,0];lo=max(0,center-3);hi=min(CFG['anchor_offset_bounds_Ah'][1],center+3)
            # Bound by observed prefix only, never by target's future ending charge.
            hi=min(hi,ref.maximum-float(e['net'][prefix].max())/result['alpha'])
            def calc(d):
                x,a=design(e['net'][prefix],e['j'][prefix],h[prefix],result['alpha'],d,result['tau'],e['temp'][prefix]-e['T'] if result.get('temperature',True) else None)
                residual=e['y'][prefix,c]-ref.values(x,c)-a@params[c,1:]
                shift=float(np.median(residual));res=residual-shift
                # Arrival regularization is explicit; does not count as capacity information.
                return float(np.mean(res**2)+((d-center)/3*.001)**2),shift
            if hi>lo:
                opt=minimize_scalar(lambda d:calc(d)[0],bounds=(lo,hi),method='bounded',options={'xatol':.01,'maxiter':18})
                params[c,0]=float(opt.x)
            _,shift=calc(params[c,0])
            params[c,1]=np.clip(params[c,1]+shift,-CFG['bias_bound_V'],CFG['bias_bound_V'])
    result['params']=params
    result['target_voltage_available_until_Ah']=float(budget)
    result['target_pre_rest_used']=bool(use_rest and pre.sum()>=5)
    return result

def previous_curve(e,last,budget=0,use_rest=False):
    if last is None:raise ValueError('no_previous_matching_program')
    a=last['phase']==1;b=e['phase']==1
    if e['q'][b].max()>last['q'][a].max()+.1:raise ValueError('previous_curve_domain')
    prediction=np.stack([np.interp(e['q'],last['q'][a],last['y'][a,c]) for c in range(4)],axis=1)
    if use_rest:
        pre=(e['phase']==0)&(e['t']>=-300);oldpre=(last['phase']==0)&(last['t']>=-300)
        if pre.sum()>=5 and oldpre.sum()>=5:prediction+=np.median(e['y'][pre],axis=0)-np.median(last['y'][oldpre],axis=0)
    if budget>0:
        use=(e['phase']==1)&(e['q']>=.2)&(e['q']<=budget)
        if use.any():prediction+=np.median(e['y'][use]-prediction[use],axis=0)
    return prediction

def voltage_metrics(e,prediction):
    score=(e['phase']==1)&(e['q']>=CFG['score_begin_Ah'])
    valid=score&np.isfinite(prediction).all(axis=1)
    if not valid.any():raise ValueError('no_finite_score')
    err=(prediction[valid]-e['y'][valid])*1000
    return dict(mae_mV=float(abs(err).mean()),rms_mV=float(np.sqrt(np.mean(err**2))),p95_mV=float(np.quantile(abs(err),.95)),
        max_mV=float(abs(err).max()),per_cell_mae_mV=abs(err).mean(axis=0).tolist(),sample_coverage=float(valid.sum()/score.sum()),n_score=int(valid.sum()))
