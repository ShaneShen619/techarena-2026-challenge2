"""Causal shallow-window trends and bounded degradation-rate feedback."""
from __future__ import annotations
import numpy as np
import pandas as pd

SLOPES = [f"slope_{j:02d}_per_day" for j in range(9)]
SIGNAL = SLOPES + ["median_slope_per_day", "slope_spread_per_day"]
CONTROL = ["age_days", "charge_EFC", "current_temp_C", "current_A", "valid_windows", "matched_events"]

def signal_columns(axis="days"):
    if axis not in ("days","events"):
        raise ValueError("Unknown trend coordinate")
    unit="per_day" if axis=="days" else "per_event"
    return [f"slope_{j:02d}_{unit}" for j in range(9)]+[f"median_slope_{unit}",f"slope_spread_{unit}"]

def summarize_trend(fragments, at_date, axis="days"):
    columns=signal_columns(axis)
    out = {c: np.nan for c in columns}
    out.update(valid_windows=0, matched_events=0, current_temp_C=np.nan,
               current_A=np.nan, event_end="", eligible=False, age_of_signal_days=np.nan)
    if fragments.empty:
        return out
    if axis=="events" and "event_ordinal" not in fragments:
        raise ValueError("Past-only event ordinals required")
    f = fragments.sort_values("fragment_end", kind="stable").reset_index(drop=True)
    t = pd.to_datetime(f.fragment_end)
    at = pd.Timestamp(at_date)
    if not (t < at).all():
        raise ValueError("A fragment must precede query time")
    latest = f.tail(5)
    out.update(current_temp_C=float(latest.temperature_C.median()), current_A=float(latest.current_A.median()))
    used = set()
    for j, col in enumerate(columns[:9]):
        pairs, nodes = [], set()
        for b in range(len(f)):
            for a in range(b):
                days = (t.iloc[b]-t.iloc[a]).total_seconds()/86400
                if days < 1:
                    continue
                distance=days if axis=="days" else float(f.iloc[b].event_ordinal-f.iloc[a].event_ordinal)
                if distance<=0:continue
                ra, rb = f.iloc[a], f.iloc[b]
                if not np.isfinite([ra.temperature_C, rb.temperature_C, ra.current_A, rb.current_A]).all():
                    continue
                if abs(ra.temperature_C-rb.temperature_C)>5 or abs(ra.current_A-rb.current_A)>.2*abs(ra.current_A):
                    continue
                qa, qb = ra[f"w{j:02d}_Ah"], rb[f"w{j:02d}_Ah"]
                if not np.isfinite([qa,qb]).all() or min(qa,qb)<=0:
                    continue
                pairs.append(-np.log(qb/qa)/distance)
                nodes.update([a,b])
        if len(nodes)>=3:
            out[col] = float(np.median(pairs))
            used.update(nodes)
    values = np.array([out[c] for c in columns[:9]])
    valid = values[np.isfinite(values)]
    out.update(valid_windows=len(valid), matched_events=len(used))
    if len(valid):
        out[columns[-2]] = float(np.median(valid))
        out[columns[-1]] = float(np.max(valid)-np.min(valid))
        out["event_end"] = t.iloc[max(used)].isoformat()
        out["age_of_signal_days"] = (at-t.iloc[max(used)]).total_seconds()/86400
        out["eligible"] = out["age_of_signal_days"]<=60
    return out

def feedback(prior, anchor, log_measurement, quality, event_ends, gain, mode):
    """Forward: observation at t changes only increments AFTER t.

    Damage: separate retrospective average-loss rescaling, not forward rate.
    A sign is never forced; only a learned positive multiplier is bounded.
    """
    prior = np.asarray(prior, float)
    if mode not in ("forward", "damage") or not 0<=gain<=1:
        raise ValueError("Invalid feedback mode or gain")
    if any(len(a)!=len(prior) for a in (log_measurement,quality,event_ends)):
        raise ValueError("Feedback inputs must have equal length")
    values, logs = [], []
    state = 0.; last_event = ""; previous_b = float(anchor); current_q = float(anchor)
    for i, (b,z,ok,event) in enumerate(zip(prior, log_measurement, quality, event_ends)):
        before = state
        if mode == "forward":
            current_q -= np.exp(before)*max(0., previous_b-b)
        accepted = bool(ok and event and event!=last_event and np.isfinite(z))
        if accepted:
            state = float(np.clip((1-gain)*state+gain*np.clip(z, np.log(.5), np.log(2)), np.log(.5), np.log(2)))
            last_event = str(event)
        if mode == "damage":
            current_q = float(anchor)-np.exp(state)*max(0., float(anchor)-b)
        values.append(current_q)
        logs.append(dict(target_ordinal=i+1, accepted=accepted, multiplier_used=float(np.exp(before)),
                         multiplier_next=float(np.exp(state)), event_end=str(event)))
        previous_b = b
    return np.asarray(values), logs

def training_log_ratios(prior, truth, anchor, mode):
    """Capacity labels used ONLY for training entities, never as A inputs."""
    prior, truth = np.asarray(prior), np.asarray(truth)
    if mode == "damage":
        denominator = float(anchor)-prior
        numerator = float(anchor)-truth
    else:
        end = np.minimum(np.arange(len(prior))+3, len(prior)-1)
        denominator = prior-prior[end]
        numerator = truth-truth[end]
    valid = denominator>.05
    ratio = np.clip(numerator/np.maximum(denominator, 1e-12), .5, 2.)
    return np.where(valid, np.log(ratio), np.nan)
