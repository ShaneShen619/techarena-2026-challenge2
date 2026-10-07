"""Exploratory ablations on the reused P1 panel; NOT a new blind test.

Predeclared before execution: six feature sets, original 3 widths/4 penalties,
nested physical-cell validation plus temperature-group exclusion for full model.
Does not modify the frozen outputs or acceptance criteria.
"""
from pathlib import Path
import sys
import json
import hashlib
import itertools
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
TASK = OUT.parent
sys.path.insert(0, str(TASK / 'src'))
from multi_window_ridge import add_derived_features, feature_columns, WIDTHS
sys.path.insert(0, str(TASK / 'scripts'))
from run_m4_fixed_baseline import fit_predict

KEY = ['cell_id', 'target_ordinal']
f = pd.read_csv(TASK / 'runs/M4_feature_audit_v1/features.csv')
p = pd.read_csv(TASK / 'outputs/panel_main.csv')
a = pd.read_csv(TASK / 'runs/M4_feature_audit_v1/throughput.csv')
f = f.merge(p[KEY + ['anchor_soh_pp', 'target_soh_pp']], on=KEY, validate='one_to_one')
f = f.merge(a[KEY + ['qualified_charge_efc']], on=KEY, validate='one_to_one')
f = add_derived_features(f, age_col='qualified_charge_efc')
f['temperature_group'] = f.cell_id.str.extract(r'_(\d+)degC_')[0]
assert f.temperature_group.notna().all()

def cols_for(name, width):
    full = feature_columns(width, True)
    temperature = ['temp_C', 'initial_temp_C', 'delta_temp_C']
    usage = ['age_fraction', 'age_fraction_sq', 'event_age_days']
    if name == 'full': return full
    if name == 'no_full_CC': return [c for c in full if c != 'cc_ratio']
    if name == 'windows_T': return [c for c in full if c not in usage + ['cc_ratio']]
    if name == 'windows_noT': return [c for c in full if c not in usage + ['cc_ratio'] + temperature + ['temp_interaction']]
    if name == 'usage_T': return usage + temperature + ['delta_current_rel']
    if name == 'full_CC_T': return ['cc_ratio', 'delta_current_rel'] + temperature
    raise ValueError(name)

specs = [(m, 'cell_id') for m in ['full', 'no_full_CC', 'windows_T', 'windows_noT', 'usage_T', 'full_CC_T']]
specs += [('full', 'temperature_group')]
config = {'warning': 'Exploratory sensitivity on previously reused 6-cell P1 panel; no fresh validation data.',
          'specs': specs, 'widths': WIDTHS, 'lambdas': [.1, 1., 10., 100.],
          'panel_sha256': hashlib.sha256((TASK/'outputs/panel_main.csv').read_bytes()).hexdigest()}
(OUT/'diagnostic_config.json').write_text(json.dumps(config, indent=2)+'\n')
predictions, selections, summaries = [], [], []
for method, group in specs:
    model_rows = []
    for held in sorted(f[group].unique()):
        train, test = f[f[group] != held], f[f[group] == held]
        widths = list(WIDTHS) if method not in ['usage_T', 'full_CC_T'] else [list(WIDTHS)[0]]
        candidates = []
        for width, lam in itertools.product(widths, [.1, 1., 10., 100.]):
            inner_errors = []
            for val in sorted(train[group].unique()):
                sub, hold = train[train[group] != val], train[train[group] == val]
                pred = fit_predict(sub, hold, cols_for(method, width), lam)
                inner_errors.extend(pd.Series(np.abs(pred-hold.target_soh_pp.to_numpy()), index=hold.cell_id).groupby(level=0).mean().tolist())
            candidates.append({'width': width, 'lambda': lam, 'inner_cell_macro_mae': float(np.mean(inner_errors))})
        best = min(candidates, key=lambda c: (c['inner_cell_macro_mae'], c['lambda']))
        pred = fit_predict(train, test, cols_for(method, best['width']), best['lambda'])
        rows = test[KEY+['target_soh_pp']].copy()
        rows['prediction_soh_pp'] = pred
        rows['method'], rows['outer_group'] = method, group
        rows['held_group'] = held
        model_rows.append(rows)
        selections.append({'method': method, 'group': group, 'held': held, 'best': best, 'candidates': candidates})
    result = pd.concat(model_rows, ignore_index=True)
    result['absolute_error_pp'] = abs(result.prediction_soh_pp-result.target_soh_pp)
    per_cell = result.groupby('cell_id').absolute_error_pp.mean()
    summary = {'method': method, 'outer_group': group, 'macro_mae_pp': float(per_cell.mean()),
               'worst_cell_mae_pp': float(per_cell.max()), 'p95_absolute_error_pp': float(result.absolute_error_pp.quantile(.95)),
               'max_absolute_error_pp': float(result.absolute_error_pp.max()), 'per_cell_mae_pp': per_cell.to_dict()}
    summaries.append(summary)
    predictions.append(result)
    print(json.dumps(summary), flush=True)
assert abs(summaries[0]['macro_mae_pp'] - 1.038662897) < 1e-7, 'Original full model reproduction mismatch'
pd.concat(predictions, ignore_index=True).to_csv(OUT/'diagnostic_predictions.csv', index=False)
(OUT/'diagnostic_selections.json').write_text(json.dumps(selections, indent=2)+'\n')
(OUT/'diagnostic_summary.json').write_text(json.dumps(summaries, indent=2)+'\n')
