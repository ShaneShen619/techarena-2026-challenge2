"""Independent two-RC nonlinear LFP-like generator; synthetic evidence only."""
from __future__ import annotations
import json,copy
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from audit import RUN,CFG
from engine import Template,profile,choose,prepare,predict,restore,ekf

def ocv(z,T=25,shape=0):
    z=np.asarray(z)
    return (3.30+.04*(z-.5)+.27*np.tanh((z-.985)/.02)+.30*np.tanh((z-.025)/.018)
            +.012*np.tanh((z-.50)/.06)+.00015*(T-25)+shape*(z-.5)**2)

def step(z,p,h,j,dt,Q,r,T):
    # j positive discharge, eta charge=0.998. Generator has two RCs and hysteresis.
    z=z-j*dt/(3600*Q)*(0.998 if j<0 else 1)
    decay=np.exp(-dt/np.array([70.,900.]))
    p=p*decay[:,None]+(1-decay[:,None])*r[1:]*j
    mem=np.exp(-abs(j)*dt/(3600*3))
    h=h*mem+(1-mem)*(-np.sign(j)*.004)
    return z,p,h

def charge(Q,r,T,start,tail=5.1):
    z=start.copy();p=np.zeros((2,4));h=np.zeros(4);dt=30;lastI=20.4;cv=0
    for k in range(1500):
        available=(14.-float((ocv(z,T)-p.sum(axis=0)+h).sum()))/r[0].sum()
        I=max(0,min(20.4,available))
        v=ocv(z,T)-p.sum(axis=0)+h+I*r[0]
        if I<20.4:cv+=dt
        if k>40 and I<=tail:break
        z,p,h=step(z,p,h,-I,dt,Q,r,T)
        lastI=I
    return z,p,h,dict(end_pack_V=float(v.sum()),tail_A=float(I),cv_s=cv,qualified=bool(v.sum()>=13.95 and I<=5.5 and cv>=60))

def reference(Q,r,T,z,p,h,shape=0,dt=30):
    q=np.arange(0,float(Q.min())*1.10,5.1*dt/3600)
    zseq=z[None,:]-q[:,None]/Q[None,:]
    duration=q*3600/5.1
    pol=np.zeros_like(zseq)
    for c in range(2):
        a=np.exp(-duration/([70,900][c]))[:,None]
        pol+=p[c][None,:]*a+r[c+1][None,:]*5.1*(1-a)
    memory=np.exp(-q/3)[:,None]
    hh=h[None,:]*memory-.004*(1-memory)
    v=ocv(zseq,T,shape)-5.1*r[0][None,:]-pol+hh
    pack=v.sum(axis=1);idx=np.flatnonzero(pack<=11.2)
    if not len(idx):raise ValueError('synthetic_missing_cutoff')
    k=idx[0];capacity=float(np.interp(11.2,pack[k-1:k+1][::-1],q[k-1:k+1][::-1]))
    stop=min(len(q),k+30)
    return q[:stop],v[:stop],capacity

