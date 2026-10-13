"""Causal official development, registration diagnostics, and frozen replay."""
from __future__ import annotations
import json,pickle,time
import numpy as np
import pandas as pd
from audit import RUN,CFG
from engine import Template,prepare,fit_cell,profile,choose,predict,forecast,ekf,last_curve,errors,restore

METHODS=['B0_fixed','B1_previous','B2_reset','M1_common','M1_cell','M1_stretch','M2_shift','M2_stretch_only','M2_joint','M2_M1_prior','M2_free4','M2_common_d','M2_shrunk_d','M3_endpoint','M3_shape','M4_fixed','M4_no_M1','M4_no_M2','M4_no_M3','M4_ungated','M4_gated']

def key(e):return e['panel']+'_'+str(e['T'])

def hist(events,e):
    return [old for old in events if key(old)==key(e) and old['available_after']<e['start']][-4:]

def baseline_parameters(template,e,tau):
    p=prepare(e,tau);pars=[]
    for c in range(4):pars.append(fit_cell(template,p,1,c,tau)[1])
    return np.array(pars)

def develop(template,events):
    selected={};scores=[];fits={}
    dev=[e for e in events if e['split']=='development']
    for kk in sorted({key(e) for e in events}):
        group=[e for e in dev if key(e)==kk]
        tau_scores=[]
        for tau in CFG['tau_candidates_s']:
            previous=[];err=[]
            for e in group:
                if previous:
                    par=np.median(previous[-4:],axis=0)
                    try:
                        p,pred,_=forecast(template,e,np.ones(4),par,tau,1)
                        v=errors(p['y'],pred,p['q'])['mae_mV'];err.append(v)
                        scores.append(dict(layer=kk,tau=tau,id=e['id'],method='B0_fixed',budget='B',mae_mV=v))
                    except ValueError:pass
                try:previous.append(baseline_parameters(template,e,tau))
                except ValueError:pass
            tau_scores.append((float(np.mean(err)) if err else float('inf'),tau))
        tau=min(tau_scores)[1];bchoice={};err={a:{m:[] for m in ['B0_fixed','B1_previous','B2_reset']} for a in ['A','B']}
        oldfits=[];previous=None
        for e in group:
            if oldfits:
                par=np.median(oldfits[-4:],axis=0)
                for budgetname,budget in [('A',0),('B',1)]:
                    for method in err[budgetname]:
                        try:
                            if method=='B1_previous':pred=last_curve(e,previous,budget);v=errors(e['y'],pred,e['q'])['mae_mV']
                            else:
                                pp=par.copy()
                                if method=='B2_reset':pp[:,0]=0
                                p,pred,_=forecast(template,e,1,pp,tau,budget)
                                v=errors(p['y'],pred,p['q'])['mae_mV']
                            err[budgetname][method].append(v)
                        except ValueError:pass
            oldfits.append(baseline_parameters(template,e,tau));previous=e
        for a in ['A','B']:
            avg={m:float(np.mean(v)) if v else 1e9 for m,v in err[a].items()}
            bchoice[a]=min(avg,key=avg.get)
            for m,v in avg.items():scores.append(dict(layer=kk,tau=tau,id='development_summary',method=m,budget=a,mae_mV=v))
        selected[kk]=dict(tau=tau,baseline=bchoice,development_events=len(group),frozen_dynamic_parameters=np.median(oldfits,axis=0).tolist())
        print('development frozen',kk,selected[kk],flush=True)
    pd.DataFrame(scores).to_csv(RUN/'development_choices.csv',index=False)
    (RUN/'selected_configuration.json').write_text(json.dumps(selected,indent=2))
    return selected

def cached_profile(template,e,tau,mode='free'):
    safe=e['id'].replace(':','-');path=RUN/'profiles'/f'{safe}_{tau}_{mode}.npz'
    if path.exists():
        z=np.load(path);return {k:z[k] for k in ['sgrid','loss','params']}
    pr=profile(template,e,tau,prior=mode=='M1',rest_mode='shape' if mode=='shape' else 'free',fixed_d='zero' if mode=='fixed0' else 'anchor' if mode=='fixed_anchor' else None)
    path.parent.mkdir(exist_ok=True)
    np.savez_compressed(path,**pr)
    return pr

def history_params(history,profiles,mode):
    models=[choose(profiles[h['id']],mode) for h in history]
    return np.median([m[0] for m in models],axis=0),np.median([m[1] for m in models],axis=0)

def profile_gate(template,profiles,history):
    if not history:return False,1.,float('inf')
    vals=np.mean([profiles[h['id']]['loss'] for h in history],axis=(0,2))
    grid=profiles[history[0]['id']]['sgrid'];rms=np.sqrt(vals)*1000;k=int(rms.argmin());allowed=grid[rms<=rms[k]+1]
    caps=[template.capacity(s) for s in allowed];width=float(max(caps)-min(caps))
    return bool(width<=5 and k not in [0,len(grid)-1]),float(grid[k]),width

