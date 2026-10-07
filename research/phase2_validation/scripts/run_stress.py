"""Paired sensor/sampling stress on 20 independent mismatched-simulator seeds."""
from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
sys.path.insert(0,str(TASK/'scripts'))
from run_synthetic import RouteA,RouteB,capacities,measured_c20,operation

def main():
    perturbations=(None,'voltage_bias','voltage_bias_50mV','single_cell_bias',
                   'current_bias','current_bias_5pct','coarse_10s','coarse_30s','coarse_60s',
                   'drop_10pct','drop_30pct','voltage_noise','shape_drift','no_recent_event')
    rows=[]
    for seed in range(100,120):
        for stress in perturbations:
            rng=np.random.default_rng(seed+123456)
            scenario='linear'
            q0,ref=measured_c20(capacities(seed,scenario,0),25,rng)
            true_q,_=measured_c20(capacities(seed,scenario,2),25,rng)
            frames=[]
            for stage in range(3):
                if stage==2 and stress=='no_recent_event':continue
                frames.append(operation(seed,scenario,stage,capacities(seed,scenario,stage),rng,
                                        stress=None if stress=='no_recent_event' else stress))
            op=pd.concat(frames,ignore_index=True)
            ds=SimpleNamespace(operation=op,bol_capacity_Ah=q0,reference_discharge=ref)
            cutoff=pd.Timestamp('2025-01-15')+pd.Timedelta(days=61)
            for name,model in [('A',RouteA()),('B',RouteB())]:
                model.fit(ds)
                pred=model.estimate_soh(ds,cutoff)*102/100
                rows.append({'run_id':'E2_stress_20seeds','evidence':'E2','dataset':'simulated_four_series',
                    'seed':seed,'scenario':scenario,'stress':stress or 'baseline',
                    'method':name,'true_C20_Ah':true_q,'predicted_Ah':pred,'error_Ah':pred-true_q,
                    'fallback':model.last_diagnostics['fallback'],'updates':model.last_diagnostics['updates']})
        print('stress seed',seed,flush=True)
    df=pd.DataFrame(rows)
    df.to_csv(TASK/'outputs/stress_results.csv',index=False)
    print(df.groupby(['stress','method']).error_Ah.agg(n='size',MAE=lambda x:x.abs().mean(),bias='mean').to_string())

if __name__=='__main__':main()
