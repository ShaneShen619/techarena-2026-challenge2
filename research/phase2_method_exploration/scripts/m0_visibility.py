"""Freeze per-target historical event IDs and D1 input budget before modeling.

This stage confirms event IDs and metadata feasibility. Raw-row cropping and
window support are verified later; no full-charge quantity enters model views.
The target capacity column is never loaded by this script.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OLD = ROOT/'research/phase2_temperature_improvement'
PANEL = OLD/'outputs/panel_main.csv'
EVENTS = OLD/'runs/M4_feature_audit_v1/events.csv'
EXPECTED_PANEL = '7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c'

if hashlib.sha256(PANEL.read_bytes()).hexdigest() != EXPECTED_PANEL:
    raise RuntimeError('P1 panel hash mismatch')
panel = pd.read_csv(PANEL, usecols=['cell_id', 'target_ordinal', 'target_cycle',
                                    'target_discharge_start', 'anchor_discharge_start',
                                    'anchor_capacity_Ah'],
                    parse_dates=['target_discharge_start', 'anchor_discharge_start'])
events = pd.read_csv(EVENTS, usecols=['cell_id', 'event_id', 'event_end', 'cc_Ah'],
                     parse_dates=['event_end'])
if len(panel) != 180 or panel.groupby('cell_id').size().ne(30).any():
    raise RuntimeError('panel target count changed')
if events.event_id.duplicated().any():
    raise RuntimeError('duplicate event ID')
views = []
for budget in (15, 20, 30):
    for row in panel.itertuples(index=False):
        visible = events.loc[(events.cell_id == row.cell_id) &
                             (events.event_end < row.target_discharge_start) &
                             (events.cc_Ah >= budget),
                             ['event_id', 'event_end']].sort_values(['event_end', 'event_id'])
        ids = visible.event_id.astype(str).tolist()
        initial = ids[:10]
        recent = ids[-5:]
        current = ids[-1] if ids else None
        for mode in ('cold', 'persistent'):
            allowed = [current] if mode == 'cold' and current else (
                sorted(set(initial + recent), key=ids.index) if mode == 'persistent' else [])
            # The historical selector uses full CC Ah only to decide if a budget
            # can be cropped. No original depth/total CC Ah is exposed to models.
            views.append({'cell_id': row.cell_id, 'target_ordinal': int(row.target_ordinal),
                          'target_cycle': int(row.target_cycle),
                          'target_discharge_start': row.target_discharge_start.isoformat(),
                          'anchor_discharge_start': row.anchor_discharge_start.isoformat(),
                          'anchor_capacity_Ah': float(row.anchor_capacity_Ah),
                          'anchor_reference_curve_allowed': False,
                          'budget_Ah': budget, 'crop_position': 'first_3p50V_crossing_tail',
                          'p1_native_sampling_interval_s': 30,
                          'official_reference_sampling_interval_s': 10,
                          'resampling_rule': 'never_upsample_P1',
                          'history_mode': mode, 'candidate_event_count': len(ids),
                          'current_event_id': current,
                          'initial_event_ids_json': json.dumps(initial),
                          'recent_event_ids_json': json.dumps(recent),
                          'allowed_event_ids_json': json.dumps(allowed),
                          'allowed_event_count': len(allowed),
                          'allowed_event_end_max': visible.event_end.max().isoformat() if len(visible) else '',
                          'state_initialization': 'anchor_only_each_target' if mode == 'cold' else 'anchor_plus_allowed_cropped_history',
                          'counter_access': 'none',
                          'allowed_model_fields': 'cropped_I_V_T_time; cropped_window_Ah; window_mask; anchor_capacity_Ah',
                          'forbidden_model_fields': 'full_cc_Ah; uncut_window_Ah; target_capacity_Ah; target_soh_pp; future_events',
                          'metadata_status': 'prequalified_event_ids_raw_crop_pending',
                          'no_event_reason': '' if ids else 'no_CC_event_meeting_budget'})

out = pd.DataFrame(views)
assert len(out) == 180 * 3 * 2
assert out[['cell_id', 'target_ordinal', 'budget_Ah', 'history_mode']].duplicated().sum() == 0
for row in out.itertuples(index=False):
    allowed = json.loads(row.allowed_event_ids_json)
    if row.history_mode == 'cold' and len(allowed) > 1:
        raise RuntimeError('cold start exposed extra event')
    if row.allowed_event_end_max and not pd.Timestamp(row.allowed_event_end_max) < pd.Timestamp(row.target_discharge_start):
        raise RuntimeError('future event in input')
out.to_csv(TASK/'data_manifests/d1_target_visibility.csv', index=False)
summary = {'rows': len(out), 'target_count': 180, 'budgets_Ah': [15,20,30],
           'history_modes': ['cold','persistent'],
           'no_event_by_budget_mode': out.assign(empty=out.allowed_event_count.eq(0)).groupby(['budget_Ah','history_mode']).empty.sum().to_dict(),
           'limit': 'Event IDs and CC depth are only metadata prequalification; raw first-3.50-V 30 s native slices and window masks still must be built.'}
summary['no_event_by_budget_mode'] = {f'{a}_{b}': int(v) for (a,b),v in summary['no_event_by_budget_mode'].items()}
(TASK/'data_manifests/d1_target_visibility_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(summary, ensure_ascii=False))
