# TechArena 2026 - Challenge 2 - Student Report

**Team:** <TeamName>    **Members:** <names>    **Date:** 2026-10-15

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
2. **Post-anchor offset.** The first deep discharge after each post-checkup full charge reads
   0.4–0.46 Ah deeper. This holds for all six step-detection methods.
   - The offset is the same every month and is gone by the next deep discharge five days later.
   - The plateau voltages, the Ah balance at the top of charge and the step sharpness are
     unchanged, so we read it as a charge-path effect on the measurement.

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

**Coverage gap: temperature-weighted √t extrapolation (CK2).** Segment 3 (19 Feb – 11 Mar) is missing, so the
last visible step lies 22 days before CK2. The step signal cannot see those weeks. When the
last visible deep discharge ended more than 10 days before the checkup, the model extrapolates
the loss since the previous anchor with the square root of temperature-weighted time since CK0:

```
loss_j = 100.41 − (Q_fc(j) + EPS0 + EPS_EXTRA_AH)   over the visible anchors j = 1..k−1
a      = least-squares slope of loss_j on sqrt(t_j) through the origin
Q_est  = Q_fc(k−1) + EPS0 + EPS_EXTRA_AH − a · (sqrt(t_k) − sqrt(t_(k−1)))
t      = ∫ exp[(Ea/R)(1/318.15 − 1/T(τ))] dτ  (45 °C-equivalent days since CK0, Ea = 20.6 kJ/mol)
```

- **Why √t.** The proxy fade of this pack follows about t^0.44, i.e. calendar-like ageing.
  The cycling-aged open datasets follow 0.56–1.09, so their shape was not used.
- **Why temperature-weighted time.** Calendar ageing under changing temperature accumulates
  in Arrhenius-weighted "virtual time" (Naumann et al., J. Energy Storage 17 (2018) 153); Ea
  20.6 kJ/mol is the LFP calendar value of Schimpe et al., J. Electrochem. Soc. 165 (2018) A181.
  T(τ) is the chamber set-point of the visible segments, 25 °C during checkup gaps and 45 °C for
  the missing segment 3 (public alternation schedule). On the five one-month extrapolations the
  gap rule makes when data are cut before CK3–CK7, this lowers the mean error from 0.113 to
  0.105 pp; calendar time with a lower exponent (0.44) made every hold-out metric worse.
- **Where it applies.** Only CK2 triggers this branch.

**Fallback and CK0.**

- For CK1 and CK3 no phase-matched pair exists, and there is no coverage gap. There the model
  uses the anchor plus the step change since the anchor, with β = 1.
- For CK1 the anchor is the post-CK0 charge, which maps to exactly 100.41 Ah.
- The CK0 reference curve serves only as a cross-check of the step position.

## 2. Data

The model uses only the released data: the 13 operating segments, CK0, and the CK0 reference
discharge. No open data enters the model and nothing is pre-trained. Three open LFP datasets
were analysed to bound its assumptions.

| dataset | source / URL | licence | how it was used |
|---|---|---|---|
| ESSL1 / ESSL2 (LFP 102 Ah and 105 Ah cells; 16S and 15S lab packs) | https://zenodo.org/records/20132842 (doi 10.5281/zenodo.20132842) | CC BY 4.0 | Graphite-step β within 0–8 % fade: packs 1.1–1.2, cells 0.9–1.1. Used to judge β; a β cap was tested and rejected. |
| Gotion IFP 53 Ah LFP cell + 1P10S module (calibration every 50 cycles) | https://data.mendeley.com/datasets/4nww8p6vxf/1 (doi 10.17632/4nww8p6vxf.1) | CC BY 4.0 | Drift of full-charge Ah against independent calibration (ε): about −0.03 Ah per Ah of fade. Risk statement only. |
| TEMPEST 280 Ah prismatic LFP (0.1C RPT every 50 cycles) | https://zenodo.org/records/20813753 (doi 10.5281/zenodo.20813753) | CC BY 4.0 | ε drift −0.035 Ah per Ah of fade; no capacity rebound after RPTs (≤ 0.1 %). Risk statement only. |

A literature and transfer route based on Challenge 1 data was evaluated earlier and dropped
(see section 4).

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

**Gap branch (this model vs V2).**

