"""Train-fold input-domain gate and age fallback for shallow-window models."""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m2_features import frame_for_condition
OUT=TASK/'runs/M2_quality_gate_v1'
OUT.mkdir(parents=True,exist_ok=False)
primary=frame_for_condition(20,'persistent')
variants={'primary':primary}
for name in ['3p45','3p55','full_tail','mid_event']:
    folder=TASK/'runs'/f'M2_crop_{name}_v1'
    variants[name]=frame_for_condition(20,'persistent',folder/'visibility.csv',folder/'cropped_events.csv')
pred=pd.read_csv(TASK/'runs/M2_primary_v2/predictions.csv')
shifts=pd.read_csv(TASK/'runs/M2_crop_counterfactual_v1/same_capacity_crop_shifts.csv')
models=['fixed_window_ridge','mask_ridge','within_cell_ratio_ridge','rbf_residual']
rows=[]
for quantile in [0.01,0.05]:
    for held in primary.cell_id.unique():
        train=primary.loc[primary.cell_id.ne(held)]
        lowV,highV=train.v_end_V.quantile([quantile,1-quantile])
        lowI,highI=train.current_A.quantile([quantile,1-quantile])
        for crop,frame in variants.items():
            heldframe=frame.loc[frame.cell_id.eq(held)]
            for item in heldframe.itertuples(index=False):
                key={'cell_id':held,'target_ordinal':item.target_ordinal}
                age_row=pred.loc[(pred.cell_id==held)&(pred.target_ordinal==item.target_ordinal)&
                                 (pred.method=='age_ridge')]
                assert len(age_row)==1
                if crop=='primary':
                    age=float(age_row.pred_soh_pp.iloc[0])
                else:
                    age_shift=shifts.loc[(shifts.cell_id==held)&
                                          (shifts.target_ordinal==item.target_ordinal)&
                                          (shifts.alternate_crop==crop)&
                                          (shifts.method=='age_ridge')]
                    assert len(age_shift)==1
                    age=float(age_shift.alternate_prediction_pp.iloc[0])
                valid=bool(item.w03_mask==1 and np.isfinite(item.v_end_V) and
                           lowV<=item.v_end_V<=highV and
                           np.isfinite(item.current_A) and lowI<=item.current_A<=highI)
                for model in models:
                    base=pred.loc[(pred.cell_id==held)&(pred.target_ordinal==item.target_ordinal)&
                                  (pred.method==model)]
                    assert len(base)==1
                    raw=float(base.pred_soh_pp.iloc[0])
                    if crop!='primary':
                        alternate=shifts.loc[(shifts.cell_id==held)&
                                               (shifts.target_ordinal==item.target_ordinal)&
                                               (shifts.alternate_crop==crop)&
                                               (shifts.method==model)]
                        assert len(alternate)==1
                        raw=float(alternate.alternate_prediction_pp.iloc[0])
                    rows.append({**key,'crop':crop,'method':model,'gate_quantile':quantile,
                                 'gate_valid':valid,'raw_prediction_pp':raw,
                                 'gated_prediction_pp':raw if valid else age,
                                 'fallback':'candidate' if valid else 'age_ridge',
                                 'low_v_V':float(lowV),'high_v_V':float(highV),
                                 'low_current_A':float(lowI),'high_current_A':float(highI)})
result=pd.DataFrame(rows)
result.to_csv(OUT/'predictions.csv',index=False)
label=pd.read_csv(ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv',
                  usecols=['cell_id','target_ordinal','target_soh_pp'])
main=result.loc[result.crop=='primary'].merge(label,on=['cell_id','target_ordinal'],validate='many_to_one')
scoring=[]
for (quantile,method),part in main.groupby(['gate_quantile','method']):
    per=part.assign(ae=(part.gated_prediction_pp-part.target_soh_pp).abs()).groupby('cell_id').ae.mean()
    scoring.append({'gate_quantile':quantile,'method':method,'macro_mae_pp':float(per.mean()),
                    'worst_cell_mae_pp':float(per.max()),
                    'fallback_targets':int((~part.gate_valid).sum())})
pair=[]
for (quantile,method),part in result.groupby(['gate_quantile','method']):
    base=part.loc[part.crop=='primary',['cell_id','target_ordinal','gated_prediction_pp']].rename(
        columns={'gated_prediction_pp':'primary_gated_pp'})
    for crop,alt in part.loc[part.crop!='primary'].groupby('crop'):
        joined=alt.merge(base,on=['cell_id','target_ordinal'],validate='one_to_one')
        ae=(joined.gated_prediction_pp-joined.primary_gated_pp).abs()
        pair.append({'gate_quantile':quantile,'method':method,'crop':crop,
                     'median_abs_shift_pp':float(ae.median()),
                     'p95_abs_shift_pp':float(ae.quantile(.95)),
                     'max_abs_shift_pp':float(ae.max()),
                     'shift_gt2pp':int(ae.gt(2).sum()),
                     'fallback_targets':int((~joined.gate_valid).sum())})
pd.DataFrame(scoring).to_csv(OUT/'primary_scores.csv',index=False)
pd.DataFrame(pair).to_csv(OUT/'same_capacity_stability.csv',index=False)
(OUT/'summary.json').write_text(json.dumps({'primary_scores':scoring,'stability':pair},indent=2)+'\n')
print(pd.DataFrame(scoring).to_string(index=False),flush=True)
