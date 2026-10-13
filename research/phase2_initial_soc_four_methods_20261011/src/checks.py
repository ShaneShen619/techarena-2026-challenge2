"""Scientific invariants and causal prefix checks, not mirrored fit tests."""
from __future__ import annotations
import copy,json,pickle
import numpy as np
import pandas as pd
from audit import RUN,ROOT
from engine import Template,forecast,ekf,last_curve,restore,filtered
from synthetic import generate,baseline_par

def run_checks(events):
    results=[]
    def check(name,condition,detail):
        results.append(dict(name=name,passed=bool(condition),detail=detail))
    official=Template()
    check('CK0_first_pack_cutoff',abs(official.capacity(1)-100.41)<1e-6,official.capacity(1))
    check('serial_Ah_not_fourfold',abs(official.capacity(.97)-100.41*.97)<1e-6,official.capacity(.97))
    check('template_domain_rejection',rejects(lambda:official.values(-1,0)) and rejects(lambda:official.values(200,0)),'negative_start_and_unbounded_tail_rejected')
    check('counter_direction_not_assumed',pd.read_csv(RUN/'counter_audit.csv').query("panel=='short'").counter_direction_supported.sum()==0,'short_pulses_use_current_integral')
    chains={}
    for e in events:
        if e['chain_id']!='unknown':chains.setdefault(e['chain_id'],set()).add(e['split'])
    check('whole_chain_fold_isolation',all(len(v)==1 for v in chains.values()),len(chains))
    template,e=generate(100,'informative_60Ah');par=baseline_par(e);par[:,0]=max(0,e['net_since_anchor_Ah'])
    damaged=copy.deepcopy(e);mask=damaged['q']>1;damaged['y'][mask]+=10;damaged['post_y']+=100
    for budget in [0,1]:
        a=forecast(template,e,1,par,600,budget)[1];b=forecast(template,damaged,1,par,600,budget)[1]
        check(f'forecast_no_suffix_voltage_budget_{budget}',np.allclose(a,b,equal_nan=True),float(np.nanmax(abs(a-b))))
        a=ekf(template,e,1,par,600,budget)[0];b=ekf(template,damaged,1,par,600,budget)[0]
        check(f'EKF_snapshot_no_suffix_voltage_budget_{budget}',np.allclose(a,b,equal_nan=True),float(np.nanmax(abs(a-b))))
    check('rest_no_post_discharge_information',np.allclose(restore(e,600)[0],restore(damaged,600)[0]),'pre_rest_only')
    saved=pickle.loads(pickle.dumps((template,e,par)))
    check('serialized_state_prediction_identity',np.allclose(ekf(*saved[:2],1,saved[2],600,1)[0],ekf(template,e,1,par,600,1)[0],equal_nan=True),'template_state_and_parameters_roundtrip')
    perm=np.array([2,0,3,1]);other=Template(template.x,template.y[:,perm],template.q0);ee=copy.deepcopy(e)
    ee['y']=ee['y'][:,perm];ee['pre_y']=ee['pre_y'][:,perm]
    a=ekf(template,e,1,par,600,1)[0];b=ekf(other,ee,1,par[perm],600,1)[0]
    check('cell_permutation_prediction_equivariance',np.allclose(a[:,perm],b,equal_nan=True),'templates_states_and_observations_reordered')
    svec=np.array([.93,.935,.94,.945])
    check('cell_permutation_pack_capacity',abs(template.capacity(svec)-other.capacity(svec[perm]))<1e-8,'pack_first_crossing_within_reference_domain')
    h=filtered(np.array([0,600,1200]),np.array([20,20,20]),600)
    check('RC_seconds_units',np.allclose(h,20*(1-np.exp(-np.array([0,600,1200])/600))),h.tolist())
    # Parameter changes preserve current coordinate, future increment changes only.
    zero=copy.deepcopy(e);zero['q']=np.zeros_like(e['q'])
    a=forecast(template,zero,1,par,600,0)[1];b=forecast(template,zero,.9,par,600,0)[1]
    check('stretch_update_no_retroactive_coordinate_jump',np.allclose(a,b),'current_reference_position_preserved')
    check('reference_generator_time_step',e['reference_step_error']<.01,e['reference_step_error'])
    check('generator_charge_not_forced_100percent',not np.allclose(e['initial_z'],1),'controller_generated_end_state')
    check('operation_anchor_age_is_causal',all(e['anchor_end'] is None or e['anchor_end']<=e['start'] for e in events),'audited_raw_anchor_end_before_start')
    (RUN/'science_checks.json').write_text(json.dumps(results,indent=2))
    failed=[r['name'] for r in results if not r['passed']]
    if failed:raise AssertionError(failed)
    print('scientific checks passed',len(results),flush=True)
    return results

def rejects(fn):
    try:fn()
    except ValueError:return True
    return False
