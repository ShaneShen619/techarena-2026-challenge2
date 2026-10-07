"""Adversarial checks for the shared D1 input boundary."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK/'src'))
from visibility import D1Visibility, FEATURE_COLUMNS


def main() -> None:
    boundary = D1Visibility()
    manifest = pd.read_csv(TASK/'data_manifests/d1_target_visibility.csv')
    crops = pd.read_csv(TASK/'data_manifests/d1_cropped_events.csv')
    assert len(manifest) == 1080
    assert len(crops) > 0
    assert not {'target_capacity_Ah', 'target_soh_pp', 'full_cc_Ah_audit_only'} & set(FEATURE_COLUMNS)
    assert crops.groupby(['event_id','budget_Ah']).size().eq(1).all()
    for row in manifest.itertuples(index=False):
        view = boundary.get(row.cell_id, int(row.target_ordinal), int(row.budget_Ah), row.history_mode)
        assert list(view['fragments'].columns) == FEATURE_COLUMNS
        assert len(view['fragments']) == row.allowed_event_count
        assert view['prefix_prequalified_charge_count'] == row.candidate_event_count
        assert view['prefix_prequalified_charge_count'] >= len(view['fragments'])
        assert pd.to_datetime(view['fragments'].fragment_end).lt(pd.Timestamp(row.target_discharge_start)).all()
        assert view['fragments'].observed_span_Ah.le(row.budget_Ah + 1e-8).all()
        assert view['fragments'].max_dt_s.le(60).all()
        assert not any('event_id' in x or 'cell_id' in x or 'full' in x or 'target_capacity' in x for x in view['fragments'].columns)
        if row.history_mode == 'cold':
            assert len(view['fragments']) <= 1
        else:
            assert len(view['fragments']) <= 15
        if len(view['fragments']):
            assert view['fragments'].fragment_end.is_monotonic_increasing
    # Deliberately inject a future source event into an earlier query: adapter must fail closed.
    source = manifest.iloc[0]
    later = crops.loc[(crops.cell_id == source.cell_id) & (crops.budget_Ah == source.budget_Ah) &
                      (pd.to_datetime(crops.fragment_end) > pd.Timestamp(source.target_discharge_start))]
    assert len(later)
    mutated = manifest.copy()
    mutated.at[0, 'allowed_event_ids_json'] = json.dumps([str(later.iloc[-1].event_id)])
    with tempfile.TemporaryDirectory() as temp:
        vpath = Path(temp)/'v.csv'
        cpath = Path(temp)/'c.csv'
        mutated.to_csv(vpath, index=False)
        crops.to_csv(cpath, index=False)
        poisoned = D1Visibility(vpath, cpath)
        try:
            poisoned.get(source.cell_id, int(source.target_ordinal), int(source.budget_Ah), source.history_mode)
        except AssertionError:
            pass
        else:
            raise AssertionError('future event contamination accepted')
        # Label and full-depth columns are forbidden even if not in the public field list.
        for forbidden in ('target_capacity_Ah', 'full_cc_Ah_audit_only'):
            contaminated = crops.assign(**{forbidden: 999.0})
            contaminated.to_csv(cpath, index=False)
            try:
                D1Visibility(vpath, cpath)
            except AssertionError:
                pass
            else:
                raise AssertionError(f'{forbidden} admitted')
    print(json.dumps({'views_checked': len(manifest), 'fragments_checked': len(crops),
                      'future_injection_rejected': True, 'label_and_depth_injections_rejected': True}))


if __name__ == '__main__':
    main()