def run_replay(template,events,selected,split='evaluation'):
    rows=[];traces=[];online=[];states=[];priorprofiles={};profiles={};shapecache={};fixedcache={};anchorcache={};tracking={}
    for e in events:
        kk=key(e);tau=selected[kk]['tau'];history=hist(events,e);gate=False;sbest=1;width=np.nan
        # Only completed history; current profile is computed AFTER all forecasts.
        if history:
            sshift,pbase=history_params(history,profiles,'shift')
            sjoint,pjoint=history_params(history,profiles,'joint')
            sfree,pfree=history_params(history,profiles,'free4')
            sprior,pprior=history_params(history,priorprofiles,'joint')
            _,pshape=history_params(history,shapecache,'shift')
            sfixed,pfixed=history_params(history,fixedcache,'joint')
            sanchor,panchor=history_params(history,anchorcache,'joint')
            gate,sbest,width=profile_gate(template,profiles,history)
        else:
            pbase=np.tile([0,0,.001*20,.001*20,0],(4,1));pjoint=pbase.copy();pfree=pbase.copy();pprior=pbase.copy();pshape=pbase.copy()
            sjoint=sfree=sprior=np.ones(4)
            sfixed=sanchor=np.ones(4);pfixed=pbase.copy();panchor=pbase.copy()
        # M1 known net throughput coordinates; learned controller-end difference.
        anchored=np.isfinite(e['net_since_anchor_Ah']) and e['net_since_anchor_Ah']>=0 and e['chain_ok']
        offsets=[]
        for h in history:
            if h['chain_ok'] and np.isfinite(h['net_since_anchor_Ah']):
                _,hp=choose(profiles[h['id']],'shift');offsets.append(hp[:,0]-h['net_since_anchor_Ah'])
        offset=np.median(offsets,axis=0) if offsets else np.zeros(4)
        m1=pbase.copy()
        if anchored:m1[:,0]=e['net_since_anchor_Ah']+offset
        else:m1[:,0]=pbase[:,0]
        common=m1.copy();common[:,0]=np.mean(m1[:,0])
        continuous=m1.copy()
        oldstate=tracking.get(e['chain_id'])
        if anchored and oldstate is not None and oldstate['end']<e['start']:
            # Corrected reference charge survives between events; net Ah comes
            # from the audited complete anchor chain, not guessed gap waveform.
            continuous[:,0]=oldstate['x_end']+(e['net_since_anchor_Ah']-oldstate['net_at_end'])
        if e['split']==split:
            for budgetname,budget in [('A',0),('B',1)]:
                base_method=selected[kk]['baseline'][budgetname]
                for method in METHODS:
                    fallback=False;reason='';s=np.ones(4);par=pbase.copy();is_ekf=method.startswith('M4');rest_mode=None;cal='shift'
                    if method=='B2_reset':par[:,0]=0
                    elif method=='M1_common':par=common.copy()
                    elif method=='M1_cell':par=m1.copy()
                    elif method=='M1_stretch':s=sanchor;par=panchor.copy();par[:,0]=e['net_since_anchor_Ah']/s if anchored else pbase[:,0]
                    elif method=='M2_shift':cal='d'
                    elif method=='M2_stretch_only':s=sfixed;par=pfixed.copy();par[:,0]=0
                    elif method=='M2_joint':s=sjoint;par=pjoint.copy();cal='d'
                    elif method=='M2_M1_prior':s=sprior;par=pprior.copy();cal='d'
                    elif method=='M2_free4':s=sfree;par=pfree.copy();cal='d'
                    elif method=='M2_common_d':s=sjoint;par=pjoint.copy();par[:,0]=par[:,0].mean();cal='d'
                    elif method=='M2_shrunk_d':s=sjoint;par=pjoint.copy();par[:,0]=.5*par[:,0]+.5*par[:,0].mean();cal='d'
                    elif method=='M3_endpoint':par=pbase.copy();rest_mode='endpoint'
                    elif method=='M3_shape':par=pshape.copy();rest_mode='shape'
                    elif method=='M4_fixed':par=continuous.copy()
                    elif method=='M4_no_M1':par=pbase.copy()
                    elif method=='M4_no_M2':par=np.array(selected[kk]['frozen_dynamic_parameters']);par[:,0]=continuous[:,0]
                    elif method=='M4_no_M3':par=continuous.copy()
                    elif method=='M4_ungated':s=sjoint;par=pjoint.copy()
                    elif method=='M4_gated':s=np.full(4,sbest) if gate else np.ones(4);par=pjoint.copy() if gate else continuous.copy()
                    if method.startswith('M1') and not anchored:fallback=True;reason='no_qualified_continuous_anchor'
                    if method in ['M3_endpoint','M3_shape']:
                        # Same endpoint information for the two rest alternatives.
                        # It is a voltage alignment, not a SOC measurement.
                        olds=[h['pre_y'][-1] for h in history if len(h['pre_y'])]
                        if len(e['pre_y']) and olds:par[:,1]+=e['pre_y'][-1]-np.median(olds,axis=0)
                        if method=='M3_shape' and not restore(e,tau)[1]:fallback=True;reason='insufficient_rest_prefix_for_shape'
                    start_time=time.perf_counter()
                    try:
                        if fallback:raise ValueError(reason)
                        if method=='B1_previous':
                            pred=last_curve(e,history[-1] if history else None,budget);yy=e['y'];q=e['q'];tt=e['t']
                        elif is_ekf:
                            pred,x,var=ekf(template,e,s,par,tau,budget,rest_mode=method!='M4_no_M3');yy=e['y'];q=e['q'];tt=e['t']
                            if method in ['M4_fixed','M4_gated'] and budgetname=='B':
                                for k in range(0,len(q),5):states.append(dict(id=e['id'],method=method,q_Ah=float(q[k]),reference_position_mean_Ah=float(np.nanmean(x[k])),position_sd_mean_Ah=float(np.nanmean(np.sqrt(var[k]))),mode='prefix_forecast_no_suffix_voltage'))
                        else:
                            p,pred,calpar=forecast(template,e,s,par,tau,budget,cal,rest_mode);yy=p['y'];q=p['q'];tt=p['t']
                        score=errors(yy,pred,q)
                    except (ValueError,np.linalg.LinAlgError) as ex:
                        fallback=True;reason=str(ex)
                        try:
                            if base_method=='B1_previous':pred=last_curve(e,history[-1] if history else None,budget);yy=e['y'];q=e['q'];tt=e['t']
                            else:
                                pp=pbase.copy()
                                if base_method=='B2_reset':pp[:,0]=0
                                p,pred,_=forecast(template,e,1,pp,tau,budget);yy=p['y'];q=p['q'];tt=p['t']
                            score=errors(yy,pred,q)
                        except ValueError:
                            score=dict(mae_mV=np.nan,rms_mV=np.nan,pack_mae_mV=np.nan,n_score=0,max_cell_error_mV=np.nan,per_cell_mae_mV=[np.nan]*4)
                            pred=np.full_like(e['y'],np.nan);yy=e['y'];q=e['q'];tt=e['t']
                    rows.append(dict(id=e['id'],start=e['start'],panel=e['panel'],T=e['T'],budget=budgetname,method=method,executed_method=base_method if fallback else method,baseline=base_method,split=split,history_events=len(history),latest_parameter_data_end=history[-1]['available_after'] if history else None,target_voltage_prefix_Ah=budget,capacity_gate=gate,conditional_profile_width_Ah=width,s_mean=float(np.mean(s)),s_spread=float(np.ptp(s)),fallback=fallback,reason=reason,runtime_s=time.perf_counter()-start_time,**score))
                    if method in ['B1_previous','M1_cell','M2_joint','M3_shape','M4_fixed','M4_gated']:
                        for k in range(0,len(q),5):
                            traces.append(dict(id=e['id'],panel=e['panel'],T=e['T'],budget=budgetname,method=method,q_Ah=float(q[k]),t_s=float(tt[k]),actual_cell_mean_V=float(yy[k].mean()),predicted_cell_mean_V=float(np.nanmean(pred[k])),suffix_voltage_used=False))
            # Full online tracking is diagnostic and can only serve later events.
            pp,xx,vv=ekf(template,e,1,continuous,tau,1,observe_full=True)
            use=e['q']>=2
            online.append(dict(id=e['id'],panel=e['panel'],T=e['T'],method='M4_fixed_online',mae_mV=float(np.nanmean(abs(pp[use]-e['y'][use]))*1000),mode='online_voltage_corrected_not_forward_score'))
        else:
            pp,xx,vv=ekf(template,e,1,continuous,tau,1,observe_full=True)
        if anchored and np.isfinite(xx[-1]).all():
            tracking[e['chain_id']]=dict(x_end=xx[-1].copy(),net_at_end=e['net_since_anchor_Ah']+e['q_total'],end=e['end'])
        profiles[e['id']]=cached_profile(template,e,tau)
        priorprofiles[e['id']]=cached_profile(template,e,tau,'M1')
        shapecache[e['id']]=cached_profile(template,e,tau,'shape')
        fixedcache[e['id']]=cached_profile(template,e,tau,'fixed0')
        anchorcache[e['id']]=cached_profile(template,e,tau,'fixed_anchor')
        print('replay',split,e['id'],len(history),'profile_gate',gate,flush=True)
    pd.DataFrame(rows).to_csv(RUN/f'official_{split}_metrics.csv',index=False)
    pd.DataFrame(traces).to_csv(RUN/f'official_{split}_predictions.csv',index=False)
    pd.DataFrame(states).to_csv(RUN/f'official_{split}_state_forecasts.csv',index=False)
    pd.DataFrame(online).to_csv(RUN/f'official_{split}_online_metrics.csv',index=False)
    return pd.DataFrame(rows),profiles

