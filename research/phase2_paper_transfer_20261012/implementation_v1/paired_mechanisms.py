"""Small prespecified multi-event mechanism panel; target suffix never fitted."""
import argparse
import numpy as np
import pandas as pd
import model
from mechanisms import generate
from common import *

def main(phase):
    if phase=='evaluation':
        from run import verify_freeze
        verify_freeze()
    scenarios=['informative_60Ah','shallow_10Ah','start_only','resistance_growth','cell_capacity_imbalance']
    seeds=CFG[phase+'_seeds'][:2];rows=[]
    for scenario in scenarios:
        for seed in seeds:
            histories=[generate(seed,scenario,d) for d in [0,2]]
            template,target=generate(seed,scenario,4)
            for loss in ['L2','LAD']:
                for mode in ['free','independent']:
                    prs=[model.profile(t,e,600,loss,mode,cache=True) for t,e in histories]
                    for kind in ['single_common','multi_common','multi_shrunk4']:
                        subset=prs[-1:] if kind=='single_common' else prs
                        ss,params,_=model.select(subset,kind='free4' if kind=='multi_shrunk4' else 'common',shrink=kind=='multi_shrunk4',loss=loss)
                        # Measured, controller-relative net Ah is an operation
                        # coordinate; no truth SOC or capacity enters this propagation.
                        if np.isfinite(target['net_since_anchor_Ah']):
                            idx=np.array([np.argmin(abs(prs[0]['sgrid']-s)) for s in ss])
                            offsets=[]
                            for pr,(_,e) in zip(prs,histories):
                                offsets.append(np.array([pr['params'][idx[c],c,0]*ss[c]-e['net_since_anchor_Ah'] for c in range(4)]))
                            params[:,0]=(target['net_since_anchor_Ah']+np.median(offsets,axis=0))/ss
                        reason='';valid=True
                        try:
                            p,pred,_=model.forecast(template,target,ss,params,600,1)
                            score=legacy.errors(p['y'],pred,p['q'])['mae_mV']
                        except ValueError as ex:valid=False;reason=str(ex);score=np.nan
                        diag,_=model.diagnosis(subset,loss,template.q0)
                        rows.append(dict(scenario=scenario,seed=seed,loss=loss,mode=mode,kind=kind,
                            s_mae=float(abs(ss-target['truth_s']).mean()),
                            B_forward_mae_mV=score,valid=valid,reason=reason,
                            historical_events=len(subset),profile_width_Ah=diag['width_Ah'],
                            gate=diag['gate'],target_suffix_voltage_used=False,
                            truth_constant_capacity=bool(np.all(target['truth_s']==1))))
            print('paired',phase,scenario,seed,flush=True)
    pd.DataFrame(rows).to_csv(TASK/f'paired_{phase}_metrics.csv',index=False)
    if phase=='evaluation':verify_freeze();(TASK/'PAIRED_COMPLETE').write_text('2026-10-13\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['development','evaluation']);main(p.parse_args().phase)
