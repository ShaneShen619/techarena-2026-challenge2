"""Path setup for round 17: import the (copied) round-3 harness, events and V2 from this worktree only."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
RESEARCH = os.path.dirname(STUDY)
WORKTREE = os.path.dirname(RESEARCH)
assert WORKTREE.endswith("Arena_1021_r17_r5c"), WORKTREE
for p in (HERE,):
    if p not in sys.path:
        sys.path.insert(0, p)

import harness as H  # noqa: E402  (study copy; also puts events.py, v2.py and the framework on sys.path)

assert H.CACHE.startswith(STUDY), H.CACHE
CACHE5 = os.path.join(STUDY, "cache")
os.makedirs(CACHE5, exist_ok=True)
