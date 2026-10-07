# FRAMEWORK - DO NOT EDIT (identical across all teams; the organizers use their own copy)
"""Data access for Challenge 2. The evaluation calls the same functions, so anything
your model can see here is exactly what it will see during scoring."""
import glob, os
from dataclasses import dataclass
import pandas as pd

NOMINAL_CAPACITY_AH = 102.0   # SOH is defined as C/20 capacity / nominal capacity


@dataclass
class Dataset:
    operation: pd.DataFrame          # all operating rows with timestamp <= until (if given)
    checkups_released: pd.DataFrame  # released checkup capacities (checkup, date, capacity_Ah, SOH_pct)
    eval_points: pd.DataFrame        # all checkups: checkup, date, released
    reference_discharge: pd.DataFrame  # CK0 C/20 discharge curve
    until: pd.Timestamp | None = None

    @property
    def bol_capacity_Ah(self) -> float:
        return float(self.checkups_released.sort_values("date")["capacity_Ah"].iloc[0])


def load_operation(data_dir, until=None):
    files = sorted(glob.glob(os.path.join(data_dir, "operation", "segment_*.csv*")))
    if not files:
        raise FileNotFoundError(f"no operation files under {data_dir}/operation")
    frames = []
    for f in files:
        df = pd.read_csv(f, parse_dates=["timestamp"])
        if until is not None:
            df = df[df["timestamp"] <= until]
            if df.empty:
                continue
        frames.append(df)
    op = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return op


def load_checkups(data_dir):
    ck = pd.read_csv(os.path.join(data_dir, "checkups", "checkup_capacities_released.csv"),
                     parse_dates=["date"])
    return ck.sort_values("date").reset_index(drop=True)


def load_eval_points(data_dir):
    ev = pd.read_csv(os.path.join(data_dir, "checkups", "evaluation_points.csv"), parse_dates=["date"])
    return ev.sort_values("date").reset_index(drop=True)


def load_reference_discharge(data_dir):
    files = glob.glob(os.path.join(data_dir, "checkups", "CK0_reference_discharge.csv*"))
    return pd.read_csv(files[0], parse_dates=["timestamp"]) if files else pd.DataFrame()


def load_dataset(data_dir, until=None):
    """Everything the model may use. With `until`, operating data is cut at that
    timestamp and released checkups after it are removed (causal evaluation)."""
    until = pd.Timestamp(until) if until is not None else None
    ck = load_checkups(data_dir)
    if until is not None:
        ck = ck[ck["date"] <= until].reset_index(drop=True)
    return Dataset(operation=load_operation(data_dir, until), checkups_released=ck,
                   eval_points=load_eval_points(data_dir),
                   reference_discharge=load_reference_discharge(data_dir), until=until)
