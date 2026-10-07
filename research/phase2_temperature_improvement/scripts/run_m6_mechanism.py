"""Independent 4S discharge truth and packaged-fallback diagnostic simulation."""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
RUN = TASK / "runs/M6_mechanism_v1"
sys.path.insert(0, str(TASK / "src"))
from official_fallback import OfficialFallback  # noqa: E402


def pack_voltage(q_Ah: np.ndarray, cap: np.ndarray, temp: np.ndarray,
                 soc0: np.ndarray, r_ohm: np.ndarray, r_pol: np.ndarray,
                 current_A: float) -> np.ndarray:
    q = np.asarray(q_Ah, float)[:, None]
    reversible = 1.-.004*np.maximum(25.-temp, 0.)
    soc = soc0[None, :]-q/(cap*reversible)[None, :]
    ocv = 2.84+.49*soc+.055*np.tanh((soc-.12)/.055)+.035*np.tanh((soc-.84)/.065)
    r_temp = r_ohm*np.exp(.018*(25.-temp))
    elapsed_s = q/current_A*3600.
    polarization = current_A*r_pol[None, :]*(1.-np.exp(-elapsed_s/900.))
    cell_v = ocv + .0005*(temp-25.)[None, :]-current_A*r_temp[None, :]-polarization
    return cell_v.sum(axis=1)


def discharge_truth(cap: np.ndarray, temp: np.ndarray, soc0: np.ndarray,
                    r: np.ndarray, rp: np.ndarray, current: float, cutoff: float,
                    dt_s: float) -> float:
    max_q = 130.
    dq = current*dt_s/3600.
    q = np.arange(0., max_q+dq, dq)
    voltage = pack_voltage(q, cap, temp, soc0, r, rp, current)
    hits = np.flatnonzero(voltage <= cutoff)
    if not len(hits) or hits[0] == 0:
        raise AssertionError("independent pack discharge has no valid cutoff crossing")
    idx = int(hits[0])
    fraction = (voltage[idx-1]-cutoff)/(voltage[idx-1]-voltage[idx])
    return float(q[idx-1]+fraction*(q[idx]-q[idx-1]))


def charge_event(start: pd.Timestamp, cap: np.ndarray, true_temp: np.ndarray,
                 sensor_temp: float, current: float, points: int, step_s: float,
                 counter_offset: float, segment: int) -> pd.DataFrame:
    times = [start+pd.Timedelta(seconds=i*step_s) for i in range(points)]
    q = np.arange(points)*current*step_s/3600.
    data = pd.DataFrame({"timestamp": times, "current_A": current,
                         "temp_mean_C": sensor_temp, "segment": segment,
                         "charge_Ah_cum": counter_offset+q})
    for ci in range(4):
        frac = q/cap[ci]
        cell_v = (3.05+.42*np.sqrt(np.maximum(frac, 0.))+
                  .045*np.tanh((frac-.82)/.06)+.0007*(true_temp[ci]-25.)+
                  current*.006)
        data[f"cell{ci+1}_V"] = cell_v
    rest = data.tail(1).copy()
    rest["timestamp"] = rest.timestamp+pd.Timedelta(seconds=step_s)
    rest["current_A"] = 0.
    return pd.concat([data, rest], ignore_index=True)


