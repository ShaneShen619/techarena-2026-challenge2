"""Independent voltage/RC generator; stress evidence, never fitting data."""
import ast, hashlib, json, sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1]
ROOT=TASK.parents[1]
sys.path.insert(0,str(TASK/'src'))
from age_prior import MyModel

def main():
    source=ROOT/'research/phase2_temperature_improvement/scripts/run_m6_mechanism.py'
    tree=ast.parse(source.read_text())
    names={'pack_voltage','discharge_truth','charge_event','scenario_parameters'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    namespace={'np':np,'pd':pd}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),namespace)
    truth=namespace['discharge_truth'];event=namespace['charge_event'];params=namespace['scenario_parameters']
    scenarios=['constant_capacity_varying_temperature','constant_temperature_capacity_fade',
               'coupled_temperature_and_fade','sensor_bias','self_heating_change',
               'four_series_capacity_imbalance','four_series_soc_imbalance','limiting_cell_switch',
               'prior_too_fast','prior_too_slow','polarization_start_soc_confounds_A']
    rows=[]
    for si,name in enumerate(scenarios):
        for offset in range(10):
            seed=20261010+10000*si+offset;rng=np.random.default_rng(seed)
            base=rng.uniform(98,104);basecap=np.full(4,base);r=rng.uniform(.004,.012,4);rp=rng.uniform(.001,.004,4)
            scenario=name if name in scenarios[:7] else 'constant_temperature_capacity_fade'
            cap,temp,soc,sensor=params(scenario,rng,base)
            if name=='limiting_cell_switch':cap=base*np.array([.97,.98,.75,.96]);soc=np.array([.92,1.,1.,1.])
            if name=='polarization_start_soc_confounds_A':cap=basecap.copy();soc=rng.uniform(.8,1.,4)
            # Reference RPT temperature is fixed; operating temperature affects
            # charging waveforms but must not become a different truth protocol.
            rpt_temp=np.full(4,25.)
            q0=truth(basecap,rpt_temp,np.ones(4),r,rp,5.1,11.2,1.)
            q=truth(cap,rpt_temp,soc,r,rp,5.1,11.2,1.)
            coarse=truth(cap,rpt_temp,soc,r,rp,5.1,11.2,2.)
            perm=rng.permutation(4)
            qp=truth(cap[perm],rpt_temp[perm],soc[perm],r[perm],rp[perm],5.1,11.2,1.)
            assert abs(q-coarse)<.001 and abs(q-qp)<1e-9
            anchor=pd.Timestamp('2025-01-14')
            op=pd.concat([event(anchor+pd.Timedelta(days=1),basecap,np.full(4,25.),25.,7.,1801,30.,0.,1),
                          event(anchor+pd.Timedelta(days=30),cap,temp,sensor,7.,1801,30.,110.,2)],ignore_index=True)
            if name=='polarization_start_soc_confounds_A':
                mask=op.segment.eq(2)
                for i in range(4):op.loc[mask,f'cell{i+1}_V']+=.03+(1-soc[i])*.2
            ck=pd.DataFrame({'date':[anchor],'capacity_Ah':[q0]});ds=SimpleNamespace(operation=op,checkups_released=ck)
            model=MyModel(TASK/'artifacts/source_prior.json');model.fit(ds)
            if name in ['prior_too_fast','prior_too_slow']:
                # Intentional frozen-model mismatch; no tuning or calibration.
                model.artifact['model']['parameters']['lnA']+=(-np.log(10) if name=='prior_too_fast' else np.log(10))
            value=model.estimate_soh(ds,anchor+pd.Timedelta(days=31))
            rows.append({'scenario':name,'seed':seed,'truth_RPT_Ah':q,'truth_soh_pp':q*100/102,
                         'estimate_soh_pp':value,'error_pp':value-q*100/102,'anchor_soh_pp':q0*100/102,
                         'false_decay_pp':value-q0*100/102 if name in ['constant_capacity_varying_temperature','sensor_bias','self_heating_change','polarization_start_soc_confounds_A'] else np.nan,
                         'status':model.last_diagnostics['status'],'A_matched_events':model.last_diagnostics.get('A_matched_events',0),
                         'coarse_fine_difference_Ah':abs(q-coarse),'permutation_difference_Ah':abs(q-qp)})
        print(name,'done',flush=True)
    f=pd.DataFrame(rows);f.to_csv(TASK/'outputs/mechanism_cases.csv',index=False)
    summary=f.assign(ae=f.error_pp.abs()).groupby('scenario').agg(n=('seed','size'),MAE_pp=('ae','mean'),
                    max_error_pp=('ae','max'),max_step_error_Ah=('coarse_fine_difference_Ah','max'),
                    A_matches=('A_matched_events','sum'),mean_false_decay_pp=('false_decay_pp','mean'))
    summary.to_csv(TASK/'outputs/mechanism_summary.csv')
    (TASK/'outputs/mechanism_provenance.json').write_text(json.dumps({'generator_path':str(source),
        'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'functions':sorted(names),'n_cases':len(f),
        'reference_protocol':'synthetic fixed25C 5.1A pack first11.2V; SOC mismatch is intentional protocol failure',
        'model_training_use':False,'proves_real_accuracy':False,'seed_first':20261010},indent=2)+'\n')

if __name__=='__main__':main()
