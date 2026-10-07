from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/phase2_temperature_improvement/src"))
from event_core import extract_charge_events  # noqa: E402
from route_a_repaired import RouteARepaired, stable_cc_prefix  # noqa: E402


def real_charge() -> pd.DataFrame:
    path = ROOT / "research/phase2_validation/preflight/downloaded_data/fixtures/102Ah_25degC_0p5C_cell3_cycle504_charge.csv"
    return pd.read_csv(path, parse_dates=["absolute_time"])


def repeated_charge(*, temperature_shift_second: float = 0., first_missing: bool = False) -> pd.DataFrame:
    first = real_charge().copy()
    first["cycle_number"] = 1
    first["temperature_C"] += 15.
    if first_missing:
        first["temperature_C"] = np.nan
    second = real_charge().copy()
    second["cycle_number"] = 2
    second["absolute_time"] += pd.Timedelta(days=1)
    second["temperature_C"] += 15. + temperature_shift_second
    return pd.concat([first, second], ignore_index=True)


def fit_and_predict(frame: pd.DataFrame, **kwargs) -> RouteARepaired:
    ds = SimpleNamespace(operation=frame, bol_capacity_Ah=100.,
                         anchor_discharge_start=pd.Timestamp(frame.absolute_time.min())+pd.Timedelta(hours=3))
    model = RouteARepaired(**kwargs)
    model.fit(ds)
    model.estimate_soh(ds, pd.Timestamp(frame.absolute_time.max())+pd.Timedelta(hours=1))
    return model


def test_cv_tail_is_removed_before_window_evidence() -> None:
    event = extract_charge_events(real_charge(), time_col="absolute_time",
                                  voltage_cols=("voltage_V",), temp_col="temperature_C", counter_col=None)[0]
    cc, reason = stable_cc_prefix(event)
    assert reason == "pass"
    assert cc is not None
    assert 0 < cc.ah < event.ah
    assert cc.end < event.end
    assert cc.ah > 90.


def test_true_temperature_pair_rejects_old_20_c_bin_false_match() -> None:
    frame = repeated_charge(temperature_shift_second=10.)
    repaired = fit_and_predict(frame)
    old_bin_ablation = fit_and_predict(frame, true_pair_temperature=False)
    assert repaired.last_diagnostics["updates"] == 0
    assert old_bin_ablation.last_diagnostics["updates"] > 0
    assert repaired.last_diagnostics["reference_keys"] >= 2


def test_missing_temperature_cannot_seed_a_reference() -> None:
    frame = repeated_charge(first_missing=True)
    repaired = fit_and_predict(frame)
    assert repaired.evidence_events[0]["reason"] == "missing_temperature"
    assert repaired.evidence_events[0]["quality_pass"] is False
    assert repaired.last_diagnostics["reference_keys"] <= 2


def test_future_rows_do_not_change_an_earlier_answer() -> None:
    frame = repeated_charge()
    cutoff = pd.Timestamp(frame.absolute_time.max()) + pd.Timedelta(hours=1)
    ds = SimpleNamespace(operation=frame, bol_capacity_Ah=100.,
                         anchor_discharge_start=pd.Timestamp(frame.absolute_time.min())+pd.Timedelta(hours=3))
    m = RouteARepaired()
    m.fit(ds)
    old = m.estimate_soh(ds, cutoff)
    future = frame.copy()
    extra = frame.tail(30).copy()
    extra["absolute_time"] += pd.Timedelta(days=100)
    extra["voltage_V"] = 99.
    future = pd.concat([future, extra], ignore_index=True)
    ds_future = SimpleNamespace(operation=future, bol_capacity_Ah=100.,
                                anchor_discharge_start=ds.anchor_discharge_start)
    assert RouteARepaired().fit(ds_future) is None
    m2 = RouteARepaired()
    m2.fit(ds_future)
    new = m2.estimate_soh(ds_future, cutoff)
    assert old == new