def identifiability(template,events,selected,profiles):
    curves=[];diagnostics=[];witnesses=[];restrows=[]
    for panel in ['short','wide']:
        for T in [25,45]:
            group=[e for e in events if e['panel']==panel and e['T']==T]
            chosen=group[-4:];tau=selected[key(chosen[-1])]['tau']
            grid=profiles[chosen[0]['id']]['sgrid'];loss=np.mean([profiles[e['id']]['loss'] for e in chosen],axis=0)
            rms=np.sqrt(loss.mean(axis=1))*1000;k=int(rms.argmin());caps=np.array([template.capacity(s) for s in grid]);allow=caps[rms<=rms[k]+1]
            for s,c,r in zip(grid,caps,rms):curves.append(dict(panel=panel,T=T,configuration='free_start_bias_50mV',s=s,conditional_capacity_Ah=c,rms_mV=r))
            alt=[]
            # Independent common-scale grids, nuisance/RC/anchor-prior sensitivity.
            for variant in ['tight_bias','tau_half','tau_double','M1_prior']:
                ll=[]
                for e in chosen:
                    tt=tau/2 if variant=='tau_half' else tau*2 if variant=='tau_double' else tau
                    pr=profile(template,e,tt,prior=variant=='M1_prior',bias=.01 if variant=='tight_bias' else .05)
                    ll.append(pr['loss'])
                rr=np.sqrt(np.mean(ll,axis=(0,2)))*1000;bi=int(rr.argmin());alt.append(caps[bi])
                for s,c,r in zip(grid,caps,rr):curves.append(dict(panel=panel,T=T,configuration=variant,s=s,conditional_capacity_Ah=c,rms_mV=r))
            # Any legal 4D witness suffices to refute; this is NOT exhaustive proof.
            rng=np.random.default_rng(421+T+len(panel));vecs=[np.ones(4)*grid[k],np.ones(4)*.8,np.ones(4),*list(rng.uniform(.7,1.05,(CFG['joint_witness_samples'],4)))]
            accepted=[]
            for svec in vecs:
                losses=[]
                for e in chosen:
                    p=prepare(e,tau)
                    losses.append([fit_cell(template,p,float(svec[c]),c,tau)[0] for c in range(4)])
                rr=float(np.sqrt(np.mean(losses))*1000)
                try:cap=template.capacity(svec)
                except ValueError:cap=np.nan
                legal=bool(rr<=rms[k]+1 and np.isfinite(cap))
                witnesses.append(dict(panel=panel,T=T,s1=svec[0],s2=svec[1],s3=svec[2],s4=svec[3],rms_mV=rr,conditional_capacity_Ah=cap,within_1mV=legal))
                if legal:accepted.append(cap)
            jointwidth=max(accepted)-min(accepted) if accepted else np.nan
            diagnostics.append(dict(panel=panel,T=T,n_completed_events=len(chosen),best_s=grid[k],conditional_best_capacity_Ah=caps[k],best_rms_mV=rms[k],conditional_profile_width_Ah=float(allow.max()-allow.min()),boundary=bool(k in [0,len(grid)-1]),nuisance_best_capacity_spread_Ah=float(max(alt+[caps[k]])-min(alt+[caps[k]])),joint_witness_capacity_span_Ah=jointwidth,joint_search_exhaustive=False,capacity_identification='refuted_by_witness' if jointwidth>5 else 'not_confirmed_nonexhaustive_search',absolute_reference_state_confirmed=False))
            for e in chosen:
                for budget in [300,900,1800]:
                    a,ok,inf=restore(e,tau,budget)
                    for c in range(4):restrows.append(dict(id=e['id'],panel=panel,T=T,cell=c+1,rest_budget_s=budget,amplitude_at_discharge_mV=float(a[c]*1000),asymptote_V=float(inf[c]),valid=ok))
            print('identifiability',panel,T,diagnostics[-1],flush=True)
    pd.DataFrame(curves).to_csv(RUN/'official_profile_curves.csv',index=False)
    pd.DataFrame(diagnostics).to_csv(RUN/'identifiability.csv',index=False)
    pd.DataFrame(witnesses).to_csv(RUN/'joint_capacity_witnesses.csv',index=False)
    pd.DataFrame(restrows).to_csv(RUN/'rest_budget_diagnostics.csv',index=False)
    return diagnostics
