"""Paths, the registered protocol, and access to the submitted model module."""
import contextlib
import json
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
REPO = STUDY.parents[1]
PACKAGE = REPO / "TechArena_Challenge2_Team_Package"
OUTPUTS = STUDY / "outputs"
CACHE = STUDY / "cache"

if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

import my_model.model_template as mt  # noqa: E402,F401  (the submitted model, read only; re-exported)

with open(STUDY / "protocol.json", encoding="utf-8") as _f:
    PROTOCOL = json.load(_f)


@contextlib.contextmanager
def patched(module, **values):
    """Temporarily set module-level constants; always restored."""
    old = {k: getattr(module, k) for k in values}
    try:
        for k, v in values.items():
            setattr(module, k, v)
        yield
    finally:
        for k, v in old.items():
            setattr(module, k, v)
