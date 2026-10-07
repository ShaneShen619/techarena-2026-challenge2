"""Expand the recorded official B diagnostics into an auditable event funnel.

The gap flag is informational and may coincide with a later fit rejection;
it is not subtracted as an additional mutually exclusive outcome.
"""
from pathlib import Path
import ast
import pandas as pd

task=Path(__file__).resolve().parents[1]
raw=pd.read_csv(task/'runs/official_diagnostics.csv')
rows=[]
previous={'charge_runs':0,'short_event':0,'fit_attempt':0,'accepted':0}
reasons=('temperature_mismatch','implausible_episode_jump','capacity_at_bound',
         'unidentifiable','model_mismatch','invalid_voltage','insufficient_Ah')
previous.update({key:0 for key in reasons})
previous['gap_flag']=0
for row in raw[raw.route.eq('route_b')].itertuples():
    if row.checkup=='CK0':
        continue
    rejected=ast.literal_eval(row.rejections)
    current={'charge_runs':int(row.charge_runs),'accepted':int(row.updates)}
    current.update({key:int(rejected.get(key,0)) for key in reasons})
    current['gap_flag']=int(rejected.get('gap_reinitialization',0))
    current['fit_attempt']=current['accepted']+sum(current[key] for key in reasons if key!='temperature_mismatch')
    current['short_event']=current['charge_runs']-current['fit_attempt']-current['temperature_mismatch']
    assert current['short_event']>=0
    assert current['charge_runs']==current['short_event']+current['temperature_mismatch']+current['fit_attempt']
    rows.append({'checkup':row.checkup,**{f'cumulative_{k}':v for k,v in current.items()},
                 **{f'new_{k}':v-previous[k] for k,v in current.items()}})
    previous=current
pd.DataFrame(rows).to_csv(task/'outputs/route_b_rejection_funnel.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
