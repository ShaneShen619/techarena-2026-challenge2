"""Frozen sensitivity, four-dimensional witnesses, and feature feasibility."""
import json
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter,find_peaks
import model
from common import *
from audit_stage import restfit

def stored(e,loss,mode):
    z=np.load(profile_path(e,loss,mode));return {k:z[k] for k in z.files}

def projection(s,tail=0):
    reference=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
    pack=legacy.PackPrototype(reference,tail_Ah=tail)
    try:return pack.capacity(s)
    except ValueError:return np.nan

def main():
    from run import verify_freeze
    verify_freeze()
    es=events();template=StrictTemplate();pulses=pd.read_csv(TASK/'pulse_registry.csv')
    selected=json.loads((TASK/'selected_legacy.json').read_text())
    rows=[];curves=[];sensitivity=[];joint=[]
    for kk in sorted({key(e) for e in es}):
        group=[e for e in es if key(e)==kk][-4:];tau=selected[kk]['tau']
        for loss in ['L2','LAD']:
            for mode in ['free','independent']:
                prs=[stored(e,loss,mode) for e in group]
                d,curve=model.diagnosis(prs,loss,template.q0)
                grid=prs[0]['sgrid']
                for s,v in zip(grid,curve):curves.append(dict(layer=kk,loss=loss,variant=mode,s=s,loss_mV=v,conditional_capacity_Ah=100.41*s))
                rows.append(dict(layer=kk,loss=loss,mode=mode,n_events=len(group),**d))
            base=[stored(e,loss,'independent') for e in group]
            baseline,_=model.diagnosis(base,loss,template.q0)
            for variant in ['tau_half','tau_double','tight_bias','dense_fit']:
                alt=[]
                for e in group:
                    tt=tau/2 if variant=='tau_half' else tau*2 if variant=='tau_double' else tau
                    pr=model.profile(template,e,tt,loss,'independent',pulses,cache=False,
                        tight_bias=variant=='tight_bias',fit_points=128 if variant=='dense_fit' else 64)
                    alt.append(pr)
                d,curve=model.diagnosis(alt,loss,template.q0)
                sensitivity.append(dict(layer=kk,loss=loss,variant=variant,best_s=d['best_s'],
                    best_capacity_Ah=100.41*d['best_s'],delta_from_primary_Ah=100.41*(d['best_s']-baseline['best_s']),width_Ah=d['width_Ah'],boundary=d['boundary']))
                for s,v in zip(grid,curve):curves.append(dict(layer=kk,loss=loss,variant=variant,s=s,loss_mV=v,conditional_capacity_Ah=100.41*s))
            # Joint witnesses use L2 for physical error comparable to 1mV RMS.
            if loss=='L2':
                prs=[stored(e,loss,'independent') for e in group]
                best,_=model.diagnosis(prs,loss,template.q0)
                rng=np.random.default_rng(CFG['joint_witness_seed']+len(kk)+group[-1]['T'])
                vectors=[np.ones(4)*best['best_s'],np.ones(4)*.8,np.ones(4),*rng.uniform(.7,1.05,(CFG['joint_witness_count'],4))]
                for s in vectors:
                    objectives=[]
                    for e in group:
                        p=prepare(e,tau,64);lo,hi,_=model.bounds_for(e,tau,'independent',pulses)
                        objectives.append([model.fit_cell(template,p,float(s[c]),c,tau,'L2',lo[c],hi[c])[0] for c in range(4)])
                    rms=float(np.sqrt(np.mean(objectives))*1000)
                    accepted=rms<=best['minimum_loss_mV']+1
                    cap0=projection(s,0);cap2=projection(s,2)
                    joint.append(dict(layer=kk,s1=s[0],s2=s[1],s3=s[2],s4=s[3],rms_mV=rms,
                        within_tolerance=accepted,strict_capacity_Ah=cap0,tail2_capacity_Ah=cap2,
                        strict_domain_valid=bool(np.isfinite(cap0)),search_exhaustive=False))
            print('diagnostic sensitivity',kk,loss,flush=True)
        pd.DataFrame(rows).to_csv(TASK/'identifiability.csv',index=False)
        pd.DataFrame(curves).to_csv(TASK/'sensitivity_profile_curves.csv',index=False)
        pd.DataFrame(sensitivity).to_csv(TASK/'sensitivity_best_states.csv',index=False)
        pd.DataFrame(joint).to_csv(TASK/'joint_witnesses.csv',index=False)
    feature_audit(template,es)
    pulse_validation(pulses)
    verify_freeze();(TASK/'DIAGNOSTICS_COMPLETE').write_text('2026-10-13\n')

def feature_audit(template,es):
    # Observed loaded-curve derivative audit, NOT identified OCV/ICA features.
    rows=[];features=[]
    for window in [11,21,41]:
        for c in range(4):
            smooth=savgol_filter(template.y[:,c],window,3)
            derivative=np.gradient(smooth,template.x)
            peaks,_=find_peaks(-derivative,prominence=.001,distance=20)
            for k in peaks:features.append(dict(source='CK0_loaded',window_points=window,cell=c+1,
                reference_Ah=template.x[k],voltage_V=smooth[k],dV_dQ_V_per_Ah=derivative[k]))
    for e in es:
        span=np.ptp(e['j']);cv=np.std(e['j'])/np.mean(e['j'])
        rows.append(dict(id=e['id'],panel=e['panel'],T=e['T'],split=e['split'],q_Ah=e['q_total'],
            current_min_A=float(e['j'].min()),current_max_A=float(e['j'].max()),current_CV=float(cv),
            constant_current_candidate=bool(cv<.02),
            certified_OCV=False,complete_per_cell_OCV=False,
            Sun_reconstruction_ready=False,reason='missing_OCV_scale_and_full_transformation_formula'))
    pd.DataFrame(features).to_csv(TASK/'CK0_derivative_features.csv',index=False)
    pd.DataFrame(rows).to_csv(TASK/'feature_feasibility.csv',index=False)

def pulse_validation(pulses):
    rows=[]
    qualified=pulses[pulses.qualified].drop_duplicates('pulse_uid').sort_values('timestamp')
    for _,r in qualified.iterrows():
        prior=qualified[(qualified['T']==r['T']) & (qualified.panel==r.panel) & (qualified.available_after<r.timestamp)].tail(8)
        dev=qualified[(qualified['T']==r['T']) & (qualified.panel==r.panel) & (qualified.split=='development') & (qualified.available_after<r.timestamp)]
        if len(prior)<3 or len(dev)<3:continue
        for c in range(4):
            estimate=float(prior[f'R{c+1}_ohm'].median());baseline=float(dev[f'R{c+1}_ohm'].median())
            observed=float(r[f'delta_V{c+1}_V']);dj=float(r.delta_I_D_A)
            rows.append(dict(id=r.id,split=r.split,T=int(r['T']),cell=c+1,dt_s=float(r.dt_s),
                pulse_uid=r.pulse_uid,history_pulses=len(prior),
                prediction_error_mV=abs(-estimate*dj-observed)*1000,
                frozen_dev_baseline_error_mV=abs(-baseline*dj-observed)*1000,
                apparent_R_ohm=estimate,observed_R_ohm=float(r[f'R{c+1}_ohm'])))
    pd.DataFrame(rows).to_csv(TASK/'pulse_forward_validation.csv',index=False)

if __name__=='__main__':main()