def generate(seed,scenario,extra_deficit=0):
    rng=np.random.default_rng(seed)
    Q0=np.full(4,102.)
    r=np.vstack([rng.uniform(.0007,.0013,4),rng.uniform(.0003,.0006,4),rng.uniform(.0004,.0008,4)])
    initial=rng.uniform(.15,.25,4)
    zr,pr,hr,refmeta=charge(Q0,r,25,initial)
    zr,pr,hr=step(zr,pr,hr,0,1800,Q0,r,25)
    rx,rv,refcap=reference(Q0,r,25,zr,pr,hr)
    template=Template(rx,rv,q0=refcap)
    s=np.ones(4);deficit=15.;span=33.;T=25;shape=0;bias=np.zeros(4);I_bias=0;tail=5.1;ri=r.copy();path=False
    if scenario=='informative_60Ah':s[:]=rng.uniform(.85,.92);deficit=25;span=60
    if scenario=='shallow_10Ah':span=10;deficit=0
    if scenario=='capacity_only':s[:]=rng.uniform(.85,.95);deficit=0
    if scenario=='start_only':deficit=rng.uniform(5,25)
    if scenario=='capacity_and_start':s[:]=rng.uniform(.85,.95);deficit=rng.uniform(5,20)
    if scenario=='cell_capacity_imbalance':s=rng.uniform(.85,1,4);deficit=5
    if scenario=='cell_start_imbalance':initial=initial+rng.uniform(-.10,.10,4)
    if scenario=='temperature_45C':T=45;ri=r*.78
    if scenario=='resistance_growth':ri=r*np.array([1.7,1.2,1.4])[:,None]
    if scenario=='path_hysteresis':path=True
    if scenario=='voltage_bias':bias=rng.uniform(-.010,.010,4)
    if scenario=='current_bias_gap':I_bias=float(rng.choice([-.1,.1]))
    if scenario=='undercharge':tail=10.2
    if scenario=='shape_change':shape=.06
    deficit+=extra_deficit
    Q=Q0*s
    z,p,h,meta=charge(Q,ri,T,initial,tail)
    # Initial position follows controller end-state, not a forced 100% SOC.
    zfull=z.copy();pfull=p.copy();hfull=h.copy()
    z,p,h=step(z,p,h,20.4,deficit/20.4*3600,Q,ri,T)
    if path:z,p,h=step(z,p,h,-5.1,900,Q,ri,T);deficit-=5.1*.998*.25
    if scenario=='unobserved_balancing':z[2]-=2/Q[2]
    pre_t=np.arange(-1800,0,30.);pre=[]
    for t in pre_t:
        pre.append(ocv(z,T,shape)-p.sum(axis=0)+h+bias)
        z,p,h=step(z,p,h,0,30,Q,ri,T)
    zstart=z.copy();q=0;elapsed=0;tlist=[];qlist=[];jlist=[];volts=[];truth=[]
    while q<=span+1e-9:
        j=20.4 if scenario=='shallow_10Ah' else (18+5*np.sin(elapsed/250)+2*np.sin(elapsed/70))
        tlist.append(elapsed);qlist.append(q);jlist.append(j);truth.append(z.copy())
        volts.append(ocv(z,T,shape)-j*ri[0]-p.sum(axis=0)+h+bias)
        z,p,h=step(z,p,h,j,30,Q,ri,T);q+=j*30/3600;elapsed+=30
    t=np.array(tlist);j=np.array(jlist);qtrue=np.array(qlist);y=np.array(volts)
    noise=.0002 if scenario=='informative_60Ah' else .0005
    y=np.round((y+rng.normal(0,noise,y.shape))/.001)*.001
    pre=np.array(pre)+rng.normal(0,noise,(len(pre_t),4))
    jmeas=j+I_bias
    # Generator state follows left-constant drive. Estimator sees measured drive.
    qobs=np.r_[0,np.cumsum(jmeas[:-1]*np.diff(t)/3600)]
    keep=np.ones(len(t),bool)
    if scenario=='current_bias_gap':keep[40:45]=False
    post_t=np.arange(0,1800,30.);post=[]
    for tt in post_t:
        post.append(ocv(z,T,shape)-p.sum(axis=0)+h+bias)
        z,p,h=step(z,p,h,0,30,Q,ri,T)
    e=dict(id=f'{scenario}_{seed}',start=f'{seed}',panel='synthetic',T=T,t=t[keep],q=qobs[keep],j=jmeas[keep],y=y[keep],pre_t=pre_t,pre_y=pre,post_t=post_t,post_y=np.array(post),net_since_anchor_Ah=deficit if meta['qualified'] else np.nan,chain_ok=meta['qualified'],q_total=float(qobs[-1]),truth_z=np.array(truth)[keep],truth_s=s,truth_d=(zr-zstart)*102,reference_z=zr,initial_z=zstart,scenario=scenario,seed=seed,anchor_meta=meta)
    # Capacity truth requires a new reference charge/rest, independent of run start.
    zc,pc,hc,_=charge(Q,ri,T,initial)
    zc,pc,hc=step(zc,pc,hc,0,1800,Q,ri,T)
    _,_,truecap=reference(Q,ri,T,zc,pc,hc,shape)
    _,_,finecap=reference(Q,ri,T,zc,pc,hc,shape,dt=10)
    e['truth_capacity']=truecap;e['reference_step_error']=abs(truecap-finecap)
    return template,e

