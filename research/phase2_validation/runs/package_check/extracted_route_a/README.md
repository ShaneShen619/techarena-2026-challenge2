# Route A candidate

Official entry: `python run_model.py --model train --input /path/to/data --output-dir out`, followed by `python run_model.py --model test --input /path/to/data --state-dir out --output-dir out --eval-point all`. The unmodified official entry, framework, validator and sample data are included; only `my_model/` supplies this candidate.

The model stores the released CK0 capacity, extracts completed contiguous positive-current runs from each evaluation prefix, and measures Ah between cell-voltage thresholds. It compares like temperature/current and deep/shallow charge events, takes recent medians, and falls back to CK0 when coverage is inadequate. A later first reference within a new temperature stratum is not an independent capacity calibration. `last_diagnostics` records event counts, fallback and raw capacity. CK1–CK7 truth is unavailable.

Python 3.11/3.12; requirements in `requirements.txt`. Local macOS validation is recorded in `research/phase2_validation/runs/`; official Linux scoring has not been run.
