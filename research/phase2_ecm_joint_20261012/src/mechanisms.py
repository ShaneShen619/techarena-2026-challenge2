"""Independent nonlinear OCV/two-RC/control generator. Mechanism evidence only."""
from __future__ import annotations
import copy,time
import numpy as np
import pandas as pd
from common import CFG,OUT,json_dump
from ecm import Reference
from joint_estimation import Window
from identifiability import profile

TAUS=np.array([50.,1100.])

def U(z,T=25.,shape=0.,informative=False):
    z=np.asarray(z)
    mid=.018 if informative else .008
    return (3.30+.04*(z-.5)+.26*np.tanh((z-.985)/.025)+.30*np.tanh((z-.025)/.020)
        +mid*np.tanh((z-.50)/(.04 if informative else .08))+.00010*(T-25)+shape*(z-.5)**2)

def simulate_charge(Q,R,T,start,tail=5.1,informative=False):
    z=start.copy();p=np.zeros((2,4));h=np.zeros(4);dt=CFG['synthetic_dt_s'];trace=[];cv=0
    for k in range(4000):
        available=(14.-float((U(z,T,informative=informative)+p.sum(axis=0)+h).sum()))/R[0].sum()
        I=float(np.clip(available,0,20.4))
        v=U(z,T,informative=informative)+p.sum(axis=0)+h+I*R[0]
        trace.append(I)
        if I<20.4:cv+=dt
        if k>30 and I<=tail and cv>=60:break
        z,p,h=advance(z,p,h,I,dt,Q,R)
    return z,p,h,np.array(trace),dict(tail_A=I,cv_s=cv,qualified=bool(I<=5.5 and v.sum()>=13.95 and cv>=60))

def advance(z,p,h,I,dt,Q,R,H=.004):
    z=z+(I*.998 if I>0 else I)*dt/(3600*Q)
    decay=np.exp(-dt/TAUS)
    p=decay[:,None]*p+(1-decay[:,None])*R[1:]*I
    memory=np.exp(-abs(I)*dt/(3600*3.))
    h=memory*h+(1-memory)*np.sign(I)*H
    return z,p,h

def reference(Q,R,T,start,informative=False,shape=0,dt=10.):
    z,p,h,_,_=simulate_charge(Q,R,T,start,informative=informative)
    z,p,h=advance(z,p,h,0,1800,Q,R)
    xx=[];vv=[];q=0
    max_steps=int(np.ceil(float(Q.max())*1.2*3600/(5.1*dt)))+1
    for k in range(max_steps):
        v=U(z,T,shape,informative)+p.sum(axis=0)+h-5.1*R[0]
        xx.append(q);vv.append(v)
        if v.sum()<=11.2:break
        z,p,h=advance(z,p,h,-5.1,dt,Q,R);q+=5.1*dt/3600
    x=np.asarray(xx);v=np.asarray(vv);pack=v.sum(axis=1)-.003
    hits=np.flatnonzero(pack<=11.2)
    if not len(hits):raise ValueError('generator_reference_never_reached_cutoff')
    k=int(hits[0]);cap=float(np.interp(11.2,pack[k-1:k+1][::-1],x[k-1:k+1][::-1]))
    return x,v,pack,cap