def baseline_par(e):
    return np.tile([0.,0.,.001*20,.001*20,0.],(4,1))

def mechanism_scores(seeds,phase):
    rows=[];witness=[];example=[]
    for scenario in CFG['synthetic_scenarios']:
        for seed in seeds:
            template,e=generate(seed,scenario);tau=600;p=prepare(e,tau)
            pr=profile(template,e,tau);ss,pp=choose(pr);sf,pf=choose(pr,'free4')
            rms=np.sqrt(pr['loss'].mean(axis=1))*1000;best=int(rms.argmin());allow=pr['sgrid'][rms<=rms[best]+1]
            caps=[]
            for a in allow:
                try:caps.append(template.capacity(a))
                except ValueError:pass
            width=max(caps)-min(caps) if caps else float('inf')
            gate=bool(width<=5 and best not in [0,len(rms)-1])
            m1=baseline_par(e);m1[:,0]=max(0,e['net_since_anchor_Ah']) if np.isfinite(e['net_since_anchor_Ah']) else 0
            amp,rest_ok,vinf=restore(e,tau)
            variants={
                'B2_full_reset':(np.ones(4),baseline_par(e)),
                'M1_anchor_integral':(np.ones(4),m1),
                'M2_shift_only':choose(pr,'shift'),
                'M2_joint_common':(ss,pp),
                'M2_joint_free4':(sf,pf),
                'M2_gated':(ss,pp) if gate else (np.ones(4),m1),
            }
            for method,(s,par) in variants.items():
                x=e['q'][:,None]/s[None,:]+par[:,0]
                z=e['reference_z'][None,:]-x/102
                error=(z-e['truth_z'])*100
                pred=np.stack([predict(template,p,s[c],par[c],c,tau) for c in range(4)],axis=1)
                try:cap=template.capacity(s)
                except ValueError:cap=np.nan
                rows.append(dict(phase=phase,scenario=scenario,seed=seed,method=method,SOC_mae_pp=float(abs(error).mean()),initial_SOC_mae_pp=float(abs(error[0]).mean()),SOC_p95_pp=float(np.quantile(abs(error),.95)),s_mae=float(abs(s-e['truth_s']).mean()),d_mae_reference_Ah=float(abs(par[:,0]-e['truth_d']).mean()),voltage_mae_mV=float(abs(pred-p['y']).mean()*1000),capacity_error_Ah=float(abs(cap-e['truth_capacity'])),capacity_est_Ah=cap,capacity_delta_from_anchor_Ah=float(abs(cap-template.capacity(1))),capacity_true_Ah=e['truth_capacity'],profile_width_Ah=width,accepted_update=gate if method=='M2_gated' else method.startswith('M2_joint'),anchor_qualified=e['anchor_meta']['qualified'],reference_step_error_Ah=e['reference_step_error']))
            # M3 SOC only with an independent INITIAL zero-current calibration in S.
            zgrid=np.linspace(-.01,1.03,10001);z_m3=[]
            endpoint=e['pre_y'][-1]
            for mode,voltage in [('M3_endpoint_calibrated_OCV',endpoint),('M3_shape_calibrated_OCV',vinf)]:
                zz=np.array([np.interp(voltage[c],ocv(zgrid,e['T']),zgrid) for c in range(4)])
                z=zz[None,:]-e['q'][:,None]/102;err=(z-e['truth_z'])*100
                rows.append(dict(phase=phase,scenario=scenario,seed=seed,method=mode,SOC_mae_pp=float(abs(err).mean()),initial_SOC_mae_pp=float(abs(err[0]).mean()),SOC_p95_pp=float(np.quantile(abs(err),.95)),s_mae=np.nan,d_mae_reference_Ah=np.nan,voltage_mae_mV=np.nan,capacity_error_Ah=np.nan,capacity_est_Ah=np.nan,capacity_true_Ah=e['truth_capacity'],profile_width_Ah=np.nan,accepted_update=False,anchor_qualified=e['anchor_meta']['qualified'],reference_step_error_Ah=e['reference_step_error']))
            # A SECOND controller-reset event has 2 Ah more initial deficit.
            # Health/OCV stay fixed, measurements come from a separate trajectory.
            # Its parameters only use the first completed event, never its suffix.
            _,e2=generate(seed,scenario,extra_deficit=2)
            m1next=m1.copy();m1next[:,0]+=2
            pnext=pp.copy();pnext[:,0]+=2/ss
            for name,use_rest,s,par in [('M4_fixed',True,np.ones(4),m1next),('M4_no_M1',True,np.ones(4),baseline_par(e2)),('M4_no_M3',False,np.ones(4),m1next),('M4_ungated_s',True,ss,pnext),('M4_gated_s',True,ss if gate else np.ones(4),pnext if gate else m1next)]:
                pred,x,var=ekf(template,e2,s,par,tau,1,use_rest,observe_full=True)
                z=e2['reference_z'][None,:]-x/102;err=(z-e2['truth_z'])*100
                rows.append(dict(phase=phase,scenario=scenario,seed=seed,method=name,SOC_mae_pp=float(np.nanmean(abs(err))),initial_SOC_mae_pp=float(np.nanmean(abs(err[0]))),SOC_p95_pp=float(np.nanquantile(abs(err),.95)),s_mae=float(abs(s-e2['truth_s']).mean()),d_mae_reference_Ah=np.nan,voltage_mae_mV=float(np.nanmean(abs(pred-e2['y']))*1000),capacity_error_Ah=np.nan,capacity_est_Ah=np.nan,capacity_true_Ah=e2['truth_capacity'],profile_width_Ah=width,accepted_update=gate if name=='M4_gated_s' else False,anchor_qualified=e2['anchor_meta']['qualified'],reference_step_error_Ah=e2['reference_step_error'],position_interval_coverage=float(np.nanmean(abs(err)*1.02<=1.96*np.sqrt(var))),parameter_source='previous_completed_controller_reset_event',mode='online_tracking'))
            if seed==seeds[0]:
                witness.extend(dict(phase=phase,scenario=scenario,s=float(s),rms_mV=float(r),capacity_Ah=float(template.capacity(s))) for s,r in zip(pr['sgrid'],rms))
                if scenario in ['informative_60Ah','start_only','voltage_bias']:
                    for k in range(0,len(e['q']),3):
                        example.append(dict(phase=phase,scenario=scenario,q_Ah=float(e2['q'][k]),true_SOC_mean=float(e2['truth_z'][k].mean()*100),estimated_M4_SOC_mean=float(z[k].mean()*100),cell1_V=float(e2['y'][k,0])))
        print('synthetic',phase,scenario,flush=True)
    f=pd.DataFrame(rows);f.to_csv(RUN/f'synthetic_{phase}_metrics.csv',index=False)
    pd.DataFrame(witness).to_csv(RUN/f'synthetic_{phase}_profiles.csv',index=False)
    pd.DataFrame(example).to_csv(RUN/f'synthetic_{phase}_examples.csv',index=False)
    return f

def initial_error_test(seeds):
    rows=[]
    for seed in seeds:
        template,e=generate(seed,'informative_60Ah')
        par=baseline_par(e);par[:,0]=e['truth_d']
        for pp in [-20,-10,-5,5,10,20]:
            pred,x,var=ekf(template,e,np.ones(4),par,600,1,True,observe_full=True,initial_error=pp*1.02)
            err=np.nanmean(abs(e['reference_z'][None,:]-x/102-e['truth_z'])*100,axis=1)
            good=np.flatnonzero(np.convolve((err<3).astype(int),np.ones(10,dtype=int),'valid')==10)
            rows.append(dict(seed=seed,initial_error_pp=pp,SOC_mae_pp=float(np.nanmean(err)),final_error_pp=float(err[-1]),convergence_Ah=float(e['q'][good[0]]) if len(good) else np.nan,finite_fraction=float(np.isfinite(x).mean())))
    pd.DataFrame(rows).to_csv(RUN/'initial_error_convergence.csv',index=False)
