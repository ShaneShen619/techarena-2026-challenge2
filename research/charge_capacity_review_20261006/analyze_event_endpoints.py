"""Read-only audit of operating charge/discharge endpoints and comparable windows."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
events, windows = [], []
for path in sorted((ROOT / 'data/operation').glob('*.csv.gz')):
    d = pd.read_csv(path, parse_dates=['timestamp'])
    t = (d.timestamp - d.timestamp.iloc[0]).dt.total_seconds().to_numpy()
    i, v = d.current_A.to_numpy(), d.pack_voltage_V.to_numpy()
    state = np.where(i > .5, 1, np.where(i < -.5, -1, 0))
    boundaries = np.r_[0, np.flatnonzero((state[1:] != state[:-1]) | (np.diff(t) > 30) | (np.diff(t) < 0)) + 1, len(d)]
    for a, end in zip(boundaries[:-1], boundaries[1:]):
        b = end - 1
        if state[a] == 0 or b <= a or t[b] - t[a] < 900:
            continue
        tt, ii, vv = t[a:b+1], i[a:b+1], v[a:b+1]
        q = float(abs(np.sum((ii[:-1] + ii[1:]) * np.diff(tt) / 7200)))
        median_i = float(np.median(ii))
        kind = 'charge' if state[a] == 1 else 'discharge'
        if state[a] == 1 and vv[-1] >= 13.95 and median_i > 15:
            kind = 'full_charge'
        elif state[a] == -1 and abs(median_i + 20.4) < .1 and np.ptp(ii) < .2 and 1500 <= tt[-1] - tt[0] <= 2100:
            kind = 'scheduled_pulse'
        elif state[a] == -1 and q >= 15:
            kind = 'long_dynamic_discharge'
        pre = a - 1 if a > 0 and 0 <= t[a] - t[a-1] <= 30 else None
        post = b + 1 if b + 1 < len(d) and 0 <= t[b+1] - t[b] <= 30 else None
        row = dict(file=path.name, segment=int(d.segment.iloc[a]), setpoint_C=int(d.chamber_temperature_C.iloc[a]),
                   kind=kind, start_index_in_file=int(a), end_index_in_file=int(b), t_start=str(d.timestamp.iloc[a]),
                   t_end=str(d.timestamp.iloc[b]), n_rows=int(b-a+1), duration_min=float((tt[-1]-tt[0])/60),
                   Q_Ah=q, start_loaded_V=float(vv[0]), end_loaded_V=float(vv[-1]),
                   pre_voltage_V=float(v[pre]) if pre is not None else None,
                   pre_current_A=float(i[pre]) if pre is not None else None,
                   post_voltage_V=float(v[post]) if post is not None else None,
                   post_current_A=float(i[post]) if post is not None else None,
                   current_median_A=median_i, current_min_A=float(ii.min()), current_max_A=float(ii.max()),
                   mean_temp_C=float(d.temp_mean_C.iloc[a:b+1].mean()),
                   start_temp_C=float(d.temp_mean_C.iloc[a]), end_temp_C=float(d.temp_mean_C.iloc[b]),
                   max_gap_s=float(np.diff(tt).max()))
        events.append(row)
        if kind != 'full_charge':
            continue
        def crossing(target):
            hit = np.flatnonzero(vv >= target)
            if not len(hit) or hit[0] == 0:
                return None
            j = int(hit[0])
            f = (target - vv[j-1]) / (vv[j] - vv[j-1])
            # Require the threshold to be reached under the same 20.4 A CC regime.
            if min(ii[j-1], ii[j]) < 20.2 or max(ii[j-1], ii[j]) > 20.6:
                return None
            return j, float(tt[j-1] + f * (tt[j] - tt[j-1])), float(ii[j-1] + f * (ii[j] - ii[j-1]))
        for lo, hi in [(12.2, 13.9), (12.4, 13.9), (12.6, 13.9), (13.0, 13.9),
                       (13.5, 13.9), (13.6, 13.9), (13.7, 13.9), (13.8, 13.9)]:
            left, right = crossing(lo), crossing(hi)
            if left is None or right is None or right[1] <= left[1]:
                continue
            mid = (tt > left[1]) & (tt < right[1])
            tx = np.r_[left[1], tt[mid], right[1]]
            ix = np.r_[left[2], ii[mid], right[2]]
            if np.any((ix < 20.2) | (ix > 20.6)):
                continue
            qw = float(np.sum((ix[:-1] + ix[1:]) * np.diff(tx) / 7200))
            windows.append(dict(t_start=row['t_start'], segment=row['segment'], setpoint_C=row['setpoint_C'],
                                mean_temp_C=row['mean_temp_C'], V_lo=lo, V_hi=hi, Q_window_Ah=qw,
                                duration_min=float((right[1]-left[1])/60)))

ev = pd.DataFrame(events).sort_values('t_start').reset_index(drop=True)
ev['first_full_charge_in_segment'] = False
full_indices = ev[ev.kind == 'full_charge'].groupby('segment', sort=False).head(1).index
ev.loc[full_indices, 'first_full_charge_in_segment'] = True
ev.to_csv(OUT / 'operating_events.csv', index=False)
win = pd.DataFrame(windows).sort_values('t_start').reset_index(drop=True)
win.to_csv(OUT / 'fixed_CC_voltage_windows.csv', index=False)

def summary(x):
    columns = ['start_loaded_V', 'end_loaded_V', 'pre_voltage_V', 'post_voltage_V', 'Q_Ah', 'duration_min', 'mean_temp_C']
    return dict(count=len(x), **{c: {'min': float(x[c].min()), 'median': float(x[c].median()), 'max': float(x[c].max())} for c in columns})

summaries = {}
for kind in ['full_charge', 'scheduled_pulse', 'long_dynamic_discharge']:
    x = ev[ev.kind == kind]
    summaries[kind] = summary(x)
    for temp, g in x.groupby('setpoint_C'):
        summaries[f'{kind}_{temp}C'] = summary(g)
regular = ev[(ev.kind == 'full_charge') & (ev.pre_voltage_V >= 13.3)]
deep = ev[(ev.kind == 'full_charge') & (ev.pre_voltage_V < 13.3)]
summaries['regular_topup_charge'] = summary(regular)
summaries['deep_charge'] = summary(deep)
matched = regular[~regular.first_full_charge_in_segment]
regular_comparisons = []
for temp, g in matched.groupby('setpoint_C'):
    g = g.sort_values('t_start')
    early, late = g.head(3), g.tail(3)
    regular_comparisons.append(dict(setpoint_C=int(temp), count=len(g),
        early3_median_Ah=float(early.Q_Ah.median()), late3_median_Ah=float(late.Q_Ah.median()),
        change_pct=float((late.Q_Ah.median()/early.Q_Ah.median()-1)*100),
        early_dates=early.t_start.tolist(), late_dates=late.t_start.tolist(),
        early_start_rest_V=early.pre_voltage_V.tolist(), late_start_rest_V=late.pre_voltage_V.tolist(),
        early_mean_temp_C=float(early.mean_temp_C.mean()), late_mean_temp_C=float(late.mean_temp_C.mean())))
matched_win = win[win.t_start.isin(matched.t_start)]
deep_win = win[win.t_start.isin(deep.t_start) & (win.V_lo <= 13.0)]
deep_comparisons = []
for (lo, hi, temp), g in deep_win.groupby(['V_lo', 'V_hi', 'setpoint_C']):
    g = g.sort_values('t_start')
    if len(g) < 2:
        continue
    deep_comparisons.append(dict(V_lo=float(lo), V_hi=float(hi), setpoint_C=int(temp), count=len(g),
        first_date=g.t_start.iloc[0], last_date=g.t_start.iloc[-1],
        first_Ah=float(g.Q_window_Ah.iloc[0]), last_Ah=float(g.Q_window_Ah.iloc[-1]),
        first_to_last_change_pct=float((g.Q_window_Ah.iloc[-1]/g.Q_window_Ah.iloc[0]-1)*100),
        early3_median_Ah=float(g.head(3).Q_window_Ah.median()), late3_median_Ah=float(g.tail(3).Q_window_Ah.median()),
        early3_to_late3_change_pct=float((g.tail(3).Q_window_Ah.median()/g.head(3).Q_window_Ah.median()-1)*100)))
segment_summary = []
for (kind, seg, temp), g in ev[ev.kind.isin(['full_charge', 'scheduled_pulse', 'long_dynamic_discharge'])].groupby(['kind', 'segment', 'setpoint_C']):
    segment_summary.append(dict(kind=kind, segment=int(seg), setpoint_C=int(temp), **summary(g)))
comparisons = []
for (lo, hi, temp), g in matched_win.groupby(['V_lo', 'V_hi', 'setpoint_C']):
    g = g.sort_values('t_start')
    early, late = g.head(3), g.tail(3)
    comparisons.append(dict(V_lo=float(lo), V_hi=float(hi), setpoint_C=int(temp), count=len(g),
                            early3_median_Ah=float(early.Q_window_Ah.median()), late3_median_Ah=float(late.Q_window_Ah.median()),
                            change_pct=float((late.Q_window_Ah.median()/early.Q_window_Ah.median()-1)*100),
                            early_start=early.t_start.iloc[0], early_end=early.t_start.iloc[-1],
                            late_start=late.t_start.iloc[0], late_end=late.t_start.iloc[-1],
                            early_temp_mean_C=float(early.mean_temp_C.mean()), late_temp_mean_C=float(late.mean_temp_C.mean())))
out = dict(event_definition='Uninterrupted current-sign runs with |I| > 0.5 A, duration >= 15 min, same file, no gap >30 s. Q trapezoid between first and last active samples. Endpoints are loaded; adjacent pre/post measurements are separate.',
           full_charge_definition='Charge run ending at >=13.95 V and median current >15 A. Does not imply full discharge starts.',
           window_definition='First interpolated upward crossings of fixed group voltages within complete CC charge runs; every window current 20.2–20.6 A. Exploratory proxy, not hidden reference capacity.',
           summaries=summaries, segment_summary=segment_summary, regular_comparisons=regular_comparisons,
           matched_definition='Regular top-ups pre_voltage >=13.3 V, excluding first full-charge event of each segment to avoid different preceding history. 28 events: 9 at 25C and 19 at 45C.',
           window_comparisons=comparisons, deep_window_comparisons=deep_comparisons)
(OUT / 'endpoint_summary.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'selected_summaries': {k:summaries[k] for k in ['regular_topup_charge','deep_charge']},
                  'regular_comparisons': regular_comparisons, 'window_comparisons': comparisons,
                  'deep_window_comparisons': deep_comparisons}, ensure_ascii=False, indent=2))
