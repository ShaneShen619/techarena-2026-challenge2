"""D1 target-to-native-event mapping with strict prefix checks, no labels."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M7_target_map_v1';OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(TASK/'src'))
from m2_features import frame_for_condition
v=pd.read_csv(TASK/'data_manifests/d1_target_visibility.csv')
v=v.loc[v.budget_Ah.eq(20)&v.history_mode.eq('persistent')].sort_values(['cell_id','target_ordinal'])
assert len(v)==180
data=np.load(TASK/'runs/M7_sequences_v1/native_sequences.npz')
event_ids=data['event_ids'].astype(str);index={e:i for i,e in enumerate(event_ids)}
manifest=pd.read_csv(TASK/'runs/M7_sequences_v1/sequence_manifest.csv').set_index('event_id')
slots=[];rows=[]
for row in v.itertuples(index=False):
    allowed=json.loads(row.allowed_event_ids_json)
    initial=[e for e in json.loads(row.initial_event_ids_json) if e in allowed][:10]
    recent=[e for e in json.loads(row.recent_event_ids_json) if e in allowed][-5:]
    assert row.current_event_id in allowed
    selected=[row.current_event_id]+initial+recent
    selected+= [None]*(16-len(selected))
    assert len(selected)==16
    for e in selected:
        if e is not None:
            assert e in index
            assert pd.Timestamp(manifest.loc[e].fragment_end)<pd.Timestamp(row.target_discharge_start)
    slots.append([index[e] if e is not None else -1 for e in selected])
    rows.append({'cell_id':row.cell_id,'target_ordinal':int(row.target_ordinal),
                 'target_cutoff':row.target_discharge_start,'current_event_id':row.current_event_id,
                 'current_index':index[row.current_event_id],
                 'initial_event_count':len(initial),'recent_event_count':len(recent),
                 'total_unique_allowed_events':len(set(allowed)),
                 'max_fragment_end':max(manifest.loc[e].fragment_end for e in allowed)})
mapframe=pd.DataFrame(rows)
x=frame_for_condition(20,'persistent').sort_values(['cell_id','target_ordinal'])
assert (x[['cell_id','target_ordinal']].to_numpy()==mapframe[['cell_id','target_ordinal']].to_numpy()).all()
meta=x[['anchor_pp','age_days','age_log1p','history_count','last_gap_days','prefix_prequalified_charge_count',
        'current_A','current_temp_C']].to_numpy(float)
np.savez_compressed(OUT/'target_inputs.npz',indices=np.array(slots,dtype=np.int16),metadata=meta,
                    cell_ids=mapframe.cell_id.to_numpy(str),target_ordinals=mapframe.target_ordinal.to_numpy(int))
mapframe.to_csv(OUT/'target_map.csv',index=False)
summary={'targets':len(rows),'mean_unique_allowed_events':float(mapframe.total_unique_allowed_events.mean()),
         'all_current_present':bool(mapframe.current_index.ge(0).all()),
         'all_fragment_ends_before_target':bool((pd.to_datetime(mapframe.max_fragment_end)<pd.to_datetime(mapframe.target_cutoff)).all()),
         'labels_in_inputs':False}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
