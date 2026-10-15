"""Path setup for round 5C: import the round-3 harness, events and V2 from this worktree only."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
RESEARCH = os.path.dirname(STUDY)
WORKTREE = os.path.dirname(RESEARCH)
assert WORKTREE.endswith("Arena_1015_r5c_stressfix"), WORKTREE
R3_SRC = os.path.join(RESEARCH, "phase2_round3_models_20261014", "src")
for p in (HERE, R3_SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

import harness as H  # noqa: E402  (also puts events.py, v2.py and the framework on sys.path)

assert H.CACHE.startswith(WORKTREE), H.CACHE
CACHE5 = os.path.join(STUDY, "cache")
os.makedirs(CACHE5, exist_ok=True)
