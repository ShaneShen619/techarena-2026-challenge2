"""Comparators that are not the submitted model: the ExampleModel analogue and an anchor trend."""
import numpy as np

from .common import PROTOCOL

LAST_N = PROTOCOL["baseline"]["last_n"]


def e4_baseline(view, k):
    """label0 x median(last LAST_N visible partial charges) / median(window-0 partial charges)."""
    cut = view.boundaries[k]
    vis = [p for p in view.programs if p["t_end"] <= cut and p["q_partial"] > 0]
    ref = [p["q_partial"] for p in vis if p["m"] == 0]
    if not vis or not ref:
        return view.label0
    last = [p["q_partial"] for p in sorted(vis, key=lambda p: p["t_end"])[-LAST_N:]]
    return view.label0 * float(np.median(last)) / float(np.median(ref))


def e5_trend(view, k):
    """Last visible anchor (+ eps0) extrapolated linearly with the slope of the last two anchors."""
    cut = view.boundaries[k]
    vis = sorted((a for a in view.anchors if a["t_end"] <= cut), key=lambda a: a["t_end"])
    last = vis[-1]
    q_last = view.label0 if last["m"] == 0 else last["q"] + view.eps0
    if len(vis) < 2:
        return q_last
    prev = vis[-2]
    days = (last["t_end"] - prev["t_end"]).total_seconds() / 86400.0
    slope = (last["q"] - prev["q"]) / days if days > 0 else 0.0
    return q_last + slope * (cut - last["t_end"]).total_seconds() / 86400.0
