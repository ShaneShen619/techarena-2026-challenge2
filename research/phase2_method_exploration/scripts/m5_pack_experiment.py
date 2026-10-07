"""M5 4S cutoff: CK0 reconstruction, independent-shape synthetic truth and uncertainty."""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M5_pack_v1';OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(TASK/'src'))
from m5_pack import CK0Pack,PackState,Q0,uniform_mean_state,minimum_cell_usable_Ah,I_DISCHARGE_A
cfg=json.loads((TASK/'configs/m5_pack.json').read_text())
ref=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
pack=CK0Pack(ref);rng=np.random.default_rng(cfg['synthetic_seed'])
ck0=PackState(np.full(4,Q0),np.ones(4),np.zeros(4))
recon=pack.cutoff(ck0)
step=[{'step_s':s,'capacity_Ah':pack.stepped_cutoff(ck0,s),
       'difference_vs_root_Ah':pack.stepped_cutoff(ck0,s)-recon['group_capacity_Ah']}
      for s in cfg['step_seconds']]
perm=np.array([2,0,3,1])
permuted=PackState(ck0.capacity_Ah[perm],ck0.initial_SOC[perm],ck0.delta_R_ohm[perm])
# Permuting state alone on CK0's distinct cell curves need not preserve the
# result: the cell-specific curve travels with the physical cell. Verify the
# mathematical sum by permuting voltage contributions at fixed Ah instead.
permutation_error=max(abs(np.sum(pack.cell_voltage(a,ck0))-np.sum(pack.cell_voltage(a,ck0)[perm]))
                      for a in (0,20,60,90,100))
assert abs(recon['group_capacity_Ah']-100.412)<.03
assert abs(recon['cutoff_voltage_sum_V']-11.2)<1e-6
assert permutation_error<1e-12

fixed=[
 ('uniform_95Ah',[95,95,95,95],[1,1,1,1],[.0005]*4,[-5]*4),
 ('single_weak_85Ah',[85,100,100,100],[1]*4,[.001,0,0,0],[-15,5,5,5]),
 ('two_weak_90Ah',[90,93,102,102],[1]*4,[.001,.001,0,0],[-10,-10,5,5]),
 ('SOC_imbalance',[100]*4,[1,.96,.98,1],[0]*4,[0]*4),
 ('R_imbalance',[100]*4,[1]*4,[0,.003,0,0],[0]*4),
 ('combined_weak_SOC_R',[90,103,98,101],[.97,1,.95,.99],[.001,0,.002,.0005],[-15,5,-10,5])]
scenarios=[]
for name,Q,z,R,shape in fixed:
 scenarios.append((name,PackState(np.array(Q,float),np.array(z,float),np.array(R,float)),np.array(shape,float),'fixed'))
for j in range(cfg['random_scenarios']):
    Q=rng.uniform(*cfg['truth_range']['capacity_Ah'],size=4)
    z=rng.uniform(*cfg['truth_range']['initial_SOC'],size=4)
    R=rng.uniform(*cfg['truth_range']['delta_R_ohm'],size=4)
    shape=rng.uniform(*cfg['truth_range']['nonlinear_tail_shape_mV'],size=4)
    scenarios.append((f'random_{j:04d}',PackState(Q,z,R),shape,'random_stress'))

results=[];state_rows=[]
for name,true,shape,family in scenarios:
    truth=pack.cutoff(true,truth_shape_mV=shape,truth_dynamic_R=True)
    state_rows.append({'scenario':name,'family':family,
                       **{f'true_Q{i}_Ah':true.capacity_Ah[i-1] for i in range(1,5)},
                       **{f'true_z{i}':true.initial_SOC[i-1] for i in range(1,5)},
                       **{f'true_deltaR{i}_mOhm':1000*true.delta_R_ohm[i-1] for i in range(1,5)},
                       **{f'true_shape{i}_mV':shape[i-1] for i in range(1,5)}})
    Qn=np.clip(true.capacity_Ah+rng.normal(0,5,4),70,120)
    zn=np.clip(true.initial_SOC+rng.normal(0,.02,4),.85,1)
    Rn=np.clip(true.delta_R_ohm+rng.normal(0,.0005,4),-.001,.004)
    noisy=PackState(Qn,zn,Rn)
    for information,state in [('oracle_state',true),('same_noisy_state',noisy)]:
        model_outputs={
          'minimum_cell_usable_Ah':minimum_cell_usable_Ah(state),
          'uniform_mean_cell':pack.cutoff(uniform_mean_state(state))['group_capacity_Ah'],
          'explicit_four_cell':pack.cutoff(state)['group_capacity_Ah']}
        for method,pred in model_outputs.items():
            results.append({'scenario':name,'family':family,'information':information,'method':method,
                            'truth_group_capacity_Ah':truth['group_capacity_Ah'],
                            'prediction_Ah':float(pred),'error_Ah':float(pred-truth['group_capacity_Ah']),
                            'truth_lowest_cell':truth['lowest_voltage_cell'],
                            'truth_lowest_cell_V':float(np.min(truth['cutoff_cell_V'])),
                            'truth_below_2p5V':truth['below_2p5V_at_group_cutoff']})
