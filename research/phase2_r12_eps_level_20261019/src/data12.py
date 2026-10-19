"""Round 12 data access: the challenge data of this worktree, read-only, cached as pickles under cache/."""
import glob, os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(ST, "..", ".."))
PKG = os.path.join(WT, "TechArena_Challenge2_Team_Package")
DATA = os.path.join(PKG, "data")
CACHE = os.path.join(ST, "cache")
CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]
MAX_DT_S = 600          # package convention (_integrated_ah): samples with dt > 600 s contribute 0
CK_DATES = pd.to_datetime(pd.read_csv(os.path.join(DATA, "checkups", "evaluation_points.csv"))["date"])
Q_CK0 = 100.41


def segments():
    """{segment number: DataFrame} for every operating file, in time order (cached)."""
    p = os.path.join(CACHE, "segments.pkl")
    if os.path.exists(p):
        return pd.read_pickle(p)
    out = {}
    for f in sorted(glob.glob(os.path.join(DATA, "operation", "segment_*.csv.gz"))):
        df = pd.read_csv(f, parse_dates=["timestamp"])
        out[int(df["segment"].iloc[0])] = df.reset_index(drop=True)
    os.makedirs(CACHE, exist_ok=True)
    pd.to_pickle(out, p)
    return out


def ck0_curve():
    return pd.read_csv(os.path.join(DATA, "checkups", "CK0_reference_discharge.csv.gz"), parse_dates=["timestamp"])


def integrated_ah(seg):
    """(current, cumulative Ah) with the package convention: per-sample i*dt, dt > 600 s or <= 0 -> 0."""
    t = seg["elapsed_s"].to_numpy(float)
    i = seg["current_A"].to_numpy(float)
    dt = np.diff(t, prepend=t[0])
    dt[(dt > MAX_DT_S) | (dt <= 0)] = 0.0
    return i, np.cumsum(i * dt / 3600.0)
