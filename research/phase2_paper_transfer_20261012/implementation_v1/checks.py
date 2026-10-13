"""Numerical, causal, and domain checks; not accuracy claims."""
import copy,json
import numpy as np
import pandas as pd
import model
from common import *
from diagnostics import projection

def main():
    passed=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        passed.append(name)
    check('raw_Ah_integral_cache_agree',pd.read_csv(TASK/'raw_reaudit.csv').delta_q_Ah.abs().max()<1e-8)
    verify=pd.read_csv(TASK/'raw_voltage_verification.csv')
    check('four_cell_voltage_and_time_cache_exact',verify.max_y_delta_mV.max()==0 and verify.max_time_delta_s.max()==0)
    check('protected_sources_unchanged',protected()==json.loads((TASK/'protected_before.json').read_text()))
    es=events();pulse=pd.read_csv(TASK/'pulse_registry.csv')
    check('same_pulse_not_split',pulse.groupby('pulse_uid').split.nunique().max()==1)
    known=pd.read_csv(TASK/'event_registry.csv');known=known[known.chain_id!='unknown']
    check('known_anchor_chains_not_split',known.groupby('chain_id').split.nunique().max()==1)
    template=StrictTemplate()
    try:template.values(template.x[-1]+.01,0);rejected=False
    except ValueError:rejected=True
    check('strict_domain_rejects_outside',rejected)
    check('CK0_first_pack_cutoff_identity',abs(projection(np.ones(4))-100.41)<1e-6)
    check('common_scale_capacity_identity',abs(projection(np.ones(4)*.93)-.93*100.41)<1e-6)
    ref=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
    order=[2,0,3,1];permuted=ref.copy()
    permuted[[f'cell{i}_V' for i in range(1,5)]]=ref[[f'cell{i+1}_V' for i in order]].to_numpy()
    svec=np.array([.94,.945,.95,.955])
    first=legacy.PackPrototype(ref,tail_Ah=2).capacity(svec)
    second=legacy.PackPrototype(permuted,tail_Ah=2).capacity(svec[order])
    check('pack_channel_permutation_invariant',abs(first-second)<1e-8)
    a=np.ones((5,1));y=np.array([1,2,2,3,100.])
    lad=model.linear(a,y,np.array([-1000]),np.array([1000]),'LAD')
    l2=model.linear(a,y,np.array([-1000]),np.array([1000]),'L2')
    check('LAD_median_epigraph_optimum',abs(lad[1][0]-2)<1e-7)
    check('L2_mean_optimum',abs(l2[1][0]-21.6)<1e-7)
    check('LP_objective_is_mean_absolute_residual',abs(lad[0]-np.abs(lad[1][0]-y).mean())<1e-8)
    e=next(v for v in es if v['panel']=='short' and v['split']=='development')
    tau=json.loads((TASK/'selected_legacy.json').read_text())[key(e)]['tau']
    z=np.load(profile_path(e,'L2','free'));pr={k:z[k] for k in z.files}
    s,params,_=model.select([pr],fixed=True)
    altered=copy.deepcopy(e);altered['y'][altered['q']>1]+=10
    for budget in [0,1]:
        p,v,_=model.forecast(template,e,s,params,tau,budget)
        _,vv,_=model.forecast(template,altered,s,params,tau,budget)
        check(f'suffix_voltage_poison_has_no_effect_budget_{budget}',np.allclose(v,vv))
    check('current_polarization_reference_separate',model.design(prepare(e,tau),1,1,tau)[0].shape[1]==5)
    future=pulse.copy();future['available_after']='2099-01-01';future['qualified']=True
    lo,hi,flags=model.bounds_for(e,tau,'independent',future)
    check('future_pulse_not_used','sampling_scale_R_app' not in flags)
    savejson('science_checks.json',dict(passed=len(passed),checks=passed,all_passed=True))
    print('Science checks passed:',len(passed),flush=True)

if __name__=='__main__':main()
