"""Read-only inventory of roughly 20 A / 30 minute discharge candidates.

Inventory only: candidates are not confirmed full-charge diagnostic episodes.
"""
from pathlib import Path
import json
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / 'runs/M0_pulse_replay_v1'
OUT.mkdir(parents=True, exist_ok=False)
ROOT = Path(__file__).resolve().parents[3]
rows = []
for path in sorted((ROOT/'data/operation').glob('*.csv.gz')):
    f = pd.read_csv(path, parse_dates=['timestamp'])
    selected = f.current_A.between(-20.5, -19.5)
    dt = f.timestamp.diff().dt.total_seconds()
    groups = (selected.ne(selected.shift()) | dt.gt(20) | dt.le(0)).cumsum()
    for _, event in f.loc[selected].groupby(groups[selected]):
        duration = (event.timestamp.iloc[-1]-event.timestamp.iloc[0]).total_seconds()
        if not 1500 <= duration <= 2100:
            continue
        idx = event.index[0]
        prior = f.loc[(f.timestamp < event.timestamp.iloc[0]) &
                      (f.timestamp >= event.timestamp.iloc[0]-pd.Timedelta(hours=1))]
        rows.append({'file': path.name, 'start': event.timestamp.iloc[0].isoformat(),
                     'end': event.timestamp.iloc[-1].isoformat(), 'duration_s': duration,
                     'n_samples': len(event), 'mean_current_A': float(event.current_A.mean()),
                     'mean_temperature_C': float(event.temp_mean_C.mean()),
                     'chamber_C': float(event.chamber_temperature_C.median()),
                     'prior_1h_max_pack_voltage_V': float(prior.pack_voltage_V.max()) if len(prior) else None,
                     'before_CK7': bool(event.timestamp.iloc[-1] < pd.Timestamp('2025-08-28'))})
pd.DataFrame(rows).to_csv(OUT/'pulse_candidates.csv', index=False)
summary = {'definition': 'Current -20 ±0.5 A, adjacent gap <=20 s, span 1500–2100 s; not confirmed diagnostic events.',
           'all_candidates': len(rows), 'before_CK7': sum(r['before_CK7'] for r in rows),
           'by_chamber_C': pd.Series([r['chamber_C'] for r in rows]).value_counts().to_dict(),
           'prior_hour_max_pack_at_least_13p95V': sum(r['prior_1h_max_pack_voltage_V'] is not None and r['prior_1h_max_pack_voltage_V'] >= 13.95 for r in rows)}
(OUT/'pulse_candidate_summary.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary))
