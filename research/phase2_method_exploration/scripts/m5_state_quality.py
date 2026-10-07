"""Supplemental M5 sensitivity to four-cell state quality on milder heterogeneity."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M5_state_quality_v1';OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(TASK/'src'))
from m5_pack import CK0Pack,PackState,uniform_mean_state,minimum_cell_usable_Ah
cfg=json.loads((TASK/'configs/m5_state_quality.json').read_text())
pack=CK0Pack(pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz'))
rng=np.random.default_rng(cfg['seed']);rows=[];truth_rows=[]
for i in range(cfg['scenarios']):
    common=rng.uniform(90,100)
    Q=np.clip(common+np.clip(rng.normal(0,2,4),-4,4),80,105)
    z=rng.uniform(.985,1,4);R=rng.uniform(0,.001,4)
    shape=rng.uniform(-10,10,4)
    true=PackState(Q,z,R);tt=pack.cutoff(true,truth_shape_mV=shape,truth_dynamic_R=True)
    truth_rows.append({'scenario':i,'common_Q_Ah':common,'truth_capacity_Ah':tt['group_capacity_Ah'],
                       'truth_min_cell_V':float(tt['cutoff_cell_V'].min()),'below_2p5V':tt['below_2p5V_at_group_cutoff']})
    for level in cfg['quality_levels']:
        est=PackState(np.clip(Q+rng.normal(0,level['Q_noise_Ah'],4),70,120),
                      np.clip(z+rng.normal(0,level['SOC_noise'],4),.85,1),
                      np.clip(R+rng.normal(0,level['R_noise_ohm'],4),-.001,.004))
        methods={'minimum_cell_usable_Ah':minimum_cell_usable_Ah(est),
                 'uniform_mean_cell':pack.cutoff(uniform_mean_state(est))['group_capacity_Ah'],
                 'explicit_four_cell':pack.cutoff(est)['group_capacity_Ah']}
        for method,pred in methods.items():
            rows.append({'scenario':i,'quality':level['name'],'method':method,
                         'true_capacity_Ah':tt['group_capacity_Ah'],'prediction_Ah':pred,
                         'error_Ah':pred-tt['group_capacity_Ah'],
                         'truth_below_2p5V':tt['below_2p5V_at_group_cutoff']})
pred=pd.DataFrame(rows);pred.to_csv(OUT/'quality_predictions.csv',index=False)
pd.DataFrame(truth_rows).to_csv(OUT/'truth_scenarios.csv',index=False)
scores=[]
for (quality,method),g in pred.groupby(['quality','method']):
    scores.append({'quality':quality,'method':method,'n':len(g),
                   'MAE_Ah':float(g.error_Ah.abs().mean()),
                   'P95_abs_Ah':float(g.error_Ah.abs().quantile(.95)),
                   'max_abs_Ah':float(g.error_Ah.abs().max()),
                   'bias_Ah':float(g.error_Ah.mean())})
pd.DataFrame(scores).to_csv(OUT/'quality_scores.csv',index=False)
s=pd.DataFrame(scores)
summary={'scenarios':len(truth_rows),'fraction_below_2p5V':float(pd.DataFrame(truth_rows).below_2p5V.mean()),
         'scores':scores,'selection_notice':cfg['status'],
         'interpretation':'Explicit model structural merit requires sufficiently precise per-cell state. Same CK0 base and synthetic truth only.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'scenarios':summary['scenarios'],'fraction_below_2p5V':summary['fraction_below_2p5V']},ensure_ascii=False),flush=True)
