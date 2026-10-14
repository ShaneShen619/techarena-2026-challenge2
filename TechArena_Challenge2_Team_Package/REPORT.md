# TechArena 2026 - Challenge 2 - Student Report

**Team:** <TeamName>    **Members:** <names>    **Date:** 2026-10-14

## 1. Approach

The model combines two signals that a BMS sees under the repeating profile. Neither depends
on a voltage threshold on the flat LFP plateau.

**Anchor: the post-checkup full charge.** After every monthly checkup, the first operating
segment opens with a CCCV charge from near empty to the end of the 14.0 V CV phase.

- The charge starts at 2.87–3.00 V/cell after a 2.0 h rest and runs at 20.4 A.
- It ends at 5.10 A, at about 26.4 °C on the 25 °C segments.
- The charged Ah, integrated from `current_A`, measures nearly the usable capacity: 100.12,
  97.00, 95.67, 94.64, 93.75, 93.08, 92.64 and 91.95 Ah after CK0 to CK7.
- The current integral agrees with the cycler counters to 0.022 Ah. We integrate the current
  rather than use the counters, because the counters book the 20 A pulse as charge.

For each evaluation date the latest visible anchor is used. A constant offset maps it to the
checkup C/20 protocol:

- `EPS0 = 100.41 − 100.122 = 0.288 Ah` is defined by the released CK0 capacity and the
  post-CK0 charge at 45 °C.
- An extra `EPS_EXTRA_AH = 0.4 Ah` is assumed for the 25 °C post-checkup charges.

**In-month signal: the graphite staging step.** Roughly every 5 days the profile runs this
sequence: CCCV full charge, then a 20 A / 10.2 Ah pulse, then a ~45.7 Ah dynamic discharge.

- The sequence reaches 55.9 Ah below the CV end and crosses the graphite staging step.
- For each cell, the step is the first crossing of the midpoint between the upper-plateau
  median voltage (15–25 Ah) and the lower-plateau median voltage (42–50 Ah), in the ~10 A part
  of the discharge.
- The step was located in 41 of 41 events, with a median spread of 0.63 Ah across the cells.
- The step depth fell from 32.81 Ah (20 Jan) to 25.87 Ah (6 Sep).

**What else moves the step.** Splitting each month by segment showed two effects that are not
ageing:

1. **Temperature.** The step reads about +0.18 Ah deeper at 45 °C than at 25 °C, at every
   25 → 45 °C switch.
2. **Post-checkup recovery.** Right after each checkup the step is deeper, and it falls fast in
   the first days of the 25 °C segment (0.07–0.13 Ah/day, against 0.02–0.04 Ah/day at 45 °C).

A simple "last step minus first step after the anchor" (our V1) mixes both effects with
ageing.

**Phase-matched update (this model, V2).** We compare only month-end 45 °C steps of
consecutive months. Both lie just before a checkup and at the same temperature, so both
effects cancel:

```
Q_est(CK_k) = Q_fc(k−1) + EPS0 + EPS_EXTRA_AH + β_k · [E45(k−1) − E45(k−2) + r · (d(k−1) − d(k−2))]
SOH_est     = 100 · Q_est / 102
```

- `E45(m)` is the last 45 °C step of month m, and `d(m)` its distance in days to the checkup.
- `r` is the current month's 45 °C Theil–Sen rate.
- The pair is used only when both month-ends are complete 45 °C segments within 10 days of
  their checkups. This holds for CK4–CK7.

**β from physics.** The step measures the lithium-inventory part of the fade only. Inside each
anchor charge we also locate the charge-direction step. 68–79 % of the anchor-to-anchor loss
lies between the step and the top of charge, so the step under-reads the total loss.

- β_k is the least-squares ratio of full-charge loss to step-to-top loss over the visible
  25 °C anchors, shrunk towards 1.
- Values: 1.06 (CK4), 1.24, 1.41 and 1.51 (CK7).

**Fallback and CK0.**

- For CK1–CK3 no phase-matched pair exists (too few months, plus the missing segment 3).
  There the model uses the anchor plus the step change since the anchor, with β = 1.
- For CK1 the anchor is the post-CK0 charge, which maps to exactly 100.41 Ah.
- The CK0 reference curve serves only as a cross-check of the step position.

## 2. Data

We used only the released data: the 13 operating segments, CK0, and the CK0 reference
discharge.

| dataset | source / URL | licence | how it was used |
|---|---|---|---|
| none | - | - | No open-source data is used. A literature and transfer route based on Challenge 1 data was evaluated and dropped (see section 4). |

