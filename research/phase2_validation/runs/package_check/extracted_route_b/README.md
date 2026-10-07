# Route B candidate

Official entry: `python run_model.py --model train --input /path/to/data --output-dir out`, followed by `python run_model.py --model test --input /path/to/data --state-dir out --output-dir out --eval-point all`. The unmodified official entry, framework, validator and sample data are included; only `my_model/` and the additional SciPy dependency supply this candidate.

The released CK0 C/20 discharge gives a *quasi*-OCV shape, not equilibrium OCV. For each completed charge episode, the model propagates SOC with positive charging current and a first-order polarization state, profiles an initial SOC and constant voltage offset, and fits a common capacity scale. It updates capacity only if excitation, normalized Jacobian rank, slope, residual and physical bounds pass. Gaps reset SOC by independently profiling each episode; hidden checkup throughput is never integrated. `last_diagnostics` records updates, rejections and raw capacity. On the current official operating record all updates are rejected, so this candidate returns CK0: this is a documented identification limitation, not validated tracking.

Python 3.11/3.12; requirements in `requirements.txt`. Local macOS validation is recorded in `research/phase2_validation/runs/`; official Linux scoring has not been run.
