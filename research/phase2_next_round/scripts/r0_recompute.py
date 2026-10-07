"""Independent metric recomputation from frozen point predictions."""
from pathlib import Path
import hashlib, json
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OLD=ROOT/'research/phase2_method_exploration'
specs=[
 ('within_cell_ratio_ridge',OLD/'runs/M9_D1_v15_M2_20Ah_persistent_v1/predictions.csv','within_cell_ratio_ridge'),
 ('TCN_finetune',OLD/'runs/M9_D1_v15_TCN_v1/predictions.csv','TCN_finetune'),
 ('TCN_scratch',OLD/'runs/M9_D1_v15_TCN_v1/predictions.csv','TCN_from_scratch'),
 ('TCN_scratch_no_voltage',OLD/'runs/M9_D1_v15_no_voltage_v1/predictions.csv','TCN_scratch_no_voltage'),
 ('TCN_scratch_meta_only',OLD/'runs/M9_D1_v15_meta_only_v1/predictions.csv','TCN_scratch_meta_only'),
 ('prefix_temperature_MLP',OLD/'runs/M9_D1_v15_prefix_temperature_v1/predictions.csv','prefix_temperature_MLP')]
rows=[]; hashes={}
for label,path,method in specs:
    hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    d=pd.read_csv(path); d=d.loc[d.method.eq(method)].copy()
    assert len(d)>0
    d=d.groupby(['cell_id','target_ordinal'],as_index=False).agg(
        truth=('target_soh_pp','first'),prediction=('pred_soh_pp','mean'))
    assert len(d)==180 and d.cell_id.nunique()==6
    d['error']=d.prediction-d.truth; d['abs']=d.error.abs(); d['late']=d.target_ordinal.ge(21)
    per=d.groupby('cell_id')['abs'].mean(); late=d.loc[d.late].groupby('cell_id')['abs'].mean()
    rows.append({'method':label,'macro_MAE_pp':per.mean(),'worst_cell_MAE_pp':per.max(),
                 'max_abs_error_pp':d['abs'].max(),'p95_abs_error_pp':d['abs'].quantile(.95),
                 'late_macro_MAE_pp':late.mean(),'late_worst_cell_MAE_pp':late.max(),
                 'targets':len(d),'cells':d.cell_id.nunique()})
out=pd.DataFrame(rows); out.to_csv(TASK/'outputs/r0_baseline_recompute.csv',index=False)
summary={'source_hashes':hashes,'rows':rows,
         'note':'pointwise seed ensemble then entity-equal macro MAE; late means ordinals 21-30; D1 development only'}
(TASK/'outputs/r0_baseline_recompute.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(out.to_string(index=False))
