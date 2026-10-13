"""Joint four-cell position/polarization EKF conditional on frozen slow parameters."""
from __future__ import annotations
import numpy as np
from common import CFG
from ecm import actual_response

def gaussian_nlml(innovation,S):
    sign,logdet=np.linalg.slogdet(S)
    if sign<=0:raise ValueError('nonpositive_innovation_covariance')
    return float(.5*(innovation@np.linalg.solve(S,innovation)+logdet+len(innovation)*np.log(2*np.pi)))

def joseph(P,H,R,K):
    A=np.eye(len(P))-K@H
    out=A@P@A.T+K@R@K.T
    return (out+out.T)/2

def track(ref,e,fit,observe=True):
    tau=fit['tau'];alpha=fit['alpha'];par=fit['params'];h=actual_response(e,tau,fit.get('charge_history',True))
    state=np.r_[e['net'][0]/alpha+par[:,0],par[:,3]/20*h[0]]
    P=np.diag(np.r_[np.full(4,25.),np.full(4,.003**2)])
    R=.003**2*(.85*np.eye(4)+.15*np.ones((4,4)))
    rows=[];nlml=0.
    for k,t in enumerate(e['t']):
        if k:
            dt=t-e['t'][k-1];a=np.exp(-dt/tau)
            state[:4]+=(e['net'][k]-e['net'][k-1])/alpha
            state[4:]=a*state[4:]+(1-a)*par[:,3]/20*e['j'][k-1]
            F=np.diag(np.r_[np.ones(4),np.full(4,a)])
            # Shared current uncertainty produces correlated position noise.
            shared=np.r_[np.ones(4)*dt/(3600*alpha)*.05,np.zeros(4)]
            P=F@P@F.T+np.outer(shared,shared)+np.diag(np.r_[np.full(4,1e-7*dt),np.full(4,1e-8*dt)])
        if np.any(state[:4]<0) or np.any(state[:4]>ref.maximum):
            rows.append(dict(index=k,valid=False,reason='state_outside_reference_domain'));continue
        href=5.1*(-np.expm1(-3600*state[:4]/(5.1*tau)))
        dv=np.array([ref.values(state[c],c) for c in range(4)])+par[:,1]-par[:,2]/20*(e['j'][k]-5.1)-state[4:]+par[:,3]/20*href
        if fit.get('temperature',True):dv+=par[:,4]*(e['temp'][k]-e['T'])
        H=np.zeros((4,8))
        for c in range(4):
            H[c,c]=ref.derivative(state[c],c)+par[c,3]/20*3600/tau*np.exp(-3600*state[c]/(5.1*tau));H[c,c+4]=-1
        innovation=e['y'][k]-dv;S=H@P@H.T+R
        updated=False
        if observe and not (0<=t<20):
            K=np.linalg.solve(S,H@P).T;proposal=state+K@innovation
            if np.all(proposal[:4]>=0)&np.all(proposal[:4]<=ref.maximum):
                state=proposal;P=joseph(P,H,R,K);updated=True
            nlml+=gaussian_nlml(innovation,S)
        rows.append(dict(index=k,valid=True,updated=updated,reference_position_Ah=state[:4].copy(),position_variance_Ah2=np.diag(P)[:4].copy(),polarization_V=state[4:].copy(),
            predicted_before_update_V=dv.copy(),innovation_mV=innovation*1000,min_covariance_eigenvalue=float(np.linalg.eigvalsh(P).min())))
    return rows,dict(nlml=nlml,capacity_frozen=True,conditional_covariance='Fixed alpha/R/b/tau uncertainty omitted; not calibrated SOC or capacity intervals')
