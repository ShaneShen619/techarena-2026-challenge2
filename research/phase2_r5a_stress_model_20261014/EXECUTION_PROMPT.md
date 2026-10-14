<a id="en"></a>

# Round 5A: Self-Calibrated Stress-History Ageing Model — Unattended Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-14. This document is self-contained. The English text is the execution text; the Chinese section is a translation for the reader, and if they differ the English governs. A separate prompt (round 5B, electrode-level model) may run at the same time in another worktree; it shares nothing with this run.

## 0. Mode of work

- **Unattended run.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Context may be compacted or restarted.** Keep `notes/STATUS.md` current after every step: stage, done, next, last commit. On restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume. Never redo a finished stage.
- **Time budget.** About 7 hours in total, with a cap per stage (§7). At a cap, write up what exists (including "inconclusive"), commit, and move on.
- **Done means** (all must hold):
  1. every stage in §6 is finished or capped, and `notes/STATUS.md` says so;
  2. `FINAL_REPORT.md` and `README.md` exist in the study directory, bilingual, conclusions first;
  3. every registered protocol has its `protocol.sha256` committed before its evaluation commit;
  4. every commit is pushed to `origin exp/phase2-r5a-stress-model-20261014`;
  5. `git status` in the worktree shows no uncommitted study files.

## 1. Workspace, isolation and git

- **Worktree and branch (already created).**
  - Work only in the worktree `/Users/shane/Desktop/Arena_1014_r5a_stress`, on branch `exp/phase2-r5a-stress-model-20261014`. It starts from `exp/phase2-round4-signals-20261014` at `a6bc61f`.
  - Never `cd` into any other checkout (`/Users/shane/Desktop/Arena_1013_model`, `Arena_1014_round4`, `Arena_1014_r5b_electrode`, or the archive).
  - All new work goes into `research/phase2_r5a_stress_model_20261014/` (the "study directory").
- **Concurrency guard.**
  - At the start and before every commit, run `git log --oneline -5` and compare with your own last commit.
  - If a commit you did not make appears, or a tracked file changes that you did not change: stop editing shared files, record it in `notes/DECISIONS.md`, and only add files by explicit path from then on.
  - Never use `git add -A` or `git add .`, never revert or rewrite someone else's work, never use bare `git stash`.
- **Commits and pushes.**
  - Commit this prompt as the first commit.
  - Commit at the end of every stage and after meaningful sub-steps.
  - After each stage commit, run `git push -u origin exp/phase2-r5a-stress-model-20261014`. Never push anywhere else, and never force-push.
  - Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify:**
  - `TechArena_Challenge2_Team_Package/` (framework, `run_model.py`, `validate_submission.py`, `my_model/`, `data/`);
  - any earlier study directory (`phase2_anchor_step_20261013`, `phase2_v2_phase_matched_20261013`, `phase2_round3_models_20261014`, `phase2_round4_signals_20261014`);
  - the Challenge 1 data at `/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original/` and the Challenge 1 project at `/Users/shane/Desktop/项目/Current State_Challenge1/` (read only).

  Import or read their code; do not edit it.
- **Document language.** Every Markdown document you write is English first, Chinese second, in the same layout as this file (`<a id="en"></a>`, language line, `---`, `<a id="zh"></a>`). Code comments and docstrings are English only.
- **Bytecode.** Run Python with `python3 -B`.

## 2. Task, current state and why this round exists

**Task (TechArena 2026 Challenge 2).** Estimate the SOH of a 4 × 102 Ah LFP series pack on each checkup date.

- **Target.** SOH = C/20 capacity ÷ 102 Ah. The C/20 capacity is the Ah from a 5.1 A discharge after a full charge, until the pack voltage first reaches 11.2 V.
- **Labels.** Only CK0 = 100.41 Ah is released. CK1–CK7 are hidden and scored (several error metrics including the worst case, each normalised by the official baseline).
- **Checkup dates:** CK0 2025-01-14, CK1 02-08, CK2 03-11, CK3 04-14, CK4 05-16, CK5 06-16, CK6 07-25, CK7 08-28.
- **Causal cut.** A prediction for CK_k may use only `load_dataset(data, until=CK_k)`, which cuts at 00:00 of that date.

**Data and calendar (verified 2026-10-14).**

| Month m (CK_m → CK_m+1) | 25 °C segment | 45 °C segment |
|---|---|---|
| 0 (CK0 → CK1) | none | seg 1, 01-19 → 02-08 |
| 1 (CK1 → CK2) | seg 2, 02-11 → 02-19 | seg 3, 02-19 → 03-11, **missing** |
| 2 (CK2 → CK3) | seg 4, 03-14 → 03-22 | seg 5, 03-23 → 04-13 |
| 3 | seg 6, 04-16 → 04-25 | seg 7, 04-25 → 05-15 |
| 4 | seg 8, 05-19 → 05-26 | seg 9, 05-26 → 06-16 |
| 5 | seg 10, 06-21 → 07-02 | seg 11, 07-03 → 07-22 |
| 6 | seg 12, 07-28 → 08-07 | seg 13, 08-08 → 08-28 |
| after CK7 | seg 14, 09-01 → 09-11 | — |

- 10-s sampling. Columns: `timestamp`, `elapsed_s`, `segment`, `chamber_temperature_C`, `current_A` (+ charge), `charge_Ah_cum`, `discharge_Ah_cum`, `cell1_V`..`cell4_V`, `pack_voltage_V`, `temp_mean_C`/`min`/`max`. Mean cell temperature is about 46 °C in 45 °C segments and about 25.6 °C in 25 °C segments.
- The Ah counters continue through recording gaps and through segment 3, but checkup throughput is not counted. The counter jump across segment 3 becomes visible only once segment 4 is visible, i.e. **after** the CK2 cutoff.
- About 1600 Ah of charge per 45 °C segment and 600–900 Ah per 25 °C segment.
- The gaps between months are the checkups (2–6 days).

**Anchors.** After each checkup the pack is charged from near empty (pack ≈ 11.6–12.0 V after a 2 h rest) at about 20 A CC, then CV at 14.0 V to 5.1 A. The charged Ah `Q_fc,j` (from `events.full_charges`) is the anchor j. Anchor 0 is in segment 1 at 45 °C; anchors 1–7 are in the 25 °C segments 2, 4, 6, 8, 10, 12, 14, two to five days after CK_j.

**Current leading candidate: V2** (`research/phase2_v2_phase_matched_20261013/src/v2.py`). The submission package on branch `exp/phase2-anchor-step-20261013` currently points to V2 (commit `1f7deb3`); do not touch it.

