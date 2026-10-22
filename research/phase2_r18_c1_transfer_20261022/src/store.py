"""Where a run writes: views cache and outputs (the study folders, or a scratch folder for dry runs)."""
import argparse
import pickle
from pathlib import Path

from .common import CACHE, OUTPUTS, PROTOCOL

VIEW_SPECS = {
    "w30": {"window_days": PROTOCOL["information_structure"]["window_days"],
            "program_rule": "every5d", "with_full": True},
    "w20": {"window_days": PROTOCOL["information_structure"]["window_days_sensitivity"][0],
            "program_rule": "every5d", "with_full": False},
    "w45": {"window_days": PROTOCOL["information_structure"]["window_days_sensitivity"][1],
            "program_rule": "every5d", "with_full": False},
    "w30all": {"window_days": PROTOCOL["information_structure"]["window_days"],
               "program_rule": "all", "with_full": False},
}
PRIMARY = "w30"


def parser(description):
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--work", default=None,
                   help="folder for cache/ and outputs/ (default: the study folders)")
    return p


def dirs(work):
    if work is None:
        cache, out = CACHE, OUTPUTS
    else:
        cache, out = Path(work) / "cache", Path(work) / "outputs"
    (cache / "views").mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    return cache, out


def save_view(cache, cell, spec, vw):
    with open(cache / "views" / f"{cell}__{spec}.pkl", "wb") as f:
        pickle.dump(vw, f)


def load_views(cache, spec=PRIMARY):
    """{cell: CellView} for one view spec, in the protocol's cell order when present."""
    out = {}
    for path in sorted((cache / "views").glob(f"*__{spec}.pkl")):
        with open(path, "rb") as f:
            out[path.name.split("__")[0]] = pickle.load(f)
    order = [c for c in PROTOCOL["data"]["cells"] if c in out] + [c for c in out if c not in PROTOCOL["data"]["cells"]]
    return {c: out[c] for c in order}
