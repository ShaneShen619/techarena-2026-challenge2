"""M5 H14: causal delayed deep-charge proxy under synthetic bias drift."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M5_delayed_proxy_v1';OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(TASK/'src'))
from m5_pack import CK0Pack,PackState,Q0
cfg=json.loads((TASK/'configs/m5_delayed_proxy.json').read_text())
pack=CK0Pack(pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz'))
rng=np.random.default_rng(cfg['seed']);rows=[];truthrows=[]
for trajectory in range(cfg['trajectories']):
    fade=rng.uniform(*cfg['cell_fade_Ah_per_month_range'],4)
    accel=rng.uniform(*cfg['cell_fade_acceleration_Ah_per_month2_range'],4)
    socloss=rng.uniform(*cfg['initial_SOC_loss_per_month_range'],4)
    rgrowth=rng.uniform(*cfg['delta_R_growth_ohm_per_month_range'],4)
    shape=rng.uniform(*cfg['truth_tail_shape_mV_at_CK7_range'],4)
    true=[]
    for k in range(cfg['checkpoints']):
        state=PackState(Q0-fade*k-accel*k*k,1-socloss*k,rgrowth*k)
        t=pack.cutoff(state,truth_shape_mV=shape*k/7,truth_dynamic_R=True)['group_capacity_Ah']
        true.append(t)
        truthrows.append({'trajectory':trajectory,'checkup':f'CK{k}','true_group_Ah':t})
    for mode in ('stable','drift','step'):
        basebias=rng.uniform(0,2)
        observed=[]
        for k in range(cfg['checkpoints']):
            bias=basebias+(.5*k if mode=='drift' else 2*(k>=3) if mode=='step' else 0)
            observed.append(true[k]+bias+rng.normal(0,.5))
        calibration=Q0-observed[0]
        for k in range(1,cfg['checkpoints']):
            prior=observed[k-1]
            p={'CK0_hold':Q0,
               'last_deep_CK0_calibrated':prior+calibration,
               'last_two_deep_linear_extrapolation':prior+calibration+(prior-observed[k-2] if k>=2 else 0)}
            for method,pred in p.items():
                rows.append({'trajectory':trajectory,'mode':mode,'checkup':f'CK{k}',
                             'method':method,'truth_Ah':true[k],
                             'latest_observation_checkpoint':f'CK{k-1}',
                             'pred_Ah':pred,'error_Ah':pred-true[k],
                             'within_assumed_plusminus4Ah':abs(pred-true[k])<=4})
pred=pd.DataFrame(rows);pred.to_csv(OUT/'causal_predictions.csv',index=False)
pd.DataFrame(truthrows).to_csv(OUT/'truth_trajectories.csv',index=False)
scores=[]
for (mode,method),g in pred.groupby(['mode','method']):
    scores.append({'bias_mode':mode,'method':method,'n':len(g),
                   'MAE_Ah':float(g.error_Ah.abs().mean()),
                   'P95_abs_Ah':float(g.error_Ah.abs().quantile(.95)),
                   'max_abs_Ah':float(g.error_Ah.abs().max()),
                   'bias_Ah':float(g.error_Ah.mean()),
                   'plusminus4Ah_coverage_synthetic':float(g.within_assumed_plusminus4Ah.mean())})
pd.DataFrame(scores).to_csv(OUT/'method_scores.csv',index=False)
summary={'trajectories':cfg['trajectories'],'causal_predictions':len(pred),'scores':scores,
         'limitation':cfg['limitation']}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'trajectories':summary['trajectories'],'causal_predictions':summary['causal_predictions']},ensure_ascii=False),flush=True)
