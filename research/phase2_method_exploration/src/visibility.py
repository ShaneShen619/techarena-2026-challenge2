"""D1 model input boundary: expose only budgeted fragments and P1 anchor.

Evaluation code keeps cell IDs and event IDs for grouping/audit separately.
The returned feature frame omits those identifiers and any full-charge depth.
"""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
VIEW=TASK/'data_manifests/d1_target_visibility.csv'
CROPS=TASK/'data_manifests/d1_cropped_events.csv'
FEATURE_COLUMNS=['fragment_start','fragment_end','n_samples','observed_span_Ah',
                 'median_dt_s','max_dt_s','temperature_C','current_A',
                 'v_start_V','v_end_V'] + [f'w{i:02d}_{suffix}' for i in range(9) for suffix in ('Ah','visible')]


class D1Visibility:
    def __init__(self, visibility_path:Path=VIEW, crop_path:Path=CROPS):
        self._v=pd.read_csv(visibility_path)
        self._e=pd.read_csv(crop_path)
        assert len(self._v)==1080 and self._v.metadata_status.eq('native_fragment_verified').all()
        assert not any(x in self._e for x in ('full_cc_Ah_audit_only','target_capacity_Ah','target_soh_pp'))
        self._index=self._e.set_index(['event_id','budget_Ah'],verify_integrity=True)

    def get(self, cell_id:str,target_ordinal:int,budget_Ah:int=20,history_mode:str='persistent'):
        matches=self._v.loc[(self._v.cell_id==cell_id)&(self._v.target_ordinal==target_ordinal)&
                            (self._v.budget_Ah==budget_Ah)&(self._v.history_mode==history_mode)]
        if len(matches)!=1: raise KeyError((cell_id,target_ordinal,budget_Ah,history_mode))
        info=matches.iloc[0]
        ids=json.loads(info.allowed_event_ids_json)
        crop_rows=[]
        for eid in ids:
            source=self._index.loc[(eid,budget_Ah)]
            assert str(source.crop_position)==str(info.crop_position)
            assert pd.Timestamp(source.fragment_end)<pd.Timestamp(info.target_discharge_start)
            crop_rows.append(source[FEATURE_COLUMNS])
        features=pd.DataFrame(crop_rows,columns=FEATURE_COLUMNS).reset_index(drop=True)
        return {'anchor_capacity_Ah':float(info.anchor_capacity_Ah),
                'anchor_time':str(info.anchor_discharge_start),
                'prefix_prequalified_charge_count':int(info.candidate_event_count),
                'target_cutoff':str(info.target_discharge_start),
                'history_mode':history_mode,'budget_Ah':int(budget_Ah),
                'fragments':features}

    def audit_event_ids(self,cell_id:str,target_ordinal:int,budget_Ah:int=20,history_mode:str='persistent'):
        matches=self._v.loc[(self._v.cell_id==cell_id)&(self._v.target_ordinal==target_ordinal)&
                            (self._v.budget_Ah==budget_Ah)&(self._v.history_mode==history_mode)]
        if len(matches)!=1: raise KeyError((cell_id,target_ordinal,budget_Ah,history_mode))
        return json.loads(matches.iloc[0].allowed_event_ids_json)
