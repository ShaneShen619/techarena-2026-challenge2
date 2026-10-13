# TechArena 2026 – Challenge 2: Anchor + Graphite-Step SOH Estimator

Estimates the SOH (C/20 capacity ÷ 102 Ah) of the 4 × 102 Ah LFP pack at each
checkup date. It reads only the operating data before that date. The model lives
in [`my_model/model_template.py`](my_model/model_template.py), and
[`my_model/__init__.py`](my_model/__init__.py) points `ActiveModel` at it.
Dependencies are numpy and pandas only. No open-source datasets and no
pre-trained artefacts are used.

## Method

The model reads two signals from the operating data. Neither depends on a
voltage threshold on the flat LFP plateau.

1. **Post-checkup full-charge anchor.** Every operating segment that follows a
   checkup opens with a CCCV charge from near empty (2.9–3.0 V/cell at rest) to
   the end of the 14.0 V CV phase, at 20.4 A. The charged Ah, integrated from
   `current_A`, is nearly the usable capacity at that time. For each evaluation
   date the model uses the latest such charge it can see as its anchor.
   - A constant offset maps the anchor to the checkup protocol.
   - `EPS0 = 100.41 Ah − Q(post-CK0 charge)` is defined by the released CK0
     capacity (0.29 Ah).
   - An extra 0.4 Ah (`EPS_EXTRA_AH`) is assumed for the 25 °C post-checkup
     charges. This is the midpoint of the registered range 0–0.8 Ah.
2. **Graphite-step displacement (in-month update).** Roughly every 5 days the
   profile runs CCCV full charge → 20 A pulse (10.2 Ah) → dynamic discharge.
   That sequence reaches ~56 Ah below full and crosses the graphite staging
   step (~33 Ah below full at BOL).
   - For each cell, the step is located in the ~10 A part of the discharge as
     the first crossing of the midpoint between the upper-plateau and
     lower-plateau median voltages. The four cells are averaged.
   - Loss of lithium inventory, the dominant mechanism in this pack, shortens
     the top-to-step distance one-to-one.
   - The change in step depth since the anchor is added to the anchor capacity
     (`BETA = 1`).

```
Q_est = Q_anchor + EPS0 + EPS_EXTRA_AH + (step_depth_latest − step_depth_first_after_anchor)
SOH_est = 100 · Q_est / 102
```

For CK1, the latest visible anchor is the post-CK0 charge, which maps to
exactly 100.41 Ah. The estimate is then CK0 plus the first month's step
displacement. When no anchor is visible, the model returns the CK0 capacity.

### Why not the reference approach

The reference baseline counts charge from a 13.4 V threshold up to full. On the
LFP plateau that threshold drifts with ageing, so the baseline sees only part of
the fade and is optimistic. Here the capacity observation is a near-full
empty-to-full charge, and the in-month signal is a structural feature of the
graphite electrode (the staging step), not a voltage level.

## Validation (summary)

The hidden capacities are not available, so we validated against **proxy
labels**: the post-checkup full charge plus the offset ε. These proxies are not
the hidden truth. Every prediction is strictly causal: it uses only
`load_dataset(until=CK_k)`, and the framework cuts the data at 00:00 on the
checkup date.

| model | proxy MAE (pp) | proxy max error (pp) |
|---|---|---|
| ExampleModel (reference) | 3.9–4.7 | 4.9–5.7 |
| **this model** | **0.29–0.35** | **0.67** |

The ranges cover ε ∈ {ε0, ε0+0.4, ε0+0.8}. Robustness checks:

- 6 step-detection variants
- β = 0.7–1.5
- leave-one-anchor-out
- ε-drift checks
- a synthetic half-cell LLI/LAM test

Details are in [`REPORT.md`](REPORT.md).

## Run

```
pip install -r requirements.txt
python run_model.py --model train --input data --output-dir out
python run_model.py --model test  --input data --state-dir out --output-dir out --eval-point all
python validate_submission.py
```

- **Runtime:** about 1 s for train and about 10 s for all 8 evaluation points
  (Apple M-series, Python 3.11).
- **Determinism:** the model is deterministic, with no seeds and no fitted
  parameters beyond the CK0 capacity.
- **Tested environments:** identical outputs with Python 3.11 + numpy 1.24.4 /
  pandas 2.0.3, and with numpy 2.4.6 / pandas 3.0.6.

## Estimates

| checkup | CK0 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|
| SOH_est (%) | 98.441 | 95.992 | 95.137 | 93.541 | 92.862 | 91.819 | 91.091 | 90.544 |

## Known limits

- **ε (checkup protocol vs operating charge).** An error in the assumed offset
  shifts all estimates by about ±0.4 pp.
- **Reversible post-checkup recovery.** The step depth jumps by +0.05 to
  +0.54 Ah across each checkup. We cannot tell whether the hidden C/20 value
  reflects the state before or after this recovery.
- **CK1.** This estimate depends on the step-to-capacity ratio β. Over the
  range 0.7–1.5 it moves by about 2 pp.
- **LAM.** Loss of active material, rather than lithium, is only partly visible
  to the step signal. Monthly re-anchoring limits the error to roughly one
  month of LAM.
- **Reduced data budget.** Behaviour on the reduced-budget run has not been
  tested yet. If the start of a segment is missing, its anchor is lost.
