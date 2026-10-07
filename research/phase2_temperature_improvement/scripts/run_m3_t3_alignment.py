"""Constrained Q–V alignment identifiability diagnostic on P1 charge pairs.

Parameters distinguish capacity-axis scale, SOC/start offset, and voltage
offset/polarization proxy.  No target-cell labels enter online model tuning;
labels here are training-side diagnostic comparison only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "src"))
from event_core import extract_charge_events  # noqa: E402
from route_a_repaired import stable_cc_prefix  # noqa: E402

PAIRS = [
    ("102Ah_25degC_1C_cell3", 12, 3095),
    ("102Ah_25degC_1C_cell3", 12, 5307),
    ("102Ah_45degC_0p5C_cell3", 11, 2205),
    ("102Ah_45degC_0p5C_cell3", 11, 4501),
    ("102Ah_55degC_1C_cell3", 11, 1312),
    ("102Ah_55degC_1C_cell3", 11, 2415),
]


def curve(cell: str, cycle: int) -> tuple[np.ndarray, np.ndarray, float]:
    path = ROOT / "research/phase2_validation/preflight/downloaded_data/fixtures" / f"{cell}_cycle{cycle}_charge.csv"
    frame = pd.read_csv(path, parse_dates=["absolute_time"])
    # Preflight fixture export repeats identical rows three times; remove
    # exact duplicates only for this read-only shape diagnostic.
    frame = frame.drop_duplicates(subset=["absolute_time", "voltage_V", "current_A", "temperature_C"])
    # Fixtures end at the exported charge endpoint without a following rest
    # sample.  Add a rest sentinel to mark the known completed fixture event.
    sentinel = frame.tail(1).copy()
    sentinel["absolute_time"] = sentinel.absolute_time+pd.Timedelta(seconds=30)
    sentinel["current_A"] = 0.
    frame = pd.concat([frame, sentinel], ignore_index=True)
    frame["cycle_number"] = cycle
    events = extract_charge_events(frame, time_col="absolute_time", voltage_cols=("voltage_V",),
                                   temp_col="temperature_C", segment_col="cycle_number", counter_col=None)
    usable = []
    for ev in events:
        cc, status = stable_cc_prefix(ev)
        if status == "pass" and cc is not None:
            usable.append(cc)
    if not usable:
        raise AssertionError(f"no charge event: {path}")
    ev = max(usable, key=lambda x: x.ah)
    v = pd.Series(ev.voltages[:, 0]).rolling(5, center=True, min_periods=1).median().to_numpy(float)
    q = ev.q_ah
    ok = np.isfinite(v) & np.isfinite(q)
    return q[ok], v[ok], ev.median_temp


def main() -> None:
    labels = pd.read_csv(ROOT / "research/phase2_validation/preflight/downloaded_data/phase1_label_inventory.csv")
    rows = []
    for cell, first_cycle, late_cycle in PAIRS:
        q0, v0, t0 = curve(cell, first_cycle)
        q1, v1, t1 = curve(cell, late_cycle)
        use = (v1 >= 3.32) & (v1 <= 3.45) & (q1 >= 5.) & (q1 <= min(q1.max()-2, 90.))
        x = q1[use][::max(1, int(use.sum()/200))]
        observed = v1[use][::max(1, int(use.sum()/200))]
        if len(x) < 20:
            raise AssertionError("insufficient common local curve")
        def residual(params):
            scale, offset_Ah, voltage_offset_V = params
            mapped = scale*x+offset_Ah
            model = np.interp(mapped, q0, v0, left=v0[0], right=v0[-1])+voltage_offset_V
            return model-observed
        starts = ([1., 0., 0.], [.85, 5., .015], [1.15, -5., -.015])
        fits = [least_squares(residual, start, bounds=([.7, -15., -.1], [1.3, 15., .1]),
                             max_nfev=3000) for start in starts]
        best = min(fits, key=lambda fit: np.mean(fit.fun**2))
        singular = np.linalg.svd(best.jac, compute_uv=False)
        cond = float(singular[0]/singular[-1]) if singular[-1] > 0 else float("inf")
        costs = []
        for fixed_scale in np.linspace(.75, 1.25, 51):
            def prof(p):
                return residual([fixed_scale, p[0], p[1]])
            fit = least_squares(prof, [0., 0.], bounds=([-15., -.1], [15., .1]), max_nfev=1000)
            costs.append(float(np.mean(fit.fun**2)))
        best_cost = min(costs)
        plausible = np.linspace(.75, 1.25, 51)[np.asarray(costs) <= best_cost+(.002**2)]
        source = labels.loc[labels.cell_id.eq(cell) & labels.cycle.eq(first_cycle)].iloc[0]
        target = labels.loc[labels.cell_id.eq(cell) & labels.cycle.eq(late_cycle)].iloc[0]
        rows.append({"cell_id": cell, "first_cycle": first_cycle, "late_cycle": late_cycle,
                     "reference_temp_C": t0, "target_temp_C": t1,
                     "fitted_q_scale": float(best.x[0]), "fitted_soc_offset_Ah": float(best.x[1]),
                     "fitted_voltage_offset_V": float(best.x[2]),
                     "curve_rmse_mV": float(np.sqrt(np.mean(best.fun**2))*1000.),
                     "jacobian_condition": cond,
                     "scale_plausible_min_2mV": float(plausible.min()) if len(plausible) else np.nan,
                     "scale_plausible_max_2mV": float(plausible.max()) if len(plausible) else np.nan,
                     "implied_capacity_ratio_inverse_scale": float(1./best.x[0]),
                     "true_capacity_ratio_training_diagnostic": float(target.capacity_Ah/source.capacity_Ah),
                     "training_diagnostic_only": True})
    out = pd.DataFrame(rows)
    out.to_csv(TASK / "runs/M3_t3_alignment.csv", index=False)
    print(out.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
