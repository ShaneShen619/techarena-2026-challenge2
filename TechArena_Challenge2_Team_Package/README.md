# TechArena 2026 – Challenge 2: Anchor + Phase-Matched Graphite-Step SOH Estimator

Estimates the SOH (C/20 capacity ÷ 102 Ah) of the 4 × 102 Ah LFP pack at each
checkup date. It reads only the operating data before that date.

- **Code:** the model lives in [`my_model/model_template.py`](my_model/model_template.py), and
  [`my_model/__init__.py`](my_model/__init__.py) points `ActiveModel` at it.
- **Dependencies:** numpy and pandas only.
- **No open data in the model, no pre-trained artefacts.** Three open LFP datasets
  were examined to bound the model's assumptions. They are listed under
  [Open data examined](#open-data-examined).

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
     upper-plateau and lower-plateau median voltages. The same is done with five
     more detection variants: a narrower current band, plateau windows shifted
     by ±3 Ah, an IR-corrected voltage, and the dV/dQ peak.
   - **Robust step value.** Each cell's step is the median over the six
     variants, and the discharge's step is the median over the four cells. A
     single noisy detection method (the dV/dQ peak sits on a 0.25 Ah grid) or a
     single cell that slowly drifts away from the others (cell 1 here) cannot
     pull the value. Which discharges are used is unchanged.
   - **Why the step tracks capacity.** Loss of lithium inventory, the dominant
     mechanism here, shortens the top-to-step distance.
   - **Phase matching.** The step depth also moves for two reasons that are not
     ageing:
     - it reads deeper at 45 °C than at 25 °C;
     - the first deep discharge after the post-checkup full charge reads about
       0.4–0.46 Ah deeper. The offset is the same every month and is gone by the
       next deep discharge five days later.

     The model therefore compares only *like with like*: the last 45 °C step of
     the current month against the last 45 °C step of the previous month. Each
     is brought to its checkup date with the current 45 °C rate. Both lie at
     the same point of the checkup cycle, so both effects cancel.
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

3. **Coverage gap: temperature-weighted √t extrapolation.** If the last visible deep discharge ended
   more than 10 days (`GAP_DAYS`) before the checkup, the step signal cannot see
   the uncovered weeks. This happens for CK2, because segment 3 (19 Feb – 11 Mar)
   is missing and the last visible step is 22 days before CK2. The model then
   extrapolates the loss since the previous anchor with the square root of
   temperature-weighted time since CK0:

```
loss_j  = 100.41 − (Q_anchor(j) + EPS0 + EPS_EXTRA_AH),   j = 1..k−1 (visible anchors)
a       = least-squares slope of loss_j on sqrt(t_j)      (through the origin)
Q_est   = Q_anchor(k−1) + EPS0 + EPS_EXTRA_AH − a · (sqrt(t_k) − sqrt(t_(k−1)))
t       = ∫ exp[(Ea/R)(1/318.15 − 1/T(τ))] dτ   (45 °C-equivalent days since CK0, Ea = 20.6 kJ/mol)
```

   `T(τ)` is the chamber set-point of the visible segments; checkup gaps count as
   25 °C, and the missing segment 3 counts as 45 °C (public schedule: short 25 °C
   segments alternate with long 45 °C ones). Calendar ageing under changing
   temperature accumulates in this "virtual time" (Naumann et al., J. Energy
   Storage 17 (2018) 153). The pack's proxy fade follows t^0.44, i.e. it fades
   like calendar ageing. The cycling-aged open datasets fade with exponents of
   0.56–1.09, so √t is a pack-specific choice, not one taken from them.

**Fallback.** When neither a phase-matched pair nor a coverage gap applies
(CK1 and CK3), the model uses the anchor plus the step change since the anchor
(β = 1). For CK1 the anchor is the post-CK0 charge, which maps to exactly
100.41 Ah. When no anchor is visible, the model returns the CK0 capacity.

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
leaves every output bit-identical (checked on all 8 checkups).

| Model | Proxy MAE (pp), ε0 / +0.4 / +0.8 | Proxy max error (pp), ε0 / +0.4 / +0.8 |
|---|---|---|
| ExampleModel (reference) | 4.7 / 4.3 / 3.9 | 4.9–5.7 |
| Anchor + step, unmatched (V1) | 0.35 / 0.29 / 0.29 | 0.67 |
| Phase-matched, no gap branch (V2) | 0.27 / 0.22 / 0.21 | 0.67 |
| V2 + calendar-time √t gap branch | 0.21 / 0.12 / 0.14 | 0.61 / 0.23 / 0.23 |
| V2 + temperature-weighted √t gap branch (previous version) | 0.20 / 0.13 / 0.15 | 0.61 / 0.23 / 0.23 |
| **This model (previous + robust multi-variant cell-median step)** | **0.19 / 0.12 / 0.14** | **0.60 / 0.24 / 0.24** |

**Robustness.**

- **The gap branch changes only CK2.** Its proxy error there moves from +0.67 to
  −0.15 / +0.04 / +0.23 pp (ε0 / +0.4 / +0.8).
- **Temperature weighting is supported by causal hold-out tests.** On the five
  one-month extrapolations that the gap rule produces when data are cut before
  CK3–CK7, weighting time by temperature lowers the mean error from 0.113 to
  0.105 pp (pseudo-cut mean 0.148 → 0.144, cold start 0.174 → 0.170). Simply
  lowering the exponent to 0.44 in calendar time made every hold-out metric
  worse. The result depends on the
  assumptions: with an exponent of 0.4–0.6 or a ±5-day time origin, the CK2
  error ranges from −0.35 to +0.29 pp at ε0 + 0.4. Every setting is still better
  than +0.67.
- **Robust step value is supported by causal hold-out tests.** On the data cuts
  that hide the last days or the start of a month (pseudo-cut and cold-start
  scenarios), the median over six detection variants and four cells lowers the
  mean error from 0.157 to 0.147 pp (pseudo-cut 0.144 → 0.134, cold start
  0.170 → 0.160). Rebuilt from any five of the six variants, it stays better
  than the previous model, so no single detection method carries the gain. It
  changes no checkup by more than 0.1 pp.
- **Exposure.** The gap branch was chosen after the proxy values had been seen,
  so this improvement is exploratory, not blind.
- **Rejected variants.** A β cap at 1.2, a plain 4-cell median and a 4-cell
  minimum were tested and rejected. The cap pushes CK5–CK7 up in the same
  direction as the ε-drift risk below. The plain median was not robust across
  detection variants (the noisy dV/dQ variant broke it), which is why the
  median is now taken over variants first. Combining per-cell changes with
  outlier rejection added nothing, and correcting each cell for its top-of-charge
  state was not supported by the data.

Details are in [`REPORT.md`](REPORT.md).

## Open data examined

None of these datasets is used by the model. They informed the choice of
assumptions and the risk statements below.

| Dataset | Source | Licence | What transferred |
|---|---|---|---|
| ESSL1/ESSL2: LFP 102 Ah / 105 Ah cells, 16S and 15S lab packs | [Zenodo 10.5281/zenodo.20132842](https://zenodo.org/records/20132842) | CC BY 4.0 | Within 0–8 % fade, packs show β ≈ 1.1–1.2 and cells ≈ 0.9–1.1, so a β around 1.2–1.5 is plausible but should not grow further. The labels are same-cycle charge Ah, not independent tests. |
| Gotion 53 Ah LFP cell + 1P10S module, 1000 cycles, calibration every 50 cycles | [Mendeley 10.17632/4nww8p6vxf.1](https://data.mendeley.com/datasets/4nww8p6vxf/1) | CC BY 4.0 | Full-charge Ah vs independent calibration: ε drifts about −0.03 Ah per Ah of fade (cell). The module result is inconclusive. |
| TEMPEST 280 Ah prismatic LFP, 700 cycles, 0.1C RPT every 50 cycles | [Zenodo 10.5281/zenodo.20813753](https://zenodo.org/records/20813753) | CC BY 4.0 | ε drifts −0.035 Ah per Ah of fade. There is no capacity rebound after an RPT (≤ 0.1 %). |

## Run

```
pip install -r requirements.txt
python run_model.py --model train --input data --output-dir out
python run_model.py --model test  --input data --state-dir out --output-dir out --eval-point all
python validate_submission.py
```

- **Runtime:** about 1 s for train and about 11 s for all 8 evaluation points
  (Apple M-series).
- **Determinism:** the model is deterministic, with no seeds and no fitted
  parameters beyond the CK0 capacity.
- **Tested environment:** a fresh Python 3.11 virtual environment installed from
  `requirements.txt`, run from a clean extraction of the submission zip.

## Estimates

| checkup | CK0 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|
| SOH_est (%) | 98.441 | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |

## Known limits

- **ε (checkup protocol vs operating charge).**
  - An error in the assumed constant offset shifts all estimates by about
    ±0.4 pp.
  - Two open datasets with independent capacity tests show ε drifting by about
    −0.03 Ah per Ah of fade. Transferred to this pack (about 8 Ah of fade by
    CK7), this suggests the estimates may read high by up to about 0.3 pp late
    in the campaign. The proxies share this bias, so it cannot be checked
    locally.
- **CK2.** The estimate rests on the √t assumption and on the CK0→CK1 loss,
  which includes the first-month break-in and the ε0 temperature confound
  (the post-CK0 anchor was charged at 45 °C). It also assumes that the missing
  segment 3 ran at 45 °C; at 25 °C, CK2 would be 94.84 %.
- **Post-anchor step offset.**
  - The first deep discharge after each post-checkup full charge reads
    0.4–0.46 Ah deeper. The offset is the same every month and is gone five
    days later.
  - The plateau voltages, the top-of-charge Ah balance and the step sharpness
    are unchanged. This points to a charge-path effect on the measurement, not
    recovered capacity.
  - The data cannot exclude a very fast (≤ 2.5 days) real relaxation. If the
    hidden C/20 missed such a relaxation, CK3–CK7 would read high by at most
    about 0.45 pp.
  - Phase matching does not use these discharges.
- **β.** β rises to 1.51 at CK7. Open-data packs suggest 1.1–1.2. If the late
  LAM share is smaller, β overstates the loss, which pulls the estimate low.
  This partly offsets the ε-drift risk.
- **Reduced data budget.** If the start of a segment is missing, its anchor is
  lost, and the model falls back to older anchors.
