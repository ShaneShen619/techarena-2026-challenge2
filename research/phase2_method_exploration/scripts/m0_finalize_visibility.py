"""Finish D1 visibility against reconstructed source fragments.

Never backfill a failed event with an unseen earlier deep-charge event. Missing
event IDs remain missing evidence and are counted for every target.
"""
import hashlib
import json
from pathlib import Path
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
manifest=TASK/'data_manifests/d1_target_visibility.csv'
events=TASK/'data_manifests/d1_cropped_events.csv'
frame=pd.read_csv(manifest)
crop=pd.read_csv(events)
available={(str(r.event_id),int(r.budget_Ah)):r for r in crop.itertuples(index=False)}
final=[]
for row in frame.to_dict(orient='records'):
    budget=int(row['budget_Ah'])
    old_allowed=json.loads(row['allowed_event_ids_json'])
    kept=[eid for eid in old_allowed if (eid,budget) in available]
    missing=[eid for eid in old_allowed if (eid,budget) not in available]
    current=row['current_event_id'] if isinstance(row['current_event_id'],str) else None
    if current not in kept: current=None
    row['allowed_event_ids_json']=json.dumps(kept)
    row['missing_qualified_event_ids_json']=json.dumps(missing)
    row['allowed_event_count']=len(kept)
    row['current_event_id']=current if current is not None else ''
    row['metadata_status']='native_fragment_verified'
    row['no_event_reason']='no_endpoint_or_budget_fragment' if not kept else ''
    row['allowed_fragment_end_max']=max((available[(eid,budget)].fragment_end for eid in kept),default='')
    if row['allowed_fragment_end_max'] and not pd.Timestamp(row['allowed_fragment_end_max'])<pd.Timestamp(row['target_discharge_start']):
        raise AssertionError('future fragment')
    final.append(row)
out=pd.DataFrame(final)
out.to_csv(TASK/'data_manifests/d1_target_visibility.csv',index=False)
summary={'target_rows':len(out),'zero_event_rows':int(out.allowed_event_count.eq(0).sum()),
         'targets_without_current_fragment':int(out.current_event_id.eq('').sum()),
         'lost_old_prequalified_event_references':int(sum(len(json.loads(x)) for x in out.missing_qualified_event_ids_json)),
         'event_source_sha256':hashlib.sha256(events.read_bytes()).hexdigest(),
         'visibility_sha256':hashlib.sha256((TASK/'data_manifests/d1_target_visibility.csv').read_bytes()).hexdigest(),
         'label_columns_in_visibility':not any('target_capacity' in c or 'target_soh' in c for c in out.columns),
         'no_substitution_for_missing_fragment':True}
(TASK/'data_manifests/d1_target_visibility_final_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary),flush=True)
