"""Path setup for round 8 (from round 7 common6.py): import the round-3 harness copy in this study (cache in this
study's cache/), events and V2 from their original study directories in this worktree, V3/T_main copies from src/."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
RESEARCH = os.path.dirname(STUDY)
WORKTREE = os.path.dirname(RESEARCH)
assert WORKTREE.endswith("Arena_1017_r8_err"), WORKTREE
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import harness as H  # noqa: E402  (also puts events.py, v2.py and the framework on sys.path)

assert H.CACHE == os.path.join(STUDY, "cache"), H.CACHE
CACHE8 = os.path.join(STUDY, "cache")
os.makedirs(CACHE8, exist_ok=True)