- Q_anchor = Q_fc + ε, ε = ε0 + Δ, ε0 = 100.41 − Q_fc,0.
- In-month update from the phase-matched difference of 45 °C graphite-step depths, scaled by a physics β (1.06–1.51); CK1–CK3 fall back to M4.
- **Proxy result** (proxy P_k = Q_fc,k + ε0 + Δ, Δ = 0.4): MAE **0.215726 pp**, MAX **0.669052 pp** (CK2). Per checkup: CK1 +0.217, CK2 +0.669, CK3 +0.080, CK4 +0.228, CK5 +0.150, CK6 −0.163, CK7 −0.004. M4: MAE 0.291265.

**What rounds 3 and 4 established (use these).**

- Every alternative inside the anchor + graphite-step family failed (round 3: D0–D3, registration β, state-space fusion; round 4: denoised month-ends, dynamic crossings, rest pseudo-OCV, top-21-Ah features, start-corrected β).
- V2's remaining error is not step noise (within-segment residual SD 0.012–0.036 Ah).
- **CK2 is V2's largest error (+0.669 pp, i.e. loss under-predicted)** because segment 3 is missing. Round 3's rate-based gap fixes over-corrected badly (D1 −1.427 pp, D2 −1.049 pp): they extrapolated a *linear* rate measured in month 0, which includes first-month break-in.
- Post-checkup recovery grows from about 0.02 Ah (CK1) to about 0.87 Ah (CK7), τ ≈ 2.5 d. Proxies are post-recovery charges.

**Why this round.** Every model so far *reads* capacity from voltage signals. This round builds a model of a different class that *predicts* capacity loss from the stress history alone (time, cell temperature, throughput). It is self-calibrated on the pack's own anchors with a physics prior. It uses no graphite-step signal, so its errors are independent of V2's. The specific hypotheses:

- **H-A (CK2).** A sublinear time law (loss ∝ effective time^z, z < 1) calibrated on month 0 predicts a smaller month-1 loss than linear extrapolation. It should therefore fix part of CK2 without D1/D2's over-correction.
- **H-B (independence).** A fixed-weight average of the stress model and V2 lowers MAE because the two error sources are weakly correlated.
- **H-C (interpretability).** Calendar and cycle contributions, and the temperature acceleration, can be reported with uncertainty. This serves the 10 % interpretability and 10 % "technical innovation / use of open data" criteria.

**Exposure.** Every CK1–CK7 proxy value has been seen, so every result is **exposed-exploratory**. State this in every report, and never present proxies as hidden truth.

## 3. Code and data to reuse

- **Shared harness:** `research/phase2_round3_models_20261014/src/harness.py`.
  - It provides `run`, `metrics`, `per_ck`, `gates_vs_v2`, `candidate_checks`, `SCENARIOS` (`real`, `PG1`, `PG2`, `PC5`, `PC10`), `BASELINES` (M4, V2), `QFC`, `EPS0`, `cut_op`, `full_op`.
  - A predictor is `f(ctx) -> Q_hat_Ah` or `(Q_hat, info)`. `ctx` holds `k`, `at_date`, `ck`, `op` (cut operation data), `fc` (anchors), `steps`, `a4`, `eps`, `eps0`, `delta`, `scenario`, `key`.
  - Importing `harness` writes its cache under `research/phase2_round3_models_20261014/cache/` inside this worktree (git-ignored, private to this worktree). Your own caches go into the study's git-ignored `cache/`, with keys that include every parameter.
