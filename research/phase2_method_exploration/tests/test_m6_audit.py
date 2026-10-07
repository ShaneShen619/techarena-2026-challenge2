"""Independent TU score recalculation and causal-filter future-injection tests."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m6_models import WienerResidual,AdaptiveWorkpointResidual

inventory=pd.read_csv(TASK/'runs/M6_TU_inventory_v1/system_inventory.csv')
steps=pd.read_csv(TASK/'runs/M6_TU_steps_v1/extraction_summary_by_system.csv')
assert len(inventory)==len(steps)==28
assert inventory.file_data_rows.sum()==steps.raw_rows.sum()==132777059
for sid in (5,6,8,9,10,12,15,18,21,22):
    x=pd.read_csv(TASK/f'runs/M6_TU_steps_v1/system_{sid:02d}_events.csv')
    x=x.loc[x.threshold_A.eq(10)]
    assert x.step_interval_s.between(1,10).all()
    assert x.delta_I_A.le(-10).all()
    assert x.SOC_BMS_pct.between(40,94).all()
    assert x.R_step_mOhm.loc[x.R_plausible].between(0,10).all()

r=TASK/'runs/M6_workpoint_time_v5'
p=pd.read_csv(r/'LOSO_online_predictions.csv')
s=pd.read_csv(r/'per_system_scores.csv')
for row in s.itertuples(index=False):
    x=p.loc[p.held_system.eq(row.held_system)&p.method.eq(row.method)]
    assert len(x)==row.n
    assert abs(x.error_mOhm.abs().mean()-row.MAE_mOhm)<1e-10
    assert abs(np.sqrt(np.mean(x.error_mOhm**2))-row.RMSE_mOhm)<1e-10
    assert x.warmup_rows_same_cell.ge(20).all()
summary=json.loads((r/'summary.json').read_text())
assert summary['held_system_count']==10
assert summary['scored_cell_events']==90231

from pandas import Timestamp
times=[Timestamp('2020-01-01'),Timestamp('2020-01-02'),Timestamp('2020-01-03')]
for maker in (lambda:WienerResidual(.2),lambda:AdaptiveWorkpointResidual(.2)):
    def path(future):
        f=maker();pred=[]
        for j,t in enumerate(times):
            if isinstance(f,WienerResidual):
                m,_=f.predict(t);pred.append(m);f.update(([.1,.2,future][j]))
            else:
                m,_,h=f.predict(t,[.1,.2,.3,.4]);pred.append(m);f.update(([.1,.2,future][j]),h)
        return pred
    assert np.allclose(path(.3)[:3],path(30.)[:3])

aux=json.loads((TASK/'runs/M6_official_R_aux_v1/summary.json').read_text())
old=json.loads((TASK/'runs/M1_voltage_forecast_v1/summary.json').read_text())
assert abs(aux['future_voltage_MAE_mV']['matched_last_shift']-old['mae_mV_by_method']['matched_last_shift'])<1e-9
print('M6 source, metric, online-causality and official auxiliary checks passed')
