"""Predeclared route component ablations on independent mismatched simulator."""
from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
sys.path.insert(0,str(TASK/'scripts'))
from run_synthetic import RouteA,RouteB,capacities,measured_c20,operation

A_VARIANTS={
 'A_default':{},
 'A_pack_voltage':{'use_pack':True},
 'A_no_condition_match':{'match_conditions':False},
 'A_counter_instead_integral':{'use_counter':True},
 'A_mean_instead_median':{'robust':False},
 'A_disagreement_gate':{'disagreement_gate':True},
 'A_no_depth_split':{'split_depth':False},
}
B_VARIANTS={
 'B_gated':{},
 'B_fixed_Q':{'fixed_q':True},
 'B_no_information_gate':{'gated':False},
 'B_no_voltage_bias_control':{'bias_control':False},
 'B_no_gap_reinitialization':{'reset_on_gap':False},
 'B_low_quasi_OCV_uncertainty':{'quasi_ocv_sigma_V':0.015},
}

def main():
    rows=[]
    for seed in range(100,120):
        scenario='linear';rng=np.random.default_rng(seed+20260928)
        q0,ref=measured_c20(capacities(seed,scenario,0),25,rng)
        true_q,_=measured_c20(capacities(seed,scenario,2),25,rng)
        op=pd.concat([operation(seed,scenario,stage,capacities(seed,scenario,stage),rng)
                      for stage in range(3)],ignore_index=True)
        ds=SimpleNamespace(operation=op,bol_capacity_Ah=q0,reference_discharge=ref)
        cutoff=pd.Timestamp('2025-01-15')+pd.Timedelta(days=61)
        for variant,settings in A_VARIANTS.items():
            m=RouteA(**settings);m.fit(ds);pred=m.estimate_soh(ds,cutoff)*102/100
            rows.append((seed,'A',variant,pred,true_q,m.last_diagnostics['fallback'],m.last_diagnostics['updates']))
        for variant,settings in B_VARIANTS.items():
            m=RouteB(**settings);m.fit(ds);pred=m.estimate_soh(ds,cutoff)*102/100
            rows.append((seed,'B',variant,pred,true_q,m.last_diagnostics['fallback'],m.last_diagnostics['updates']))
        print('ablation seed',seed,flush=True)
    df=pd.DataFrame(rows,columns=['seed','route','variant','prediction_Ah','true_C20_Ah','fallback','updates'])
    df.insert(0,'run_id','E2_ablation_20seeds')
    df.insert(1,'evidence','E2')
    df.insert(2,'dataset','simulated_four_series')
    df['error_Ah']=df.prediction_Ah-df.true_C20_Ah
    df.to_csv(TASK/'outputs/ablation_results.csv',index=False)
    print(df.groupby(['route','variant']).agg(n=('error_Ah','size'),MAE_Ah=('error_Ah',lambda x:x.abs().mean()),
        fallback_rate=('fallback','mean'),mean_updates=('updates','mean')).to_string())

if __name__=='__main__':main()
