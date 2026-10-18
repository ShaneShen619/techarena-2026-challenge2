# Decisions

- D1 (WP0): system Python 3.13 / pandas 3.0 / numpy 2.4 lacks pyarrow. Instead of a venv, LIC is cached as numpy `.npz` under `cache/` (no parquet needed). The submission packages were run with their own CLI under system Python; the 21a7a55 output reproduces round 7 exactly, so no 3.11 venv was needed.
- D2 (WP0): the WP0 rule (tolerance 0.001 pp) was fixed in EXECUTION_PROMPT.md (commit 18f8c96) before the check ran; `wp0/protocol.json` restates it and is committed before the outputs.
- D3 (WP1): LIC numbering changed from the screening's 16 entries (which counted the truncated extra test as "k5") to the 15 complete RPTs k = 0..14. The screening's k6 and k11 outliers are this round's k5 and k10, both preceded by unrecorded voltage jumps.
- D4 (WP1): Yagci only needs the two summary xlsx files plus one raw checkup file for the order check, so only those were extracted from the 19 GB archive into cache/yagci/.
- D5 (WP1): the registered event for LIC stays the single step between k = 4 and 5, as the prompt requires. A two-step model at both RPT temperature changes is registered only as a reported sensitivity (b2).
- D6 (WP1): rest before the LIC operating charge is always 0.25 h (MAD = 0), so the outlier rule uses a 1 %-of-median fallback (registered).
