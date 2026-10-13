# TechArena 2026 - Challenge 2 - Student Report

**Team:** <TeamName>    **Members:** <names>    **Date:** 2026-10-13

## 1. Approach

The model combines two signals that a BMS sees under the repeating profile. Neither depends
on a voltage threshold on the flat LFP plateau.

**Anchor: the post-checkup full charge.** After every monthly checkup, the first operating
segment opens with a CCCV charge from near empty to the end of the 14.0 V CV phase.

- The charge starts at 2.89–3.00 V/cell after a 2.0 h rest and runs at 20.4 A.
- It ends at 5.10 A, at about 26.4 °C on the 25 °C segments.
- The charged Ah, integrated from `current_A`, measures nearly the usable capacity: 100.12,
  97.00, 95.67, 94.64, 93.75, 93.08, 92.64 and 91.95 Ah after CK0 to CK7.
- The current integral agrees with the cycler counters to 0.022 Ah. We integrate the current
  rather than use the counters, because the counters book the 20 A pulse as charge.

For each evaluation date the latest visible anchor is used. A constant offset maps it to the
checkup C/20 protocol:

- `EPS0 = 100.41 − 100.122 = 0.288 Ah` is defined by the released CK0 capacity and the
  post-CK0 charge at 45 °C.
- An extra `EPS_EXTRA_AH = 0.4 Ah` is assumed for the 25 °C post-checkup charges. This is the
  midpoint of the pre-registered range {0, 0.4, 0.8}.

**In-month update: graphite-step displacement.** Roughly every 5 days the profile runs this
sequence: CCCV full charge, then a 20 A / 10.2 Ah pulse, then a ~45.7 Ah dynamic discharge.

- The sequence reaches 55.9 Ah below the CV end and crosses the graphite staging step.
- For each cell, we locate the step in the ~10 A part of the discharge. It is the first
  crossing of the midpoint between the upper-plateau median voltage (15–25 Ah) and the
  lower-plateau median voltage (42–50 Ah).
- The step was located in 41 of 41 events. The median spread across the four cells is
  0.63 Ah.
- The step depth fell from 32.81 Ah (20 Jan) to 25.87 Ah (6 Sep). Each cell lost 6.7–7.3 Ah,
  so no single cell runs away.
- The CK0 C/20 reference discharge places the step at 32.5–32.9 Ah, consistent with the first
  operating measurement at about 10 A. The current dependence is therefore small.

**Where the fade sits.** We also locate the step in the charge direction inside each full
charge. From February to September the full charge lost 5.05 Ah, and 68–79 % of that loss lies
between the step and the top of charge. This means loss of lithium inventory (LLI) dominates.
Under LLI the top-to-step distance shrinks one-to-one with capacity, so

```
Q_est(CK_k) = Q_anchor + EPS0 + EPS_EXTRA_AH + BETA * (depth_last - depth_first_after_anchor),  BETA = 1
SOH_est     = 100 * Q_est / 102
```

**How CK0 is used.** For CK1, the post-CK0 charge maps to exactly 100.41 Ah, so CK1 equals CK0
plus the first month's step displacement. The CK0 reference curve serves only as a cross-check
of the step position. The model returns the CK0 capacity if no anchor is visible.

## 2. Data

We used only the released data: the 13 operating segments, CK0, and the CK0 reference
discharge.

| dataset | source / URL | licence | how it was used |
|---|---|---|---|
| none | - | - | No open-source data is used. A literature and transfer route based on Challenge 1 data was evaluated and dropped (see section 4). |

## 3. Validation

**Causality.** Each estimate for CK_k uses only `load_dataset(until=CK_k)`. The framework cuts
the data at 00:00 on the checkup date, so, for example, the 8 Feb 08:52 step measurement is
not visible to CK1. Two checks gave bit-identical outputs:

- fitting on data cut at CK1
- replacing all rows after the cut with noise

