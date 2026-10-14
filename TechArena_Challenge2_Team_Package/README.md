# TechArena 2026 – Challenge 2: Anchor + Phase-Matched Graphite-Step SOH Estimator

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
     charges.
2. **Graphite-step depth (in-month update).** Roughly every 5 days the profile
   runs CCCV full charge → 20 A pulse (10.2 Ah) → dynamic discharge. That
   sequence reaches ~56 Ah below full and crosses the graphite staging step
   (~33 Ah below full at BOL).
   - **Locating the step.** For each cell, the step is located in the ~10 A
     part of the discharge as the first crossing of the midpoint between the
     upper-plateau and lower-plateau median voltages. The four cells are
     averaged.
   - **Why the step tracks capacity.** Loss of lithium inventory, the dominant
     mechanism here, shortens the top-to-step distance.
   - **Phase matching.** The step depth also moves for two reasons that are not
     ageing:
     - it reads about 0.18 Ah deeper at 45 °C than at 25 °C;
     - it is temporarily deeper just after each checkup, by a reversible
       recovery that fades within days of cycling.

     The model therefore compares only *like with like*: the last 45 °C step of
     the current month against the last 45 °C step of the previous month. Each
     is brought to its checkup date with the current 45 °C rate. Both lie at
     the same point of the checkup cycle, so the temperature shift and the
     recovery cancel.
   - **β.** The step sees only the lithium-inventory part of the fade. β, the
     capacity change per Ah of step change, is estimated from the visible
     25 °C anchors: their full-charge loss divided by the loss above the
     charge-side step. It is then shrunk towards 1. The values used are
     1.06–1.51 for CK4–CK7.

```
Q_est(CK_k) = Q_anchor(k−1) + EPS0 + EPS_EXTRA_AH
              + β_k · [E45(k−1) − E45(k−2) + r · (d(k−1) − d(k−2))]
SOH_est     = 100 · Q_est / 102
```

`E45(m)` is the last 45 °C step depth in month m, `d(m)` its distance in days
to the checkup date, and `r` the current month's 45 °C Theil–Sen rate.

**Fallback.** When no phase-matched pair is visible (CK1–CK3: too few months,
plus the missing segment 3), the model uses the anchor plus the step change
since the anchor (β = 1). For CK1 the anchor is the post-CK0 charge, which maps
to exactly 100.41 Ah. When no anchor is visible, the model returns the CK0
capacity.

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
`load_dataset(until=CK_k)`. Replacing all rows after the cutoff with noise
leaves every output bit-identical.

| Model | Proxy MAE (pp), ε0 / +0.4 / +0.8 | Proxy max error (pp) |
|---|---|---|
| ExampleModel (reference) | 4.7 / 4.3 / 3.9 | 4.9–5.7 |
| Anchor + step, unmatched (V1) | 0.35 / 0.29 / 0.29 | 0.67 |
| **This model (V2)** | **0.27 / 0.22 / 0.21** | **0.67** |

**Robustness.**

- V2 beats V1 under all six step-detection variants and every tested setting
  of its own parameters.
- Several alternative models were tested and none did better:
  - month-end regression;
  - extra step crossings from daily operation;
  - rest-point pseudo-OCV;
  - gap extrapolation;
  - state-space fusion;
  - full-curve registration.

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
| SOH_est (%) | 98.441 | 95.992 | 95.137 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |

## Known limits

- **Recovery state at the checkup.** Each checkup restores capacity that cycling
  had made temporarily unavailable. The recovery grows from about 0.02 Ah (CK1)
  to about 0.9 Ah (CK7) and fades with a time constant of about 2.5 days.
  - The anchors, and this model, describe the recovered state.
  - The anchor charges start near empty after a short rest. This suggests the
    C/20 discharge is the last checkup step, just before the anchor, which
    supports this choice.
  - If the hidden C/20 nevertheless saw only part of the recovery, the
    estimates for CK4–CK7 would be high by up to about 0.9 pp.
- **ε (checkup protocol vs operating charge).** An error in the assumed offset
  shifts all estimates by about ±0.4 pp.
- **CK2.** This is the largest proxy error (+0.67 pp). Segment 3 is missing,
  so the last visible step is 22 days before the checkup, and no causal
  extrapolation improved it.
- **LAM.** Loss of active material is only partly visible to the step signal.
  β and monthly re-anchoring limit its effect.
- **Reduced data budget.** If the start of a segment is missing, its anchor is
  lost, and the model falls back to older anchors.