def event(seed,number,Q,R,T,start,deficit,span,informative=False,bias=None,tail=5.1,H=.004,shape=0,gap=False):
    rng=np.random.default_rng(seed+number*10000);dt=CFG['synthetic_dt_s']
    z,p,h,charging,meta=simulate_charge(Q,R,T,start,tail,informative)
    b=np.zeros(4) if bias is None else np.asarray(bias)
    # Record the entire observed current history from charge through all following stages.
    currents=list(-charging);history_times=list(np.arange(len(charging))*dt)
    clock=history_times[-1] if history_times else 0.
    anchor_clock=clock;net=0.;obs_t=[];obs_j=[];obs_y=[];obs_net=[];phase=[];indices=[];q_dis=[]
    # Known pre-discharge consumes charge; it is an input, not a supplied true SOC.
    n=int(round(deficit/(20.4*dt/3600)))
    for k in range(n):
        clock+=dt;currents.append(20.4);history_times.append(clock)
        z,p,h=advance(z,p,h,-20.4,dt,Q,R,H);net+=20.4*dt/3600
    waveform_start=clock+1800
    def record(I,ph,q):
        nonlocal clock,z,p,h,net
        clock+=dt;history_times.append(clock);currents.append(-I)
        obs_t.append(clock-waveform_start);obs_j.append(-I);obs_net.append(net);phase.append(ph);indices.append(len(currents)-1);q_dis.append(q)
        voltage=U(z,T,shape,informative)+p.sum(axis=0)+h+R[0]*I+b
        noise=.00005 if informative else .0004
        obs_y.append(voltage+rng.normal(0,noise,4))
        z,p,h=advance(z,p,h,I,dt,Q,R,H);net+=-I*dt/3600
    for k in range(180):record(0,0,0)
    q=0.;elapsed=0.
    while q<span:
        j=20.4 if span<=11 else 18+5*np.sin(elapsed/220)+2*np.sin(elapsed/65)
        record(-j,1,q)
        q+=j*dt/3600;elapsed+=dt
    for k in range(180):record(0,2,q)
    y=np.asarray(obs_y)
    if not informative:y=np.round(y/.001)*.001
    tt=np.asarray(obs_t);jj=np.asarray(obs_j);obs_net=np.asarray(obs_net)
    ids=np.arange(0,len(tt),3)
    if gap:ids=ids[~((tt[ids]>900)&(tt[ids]<960))]
    e=dict(id=f'{seed}_{number}',panel='synthetic',T=int(T),start=f'2025-01-{number+2:02d}T00:00:00',available_after=f'2025-01-{number+2:02d}T23:00:00',
        chain_ok=bool(meta['qualified'] and not gap),qualified=True,net_since_anchor_Ah=float(deficit),q_total=float(q),
        t=tt[ids],q=np.asarray(q_dis)[ids],j=jj[ids],y=y[ids],pack=y[ids].sum(axis=1)-.003,phase=np.asarray(phase)[ids],net=obs_net[ids],
        temp=np.full(len(ids),T),htime=np.asarray(history_times),hj=np.asarray(currents),hobs=np.asarray(indices)[ids],anchor_clock=anchor_clock,
        source='independent_two_RC_generator',anchor_meta=meta)
    # Gap must remove current history too, otherwise the estimator receives hidden missing drive.
    if gap:
        ii=np.flatnonzero((e['htime']>=waveform_start+900)&(e['htime']<waveform_start+960))
        keep=np.ones(len(e['htime']),bool);keep[ii]=False
        old=e['hobs'];mapping=np.cumsum(keep)-1
        valid=keep[old]
        for key in ['t','q','j','y','pack','phase','net','temp']:e[key]=e[key][valid]
        e['hobs']=mapping[old[valid]];e['htime']=e['htime'][keep];e['hj']=e['hj'][keep]
    return e

def generate(seed,scenario):
    rng=np.random.default_rng(seed);Q0=np.full(4,102.)
    R=np.vstack([rng.uniform(.0007,.0011,4),rng.uniform(.00008,.00016,4),rng.uniform(.0004,.0007,4)])
    start=rng.uniform(.18,.24,4);informative=scenario=='informative_capacity'
    x,v,pk,q0=reference(Q0,R,25,start,informative)
    ref=Reference(x,v,pk,q0=q0)
    Q=Q0.copy();Ri=R.copy();T=25.;span=60.;deficits=[0.,5.];bias=np.zeros(4);tail=5.1;H=.004;shape=0.;gap=False
    if scenario in ['informative_capacity','capacity_plus_interference']:Q*=rng.uniform(.86,.93)
    if scenario=='shallow_constant':span=10.;deficits=[0.,0.]
    if scenario=='start_change':deficits=[12.,18.];span=45.
    if scenario=='resistance_change':Ri*=np.array([1.6,1.4,1.4])[:,None]
    if scenario=='bias_change':bias=rng.uniform(-.01,.01,4)
    if scenario=='temperature_return':T=45.;Ri=R*np.exp(-.02*(T-25))
    if scenario=='hysteresis_change':H=.010
    if scenario=='undercharge':tail=10.2
    if scenario=='imbalance':start[2]+=.10
    if scenario=='gap':gap=True
    if scenario=='capacity_plus_interference':bias=rng.uniform(-.005,.005,4);Ri*=1.2;H=.007
    es=[event(seed,k,Q,Ri,T,start,d,span,informative,bias,tail,H,shape,gap) for k,d in enumerate(deficits)]
    # Target truth uses reference 25C and normal full-charge protocol, not operating undercharge/T.
    true_R=R if scenario=='temperature_return' else Ri
    _,_,_,truecap=reference(Q,true_R,25,start,informative,shape,10.)
    _,_,_,finecap=reference(Q,true_R,25,start,informative,shape,5.)
    truth=dict(protocol_capacity_Ah=truecap,reference_capacity_Ah=q0,physical_capacity_scale=float(Q.mean()/102),fine_reference_step_error_Ah=abs(truecap-finecap),
        scope='independent simulated group; target reference temperature25C, no real-pack generalization')
    return ref,es,truth

