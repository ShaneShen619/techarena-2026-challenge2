"""Consolidate frozen evaluations with sample counts and epsilon-dependence audit."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
sys.path.insert(0,str(STUDY/'src'))
from common import dump

def consolidate():
    paths=[STUDY/'stage0/baseline_long.csv',
           STUDY/'stage_D/outputs/D_independent_robustness_long.csv',
           STUDY/'stage_A/outputs/A_independent_smoothing_long.csv']
    paths+=sorted((STUDY/'stage_C/outputs').glob('*long.csv'))
    frames=[]
    for p in paths:
        if p.exists():
            f=pd.read_csv(p).rename(columns={'smooth':'a4s','proxy_Q':'proxy'})
            f['source']=str(p.relative_to(STUDY))
            frames.append(f)
    data=pd.concat(frames,ignore_index=True)
    keys=['model','scenario','k','step','a4s','delta']
    data=data.drop_duplicates(keys,keep='last')
    data.to_csv(HERE/'outputs/independent_all_predictions.csv',index=False)
    main=data[(data.step=='main')&(data.a4s==2.)]
    summary=[]
    for key,g in main.groupby(['model','scenario','delta']):
        valid=g.err_pp.dropna()
        ef=g[g.k>=2].err_pp.dropna()
        summary.append(dict(zip(['model','scenario','delta'],key),n_predictions=len(valid),n_expected=len(g),
                            MAE=float(valid.abs().mean()),MAX=float(valid.abs().max()),
                            RMSE=float(np.sqrt((valid**2).mean())),CK2_7_MAE=float(ef.abs().mean())))
    pd.DataFrame(summary).to_csv(HERE/'outputs/independent_main_metrics.csv',index=False)
    main[(main.scenario=='real')&(main.delta==.4)].pivot_table(index='k',columns='model',values='err_pp').to_csv(HERE/'outputs/independent_per_checkup_errors.csv')
    invariance=[]
    for name,g in main[(main.scenario=='real')&(main.k>=2)].groupby('model'):
        spans=g.groupby('k').err_pp.agg(lambda x: x.max()-x.min())
        maximum=float(spans.max())
        invariance.append({'model':name,'max_error_span_across_delta_pp':maximum,
                           'epsilon_independent_within_1e_8_pp':bool(maximum<=1e-8)})
    dump(HERE/'outputs/independent_epsilon_invariance.json',invariance)
    return summary,invariance

if __name__=='__main__':
    summary,invariance=consolidate()
    print(pd.DataFrame(summary).query("scenario=='real' and delta==.4").to_string(index=False))
    print(json.dumps(invariance,indent=2))
