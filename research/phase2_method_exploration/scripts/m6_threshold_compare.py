"""Compare 10A versus 20A model scores on exactly matching target events."""
from pathlib import Path
import json
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M6_threshold_common_v1';OUT.mkdir(parents=True,exist_ok=False)
left=pd.read_csv(TASK/'runs/M6_workpoint_time_v5/LOSO_online_predictions.csv')
right=pd.read_csv(TASK/'runs/M6_workpoint_time_20A_v1/LOSO_online_predictions.csv')
key=['held_system','cell','timestamp','method']
same=left.merge(right,on=key,suffixes=('_10A','_20A'),validate='one_to_one')
assert (same.actual_R_mOhm_10A-same.actual_R_mOhm_20A).abs().max()<1e-12
same.to_csv(OUT/'matched_event_predictions.csv',index=False)
rows=[]
for (sid,method),g in same.groupby(['held_system','method']):
    rows.append({'held_system':sid,'method':method,'n':len(g),
                 'MAE_10A_mOhm':float(g.error_mOhm_10A.abs().mean()),
                 'MAE_20A_mOhm':float(g.error_mOhm_20A.abs().mean())})
s=pd.DataFrame(rows);s.to_csv(OUT/'matched_system_scores.csv',index=False)
summary={'common_cell_events_for_best':int(len(same.loc[same.method.eq('global_plus_adaptive_workpoint')])),
         'system_macro_MAE_common_by_method':{str(m):{'10A':float(g.MAE_10A_mOhm.mean()),
                                                    '20A':float(g.MAE_20A_mOhm.mean())}
                                            for m,g in s.groupby('method')},
         'limit':'Different models were trained on different threshold-selected data; identical target-event comparison controls scoring composition but not training-set difference.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'common_cell_events_for_best':summary['common_cell_events_for_best']},ensure_ascii=False),flush=True)