## 3. Validation

**Causality.** Each estimate for CK_k uses only `load_dataset(until=CK_k)`. Two checks gave
bit-identical outputs:

- fitting on data cut at CK1;
- replacing all rows after the cutoff with noise.

**Proxy labels.** The hidden capacities are unknown, so we scored against the proxy
`P_k = Q_fc,k + ε`, with ε ∈ {ε0, ε0 + 0.4, ε0 + 0.8}.

- A proxy is visible only after its own checkup, so it is never an input for that checkup.
- The proxies are not the hidden truth.
- All proxy values had been seen during development, so this validation is exploratory, even
  though every model was pre-registered before its evaluation.

**Robustness of V2.**

- It beats V1 under all six step-detection variants.
- Changing its shrinkage strength, the validity window or the smoothing used for β leaves the
  MAE at 0.205–0.224 pp, against 0.216 pp for the main setting.
- **Pseudo scenarios.** Data were cut 5 or 10 days early, or 45 °C segments truncated to
  imitate the missing segment, to create more test cases than the seven proxies.

**Alternatives tested and rejected.** All were pre-registered, and none beat V2:

- a robust regression of the month-end value;
- step crossings in daily operation (coulomb counting does not close between full charges);
- rest-point pseudo-OCV (no rests near the step);
- a feature in the top 21 Ah of the periodic charges (none found);
- rate-based extrapolation over the missing segment (over-corrects);
- registration of the full anchor charge curves (confounded by the start state);
- state-space fusion.

A key diagnostic: within a 45 °C segment, step depths scatter by only 0.012–0.036 Ah around a
line. The remaining error is systematic, not measurement noise.

**Reduced data budget.** Not separately optimised. With a missing segment start, the anchor of
that month is lost and the model falls back to the previous anchor.

## 4. Results, strengths and limits

Proxy errors with ε = ε0 + 0.4, in pp:

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | MAE | max |
|---|---|---|---|---|---|---|---|---|---|
| this model (V2) | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 | 0.22 | 0.67 |
| V1 (unmatched) | +0.22 | +0.67 | +0.08 | +0.28 | −0.11 | −0.40 | −0.28 | 0.29 | 0.67 |
| ExampleModel | +2.64 | +4.41 | +4.15 | +5.05 | +5.28 | +4.22 | +4.32 | 4.30 | 5.28 |

SOH estimates (%): CK0 98.441, CK1 95.992, CK2 95.137, CK3 93.541, CK4 92.811, CK5 92.081,
CK6 91.331, CK7 90.821.

**Strengths.**

- The capacity observation is a direct, nearly complete charge, not an inference from the
  plateau.
- The in-month signal is a physical feature of the electrode, compared under matched
  temperature and checkup phase.
- β follows from the measured LLI share. There are no tuned parameters, and every term has a
  physical meaning.

**Weak points.**

- **Recovery state at the checkup.** The recovery grows from about 0.02 Ah (CK1) to about
  0.9 Ah (CK7) and fades with τ ≈ 2.5 days of cycling. This matches rest-driven
  rehomogenisation of cycling-induced lithium/salt inhomogeneity.
  - The model, like its proxies, describes the recovered state.
  - The anchors start near empty after a short rest, which suggests that the C/20 discharge
    is the last checkup step and sees nearly the same state.
  - If the C/20 saw only part of the recovery, CK4–CK7 would be high by up to about 0.9 pp.
- **ε:** a protocol offset shifts all estimates by about ±0.4 pp. A data-based temperature
  offset (0.18 Ah instead of 0.4) would lower CK3–CK7 by about 0.2 pp.
- **CK2:** the largest error, because segment 3 is missing.
- **β:** it rises to 1.51 at CK7. If the LAM share falls late in life, β overstates the loss.

**Routes we dropped earlier.** Three earlier routes were dropped: open-data transfer, an ECM
joint estimate, and multistage plateau features. All three inferred capacity from mid-plateau
windows with a free SOC offset. Against the proxies, all were 3–5 pp optimistic.

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
- **Research code:** in the team repository.
  - V1: branch `exp/phase2-anchor-step-20261013`, under `research/phase2_anchor_step_20261013/`.
  - V2: same branch, under `research/phase2_v2_phase_matched_20261013/`.
  - Rejected alternatives: branches `exp/phase2-round3-models-20261014` and
    `exp/phase2-round4-signals-20261014`.