def scenario_parameters(name: str, rng: np.random.Generator, base: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    cap = np.full(4, base)
    temp = np.full(4, 25.)
    soc = np.ones(4)
    sensor = 25.
    if name == "constant_capacity_varying_temperature":
        temp[:] = rng.uniform(15., 55.)
        sensor = float(np.mean(temp))
    elif name == "constant_temperature_capacity_fade":
        cap *= rng.uniform(.75, 1.)
    elif name == "coupled_temperature_and_fade":
        cap *= rng.uniform(.75, 1., size=4)
        temp[:] = rng.uniform(15., 55.)
        sensor = float(np.mean(temp))
    elif name == "sensor_bias":
        sensor = 25.+rng.uniform(-5., 5.)
    elif name == "self_heating_change":
        temp[:] = 25.+rng.uniform(0., 12.)
        sensor = 25.  # chamber sensor does not observe the full cell rise
    elif name == "four_series_capacity_imbalance":
        cap *= rng.uniform(.75, 1., size=4)
    elif name == "four_series_soc_imbalance":
        soc[:] = rng.uniform(.85, 1., size=4)
    else:
        raise ValueError(name)
    return cap, temp, soc, sensor


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    config = json.loads((TASK / "configs/synthetic_mechanism.json").read_text())
    scenarios = config["scenarios"]
    # Three explicit series-cutoff identities, separate from the randomized
    # scenarios, make the target definition reviewable.
    truth_cases = []
    for case, capacities, initial_soc in (
        ("four_identical", np.full(4, 100.), np.ones(4)),
        ("capacity_mismatch", np.array([100., 97., 93., 86.]), np.ones(4)),
        ("soc_mismatch", np.full(4, 100.), np.array([1., .96, .91, .85])),
    ):
        temp = np.full(4, 25.)
        r = np.full(4, .008)
        rp = np.full(4, .002)
        q_coarse_case = discharge_truth(capacities, temp, initial_soc, r, rp,
                                        float(config["discharge_current_A"]),
                                        float(config["pack_cutoff_V"]),
                                        float(config["coarse_time_step_s"]))
        q_fine_case = discharge_truth(capacities, temp, initial_soc, r, rp,
                                      float(config["discharge_current_A"]),
                                      float(config["pack_cutoff_V"]),
                                      float(config["fine_time_step_s"]))
        permutation = [3, 1, 0, 2]
        q_permuted_case = discharge_truth(capacities[permutation], temp[permutation],
                                          initial_soc[permutation], r[permutation], rp[permutation],
                                          float(config["discharge_current_A"]),
                                          float(config["pack_cutoff_V"]),
                                          float(config["fine_time_step_s"]))
        if abs(q_fine_case-q_coarse_case) > config["step_halving_capacity_difference_max_Ah"]:
            raise AssertionError("explicit 4S truth case step-halving failed")
        if abs(q_fine_case-q_permuted_case) > config["cell_permutation_capacity_difference_max_Ah"]:
            raise AssertionError("explicit 4S truth case permutation failed")
        truth_cases.append({"case": case, "C20_group_capacity_Ah": q_fine_case,
                            "coarse_fine_difference_Ah": abs(q_fine_case-q_coarse_case),
                            "permutation_difference_Ah": abs(q_fine_case-q_permuted_case)})
    pd.DataFrame(truth_cases).to_csv(RUN / "explicit_4S_truth_cases.csv", index=False)
    records = []
    anchor_date = pd.Timestamp("2025-01-01 00:00:00")
    for scenario_index, scenario in enumerate(scenarios):
        for offset in range(config["test_seed_count_per_scenario"]):
            seed = config["test_seed_first"]+scenario_index*10_000+offset
            rng = np.random.default_rng(seed)
            base = float(rng.uniform(98., 104.))
            baseline_cap = np.full(4, base)
            resistance = rng.uniform(.004, .012, size=4)
            polarization = rng.uniform(.001, .004, size=4)
            cap, true_temp, soc, sensor = scenario_parameters(scenario, rng, base)
            current = float(config["discharge_current_A"])
            cutoff = float(config["pack_cutoff_V"])
            q0 = discharge_truth(baseline_cap, np.full(4, 25.), np.ones(4),
                                 resistance, polarization, current, cutoff,
                                 float(config["fine_time_step_s"]))
            q_coarse = discharge_truth(cap, true_temp, soc, resistance, polarization,
                                       current, cutoff, float(config["coarse_time_step_s"]))
            q_fine = discharge_truth(cap, true_temp, soc, resistance, polarization,
                                     current, cutoff, float(config["fine_time_step_s"]))
            perm = rng.permutation(4)
            q_permuted = discharge_truth(cap[perm], true_temp[perm], soc[perm],
                                         resistance[perm], polarization[perm], current, cutoff,
                                         float(config["fine_time_step_s"]))
            if abs(q_coarse-q_fine)>config["step_halving_capacity_difference_max_Ah"]:
                raise AssertionError("C/20 integration step-halving failed")
            if abs(q_fine-q_permuted)>config["cell_permutation_capacity_difference_max_Ah"]:
                raise AssertionError("4S cell permutation changed pack truth")
            charge_current = float(config["charge_event_current_A"])
            points = int(config["charge_event_points"])
            step = float(config["charge_event_sample_step_s"])
            first = charge_event(anchor_date+pd.Timedelta(days=1), baseline_cap,
                                 np.full(4, 25.), 25., charge_current, points, step, 0., 1)
            second = charge_event(anchor_date+pd.Timedelta(days=30), cap, true_temp,
                                  sensor, charge_current, points, step, 100., 2)
            operation = pd.concat([first, second], ignore_index=True)
            fallback = OfficialFallback(q0_Ah=q0, anchor_time=anchor_date)
            estimate_pp = fallback.estimate(operation, anchor_date+pd.Timedelta(days=31))
            true_pp = 100.*q_fine/102.
            records.append({"scenario": scenario, "seed": seed,
                            "baseline_irreversible_cell_capacity_Ah": base,
                            "aged_irreversible_cell_capacities_Ah": json.dumps(cap.tolist()),
                            "true_cell_temperatures_C": json.dumps(true_temp.tolist()),
                            "sensor_temperature_C": sensor,
                            "initial_soc": json.dumps(soc.tolist()),
                            "baseline_pack_C20_Ah": q0, "target_pack_C20_Ah": q_fine,
                            "target_pack_C20_soh_pp": true_pp,
                            "coarse_fine_capacity_difference_Ah": abs(q_coarse-q_fine),
                            "cell_permutation_difference_Ah": abs(q_fine-q_permuted),
                            "estimate_soh_pp": estimate_pp,
                            "error_pp": estimate_pp-true_pp,
                            "temperature_only_false_decay_pp": (estimate_pp-100.*q0/102.) if
                                scenario in ("constant_capacity_varying_temperature", "sensor_bias", "self_heating_change") else np.nan,
                            "estimator_updates_by_cell": json.dumps(fallback.last_diagnostics.get("updates")),
                            "estimator_mode": fallback.last_diagnostics.get("mode")})
        print(scenario, "seeds", config["test_seed_count_per_scenario"], flush=True)
        pd.DataFrame(records).to_csv(RUN / "results.partial.csv", index=False)
    out = pd.DataFrame(records)
    if len(out) != len(scenarios)*config["test_seed_count_per_scenario"]:
        raise AssertionError("scenario/seed coverage incomplete")
    out.to_csv(RUN / "results.csv", index=False)
    summary = out.assign(ae=out.error_pp.abs()).groupby("scenario").agg(
        n=("seed", "size"), mae_pp=("ae", "mean"), max_abs_pp=("ae", "max"),
        truth_min_Ah=("target_pack_C20_Ah", "min"), truth_max_Ah=("target_pack_C20_Ah", "max"),
        max_step_diff_Ah=("coarse_fine_capacity_difference_Ah", "max"),
        max_permutation_diff_Ah=("cell_permutation_difference_Ah", "max"))
    summary.to_csv(RUN / "summary.csv")
    print(summary.to_string(), flush=True)


if __name__ == "__main__":
    main()
