"""Mechanistic, temporal, projection and mathematical invariants; no hidden truth."""
from __future__ import annotations
import sys,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
from common import CFG,OUT,ROOT,json_dump,qualified_history
from audit_events import load
from ecm import Reference,filtered,design,predict,actual_response
from joint_estimation import Window,initialized
from online import gaussian_nlml,joseph,track

def run():
    ref=Reference();events=load();checks=[]
    def check(name,condition,detail=''):
        checks.append(dict(name=name,passed=bool(condition),detail=detail))
        if not condition:raise AssertionError(name)
    check('certified_75_events_after_stage_aware_duplicates',len(events)==75)
    check('71_continuous_anchor_chains',sum(e['chain_ok'] for e in events)==71)
    check('CK0_raw_first_pack_cutoff_100p41',abs(ref.capacity()-100.41)<1e-8)
    check('official_SOH_denominator_102',abs(100*ref.capacity()/102-98.44117647058823)<1e-9)
    check('common_alpha_exact_capacity_mapping',all(abs(ref.capacity(a)-a*100.41)<1e-7 for a in [.7,.8,1.,1.05]))
    check('common_reference_shift_moves_baseline_observation_mapping',abs(ref.capacity(.9,np.full(4,.5))-.9*(100.41-.5))<1e-7)
    sample=ref.raw_x[::117]
    check('CK0_raw_pack_residual_counted_once',np.max(abs(ref.pack_voltage(sample)-ref.values(sample,raw=True).sum(axis=1)-np.interp(sample,ref.raw_x,ref.residual)))<1e-10)
    x,a=design(np.array([0.,10.,50.]),np.full(3,5.1),5.1*(-np.expm1(-3600*np.array([0.,10.,50.])/(5.1*600))),1.,0.,600)
    check('reference_dynamic_increment_identity_zero',np.max(abs(a[:,1:]))<1e-12)
    test_t=np.arange(0,100,10.);h=filtered(test_t,np.full(10,20.),600)
    check('exact_1RC_discretization',np.max(abs(h-20*(1-np.exp(-test_t/600))))<1e-12)
    check('Ah_seconds_conversion_and_charge_sign',abs(-np.trapezoid(np.full(10,20.),np.linspace(0,3600,10))/3600+20)<1e-10)
    target=[e for e in events if e['split']=='development' and e['chain_ok'] and e['T']==25][-1]
    hist=qualified_history(events,target)
    check('all_parameter_history_available_before_target',all(pd.Timestamp(e['available_after'])<pd.Timestamp(target['start']) for e in hist))
    check('no_development_chain_crosses_evaluation',not ({e['chain_id'] for e in events if e['split']=='development'}&{e['chain_id'] for e in events if e['split']=='evaluation'}))
    fit=Window(ref,hist,600).fit(False)
    model=initialized(ref,target,fit,1)
    altered=copy.deepcopy(target);altered['y'][altered['q']>1]+=1.
    altmodel=initialized(ref,altered,fit,1)
    check('suffix_voltage_cannot_change_prefix_initialization',np.max(abs(model['params']-altmodel['params']))<1e-12)
    check('suffix_voltage_cannot_change_forward_prediction',np.max(abs(predict(ref,target,model)-predict(ref,altered,altmodel)))<1e-12)
    altered2=copy.deepcopy(target);altered2['net'][altered2['q']>1]+=2.
    testmodel=initialized(ref,altered2,fit,1)
    check('future_charge_cannot_set_prefix_parameter_bounds',np.max(abs(model['params']-testmodel['params']))<1e-12)
    check('historical_charge_response_not_reset_at_discharge',abs(actual_response(target,600)[np.flatnonzero(target['phase']==1)[0]])>1e-8)
    try:filtered(np.array([0.,10.,100.]),np.zeros(3),600);gap_rejected=False
    except ValueError:gap_rejected=True
    check('unobserved_gap_breaks_dynamic_chain',gap_rejected)
    try:ref.values(-1.,0);domain_rejected=False
    except ValueError:domain_rejected=True
    check('no_negative_coordinate_or_unbounded_tail',domain_rejected)
    P=np.array([[2.,.3],[.3,1.]]);H=np.array([[1.,.4]]);R=np.array([[.2]]);S=H@P@H.T+R;K=np.linalg.solve(S,H@P).T
    result=joseph(P,H,R,K);simple=P-P@H.T@np.linalg.solve(S,H@P)
    check('Joseph_matches_linear_Kalman_covariance',np.max(abs(result-simple))<1e-12)
    check('Joseph_covariance_PSD',np.linalg.eigvalsh(result).min()>=0)
    e=np.array([.7]);expected=.5*(.7**2/S[0,0]+np.log(S[0,0])+np.log(2*np.pi))
    check('NLML_positive_quadratic_logdet_formula',abs(gaussian_nlml(e,S)-expected)<1e-12)
    online,meta=track(ref,target,fit)
    good=[r for r in online if r['valid']]
    check('joint_four_cell_conditional_online_covariance_PSD',len(good)>0 and min(r['min_covariance_eigenvalue'] for r in good)>=-1e-12)
    check('online_capacity_remains_frozen_when_no_gate',meta['capacity_frozen'])
    check('CK_date_midnight_not_whole_calendar_day',pd.Timestamp('2025-08-28T00:00:01')>pd.Timestamp('2025-08-28'))
    json_dump(OUT/'science_checks.json',dict(checks=checks,passed=sum(c['passed'] for c in checks),reference_smoothing_rms_mV=ref.smoothing_rms_mV,
        evidence='Scientific invariants; not real SOC or capacity accuracy'))
    print('science invariants',len(checks),'passed',flush=True)
    return checks

if __name__=='__main__':run()