**Proxy labels.** The hidden capacities are unknown. We therefore scored against the proxy
`P_k = Q_fc,k + ε`, where `Q_fc,k` is the post-CK_k full charge and ε ∈ {ε0, ε0 + 0.4,
ε0 + 0.8}. A proxy is visible only after its own checkup, so it is never an input for that
checkup. The proxies are not the hidden truth. Some of the numbers were seen during
exploration before the protocol was frozen, so this validation is exploratory.

**Robustness.**

- **Six step-detection variants:** the CK7 output changes by at most 0.18 Ah.
- **β from 0.7 to 1.5:** CK7 changes by 0.78 Ah and CK1 by 2.0 Ah.
- **Leave-one-anchor-out:** errors stay at or below 0.52 pp and degrade smoothly.
- **ε drift:** the CV share, end current, rest time and charge temperature stay constant
  across all anchors. We found no drift, but we cannot exclude a change in the checkup
  protocol itself.
- **Synthetic half-cell test:**
  - Pure LLI: error at most 0.16 Ah.
  - Pure LAM_NE or LAM_PE: partly or fully invisible to the step signal.
  - The measured LLI/LAM mix: about 25 % of the in-month loss is missed. Monthly
    re-anchoring bounds this to about 0.2 Ah.
- **25 vs 45 °C:** the step depth is insensitive to the set point. All anchors after CK1 are
  at 25 °C.

**Reduced data budget.** Not yet evaluated.

## 4. Results, strengths and limits

Proxy errors with ε = ε0 + 0.4, in pp:

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | MAE | max |
|---|---|---|---|---|---|---|---|---|---|
| this model | +0.22 | +0.67 | +0.08 | +0.28 | −0.11 | −0.40 | −0.28 | 0.29 | 0.67 |
| ExampleModel | +2.64 | +4.41 | +4.15 | +5.05 | +5.28 | +4.22 | +4.32 | 4.30 | 5.28 |

SOH estimates (%): CK0 98.441, CK1 95.992, CK2 95.137, CK3 93.541, CK4 92.862, CK5 91.819,
CK6 91.091, CK7 90.544.

**Strengths.**

- The capacity observation is a direct, nearly complete charge, not an inference from the
  plateau.
- The in-month signal is a physical feature of the electrode, consistent across all four
  cells.
- There are no fitted parameters beyond the CK0 capacity, and every term has a physical
  meaning.

**Weak points.**

- **CK2:** the largest error. Segment 3 (19 Feb – 11 Mar) is missing, so the last visible step
  measurement is from 17 Feb.
- **CK1:** the estimate depends on β.
- **ε:** a protocol offset shifts all estimates by about ±0.4 pp.
- **Post-checkup recovery:** the step depth jumps by +0.05 to +0.54 Ah across each checkup and
  then falls faster during the 25 °C segment. It is unclear whether the hidden C/20 value
  reflects the state before or after this recovery.

**Routes we dropped.** We tried three routes earlier and dropped all three:

- open-data transfer
- an ECM joint estimate
- multistage plateau features

All three inferred capacity from mid-plateau windows with a free SOC offset and a
uniform-stretch ageing template. Against the proxies, all were 3–5 pp optimistic.

## 5. Reproducibility

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_model.py --model train --input data --output-dir out
python run_model.py --model test  --input data --state-dir out --output-dir out --eval-point all
python validate_submission.py
```

- **Runtime:** about 1 s for train and about 10 s for all eight evaluation points (Apple
  M-series, macOS).
- **Determinism:** there is no randomness and there are no seeds.
- **Tested environments:** Python 3.11 with numpy 1.24.4 / pandas 2.0.3 and with numpy 2.4.6 /
  pandas 3.0.6. Both give identical output.
- **Research code:** the frozen protocol and all stage scripts are in the team repository on
  branch `exp/phase2-anchor-step-20261013`, under `research/phase2_anchor_step_20261013/`.
