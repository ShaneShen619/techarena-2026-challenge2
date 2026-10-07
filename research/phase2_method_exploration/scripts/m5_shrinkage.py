"""M5 follow-up: label-free variance shrinkage of noisy per-cell states."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M5_shrinkage_v1';OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(TASK/'src'))
from m5_pack import CK0Pack,PackState,uniform_mean_state,minimum_cell_usable_Ah
cfg=json.loads((TASK/'configs/m5_shrinkage.json').read_text())
pack=CK0Pack(pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz'))
rng=np.random.default_rng(cfg['seed'])
def shrink(values,sigma):
    variance=float(np.var(values,ddof=1))
    if variance<=1e-15:return np.full(4,np.mean(values)),0.
    w=float(np.clip((variance-sigma**2)/variance,0,1))
    return np.mean(values)+w*(values-np.mean(values)),w
rows=[]
for i in range(cfg['scenarios']):
    common=rng.uniform(90,100)
    Q=np.clip(common+np.clip(rng.normal(0,2,4),-4,4),80,105)
    z=rng.uniform(.985,1,4);R=rng.uniform(0,.001,4);shape=rng.uniform(-10,10,4)
    true=PackState(Q,z,R)
    actual=pack.cutoff(true,truth_shape_mV=shape,truth_dynamic_R=True)
    for level in cfg['quality_levels']:
        qn=np.clip(Q+rng.normal(0,level['Q_noise_Ah'],4),70,120)
        zn=np.clip(z+rng.normal(0,level['SOC_noise'],4),.85,1)
        rn=np.clip(R+rng.normal(0,level['R_noise_ohm'],4),-.001,.004)
        noisy=PackState(qn,zn,rn)
        qs,wq=shrink(qn,level['Q_noise_Ah'])
        zs,wz=shrink(zn,level['SOC_noise'])
        rs,wr=shrink(rn,level['R_noise_ohm'])
        shrunk=PackState(qs,zs,rs)
        pred={'minimum_cell_usable_Ah':minimum_cell_usable_Ah(noisy),
              'uniform_mean_cell':pack.cutoff(uniform_mean_state(noisy))['group_capacity_Ah'],
              'explicit_four_cell':pack.cutoff(noisy)['group_capacity_Ah'],
              'noise_aware_shrunk_four_cell':pack.cutoff(shrunk)['group_capacity_Ah']}
        for method,value in pred.items():
            rows.append({'scenario':i,'quality':level['name'],'method':method,
                         'truth_group_Ah':actual['group_capacity_Ah'],'pred_Ah':value,
                         'error_Ah':value-actual['group_capacity_Ah'],
                         'truth_cell_below_2p5V':actual['below_2p5V_at_group_cutoff'],
                         'Q_weight':wq,'SOC_weight':wz,'R_weight':wr})
out=pd.DataFrame(rows);out.to_csv(OUT/'predictions.csv',index=False)
scores=[]
for (quality,method),g in out.groupby(['quality','method']):
    scores.append({'quality':quality,'method':method,'n':len(g),'MAE_Ah':float(g.error_Ah.abs().mean()),
                   'P95_abs_Ah':float(g.error_Ah.abs().quantile(.95)),
                   'max_abs_Ah':float(g.error_Ah.abs().max()),
                   'bias_Ah':float(g.error_Ah.mean()),
                   'mean_Q_weight':float(g.Q_weight.mean()),'mean_SOC_weight':float(g.SOC_weight.mean())})
pd.DataFrame(scores).to_csv(OUT/'scores.csv',index=False)
summary={'scenarios':cfg['scenarios'],'fraction_truth_cell_below_2p5V':float(out.drop_duplicates('scenario').truth_cell_below_2p5V.mean()),
         'scores':scores,'status':cfg['status'],'real_data_limit':cfg['claim_limit']}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'scenarios':summary['scenarios'],'fraction_truth_cell_below_2p5V':summary['fraction_truth_cell_below_2p5V']},ensure_ascii=False),flush=True)
