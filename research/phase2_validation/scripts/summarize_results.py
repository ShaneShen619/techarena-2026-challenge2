"""Rebuild metrics and paired uncertainty from immutable per-target records."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
OUT=TASK/'outputs'

def metrics(df,level,dataset,protocol,run_id,error_col,unit,group_col=None):
    rows=[]
    for method,g in df.groupby('method'):
        e=g[error_col].to_numpy(float)
        cell_mae=g.groupby(group_col)[error_col].apply(lambda x:x.abs().mean()) if group_col else None
        rows.append(dict(run_id=run_id,evidence=level,dataset=dataset,protocol=protocol,
            method=method,status='completed',n_samples=len(e),n_independent_groups=df[group_col].nunique() if group_col else np.nan,
            unit=unit,MAE_micro=np.mean(abs(e)),MAE_macro=cell_mae.mean() if cell_mae is not None else np.nan,
            RMSE=np.sqrt(np.mean(e*e)),max_abs_error=np.max(abs(e)),bias=np.mean(e),
            fallback_rate=g.fallback.mean() if 'fallback' in g else np.nan))
    return rows

def main():
    p1=pd.read_csv(OUT/'phase1_crossvalidation_predictions.csv')
    adapted=pd.read_csv(OUT/'phase1_a_ablations.csv')
    p1b=adapted[adapted.variant.eq('B2_single_cell_window')].copy()
    p1b['method']='B2_single_cell_window'
    e2=pd.read_csv(TASK/'runs/E2_twoRC_hysteresis_20seeds/predictions.csv')
    rows=metrics(p1,'E3-P1','phase1_six_cells','single_cell_0.5C_or_1C_discharge_to_2.5V',
        'E3P1_sixfold_v2_reused_development_cells','error_pp','SOH_pp','cell_id')
    rows+=metrics(p1b,'E3-P1','phase1_six_cells','single_cell_0.5C_or_1C_discharge_to_2.5V',
        'E3P1_A_ablation_reused_development_cells','error_pp','SOH_pp','cell_id')
    rows+=metrics(e2,'E2','simulated_four_series','independently_simulated_C20_to_11.2V',
        'E2_twoRC_hysteresis_20seeds','error_Ah','Ah','seed')
    pd.DataFrame(rows).to_csv(OUT/'metrics.csv',index=False)
    per_cell=p1.assign(abs_error=lambda d:d.error_pp.abs()).groupby(['cell_id','method']).abs_error.mean().unstack()
    diffs=(per_cell['A']-per_cell['B']).to_numpy()
    rng=np.random.default_rng(20260928)
    sample=rng.integers(0,len(diffs),(2000,len(diffs)))
    boots=diffs[sample].mean(axis=1)
    uncertainty=pd.DataFrame([{'contrast':'A_minus_B_absolute_error_pp','n_cells':len(diffs),
        'observed_macro_difference_pp':diffs.mean(),'cluster_bootstrap_2.5pct':np.quantile(boots,.025),
        'cluster_bootstrap_97.5pct':np.quantile(boots,.975),'seed':20260928,
        'interpretation':'descriptive uncertainty only; six development cells, not significance proof'}])
    uncertainty.to_csv(OUT/'paired_uncertainty.csv',index=False)
    per_cell.to_csv(OUT/'phase1_per_cell_mae.csv')
    print(pd.DataFrame(rows).to_string(index=False))
    print(uncertainty.to_string(index=False))

if __name__=='__main__':main()
