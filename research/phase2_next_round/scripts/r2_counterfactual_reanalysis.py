"""Strict-v1.5 endpoint and Ah-budget counterfactual reanalysis.

The target truth is unchanged while the observable crop definition changes.
Large prediction spans therefore diagnose state/crop sensitivity rather than
capacity response. This reuses frozen point predictions without refitting.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OLD=ROOT/'research/phase2_method_exploration/runs'
endpoint={
 '3.45V':OLD/'M9_D1_v15_M2_3p45_20Ah_persistent_v1/predictions.csv',
 '3.50V':OLD/'M9_D1_v15_M2_20Ah_persistent_v1/predictions.csv',
 '3.55V':OLD/'M9_D1_v15_M2_3p55_20Ah_persistent_v1/predictions.csv'}
budget={
 '15Ah':OLD/'M9_D1_v15_M2_15Ah_persistent_v1/predictions.csv',
 '20Ah':OLD/'M9_D1_v15_M2_20Ah_persistent_v1/predictions.csv',
 '30Ah':OLD/'M9_D1_v15_M2_30Ah_persistent_v1/predictions.csv'}
methods=['age_ridge','fixed_window_ridge','within_cell_ratio_ridge','rbf_residual']

def evaluate(sources, axis):
    pieces=[]
    for condition,path in sources.items():
        d=pd.read_csv(path); d=d.loc[d.method.isin(methods)].copy(); d['condition']=condition
        pieces.append(d[['cell_id','target_ordinal','method','target_soh_pp','pred_soh_pp','error_pp','condition','w01_visible','w03_visible']])
    allp=pd.concat(pieces,ignore_index=True)
    scores=[]; sensitivity=[]
    for (condition,method),g in allp.groupby(['condition','method']):
        per=g.assign(abs_pp=g.error_pp.abs()).groupby('cell_id').abs_pp.mean()
        scores.append({'axis':axis,'condition':condition,'method':method,'macro_MAE_pp':per.mean(),
                       'worst_cell_MAE_pp':per.max(),'max_abs_error_pp':g.error_pp.abs().max(),
                       'w01_coverage':g.w01_visible.mean(),'w03_coverage':g.w03_visible.mean()})
    for method,g in allp.groupby('method'):
        w=g.pivot_table(index=['cell_id','target_ordinal','target_soh_pp'],columns='condition',values='pred_soh_pp')
        assert len(w)==180 and not w.isna().any().any()
        span=w.max(axis=1)-w.min(axis=1)
        base=g.loc[g.condition.eq(list(sources)[1])].set_index(['cell_id','target_ordinal'])['error_pp'].abs().reindex(span.index.droplevel('target_soh_pp'))
        rho=float(spearmanr(span.to_numpy(),base.to_numpy()).statistic)
        sensitivity.append({'axis':axis,'method':method,'median_prediction_span_pp':span.median(),
                            'p95_prediction_span_pp':span.quantile(.95),'max_prediction_span_pp':span.max(),
                            'span_error_spearman':rho,'targets':len(span)})
    return allp,pd.DataFrame(scores),pd.DataFrame(sensitivity)

ep,eps,epsens=evaluate(endpoint,'crop_endpoint')
bu,bus,busens=evaluate(budget,'visible_Ah_budget')
point=pd.concat([ep.assign(axis='crop_endpoint'),bu.assign(axis='visible_Ah_budget')],ignore_index=True)
scores=pd.concat([eps,bus],ignore_index=True); sens=pd.concat([epsens,busens],ignore_index=True)
truth=ep.loc[ep.condition.eq('3.50V') & ep.method.eq('age_ridge'),['cell_id','target_ordinal','target_soh_pp']]
steps=[]
for _,g in truth.sort_values(['cell_id','target_ordinal']).groupby('cell_id'):
    steps.extend(np.abs(np.diff(g.target_soh_pp.to_numpy(float))))
truth_step_median=float(np.median(steps)); truth_step_p95=float(np.quantile(steps,.95))
point.to_csv(TASK/'outputs/r2_counterfactual_predictions.csv',index=False)
scores.to_csv(TASK/'outputs/r2_condition_scores.csv',index=False)
sens.to_csv(TASK/'outputs/r2_sensitivity.csv',index=False)
summary={'truth_adjacent_change_median_pp':truth_step_median,'truth_adjacent_change_p95_pp':truth_step_p95,
         'sensitivity':sens.to_dict('records'),
         'interpretation':'same target truth with changed crop endpoint/budget; prediction span is state/crop sensitivity, not capacity response',
         'claim_limit':'D1 strict-prefix development proxy; no true shallow-cycle or official capacity confirmation'}
(TASK/'outputs/r2_counterfactual_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(scores.to_string(index=False)); print(sens.to_string(index=False)); print(json.dumps(summary,ensure_ascii=False))