- **Event extraction:** `research/phase2_anchor_step_20261013/src/events.py` (`full_charges`, `segment_arrays`, `iter_segments`).
- **V2 functions:** `research/phase2_v2_phase_matched_20261013/src/v2.py` (`anchors_by_checkup`, `v2`, `m4`).
- **V2 reference class:** `research/phase2_v2_phase_matched_20261013/candidate_model/anchor_step_v2_model.py`.
- **Challenge 1 single-cell data (prior source).** Six 102 Ah prismatic LFP cells, continuous full-depth cycling: 25 °C 0.5C, 25 °C 1C, 35 °C 1C, 45 °C 0.5C, 45 °C 1C, 55 °C 1C. Raw files in `/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original/<cell>/` (multi-part `*_time_series_partNN.csv`). The Challenge 1 loader and SOH label definition are in `/Users/shane/Desktop/项目/Current State_Challenge1/` (`framework/`, `README.md` §2: SOH = max `step_capacity_Ah` in a cycle's `cc_discharge` step ÷ 102). Whether these cells are the same type as the pack cells is **not verified**; treat it as an assumption.
- **Literature prior.** Yagci et al. 2025, *J. Energy Storage* 124:116774, doi 10.1016/j.est.2025.116774 (180 Ah LFP/graphite; LLI dominated):
  - Arrhenius activation energy 37.3 ± 12.8 kJ/mol (95 % range);
  - after about 846–850 days: calendar loss 7.5 / 7.8 % at 35 °C (75 / 100 % SOC) and 13.3 / 14.0 % at 50 °C; cyclic loss (0.28C, full DoD, up to 1500 cycles) 11.0 % at 35 °C and 22.3 % at 50 °C.

  The full card is in `/Users/shane/Desktop/Arena 阶段 2 官方材料/research/phase2_literature_reassessment/outputs/LFP_SOH_核心论文精读与证据附册.md` §2. Do not download the 2.5 GB Zenodo archive.
- **Environment.** Research: `python3` (3.13, numpy/pandas/scipy/matplotlib). Candidate classes: numpy/pandas only, and they must also run in Python 3.11. Create a venv in the study's git-ignored `cache/venv311` from `/opt/homebrew/bin/python3.11` with `pip install numpy pandas`.

## 4. Rules carried over from earlier rounds

1. **No real results before the selection is committed.** Never compute or print real-data CK1–CK7 errors of a stage before its `protocol.json` is committed. A pseudo-cut at CK2 (PC5/PC10, k = 2) equals real CK2 data, so exclude k = 2 from any scenario used for a decision.
2. **Implement registered formulas exactly.** Register any deviation before running, or report it as a deviation.
3. **Cache keys contain every parameter** that changes the cached result.
4. **Causality checks compare exact floats** (future-noise and fit-on-prefix), not rounded output.
5. **6–7 anchors give diagnostics, not validation.** Word correlations that way.
6. **No artificial endpoints or invented data.** Every quantity in a hidden interval (missing segment, the part after a cutoff) is extrapolated by a registered rule from visible data and reported as extrapolated.

## 5. Evaluation rules

- **Proxies, scenarios, metrics.** Same as V2 and rounds 3–4: P_k = Q_fc,k + ε0 + Δ, Δ ∈ {0, 0.4, 0.8}; PG1/PG2 for k = 4..7; PC5/PC10 for k = 3..7 in decisions, k = 2..7 only in final reporting; MAE, MAX, RMSE per Δ; ε-free CK2–7 MAE; per-checkup errors.
- **Common gates against V2** (from `harness.gates_vs_v2`, plus G-pseudo and G-impl):

| Gate | Rule |
|---|---|
| G-causal | exact-float identity under future noise and fit-on-CK1-prefix |
| G-proxy | MAE < V2's MAE for every Δ, and MAX ≤ V2's MAX + 0.10 pp |
| G-epsfree | ε-free CK2–7 MAE ≤ V2's − 0.02 pp |
| G-robust | see per-model definition in stage 3 |
| G-pseudo | mean MAE over PG1, PG2, PC5, PC10 (k ≥ 3) not worse than V2's by more than 0.02 pp |
| G-regress | no checkup's absolute error grows by more than 0.30 pp against V2 (Δ = 0.4) |
| G-impl | a numpy/pandas-only class with the `MyModel` interface (`fit(dataset)`, `estimate_soh(dataset, at_date)`) reproduces the research implementation within 0.001 pp and passes the sample_data smoke test in the 3.11 venv |

- **Pre-registration.** Before any evaluation in a stage, write `stage_X/protocol.json` (main configuration, all variants, gates, selection rule), store its SHA256 in `stage_X/protocol.sha256`, and commit. Amend only before that stage's evaluation runs, with a reason. Never change the main configuration after seeing its results. The best variant is never reported as the main result.

## 6. Stages

### Stage 0 — Setup (cap 0.5 h)

- Create the study directory, `notes/STATUS.md`, `notes/DECISIONS.md`, `.gitignore` (`cache/`).
- Import the harness and confirm every cache write lands inside this worktree.
- Reproduce V2 (0.215726 / 0.669052 at Δ = 0.4) and M4 (0.291265) exactly. If either fails, stop the whole run and record why.

### Stage 1 — Stress-history extraction (cap 1 h; no proxy metric)

Write `src/stress.py` with a function `stress_table(op, until)` that returns, from visible rows only, one row per 10-s step (or per aggregated hour) with: time, cell temperature `temp_mean_C`, throughput, and a flag for observed / extrapolated / checkup.

- **Throughput definition (main).** Total throughput = Δ`charge_Ah_cum` + Δ`discharge_Ah_cum` between consecutive rows. Using the counters (not current integration) keeps the definition identical inside recording gaps and across segment 3. Report how it compares with ∫|I|dt on gap-free stretches.
- **Checkup intervals** (segment end → next segment start, which are not in the data): calendar time at an assumed 25 °C with zero throughput (main). Variant: an assumed 200 Ah at 25 °C per checkup (about two full cycles).
- **Hidden part of the current month.** Between the last visible row and the prediction horizon (below), extrapolate with a registered rule:
  - temperature: the chamber set point of the segment that is running at the cutoff, plus the mean (cell − chamber) offset of the last visible segment with the same set point;
  - throughput rate: the median Ah/day of the last 7 visible days at that set point.
- **Segment 3 at the CK2 cutoff.** The data description states that segment 3 is a 45 °C segment from 19 Feb to 11 Mar. Using this public schedule is allowed; record it in `DECISIONS.md`. Apply the same extrapolation rule (seg 1 supplies the 45 °C rate and offset). From the CK3 cutoff on, use the visible counter jump for its throughput, spread uniformly over its time span, with 45 °C (+ offset) as its temperature.
- **Prediction horizon.** The proxy for CK_k is the anchor charge after CK_k. Predict the state at `t*_k = CK_k date + L`, where L is the median of the visible (CK_j date → anchor j start) lags, j ≥ 1. If none is visible yet, use 3 days.
- **Audit outputs:**
  - per-month table of days and Ah at each temperature, observed vs extrapolated;
  - for k = 3..7, compare the extrapolated hidden part with what the full data later shows (PC5/PC10 analogue). This is the error of the extrapolation rule itself, not a model score.

### Stage 2 — Prior from Challenge 1 cells and literature (cap 1.5 h; no proxy metric)

**Model family (used here and in stage 3).** With T in K from cell temperature, T_ref = 298.15 K and a_T = exp[−Ea/R · (1/T − 1/T_ref)]:

- calendar loss: L_cal(t) = A_cal · (τ_eff(t))^z, with τ_eff(t) = ∫ a_T dt (days);
- cycle loss: L_cyc(t) = A_cyc · ∫ a_T dAh (Ah of throughput, linear);
- irreversible loss L = L_cal + L_cyc (Ah, on a 102 Ah cell).

**Fit to the six Challenge 1 cells.**

- Use each cell's own time axis (`absolute_time` or equivalent) and measured cell temperature. Express loss relative to the cell's median capacity over cycles 2–10.
- Use only data while relative capacity ≥ 85 % (the pack's range is about 98 → 90 %), so no knee enters the prior.
- Fit per cell, then jointly. Report:
  - z (time exponent) and its spread;
  - Ea from the temperature series;
  - A_cal and A_cyc, which are separated mainly by the 0.5C vs 1C pairs at 25 °C and 45 °C;
  - the posterior correlation between A_cal and A_cyc.
- These cells are tested at their own temperature and C-rate, so their labels mix reversible temperature effects with ageing. Say so, and use loss *ratios* or *rates* rather than absolute capacities when you build the prior.

**Prior for the pack** (`prior.json`, with provenance for each number):

- z ~ N(ẑ_C1, max(SD_C1, 0.1)²);
- Ea ~ N(Ea_C1 or 37.3 kJ/mol, 12.8/1.96 kJ/mol). Choose the Challenge 1 value only if its own 95 % interval is narrower than Yagci's, and record the choice;
- log A_cal and log A_cyc normal around the Challenge 1 values, SD = ln(3) each (weak, because the transfer is single cell → pack and continuous cycling → storage profile).

Sanity-check the prior against Yagci's published calendar and cyclic numbers at 35/50 °C; report agreement factors only. Commit `prior.json` before stage 3.

### Stage 3 — Pack model and registered evaluation (cap 2 h)

**Predictor S_main (register exactly).**

- At cutoff k, the visible anchors are j = 0..k−1. The fit data are the consecutive anchor pairs. Each pair gives ΔQ_obs,j = Q_fc,j − Q_fc,j−1 and the model ΔQ_mod,j = −[L(t_j) − L(t_j−1)], where t_j is the anchor charge start time.
- Pair (0 → 1) mixes a 45 °C anchor and a 25 °C anchor. Add one parameter o_45 (anchor 0's temperature offset in Q_fc) with prior N(0, 0.3²) Ah. It enters only that pair.
- Free parameters: log A_cal, log A_cyc and o_45. Fix z and Ea at their prior means.
- Fit by MAP: Gaussian likelihood with σ_pair = 0.20 Ah, plus the stage 2 priors.
- Prediction: Q̂_k = Q_fc,k−1 + ε − [L(t*_k) − L(t_k−1)]. With no pair (k = 1), parameters are the prior means.
- Integration origin: campaign start (first operating row). No pre-campaign age.

**Registered variants (reported, never promoted to main):**

1. z free with its prior (adds one parameter);
2. Ea at the prior mean ± 1 SD;
3. calendar only (A_cyc = 0) and cycle only (A_cal = 0);
4. z = 1 (linear law; the D1/D2 analogue, to test H-A directly);
5. pre-campaign age of 30 days at 25 °C;
6. checkup throughput 200 Ah (stage 1 variant);
7. σ_pair × 0.5 and × 2;
8. no prior on A (bounded MLE).

**Combined predictors (registered now, before any result):**

- **ENS50** = 0.5 · S_main + 0.5 · V2;
- **V2_Sfb** = V2, except that in V2's fallback branch (CK1–CK3) the prediction is S_main.

**G-robust definitions.**

- **S_main:** it does not use the step signal, so robustness is over the eight registered variants instead. It must beat V2's MAE (Δ = 0.4) in ≥ 6 of 8.
- **ENS50 and V2_Sfb:** V2's six step-detection variants, ≥ 5 of 6 wins (as in the harness).

**Order of work.**

1. Commit `stage_3/protocol.json`.
2. Run pseudo scenarios PG1, PG2, PC5 and PC10 (k ≥ 3) first and commit them.
3. Run the real scenario.
4. Compute all gates.

**Also report:**

- the fitted A_cal, A_cyc, o_45 per cutoff with posterior SDs;
- calendar vs cycle share of each month's predicted loss;
- the S_main − V2 error correlation over CK1–CK7 (a diagnostic only);
- the prior-only prediction (no anchors) for every checkup, to show how much the anchors move the model.

### Stage 4 — CK2 analysis (cap 0.5 h; descriptive, exposed)

Only after the stage 3 results are committed:

- For CK2, tabulate S_main, variant 4 (z = 1), V2, D1 (−1.427) and D2 (−1.049).
- Decompose S_main's CK2 prediction into: the observed month-1 part (segment 2), the extrapolated segment-3 part, and the checkup intervals.
- Report what segment 3 really contained once it is visible (counter jump, days). Use this only to measure the extrapolation error, never to tune.
- State plainly whether H-A is supported, refuted or inconclusive. CK2 is a single exposed point.

### Stage 5 — Final report and candidate (cap 1 h)

- **`FINAL_REPORT.md`** (bilingual, conclusions first):
  1. a table of S_main, every variant, ENS50, V2_Sfb, M4 and V2 (MAE per Δ, MAX, ε-free MAE, pseudo MAE, gates);
  2. per-checkup errors;
  3. the stage 1 and stage 2 audits;
  4. the fitted ageing law with uncertainty, as a figure: cumulative calendar and cycle loss over the campaign with the anchors overlaid;
  5. H-A / H-B / H-C verdicts;
  6. a leaderboard-only SOH table for S_main and ENS50 (CK1–CK7, rounded to 3 decimals), clearly labelled as not proxy-validated;
  7. risks: exposure; single pack; prior transfer from different cells and duty; collinearity of temperature and time in this schedule; the ε and recovery assumptions shared with V2;
  8. exact reproduction commands.
- **`README.md`** (bilingual).
- **Candidate class.** Only for a model that passes every gate: put it in `candidate_model/` with G-causal and G-impl evidence. Embed the prior as constants (no external files). Implement the MAP fit with numpy only (e.g. a damped Gauss–Newton); if the research used scipy, prove the numpy version matches within the G-impl tolerance. Nothing is wired into `my_model/`.

## 7. Order and caps

| Order | Stage | Cap |
|---|---|---|
| 0 | Setup + reproduce V2 | 0.5 h |
| 1 | Stress-history extraction (audit) | 1 h |
| 2 | Prior from Challenge 1 + literature | 1.5 h |
| 3 | Pack model, registered evaluation | 2 h |
| 4 | CK2 analysis | 0.5 h |
| 5 | Final report + candidate | 1 h |

**Stop rules.**

- If stage 0 cannot reproduce V2, stop everything.
- If stage 2 cannot fit any Challenge 1 cell, use the literature-only prior (Ea from Yagci, z ~ N(0.5, 0.15²), log A from a one-cell fit or, failing that, from the pack's anchor 0 → 1 pair with SD ln(10)). Record this, and label every later result "literature prior only".
- A candidate failing G-causal is rejected outright. A stage with no passing model is still a valid result.

## 8. Prohibitions (summary)

- **Causality.** No data after CK_k for CK_k. This covers thresholds, normalisation, rates, offsets, the horizon lag and selection. The public segment schedule is the only exception, and it is recorded.
- **Pre-registration.** No change of a registered main configuration after its results; no real-data results before the protocol commit; the best variant is never the main result.
- **Proxies.** Never present proxies as hidden truth; never reconstruct CK1–CK7 from external sources.
- **Files and git.** Do not edit the submission package, earlier studies, or the Challenge 1 data. Push only to this branch, never force-push, do not touch other checkouts.
- **No questions.** Never ask the user anything; record decisions and continue.

---

<a id="zh"></a>

# 第五轮 A：基于电池组自身锚点标定的应力历史老化模型——无人值守执行 Prompt

> **语言：** [English](#en) · 中文

编写日期：2026-10-14。本文自成一体。英文部分是执行文本，中文部分是给读者的翻译；两者不一致时以英文为准。另一份 prompt（第五轮 B，电极级模型）可以同时在另一个 worktree 里运行，两者互不共享任何东西。

## 0. 工作方式

- **无人值守运行。** 不要停下来提问。遇到未定的决策，选择遵守本文全部规则前提下最保守的方案，记入 `notes/DECISIONS.md`，然后继续。
- **上下文可能被压缩或重启。** 每一步之后都更新 `notes/STATUS.md`：阶段、已完成、下一步、最近一次提交。重启后先读 `notes/STATUS.md` 和 `notes/DECISIONS.md` 再接着做，不要重做已完成的阶段。
- **时间预算。** 全程约 7 小时，每个阶段有上限（第 7 节）。到上限时，把已有结果（包括"无定论"）写成报告、提交，然后进入下一阶段。
- **完成的标准**（必须全部满足）：
  1. 第 6 节每个阶段都已完成或到达上限，且 `notes/STATUS.md` 写明了这一点；
  2. 研究目录里有 `FINAL_REPORT.md` 和 `README.md`，双语、结论在前；
  3. 每份预登记协议的 `protocol.sha256` 都在其评估提交之前提交；
  4. 所有提交都已推送到 `origin exp/phase2-r5a-stress-model-20261014`；
  5. worktree 里 `git status` 没有未提交的研究文件。

## 1. 工作区、隔离与 git

- **worktree 与分支（已建好）。**
  - 只在 worktree `/Users/shane/Desktop/Arena_1014_r5a_stress` 的分支 `exp/phase2-r5a-stress-model-20261014` 上工作。该分支从 `exp/phase2-round4-signals-20261014` 的 `a6bc61f` 创建。
  - 不要 `cd` 到任何其他检出目录（`/Users/shane/Desktop/Arena_1013_model`、`Arena_1014_round4`、`Arena_1014_r5b_electrode` 或归档目录）。
  - 所有新工作放在 `research/phase2_r5a_stress_model_20261014/`（下称"研究目录"）。
- **并发防护。**
  - 开始时以及每次提交前，运行 `git log --oneline -5`，与自己最近一次提交对照。
  - 如果出现不是你做的提交，或有你没改过的已跟踪文件发生变化：停止编辑共享文件，记入 `notes/DECISIONS.md`，此后只按明确路径添加文件。
  - 不要使用 `git add -A` 或 `git add .`，不要撤销或改写别人的工作，不要使用裸 `git stash`。
- **提交与推送。**
  - 把本 prompt 作为第一个提交。
  - 每个阶段结束时提交，有意义的子步骤完成后也提交。
  - 每次阶段提交后运行 `git push -u origin exp/phase2-r5a-stress-model-20261014`。不要推送到其他地方，不要强制推送。
  - 提交信息结尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **不要修改：**
  - `TechArena_Challenge2_Team_Package/`（框架、`run_model.py`、`validate_submission.py`、`my_model/`、`data/`）；
  - 之前任何研究目录（`phase2_anchor_step_20261013`、`phase2_v2_phase_matched_20261013`、`phase2_round3_models_20261014`、`phase2_round4_signals_20261014`）；
  - Challenge 1 数据 `/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original/` 和 Challenge 1 项目 `/Users/shane/Desktop/项目/Current State_Challenge1/`（只读）。

  可以导入或阅读它们的代码，但不要编辑。
- **文档语言。** 你写的每个 Markdown 文档都是英文在前、中文在后，格式与本文件相同（`<a id="en"></a>`、语言切换行、`---`、`<a id="zh"></a>`）。代码注释和 docstring 只用英文。
- **字节码。** 用 `python3 -B` 运行 Python。

## 2. 任务、现状与本轮的理由

**任务（TechArena 2026 Challenge 2）。** 估计 4 × 102 Ah LFP 串联电池组在每个检查日的 SOH。

- **目标量。** SOH = C/20 容量 ÷ 102 Ah。C/20 容量是满充后以 5.1 A 放电、直到组端电压首次达到 11.2 V 时放出的 Ah。
- **标签。** 只公开 CK0 = 100.41 Ah；CK1–CK7 隐藏，用于评分（多项误差指标，含最差误差，各自除以官方基线归一）。
- **检查日：** CK0 2025-01-14，CK1 02-08，CK2 03-11，CK3 04-14，CK4 05-16，CK5 06-16，CK6 07-25，CK7 08-28。
- **因果截断。** 预测 CK_k 只能用 `load_dataset(data, until=CK_k)`，截断点是该日 00:00。

**数据与日程（2026-10-14 已核实）。**

| 月份 m（CK_m → CK_m+1） | 25 °C 段 | 45 °C 段 |
|---|---|---|
| 0（CK0 → CK1） | 无 | 第 1 段，01-19 → 02-08 |
| 1（CK1 → CK2） | 第 2 段，02-11 → 02-19 | 第 3 段，02-19 → 03-11，**缺失** |
| 2（CK2 → CK3） | 第 4 段，03-14 → 03-22 | 第 5 段，03-23 → 04-13 |
| 3 | 第 6 段，04-16 → 04-25 | 第 7 段，04-25 → 05-15 |
| 4 | 第 8 段，05-19 → 05-26 | 第 9 段，05-26 → 06-16 |
| 5 | 第 10 段，06-21 → 07-02 | 第 11 段，07-03 → 07-22 |
| 6 | 第 12 段，07-28 → 08-07 | 第 13 段，08-08 → 08-28 |
| CK7 之后 | 第 14 段，09-01 → 09-11 | — |

- 10 s 采样。列：`timestamp`、`elapsed_s`、`segment`、`chamber_temperature_C`、`current_A`（充电为正）、`charge_Ah_cum`、`discharge_Ah_cum`、`cell1_V`..`cell4_V`、`pack_voltage_V`、`temp_mean_C`/`min`/`max`。45 °C 段平均芯温约 46 °C，25 °C 段约 25.6 °C。
- Ah 计数器跨记录缺口和第 3 段连续累计，但不计检查期间的吞吐。第 3 段的计数器跳变要等第 4 段可见时才看得到，也就是在 CK2 截断**之后**。
- 每个 45 °C 段约充入 1600 Ah，每个 25 °C 段约 600–900 Ah。
- 月与月之间的缺口就是检查（2–6 天）。

**锚点。** 每次检查之后，电池组静置 2 h、从近空（组压约 11.6–12.0 V）开始，以约 20 A 恒流充电，再在 14.0 V 恒压到 5.1 A。充入的 Ah `Q_fc,j`（来自 `events.full_charges`）就是锚点 j。锚点 0 在第 1 段、45 °C；锚点 1–7 在 25 °C 段 2、4、6、8、10、12、14，在 CK_j 之后 2–5 天。

**当前领先候选：V2**（`research/phase2_v2_phase_matched_20261013/src/v2.py`）。分支 `exp/phase2-anchor-step-20261013` 上的提交包目前指向 V2（提交 `1f7deb3`），不要动它。

- Q_anchor = Q_fc + ε，ε = ε0 + Δ，ε0 = 100.41 − Q_fc,0。
- 月内更新用 45 °C 石墨台阶深度的同相位差分，乘物理 β（1.06–1.51）；CK1–CK3 回退到 M4。
- **代理结果**（代理 P_k = Q_fc,k + ε0 + Δ，Δ = 0.4）：MAE **0.215726 pp**，MAX **0.669052 pp**（CK2）。各检查点：CK1 +0.217、CK2 +0.669、CK3 +0.080、CK4 +0.228、CK5 +0.150、CK6 −0.163、CK7 −0.004。M4：MAE 0.291265。

**第三、四轮已确立的结论（要用上）。**

- 锚点 + 石墨台阶框架内的所有替代方案都失败了（第三轮：D0–D3、配准 β、状态空间融合；第四轮：月末去噪、动态越台阶、静置伪 OCV、顶部 21 Ah 特征、起点修正 β）。
- V2 的剩余误差不是台阶噪声（段内残差 SD 0.012–0.036 Ah）。
- **CK2 是 V2 最大的误差（+0.669 pp，即损失预测偏小）**，原因是第 3 段缺失。第三轮基于速率的缺口外推严重过度修正（D1 −1.427 pp，D2 −1.049 pp）：它们外推的是在第 0 月测得的*线性*速率，而第 0 月包含首月磨合。
- 检查后恢复从 CK1 的约 0.02 Ah 增长到 CK7 的约 0.87 Ah，τ ≈ 2.5 天。代理是恢复之后的充电量。

**为什么做本轮。** 目前所有模型都是从电压信号里*读出*容量。本轮建一个不同类别的模型：只从应力历史（时间、芯温、吞吐）*预测*容量损失，用物理先验，并以电池组自身的锚点标定。它不用石墨台阶信号，所以误差与 V2 相互独立。具体假设：

- **H-A（CK2）。** 用第 0 月标定的次线性时间律（损失 ∝ 等效时间^z，z < 1）对第 1 月预测的损失比线性外推小，因此应能修正一部分 CK2，而不像 D1/D2 那样过度修正。
- **H-B（独立性）。** 应力模型与 V2 的固定权重平均能降低 MAE，因为两者的误差来源相关性弱。
- **H-C（可解释性）。** 日历与循环贡献、温度加速都能带不确定度报告。这对应评分中各占 10 % 的可解释性和"技术创新 / 使用开放数据"。

**曝光。** 所有 CK1–CK7 代理值都已看过，所以每个结果都是**已曝光的探索性结果**。每份报告都要写明，并且绝不把代理当成隐藏真值。

## 3. 可复用的代码与数据

- **共享评估框架：** `research/phase2_round3_models_20261014/src/harness.py`。
  - 提供 `run`、`metrics`、`per_ck`、`gates_vs_v2`、`candidate_checks`、`SCENARIOS`（`real`、`PG1`、`PG2`、`PC5`、`PC10`）、`BASELINES`（M4、V2）、`QFC`、`EPS0`、`cut_op`、`full_op`。
  - 预测器是 `f(ctx) -> Q_hat_Ah` 或 `(Q_hat, info)`。`ctx` 含 `k`、`at_date`、`ck`、`op`（截断后的运行数据）、`fc`（锚点）、`steps`、`a4`、`eps`、`eps0`、`delta`、`scenario`、`key`。
  - 导入 `harness` 会把缓存写到本 worktree 里的 `research/phase2_round3_models_20261014/cache/`（被 git 忽略、本 worktree 私有）。你自己的缓存放在研究目录被忽略的 `cache/` 下，键名包含所有参数。
- **事件提取：** `research/phase2_anchor_step_20261013/src/events.py`（`full_charges`、`segment_arrays`、`iter_segments`）。
- **V2 函数：** `research/phase2_v2_phase_matched_20261013/src/v2.py`（`anchors_by_checkup`、`v2`、`m4`）。
- **V2 参考类：** `research/phase2_v2_phase_matched_20261013/candidate_model/anchor_step_v2_model.py`。
- **Challenge 1 单芯数据（先验来源）。** 六枚 102 Ah 方形 LFP 电芯，连续满深度循环：25 °C 0.5C、25 °C 1C、35 °C 1C、45 °C 0.5C、45 °C 1C、55 °C 1C。原始文件在 `/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original/<cell>/`（分卷 `*_time_series_partNN.csv`）。Challenge 1 的加载器和 SOH 标签定义在 `/Users/shane/Desktop/项目/Current State_Challenge1/`（`framework/`，`README.md` 第 2 节：SOH = 一个循环 `cc_discharge` 步中 `step_capacity_Ah` 的最大值 ÷ 102）。这些电芯是否与电池组电芯同型号**未经核实**，按假设处理。
- **文献先验。** Yagci 等 2025，*J. Energy Storage* 124:116774，doi 10.1016/j.est.2025.116774（180 Ah LFP/石墨；LLI 主导）：
  - Arrhenius 活化能 37.3 ± 12.8 kJ/mol（95 % 范围）；
  - 约 846–850 天后：日历损失 35 °C 时 7.5 / 7.8 %（75 / 100 % SOC），50 °C 时 13.3 / 14.0 %；循环损失（0.28C、满 DoD、最多 1500 次）35 °C 时 11.0 %，50 °C 时 22.3 %。

  完整卡片见 `/Users/shane/Desktop/Arena 阶段 2 官方材料/research/phase2_literature_reassessment/outputs/LFP_SOH_核心论文精读与证据附册.md` 第 2 节。不要下载 2.5 GB 的 Zenodo 压缩包。
- **环境。** 研究用 `python3`（3.13，numpy/pandas/scipy/matplotlib）。候选类只用 numpy/pandas，且必须能在 Python 3.11 下运行：在研究目录被忽略的 `cache/venv311` 里，用 `/opt/homebrew/bin/python3.11` 建 venv，`pip install numpy pandas`。

## 4. 沿用自前几轮的规则

1. **选择提交之前不得出真实结果。** 某阶段的 `protocol.json` 提交之前，不得计算或打印真实数据上 CK1–CK7 的误差。CK2 处的伪截断（PC5/PC10，k = 2）与真实 CK2 数据相同，因此任何用于决策的场景都要排除 k = 2。
2. **严格按登记的公式实现。** 偏离要在运行前登记，否则作为偏离报告。
3. **缓存键必须包含**所有会改变缓存结果的参数。
4. **因果检查比较精确浮点数**（未来加噪与前缀拟合），不能只比四舍五入后的输出。
5. **6–7 个锚点只能给出诊断，不是验证。** 相关性要这样措辞。
6. **不得人造端点或编造数据。** 隐藏区间（缺失段、截断之后的部分）里的每个量，都按登记的规则从可见数据外推，并标明是外推值。

## 5. 评估规则

- **代理、场景、指标。** 与 V2 和第三、四轮相同：P_k = Q_fc,k + ε0 + Δ，Δ ∈ {0, 0.4, 0.8}；PG1/PG2 用 k = 4..7；PC5/PC10 在决策中用 k = 3..7，只在最终报告中用 k = 2..7；每个 Δ 下的 MAE、MAX、RMSE；与 ε 无关的 CK2–7 MAE；各检查点误差。
- **对 V2 的通用门槛**（来自 `harness.gates_vs_v2`，另加 G-pseudo 和 G-impl）：

| 门槛 | 规则 |
|---|---|
| G-causal | 未来数据加噪、仅用 CK1 前缀拟合时，输出的浮点数完全一致 |
| G-proxy | 每个 Δ 下 MAE 都低于 V2，且 MAX ≤ V2 的 MAX + 0.10 pp |
| G-epsfree | 与 ε 无关的 CK2–7 MAE ≤ V2 的值 − 0.02 pp |
| G-robust | 见第 3 阶段中各模型的定义 |
| G-pseudo | PG1、PG2、PC5、PC10（k ≥ 3）的平均 MAE 比 V2 差不超过 0.02 pp |
| G-regress | 任何检查点的绝对误差相对 V2 的增幅不超过 0.30 pp（Δ = 0.4） |
| G-impl | 只依赖 numpy/pandas、接口为 `MyModel`（`fit(dataset)`、`estimate_soh(dataset, at_date)`）的类，与研究实现相差 ≤ 0.001 pp，并在 3.11 venv 中通过 sample_data 冒烟测试 |

- **预登记。** 每个阶段在任何评估之前写 `stage_X/protocol.json`（主配置、所有变体、门槛、选择规则），把 SHA256 存进 `stage_X/protocol.sha256` 并提交。只能在该阶段评估运行之前修订，并写明理由。看到结果之后不得更改主配置。最佳变体永远不能作为主结果报告。

## 6. 各阶段

### 第 0 阶段——准备（上限 0.5 小时）

- 建研究目录、`notes/STATUS.md`、`notes/DECISIONS.md`、`.gitignore`（`cache/`）。
- 导入 harness，确认所有缓存写入都落在本 worktree 内。
- 精确复现 V2（Δ = 0.4 时 0.215726 / 0.669052）和 M4（0.291265）。任何一个复现不了，就停止整轮并记录原因。

### 第 1 阶段——应力历史提取（上限 1 小时；不算代理指标）

写 `src/stress.py`，提供函数 `stress_table(op, until)`，只用可见行，每个 10 s 步（或每小时聚合）输出一行：时间、芯温 `temp_mean_C`、吞吐量，以及"观测 / 外推 / 检查"标记。

- **吞吐量定义（主配置）。** 总吞吐 = 相邻两行之间的 Δ`charge_Ah_cum` + Δ`discharge_Ah_cum`。用计数器而不是电流积分，记录缺口内和跨第 3 段时定义都完全一致。报告它在无缺口区段上与 ∫|I|dt 的对比。
- **检查区间**（数据中不存在的"段末 → 下一段开始"）：按假定 25 °C 计日历时间、吞吐为零（主配置）。变体：每次检查假定 25 °C 下 200 Ah（约两个满循环）。
- **当月的隐藏部分。** 最后一个可见行到预测时点（见下）之间，按登记的规则外推：
  - 温度：截断时正在运行那一段的箱温设定值，加上最近一个同设定值可见段的平均（芯温 − 箱温）偏差；
  - 吞吐速率：该设定值下最近 7 个可见日的 Ah/天中位数。
- **CK2 截断时的第 3 段。** 数据说明写明第 3 段是 2 月 19 日至 3 月 11 日的 45 °C 段。使用这个公开日程是允许的，记入 `DECISIONS.md`。外推规则同上（由第 1 段提供 45 °C 的速率和偏差）。从 CK3 截断起，第 3 段的吞吐用可见的计数器跳变，按其时间跨度均匀分配，温度取 45 °C（+ 偏差）。
- **预测时点。** CK_k 的代理是 CK_k 之后的锚点充电，所以预测 `t*_k = CK_k 日期 + L` 时刻的状态。L 是可见的（CK_j 日期 → 锚点 j 开始）滞后的中位数（j ≥ 1）。尚无可见滞后时用 3 天。
- **审计输出：**
  - 每月在各温度下的天数和 Ah，分观测与外推；
  - 对 k = 3..7，把外推的隐藏部分与完整数据后来显示的情况对比（类似 PC5/PC10）。这是外推规则本身的误差，不是模型得分。

### 第 2 阶段——由 Challenge 1 电芯和文献构建先验（上限 1.5 小时；不算代理指标）

**模型族（本阶段和第 3 阶段共用）。** T 取芯温（K），T_ref = 298.15 K，a_T = exp[−Ea/R · (1/T − 1/T_ref)]：

- 日历损失：L_cal(t) = A_cal · (τ_eff(t))^z，其中 τ_eff(t) = ∫ a_T dt（天）；
- 循环损失：L_cyc(t) = A_cyc · ∫ a_T dAh（吞吐 Ah，线性）；
- 不可逆损失 L = L_cal + L_cyc（Ah，按 102 Ah 电芯计）。

**拟合六枚 Challenge 1 电芯。**

- 用每枚电芯自己的时间轴（`absolute_time` 或等价列）和实测芯温。损失相对于该电芯第 2–10 循环容量的中位数表示。
- 只用相对容量 ≥ 85 % 的数据（电池组的范围约为 98 → 90 %），这样先验里不含拐点。
- 先逐芯拟合，再联合拟合。报告：
  - z（时间指数）及其离散程度；
  - 由温度序列得到的 Ea；
  - A_cal 和 A_cyc，二者主要靠 25 °C 和 45 °C 下 0.5C 与 1C 的配对分开；
  - A_cal 与 A_cyc 的后验相关。
- 这些电芯在各自的温度和倍率下测试，所以标签里混有可逆的温度效应和老化。要写明这一点；构建先验时用损失的*比值*或*速率*，而不是绝对容量。

**电池组的先验**（`prior.json`，每个数字都注明来源）：

- z ~ N(ẑ_C1, max(SD_C1, 0.1)²)；
- Ea ~ N(Ea_C1 或 37.3 kJ/mol, 12.8/1.96 kJ/mol)。只有当 Challenge 1 自身的 95 % 区间比 Yagci 的更窄时才用 Challenge 1 的值，并记录选择；
- log A_cal 和 log A_cyc 以 Challenge 1 的值为中心的正态分布，SD 各为 ln(3)（弱先验，因为迁移跨越了单芯 → 电池组、连续循环 → 储能工况）。

用 Yagci 公布的 35/50 °C 日历和循环数字对先验做合理性检查，只报告吻合倍数。第 3 阶段之前提交 `prior.json`。

### 第 3 阶段——电池组模型与预登记评估（上限 2 小时）

**预测器 S_main（严格按此登记）。**

- 截断 k 时，可见锚点为 j = 0..k−1。拟合数据是相邻锚点对。每对给出 ΔQ_obs,j = Q_fc,j − Q_fc,j−1，模型给出 ΔQ_mod,j = −[L(t_j) − L(t_j−1)]，t_j 为锚点充电开始时刻。
- 锚点对 (0 → 1) 混合了一个 45 °C 锚点和一个 25 °C 锚点。加一个参数 o_45（锚点 0 的 Q_fc 温度偏差），先验 N(0, 0.3²) Ah，只进入这一对。
- 自由参数：log A_cal、log A_cyc 和 o_45。z 与 Ea 固定为先验均值。
- 用 MAP 拟合：高斯似然，σ_pair = 0.20 Ah，加第 2 阶段的先验。
- 预测：Q̂_k = Q_fc,k−1 + ε − [L(t*_k) − L(t_k−1)]。没有锚点对时（k = 1），参数取先验均值。
- 积分起点：试验开始（第一行运行数据），不计试验前的老化。

**登记的变体（只报告，不升为主配置）：**

1. z 自由，带先验（多一个参数）；
2. Ea 取先验均值 ± 1 SD；
3. 只有日历项（A_cyc = 0）与只有循环项（A_cal = 0）；
4. z = 1（线性律，相当于 D1/D2，直接检验 H-A）；
5. 试验前已在 25 °C 老化 30 天；
6. 检查吞吐 200 Ah（第 1 阶段的变体）；
7. σ_pair × 0.5 和 × 2；
8. A 不加先验（有界极大似然）。

**组合预测器（现在就登记，在任何结果之前）：**

- **ENS50** = 0.5 · S_main + 0.5 · V2；
- **V2_Sfb** = V2，但在 V2 的回退分支（CK1–CK3）中改用 S_main。

**G-robust 的定义。**

- **S_main：** 它不用台阶信号，所以稳健性改为在 8 个登记变体上考察：至少 6/8 个变体的 MAE（Δ = 0.4）优于 V2。
- **ENS50 和 V2_Sfb：** 在 V2 的 6 种台阶检测方法上，至少 5/6 胜出（与 harness 相同）。

**工作顺序。**

1. 提交 `stage_3/protocol.json`。
2. 先跑伪场景 PG1、PG2、PC5、PC10（k ≥ 3）并提交。
3. 再跑真实场景。
4. 计算全部门槛。

**另外报告：**

- 每个截断下拟合的 A_cal、A_cyc、o_45 及后验 SD；
- 每月预测损失中日历与循环各占的份额；
- CK1–CK7 上 S_main 与 V2 误差的相关（仅作诊断）；
- 每个检查点的纯先验预测（不用锚点），以显示锚点把模型拉动了多少。

### 第 4 阶段——CK2 分析（上限 0.5 小时；描述性，已曝光）

只有在第 3 阶段结果提交之后才能做：

- 对 CK2 列表比较 S_main、变体 4（z = 1）、V2、D1（−1.427）、D2（−1.049）。
- 把 S_main 的 CK2 预测分解为：第 1 月的观测部分（第 2 段）、外推的第 3 段部分、检查区间。
- 第 3 段可见之后，报告它实际包含什么（计数器跳变、天数）。只用它衡量外推误差，绝不用来调参。
- 明确写出 H-A 是被支持、被否定还是无定论。CK2 只是一个已曝光的点。

### 第 5 阶段——最终报告与候选（上限 1 小时）

- **`FINAL_REPORT.md`**（双语，结论在前）：
  1. 一张表，列出 S_main、每个变体、ENS50、V2_Sfb、M4 和 V2（各 Δ 的 MAE、MAX、与 ε 无关的 MAE、伪场景 MAE、门槛）；
  2. 各检查点误差；
  3. 第 1、2 阶段的审计；
  4. 拟合出的老化律及其不确定度，配一张图：整个试验期间累计的日历损失和循环损失，叠加锚点；
  5. H-A / H-B / H-C 的结论；
  6. 只用于排行榜的 S_main 和 ENS50 SOH 表（CK1–CK7，保留 3 位小数），明确标注未经代理验证；
  7. 风险：曝光；单个电池组；先验从不同电芯和工况迁移；本日程中温度与时间共线；与 V2 共有的 ε 和恢复假设；
  8. 精确的复现命令。
- **`README.md`**（双语）。
- **候选类。** 只对通过所有门槛的模型，在 `candidate_model/` 下给出候选类，附 G-causal 和 G-impl 证据。先验以常量嵌入（不读外部文件）。MAP 拟合只用 numpy 实现（例如阻尼 Gauss–Newton）；如果研究中用了 scipy，要证明 numpy 版本在 G-impl 容差内与之一致。不接入 `my_model/`。

## 7. 顺序与上限

| 顺序 | 阶段 | 上限 |
|---|---|---|
| 0 | 准备 + 复现 V2 | 0.5 小时 |
| 1 | 应力历史提取（审计） | 1 小时 |
| 2 | 由 Challenge 1 + 文献构建先验 | 1.5 小时 |
| 3 | 电池组模型，预登记评估 | 2 小时 |
| 4 | CK2 分析 | 0.5 小时 |
| 5 | 最终报告 + 候选 | 1 小时 |

**停止规则。**

- 第 0 阶段复现不了 V2，就停止一切。
- 如果第 2 阶段一枚 Challenge 1 电芯都拟合不了，就用纯文献先验（Ea 取 Yagci，z ~ N(0.5, 0.15²)，log A 取单芯拟合；若也不行，就取电池组锚点对 0 → 1，SD 为 ln(10)）。记录这一点，此后每个结果都标注"仅文献先验"。
- 未通过 G-causal 的候选直接拒绝。没有任何模型通过的阶段同样是有效结果。

## 8. 禁止事项（汇总）

- **因果性。** 预测 CK_k 不得用 CK_k 之后的数据，包括阈值、归一化、速率、偏差、预测时点滞后和选择。公开的分段日程是唯一例外，并已记录。
- **预登记。** 看到结果后不得更改登记的主配置；协议提交之前不得出真实数据结果；最佳变体永远不作为主结果。
- **代理。** 绝不把代理当成隐藏真值；绝不从外部来源重建 CK1–CK7。
- **文件与 git。** 不修改提交包、之前的研究和 Challenge 1 数据。只推送到本分支，不强制推送，不碰其他检出目录。
- **不提问。** 绝不向用户提问；记录决策并继续。
