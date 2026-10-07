"""Additional frozen-range curve-shape stress for the official fallback.

Pack discharge truth is independent of these charge-only shape disturbances;
this deliberately breaks the fallback's q/cap similarity assumption.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "src"))
sys.path.insert(0, str(TASK / "scripts"))
from official_fallback import OfficialFallback  # noqa: E402
from run_m6_mechanism import charge_event, discharge_truth  # noqa: E402


def apply_disturbance(event: pd.DataFrame, scenario: str, amplitude: float,
                      rng: np.random.Generator) -> pd.DataFrame:
    out = event.copy()
    charge = out.current_A > 0
    n = int(charge.sum())
    phase = np.linspace(0., 1., n)
    for ci in range(1, 5):
        name = f"cell{ci}_V"
        voltage = out.loc[charge, name].to_numpy(float)
        if scenario == "charge_curve_shape_change":
            voltage += amplitude*np.sin(np.pi*phase)**2 * np.sin(2.*np.pi*phase)
        elif scenario == "charge_soc_voltage_shift":
            voltage += amplitude
        elif scenario == "charge_polarization_change":
            voltage += amplitude*(.35+.65*np.sqrt(phase))
        elif scenario == "charge_voltage_noise":
            voltage += rng.normal(0., amplitude, size=n)
        else:
            raise ValueError(scenario)
        out.loc[charge, name] = voltage
        out.loc[~charge, name] = voltage[-1]
    return out


def main() -> None:
    config = json.loads((TASK / "configs/synthetic_curve_variation.json").read_text())
    rows = []
    anchor = pd.Timestamp("2025-01-01")
    for si, scenario in enumerate(config["scenarios"]):
        lo, hi = config[{
            "charge_curve_shape_change": "shape_amplitude_V",
            "charge_soc_voltage_shift": "soc_voltage_shift_V",
            "charge_polarization_change": "polarization_shift_V",
            "charge_voltage_noise": "voltage_noise_sigma_V",
        }[scenario]]
        for ix in range(config["seeds_per_scenario"]):
            seed = config["seed_first"]+si*1000+ix
            rng = np.random.default_rng(seed)
            base = float(rng.uniform(98., 104.))
            ratio = float(rng.uniform(*config["capacity_ratio"]))
            initial = np.full(4, base)
            aged = np.full(4, base*ratio)
            temp = np.full(4, 25.)
            soc = np.ones(4)
            r = rng.uniform(.004, .012, size=4)
            rp = rng.uniform(.001, .004, size=4)
            q0 = discharge_truth(initial, temp, soc, r, rp, 5.1, 11.2, 30.)
            q1 = discharge_truth(aged, temp, soc, r, rp, 5.1, 11.2, 30.)
            first = charge_event(anchor+pd.Timedelta(days=1), initial, temp, 25., 25., 600, 20., 0., 1)
            late = charge_event(anchor+pd.Timedelta(days=30), aged, temp, 25., 25., 600, 20., 100., 2)
            amplitude = float(rng.uniform(lo, hi))
            late = apply_disturbance(late, scenario, amplitude, rng)
            fallback = OfficialFallback(q0_Ah=q0, anchor_time=anchor)
            estimate = fallback.estimate(pd.concat([first, late], ignore_index=True),
                                         anchor+pd.Timedelta(days=31))
            rows.append({"scenario": scenario, "seed": seed, "amplitude_V": amplitude,
                         "capacity_ratio": ratio, "truth_C20_Ah": q1,
                         "true_soh_pp": 100.*q1/102., "estimate_soh_pp": estimate,
                         "abs_error_pp": abs(estimate-100.*q1/102.),
                         "mode": fallback.last_diagnostics.get("mode")})
        print(scenario, "complete", flush=True)
    run = TASK / "runs/M6_curve_variation_v1"
    run.mkdir(exist_ok=True)
    out = pd.DataFrame(rows)
    if len(out) != len(config["scenarios"])*config["seeds_per_scenario"]:
        raise AssertionError("curve stress coverage incomplete")
    out.to_csv(run / "results.csv", index=False)
    summary = out.groupby("scenario").agg(n=("seed", "size"), mae_pp=("abs_error_pp", "mean"),
                                          max_abs_pp=("abs_error_pp", "max"),
                                          fallback_modes=("mode", lambda x: x.value_counts().to_dict()))
    summary.to_csv(run / "summary.csv")
    print(summary.to_string(), flush=True)


if __name__ == "__main__":
    main()