pd.DataFrame(state_rows).to_csv(OUT/'synthetic_truth_states.csv',index=False)
r=pd.DataFrame(results);r.to_csv(OUT/'synthetic_pack_predictions.csv',index=False)

# Uncertainty intervals for explicit four-cell model; calibration is against
# generated truth only. Same noise scale as the injected estimate error, with
# structural shape perturbation left unmodelled.
intervals=[]
for row in state_rows[:cfg['uncertainty_scenarios']]:
    name=row['scenario'];true=next(x[1] for x in scenarios if x[0]==name)
    shape=next(x[2] for x in scenarios if x[0]==name)
    estimated=PackState(np.clip(true.capacity_Ah+rng.normal(0,5,4),70,120),
                        np.clip(true.initial_SOC+rng.normal(0,.02,4),.85,1),
                        np.clip(true.delta_R_ohm+rng.normal(0,.0005,4),-.001,.004))
    draws=[]
    for j in range(cfg['uncertainty_draws_per_scenario']):
        sampled=PackState(np.clip(estimated.capacity_Ah+rng.normal(0,5,4),70,120),
                          np.clip(estimated.initial_SOC+rng.normal(0,.02,4),.85,1),
                          np.clip(estimated.delta_R_ohm+rng.normal(0,.0005,4),-.001,.004))
        draws.append(pack.cutoff(sampled)['group_capacity_Ah'])
    actual=pack.cutoff(true,truth_shape_mV=shape,truth_dynamic_R=True)['group_capacity_Ah']
    lo,hi=np.quantile(draws,[.05,.95])
    intervals.append({'scenario':name,'family':row['family'],'truth_Ah':actual,
                      'lower90_Ah':lo,'upper90_Ah':hi,'covered90':bool(lo<=actual<=hi),
                      'width90_Ah':hi-lo})
unc=pd.DataFrame(intervals);unc.to_csv(OUT/'synthetic_uncertainty_intervals.csv',index=False)

scores=[]
for (family,info,method),g in r.groupby(['family','information','method']):
    for subset,part in [('all',g),('no_cell_below_2p5V',g.loc[~g.truth_below_2p5V])]:
        if len(part)==0:continue
        scores.append({'family':family,'information':info,'method':method,'subset':subset,'n':len(part),
                       'MAE_Ah':float(part.error_Ah.abs().mean()),
                       'P95_abs_Ah':float(part.error_Ah.abs().quantile(.95)),
                       'max_abs_Ah':float(part.error_Ah.abs().max()),
                       'bias_Ah':float(part.error_Ah.mean())})
scores=pd.DataFrame(scores);scores.to_csv(OUT/'method_scores.csv',index=False)
summary={'CK0_rebuilt_capacity_Ah':recon['group_capacity_Ah'],
         'CK0_reference_capacity_Ah':float(ref.discharged_Ah.iloc[-1]),
         'CK0_cutoff_cell_voltages_V':recon['cutoff_cell_V'].tolist(),
         'step_convergence':step,'permutation_voltage_error_V':permutation_error,
         'scenario_count':len(scenarios),'random_stress_count':cfg['random_scenarios'],
         'fraction_truth_below_2p5V_at_group_cutoff':float(r.drop_duplicates('scenario').truth_below_2p5V.mean()),
         'random_scores_all':scores.loc[(scores.family=='random_stress')&(scores.subset=='all')].to_dict('records'),
         'uncertainty_90_coverage_synthetic':float(unc.covered90.mean()),
         'uncertainty_90_median_width_Ah':float(unc.width90_Ah.median()),
         'limit':'Analytic stress distribution, same CK0 base with unmodelled shape/R dynamics; no real hidden CK capacity accuracy; oracle state is unattainable on D3.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('random_scores_all','step_convergence')},ensure_ascii=False),flush=True)