- It changes only CK2. The proxy error moves from +0.67 to −0.21 / −0.02 / +0.18 pp across the
  three ε values.
- It improves the MAE by 0.08–0.10 pp under each of the six step-detection variants.
- **Sensitivity.** With exponent 0.4–0.6 and a ±5-day time origin, the CK2 error ranges from
  −0.35 to +0.29 pp. Every setting is still better than +0.67.
- **Exposure.** The branch was chosen after the CK2 proxy error had been seen, so this
  improvement is exploratory.
- **Rejected with it.** A β cap at 1.2 and a 4-cell median, registered together with it, were
  rejected:
  - the cap moves CK5–CK7 up, in the same direction as the ε-drift risk;
  - the median worsened the dV/dQ detection variant (MAE 0.333 → 0.448).

**Alternatives tested and rejected.** All were pre-registered, and none beat V2:

- a robust regression of the month-end value;
- step crossings in daily operation (coulomb counting does not close between full charges);
- rest-point pseudo-OCV (no rests near the step);
- a feature in the top 21 Ah of the periodic charges (none found);
- rate-based extrapolation over the missing segment from segment-level step rates
  (over-corrects; the √t branch instead extrapolates the anchor-to-anchor loss);
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
| this model (V2 + temperature-weighted √t gap) | +0.22 | +0.04 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 | 0.13 | 0.23 |
| V2 + calendar-time √t gap (previous version) | +0.22 | −0.02 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 | 0.12 | 0.23 |
| V2 without gap branch | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 | 0.22 | 0.67 |
| V1 (unmatched) | +0.22 | +0.67 | +0.08 | +0.28 | −0.11 | −0.40 | −0.28 | 0.29 | 0.67 |
| ExampleModel | +2.64 | +4.41 | +4.15 | +5.05 | +5.28 | +4.22 | +4.32 | 4.30 | 5.28 |

SOH estimates (%): CK0 98.441, CK1 95.992, CK2 94.507, CK3 93.541, CK4 92.811, CK5 92.081,
CK6 91.331, CK7 90.821.

**Strengths.**

- The capacity observation is a direct, nearly complete charge, not an inference from the
  plateau.
- The in-month signal is a physical feature of the electrode, compared under matched
  temperature and checkup phase.
- β follows from the measured LLI share. There are no tuned parameters, and every term has a
  physical meaning.

**Weak points.**

- **Post-anchor offset.** The first deep discharge after each post-checkup full charge reads
  0.4–0.46 Ah deeper. Pairwise comparison shows the offset is constant across months, not
  growing.
  - Unchanged plateaus, Ah balance and step sharpness point to a charge-path measurement
    effect.
  - A very fast (≤ 2.5 days) real relaxation cannot be excluded by timing. If the hidden C/20
    missed one, CK3–CK7 would read high by at most about 0.45 pp.
  - Phase matching does not use these discharges.
- **ε:** a protocol offset shifts all estimates by about ±0.4 pp.
  - A data-based temperature offset (0.18 Ah instead of 0.4) would lower CK3–CK7 by about
    0.2 pp.
  - Open data with independent capacity tests show ε drifting by about −0.03 Ah per Ah of
    fade. This would make the late estimates read high by up to about 0.3 pp. The proxies
    share this bias.
- **CK2:** estimated by the temperature-weighted √t extrapolation. It carries the first-month
  break-in, the ε0 temperature confound, the exponent assumption (±0.3 pp across the tested
  settings) and the assumption that segment 3 ran at 45 °C (at 25 °C, CK2 would be 94.84 %).
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
- **Tested environment:** a fresh Python 3.11 virtual environment from `requirements.txt`, run
  from a clean extraction of the submission zip. The validator passes, and the full-data output
  equals the research implementation to within 0.0004 pp.
- **Research code:** in the team repository.
  - V1: branch `exp/phase2-anchor-step-20261013`, under `research/phase2_anchor_step_20261013/`.
  - V2: same branch, under `research/phase2_v2_phase_matched_20261013/`.
  - Gap branch, β cap and median study (V3, with the submitted V2 + √t variant):
    `research/phase2_v3_20261015/`. Open-data screening: `external_data/`.
  - Rejected alternatives: branches `exp/phase2-round3-models-20261014` and
    `exp/phase2-round4-signals-20261014`.
