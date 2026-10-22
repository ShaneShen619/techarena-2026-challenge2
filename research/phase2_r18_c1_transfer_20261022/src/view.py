"""Emulate the pack's information structure on one Challenge 1 cell.

Per window of ``window_days`` (the pack's month):
* one anchor: the full CCCV charge of the first eligible cycle after the boundary (its
  discharge, a full capacity measurement, stays hidden);
* programs: the first eligible cycle after every ``program_spacing_days`` mark; of each,
  only the discharge down to ``visible_depth_ah`` and the top ``visible_charge_top_ah`` of
  the charge are visible.
Boundary B_0 plays CK0: label0 (the label of the anchor-0 cycle) is the only released label.
Truth at B_k (k >= 1) is the median of the ``truth_n`` labels nearest to B_k.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import steps
from .c1io import STEP, CellRows, cycle_summary, structural_flags
from .common import PROTOCOL

INFO = PROTOCOL["information_structure"]
MODEL = PROTOCOL["model"]
DAY = pd.Timedelta(days=1)


@dataclass
class CellView:
    cell_id: str
    boundaries: pd.DatetimeIndex
    label0: float
    anchors: list
    programs: list
    truth: dict
    truth_sd: dict
    meta: dict = field(default_factory=dict)

    @property
    def eps0(self):
        return self.label0 - self.anchors[0]["q"]


def build_view(raw, cell_id="", window_days=INFO["window_days"], program_rule="every5d",
               with_full=False):
    """CellView of one cell. ``with_full`` adds the full-discharge step depth (check C10)."""
    rows = CellRows(raw)
    cyc = cycle_summary(raw)
    flags, ref = structural_flags(cyc)
    by_time = cyc.sort_values("chg_t0", kind="stable")
    anchor_cycles = by_time.index[flags.loc[by_time.index, "anchor_ok"].to_numpy()]
    program_cycles = by_time.index[flags.loc[by_time.index, "program_ok"].to_numpy()]
    if not len(anchor_cycles):
        raise ValueError(f"{cell_id}: no eligible anchor cycle")
    b0 = cyc.loc[anchor_cycles[0], "chg_t0"] - pd.Timedelta(minutes=1)
    t_last = max(cyc["chg_t1"].max(), cyc["dis_t1"].max())
    n_win = int((t_last - b0) / (window_days * DAY))
    bounds = pd.DatetimeIndex([b0 + k * window_days * DAY for k in range(n_win + 1)])

    labelled = cyc[np.isfinite(cyc["label"]) & (cyc["dis_t1"] >= b0)]
    label0 = float(cyc.loc[anchor_cycles[0], "label"])
    if not np.isfinite(label0):
        raise ValueError(f"{cell_id}: the anchor-0 cycle has no label")
    truth, truth_sd = {}, {}
    for k in range(1, len(bounds)):
        off = (labelled["dis_t1"] - bounds[k]).abs()
        near = off.nsmallest(INFO["truth_n"])
        if len(near) == INFO["truth_n"] and near.max() <= INFO["truth_max_offset_days"] * DAY:
            vals = labelled.loc[near.index, "label"]
            truth[k], truth_sd[k] = float(vals.median()), float(vals.std(ddof=1))

    def first_after(cands, t, hi, strict, used):
        """First candidate cycle starting after t (strictly if ``strict``) and before hi."""
        t0 = cyc.loc[cands, "chg_t0"].to_numpy()
        j = int(np.searchsorted(t0, t.to_datetime64(), side="right" if strict else "left"))
        while j < len(cands) and t0[j] < hi.to_datetime64():
            if cands[j] not in used:
                return cands[j]
            j += 1
        return None

    anchors, used = [], set()
    for m in range(len(bounds)):
        hi = bounds[m + 1] if m + 1 < len(bounds) else t_last + DAY
        x = first_after(anchor_cycles, bounds[m], hi, True, used)
        if x is None:
            continue
        t, i, v, q = rows.step(x, STEP["charge"])
        anchors.append({"m": m, "cycle": int(x), "t_start": cyc.loc[x, "chg_t0"],
                        "t_end": cyc.loc[x, "chg_t1"], "q": float(cyc.loc[x, "chg_q"]),
                        "top": steps.charge_top(i, q, v, steps.cc_current(i))})
        used.add(x)
    if not anchors or anchors[0]["m"] != 0:
        raise ValueError(f"{cell_id}: no anchor in window 0")

    picks = []
    if program_rule == "every5d":
        for m in range(len(bounds)):
            hi = bounds[m + 1] if m + 1 < len(bounds) else t_last + DAY
            mark = bounds[m] + INFO["program_spacing_days"] * DAY
            while mark < hi:
                x = first_after(program_cycles, mark, hi, False, used)
                if x is not None:
                    picks.append((m, x))
                    used.add(x)
                mark += INFO["program_spacing_days"] * DAY
    elif program_rule == "all":
        for x in program_cycles:
            if x not in used:
                m = int(np.searchsorted(bounds, cyc.loc[x, "chg_t0"], side="right")) - 1
                picks.append((m, x))
    else:
        raise ValueError(program_rule)

    programs = []
    for m, x in picks:
        tc, ic, vc, qc = rows.step(x, STEP["charge"])
        td, idis, vd, qd = rows.step(x, STEP["discharge"])
        v_rest = rows.rest_voltage_before(x, td[0])
        res = steps.program_steps(idis, vd, qd, v_rest)
        vis = qd <= INFO["visible_depth_ah"]
        p = {"m": m, "cycle": int(x), "t_cv": pd.Timestamp(tc[-1]), "t_end": pd.Timestamp(td[vis][-1]),
             "q_partial": steps.partial_charge(qc, vc), **res}
        if with_full:
            p["robust_full"] = steps.program_steps(idis, vd, qd, v_rest, visible_depth=np.inf)["robust"]
        programs.append(p)
    programs.sort(key=lambda p: p["t_end"])

    meta = {"n_cycles": int(len(cyc)), "n_anchor_ok": int(len(anchor_cycles)),
            "n_program_ok": int(len(program_cycles)), "window_days": window_days,
            "program_rule": program_rule, **ref}
    return CellView(cell_id, bounds, label0, anchors, programs, truth, truth_sd, meta)


@dataclass
class EventDataset:
    """What the submitted model receives: events instead of rows, cut at a boundary."""
    operation: pd.DataFrame
    eval_points: pd.DataFrame
    checkups_released: pd.DataFrame
    charges: list
    steps: list
    until: pd.Timestamp


def make_dataset(view, k, scenario="main", key="robust", depth_override=None):
    """The events visible before boundary B_k, in the submitted model's formats.

    scenario: main | gap (programs hidden in the last gap_hide_days) | no_steps.
    depth_override: optional {program index: depth} (shuffle control).
    """
    cut = view.boundaries[k]
    charges = [{"t_start": a["t_start"], "t_end": a["t_end"], "q": a["q"], "top": a["top"],
                "setpoint": MODEL["anchor0_role_setpoint"] if a["m"] == 0 else MODEL["anchor_role_setpoint"]}
               for a in view.anchors if a["t_end"] <= cut]
    hide_after = cut - INFO["gap_hide_days"] * DAY if scenario == "gap" else cut
    evs = []
    if scenario != "no_steps":
        for n, p in enumerate(view.programs):
            d = depth_override[n] if depth_override is not None else p[key]
            if p["t_end"] <= hide_after and p["detected"] and np.isfinite(d):
                evs.append((p["t_cv"], MODEL["step_role_setpoint"], float(d), p["t_end"]))
    seen = [c["t_end"] for c in charges] + [s[3] for s in evs]
    op = pd.DataFrame({"segment": [1, 1],
                       "timestamp": [view.boundaries[0], max(seen) if seen else view.boundaries[0]],
                       "chamber_temperature_C": [MODEL["clock_setpoint"]] * 2})
    eval_points = pd.DataFrame({"checkup": [f"B{j}" for j in range(len(view.boundaries))],
                                "date": view.boundaries,
                                "released": [j == 0 for j in range(len(view.boundaries))]})
    released = pd.DataFrame({"checkup": ["B0"], "date": [view.boundaries[0]],
                             "capacity_Ah": [view.label0],
                             "SOH_pct": [100.0 * view.label0 / PROTOCOL["data"]["nominal_ah"]]})
    return EventDataset(op, eval_points, released, charges, evs, cut)
