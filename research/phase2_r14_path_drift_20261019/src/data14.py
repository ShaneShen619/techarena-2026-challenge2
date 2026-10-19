"""Shared data access for round 14: the full (uncut) operating data from the package loader, cached per segment,
and CV-end / anchor detection that reuses the package's own rules (model_template.py at the base commit)."""
import os, pickle, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(ST, "..", ".."))
PKG = os.path.join(WT, "TechArena_Challenge2_Team_Package")
DATA = os.path.join(PKG, "data")
CACHE = os.path.join(ST, "cache")
sys.path.insert(0, PKG)
from framework.data import load_dataset  # noqa: E402
from my_model import model_template as mt  # noqa: E402

CELLS = mt.CELLS
GAP_S = 60.0          # recording gap: dt between consecutive samples > 60 s (prompt section 3)
V30_S = 1800.0        # rest voltage 30 min after a CV end
CK_DATES = None


def checkup_dates():
    ev = load_dataset(DATA).eval_points.sort_values("date")
    return pd.DatetimeIndex(ev["date"]), list(ev["checkup"])


def segments():
    """{segment: DataFrame} of the full operating data, reset index, cached as a pickle under cache/."""
    path = os.path.join(CACHE, "segments.pkl")
    if os.path.exists(path):
        return pickle.load(open(path, "rb"))
    op = load_dataset(DATA).operation
    segs = {int(s): g.reset_index(drop=True) for s, g in op.groupby("segment", sort=True)}
    os.makedirs(CACHE, exist_ok=True)
    pickle.dump(segs, open(path, "wb"))
    return segs


def cv_ends(seg):
    """Indices of CV ends, exactly the package rule in _step_depths: last sample of each run with
    pack >= CV_V_MIN, 0 < I < END_I_MAX_A."""
    i, _ = mt._integrated_ah(seg)
    u = seg["pack_voltage_V"].to_numpy(float)
    cv = (u >= mt.CV_V_MIN) & (i > 0) & (i < mt.END_I_MAX_A)
    return np.where(cv & ~np.r_[cv[1:], False])[0]


def charge_start(i, e):
    """First index of the charge (I > CHARGE_I_MIN_A run) that ends at CV end e."""
    s = e
    while s > 0 and i[s - 1] > mt.CHARGE_I_MIN_A:
        s -= 1
    return s


def anchor_index(seg):
    """CV-end index of the package anchor (_first_full_charge) of this segment, or None."""
    fc = mt._first_full_charge(seg)
    if fc is None:
        return None, None
    t = seg["timestamp"]
    e = int(np.where(t == fc["t_end"])[0][0])
    return e, fc