def run(phase='test'):
    if (OUT/f'MECHANISM_{phase.upper()}_COMPLETE').exists():raise RuntimeError('Mechanism scoring already completed; use a new ECM_RUN_ID')
    seeds=CFG['synthetic_test_seeds'] if phase=='test' else CFG['synthetic_development_seeds']
    rows=[];examples=[];start=time.perf_counter()
    for scenario in CFG['synthetic_scenarios']:
        for seed in seeds:
            ref,es,truth=generate(seed,scenario)
            estimate=None;gate=False;pr=None;reason=''
            try:
                if not all(e['chain_ok'] for e in es):raise ValueError('unqualified_anchor_or_gap')
                window=Window(ref,es,CFG['default_tau_s']);pr=profile(window,1.,fine=True);estimate=pr.get('best_capacity_Ah');gate=pr.get('accepted',False)
            except ValueError as exc:reason=str(exc)
            for method in ['fixed','ungated','local_gated']:
                output=ref.capacity() if method=='fixed' or (method=='local_gated' and not gate) else estimate
                error=abs(output-truth['protocol_capacity_Ah']) if output is not None else np.nan
                rows.append(dict(phase=phase,scenario=scenario,seed=seed,method=method,output_Ah=output,true_capacity_Ah=truth['protocol_capacity_Ah'],
                    error_Ah=error,relative_error=error/truth['protocol_capacity_Ah'] if np.isfinite(error) else np.nan,
                    accepted=bool(method=='ungated' and output is not None or method=='local_gated' and gate),direct_output=output is not None,
                    profile_width_Ah=pr['width_Ah'] if pr else np.inf,unsupported_candidates=pr.get('unsupported_candidate_count') if pr else None,
                    failure=reason,physical_capacity_scale=truth['physical_capacity_scale'],reference_step_error_Ah=truth['fine_reference_step_error_Ah']))
            if seed==seeds[0] and pr:
                for C,rms in zip(pr['capacity'],pr['rms']):examples.append(dict(phase=phase,scenario=scenario,capacity_Ah=C,rms_mV=rms,true_capacity_Ah=truth['protocol_capacity_Ah']))
        print('mechanism',phase,scenario,'seeds',len(seeds),'seconds',round(time.perf_counter()-start,1),flush=True)
    df=pd.DataFrame(rows);df.to_csv(OUT/f'mechanism_{phase}_scores.csv',index=False)
    pd.DataFrame(examples).to_csv(OUT/f'mechanism_{phase}_profiles.csv',index=False)
    summary=df.groupby(['scenario','method'],as_index=False).agg(seeds=('seed','count'),finite_outputs=('output_Ah','count'),mean_error_Ah=('error_Ah','mean'),mean_relative_error=('relative_error','mean'),acceptance=('accepted','mean'),width_Ah=('profile_width_Ah','mean'))
    summary.to_csv(OUT/f'mechanism_{phase}_summary.csv',index=False)
    positive=df[(df.scenario=='informative_capacity')&(df.method=='local_gated')]
    constant=df[(~df.scenario.isin(['informative_capacity','capacity_plus_interference']))&(df.method=='local_gated')]
    false=constant.accepted&(constant.error_Ah>CFG['gate_mechanism_false_update_Ah'])
    finite=positive.output_Ah.notna()
    acceptance=float(positive.accepted.mean());meanerror=float(positive.relative_error.mean());false_rate=float(false.sum()/len(constant))
    decision=dict(phase=phase,positive_seeds=len(positive),positive_acceptance=acceptance,positive_mean_relative_error=meanerror,
        constant_pressure_seeds=len(constant),false_updates=int(false.sum()),false_update_fraction=false_rate,
        constant_rejected=int((~constant.accepted).sum()),positive_finite_outputs=int(finite.sum()),
        gate='PASS' if acceptance>=.8 and meanerror<=.03 and false_rate<=.05 else 'FAIL',
        estimator_did_not_receive_true_capacity_or_SOC=True,capacity_truth='Independent reference simulation, not same-model scale labels',
        generation_seed_separation=True,ref_dt_error_max_Ah=float(df.reference_step_error_Ah.max()),runtime_s=time.perf_counter()-start)
    json_dump(OUT/f'mechanism_{phase}_decision.json',decision)
    (OUT/f'MECHANISM_{phase.upper()}_COMPLETE').write_text('Completed immutable mechanism scoring.\n')
    print(decision,flush=True)
    return df

if __name__=='__main__':
    import sys
    run(sys.argv[1] if len(sys.argv)>1 else 'test')
