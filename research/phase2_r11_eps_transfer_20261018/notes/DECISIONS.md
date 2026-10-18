# Decisions

- D1 (WP0): system Python 3.13 / pandas 3.0 / numpy 2.4 lacks pyarrow. Instead of a venv, LIC is cached as numpy `.npz` under `cache/` (no parquet needed). The submission packages were run with their own CLI under system Python; the 21a7a55 output reproduces round 7 exactly, so no 3.11 venv was needed.
- D2 (WP0): the WP0 rule (tolerance 0.001 pp) was fixed in EXECUTION_PROMPT.md (commit 18f8c96) before the check ran; `wp0/protocol.json` restates it and is committed before the outputs.
