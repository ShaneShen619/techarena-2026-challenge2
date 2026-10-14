<a id="en"></a>

# Round 5B: Electrode-Level Degradation-Mode Model — Unattended Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-14. This document is self-contained. The English text is the execution text; the Chinese section is a translation for the reader, and if they differ the English governs. A separate prompt (round 5A, stress-history model) may run at the same time in another worktree; it shares nothing with this run.

## 0. Mode of work

- **Unattended run.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Context may be compacted or restarted.** Keep `notes/STATUS.md` current after every step: stage, done, next, last commit. On restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume. Never redo a finished stage.
- **Time budget.** About 8 hours in total, with a cap per stage (§7). At a cap, write up what exists (including "inconclusive"), commit, and move on.
- **Done means** (all must hold):
  1. every stage in §6 is finished, capped or skipped by a registered exit rule, and `notes/STATUS.md` says which;
  2. `FINAL_REPORT.md` and `README.md` exist in the study directory, bilingual, conclusions first;
  3. every registered protocol has its `protocol.sha256` committed before its evaluation commit;
  4. every commit is pushed to `origin exp/phase2-r5b-electrode-model-20261014`;
  5. `git status` in the worktree shows no uncommitted study files.

## 1. Workspace, isolation and git

- **Worktree and branch (already created).**
  - Work only in the worktree `/Users/shane/Desktop/Arena_1014_r5b_electrode`, on branch `exp/phase2-r5b-electrode-model-20261014`. It starts from `exp/phase2-round4-signals-20261014` at `a6bc61f`.
  - Never `cd` into any other checkout (`/Users/shane/Desktop/Arena_1013_model`, `Arena_1014_round4`, `Arena_1014_r5a_stress`, or the archive).
  - All new work goes into `research/phase2_r5b_electrode_model_20261014/` (the "study directory").
- **Concurrency guard.**
  - At the start and before every commit, run `git log --oneline -5` and compare with your own last commit.
  - If a commit you did not make appears, or a tracked file changes that you did not change: stop editing shared files, record it in `notes/DECISIONS.md`, and only add files by explicit path from then on.
  - Never use `git add -A` or `git add .`, never revert or rewrite someone else's work, never use bare `git stash`.
- **Commits and pushes.**
  - Commit this prompt as the first commit.
  - Commit at the end of every stage and after meaningful sub-steps.
  - After each stage commit, run `git push -u origin exp/phase2-r5b-electrode-model-20261014`. Never push anywhere else, and never force-push.
  - Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify:**
  - `TechArena_Challenge2_Team_Package/` (framework, `run_model.py`, `validate_submission.py`, `my_model/`, `data/`);
  - any earlier study directory (`phase2_anchor_step_20261013`, `phase2_v2_phase_matched_20261013`, `phase2_round3_models_20261014`, `phase2_round4_signals_20261014`).

  Import their code; do not edit it.
- **Document language.** Every Markdown document you write is English first, Chinese second, in the same layout as this file (`<a id="en"></a>`, language line, `---`, `<a id="zh"></a>`). Code comments and docstrings are English only.
- **Bytecode.** Run Python with `python3 -B`.

## 2. Task, current state and why this round exists

**Task (TechArena 2026 Challenge 2).** Estimate the SOH of a 4 × 102 Ah LFP series pack on each checkup date.

- **Target.** SOH = C/20 capacity ÷ 102 Ah. The C/20 capacity is the Ah from a 5.1 A discharge after a full charge, until the pack voltage first reaches 11.2 V.
- **Labels.** Only CK0 = 100.41 Ah is released. CK1–CK7 are hidden and scored (several error metrics including the worst case, each normalised by the official baseline).
- **Checkup dates:** CK0 2025-01-14, CK1 02-08, CK2 03-11, CK3 04-14, CK4 05-16, CK5 06-16, CK6 07-25, CK7 08-28.
- **Causal cut.** A prediction for CK_k may use only `load_dataset(data, until=CK_k)`, which cuts at 00:00 of that date.

**Data (verified 2026-10-14).**

- 13 operating segments at 10-s sampling. Segment 1 is 45 °C (01-19 → 02-08). After that, each month is a short 25 °C segment followed by a long 45 °C segment. Segment 3 (45 °C, 02-19 → 03-11) is missing.
- Columns: `timestamp`, `elapsed_s`, `segment`, `chamber_temperature_C`, `current_A` (+ charge), `charge_Ah_cum`, `discharge_Ah_cum`, `cell1_V`..`cell4_V`, `pack_voltage_V`, `temp_mean_C`/`min`/`max`.
- The counters book the 20 A pulse as charge, so integrate `current_A` over real time steps; do not integrate Δt > 600 s or Δt ≤ 0.
- **CK0 reference discharge** (`data/checkups/CK0_reference_discharge.csv.gz`, recorded 2025-01-15): constant 5.1 A, columns `timestamp`, `current_A`, `voltage_V`, `cell1_V`..`cell4_V`, `discharged_Ah`. The four-cell voltage sum ends at 11.203 V. Round 3's bounded extension puts the pack 11.2 V root at 100.416854 Ah. There is no temperature column; assume 25 °C and record that.

**Anchors (the main data for this round).** After each checkup the pack is charged from near empty (pack ≈ 11.6–12.0 V after a 2 h rest) at about 20 A CC, then CV at 14.0 V down to 5.1 A. Each such charge carries about 95 Ah, with per-cell voltages at 10 s, and crosses the graphite staging step in the charge direction. Anchor 0 is in segment 1 at 45 °C (2025-01-19). Anchors 1–7 are at 25 °C in segments 2, 4, 6, 8, 10, 12, 14, two to five days after CK_j. These are the only full-range curves in the campaign; round 3 and round 4 showed that no other event reaches the step region from the top except the ~5-day program discharges (~10 A, from the CV end, crossing the step at 45 °C).

**Current leading candidate: V2** (`research/phase2_v2_phase_matched_20261013/src/v2.py`). The submission package on branch `exp/phase2-anchor-step-20261013` currently points to V2 (commit `1f7deb3`); do not touch it.

- Q_anchor = Q_fc + ε, ε = ε0 + Δ, ε0 = 100.41 − Q_fc,0.
- In-month update: Q̂ = Q_anchor(k−1) + β_k·[E45(k−1) − E45(k−2) + r·(d(k−1) − d(k−2))]. E45 is the last 45 °C program-discharge step depth of a month.
- β_k is an *empirical* ratio. Only 68–79 % of the anchor-to-anchor loss shows up in the charge-side step → top distance, so β > 1 (1.06–1.51 as fitted; CK7's 1.51 is above the whole-campaign ratio range).
- ε is an *assumed constant*. It maps the operating anchor charge (20 A CC + CV, charge direction) onto the C/20 discharge to pack 11.2 V.
- CK1–CK3 fall back to M4.
- **Proxy result** (proxy P_k = Q_fc,k + ε0 + Δ, Δ = 0.4): MAE **0.215726 pp**, MAX **0.669052 pp** (CK2). Per checkup: CK1 +0.217, CK2 +0.669, CK3 +0.080, CK4 +0.228, CK5 +0.150, CK6 −0.163, CK7 −0.004. M4: MAE 0.291265.

**What rounds 3 and 4 established (use these).**

- **Round 3 A** registered each anchor charge against a template with two phenomenological scales (bottom and top) and was rejected (MAE 0.242, zero robustness wins).
  - With the voltage nuisance bounded, bottom/top/voltage were identifiable in only 40 % / 80 % / 20 % of fits.
  - The bottom-section change correlated with the start voltage (r = −0.975): the start state is a confounder.
- **Round 3 E** mapped causal per-cell charge maps onto the CK0 discharge. Of 105 cases, 90 had finite 11.2 V roots, with max |ε − ε0| = 0.023 pp; 15 roots were unavailable, so the result is inconclusive.
- **Round 4** showed that V2's remaining error is not step noise.
  - Post-checkup recovery grows to about 0.87 Ah by CK7 (τ ≈ 2.5 d). The proxies are post-recovery charges.
  - ε and the recovery state dominate the real-score uncertainty, and proxies cannot test them.

**Why this round.** Earlier registration models scaled an empirical template. This round uses a **physical electrode model**: literature half-cell open-circuit potentials (OCPs) for LFP and graphite, with per-cell stoichiometric alignment. It replaces two empirical pieces of V2 with mechanistic quantities:

- **β_E**: the ratio d(full-charge Ah) / d(program-step depth) along the fitted degradation direction (LLI / LAM_NE / LAM_PE). Proxy-testable.
- **ε_E**: the model's mapping from the anchor charge to the C/20 discharge to pack 11.2 V, per anchor. Leaderboard-only, because proxies share V2's ε assumption.
- **Diagnostics**: per-cell LLI, LAM_NE and LAM_PE trajectories, and which cell limits the pack at 11.2 V at each checkup. These serve the interpretability and innovation criteria (10 % each).

You do not need to identify every electrode parameter. It is enough if all parameter sets that fit the data agree on the target quantities (Q_C20, β_E). The audits are built around that.

**Exposure.** Every CK1–CK7 proxy value has been seen, so every result is **exposed-exploratory**. State this in every report, and never present proxies as hidden truth.

## 3. Code and data to reuse

- **Shared harness:** `research/phase2_round3_models_20261014/src/harness.py`.
  - It provides `run`, `metrics`, `per_ck`, `gates_vs_v2`, `candidate_checks`, `SCENARIOS` (`real`, `PG1`, `PG2`, `PC5`, `PC10`), `BASELINES` (M4, V2), `QFC`, `EPS0`, `cut_op`, `full_op`.
  - A predictor is `f(ctx) -> Q_hat_Ah` or `(Q_hat, info)`. `ctx` holds `k`, `at_date`, `ck`, `op`, `fc`, `steps`, `step`, `a4`, `a4s`, `eps`, `eps0`, `delta`, `scenario`, `key`.
  - Importing `harness` writes its cache under `research/phase2_round3_models_20261014/cache/` inside this worktree (git-ignored, private). Your own caches go into the study's git-ignored `cache/`, with keys that include every parameter.
- **Event extraction:** `research/phase2_anchor_step_20261013/src/events.py`:
  - `full_charges` gives the anchor rows with `_seg_index` (start and end row in the segment);
  - `step_programs`, `STEP_VARIANTS` and `_locate` (midpoint-crossing and dV/dQ-peak step location);
  - `charge_step_split` (charge-side bottom → step and step → top);
  - `ck0_reference_step`;
  - `segment_arrays`.
- **V2 functions:** `research/phase2_v2_phase_matched_20261013/src/v2.py` (`anchors_by_checkup`, `month_steps`, `end45`, `phase_diff`, `beta_a4`, `shrink`, `m4`, `v2`). The V2 reference class is `research/phase2_v2_phase_matched_20261013/candidate_model/anchor_step_v2_model.py`.
- **Round 3 mapping code** (`research/phase2_round3_models_20261014/stage_E/`) shows how per-cell maps and the first 11.2 V root were computed. Read it before writing your own root finder, and follow rule 1 in §4.
- **Literature background** (cards in `/Users/shane/Desktop/Arena 阶段 2 官方材料/research/phase2_literature_reassessment/outputs/LFP_SOH_核心论文精读与证据附册.md`):
  - Yagci 2025 §2.4 (five-parameter dV/dQ fit with half-cell curves, LLI dominant in LFP);
  - Bilfinger 2024 (graphite stage-2 tracking on a 106s LFP vehicle; LFP IC is sensitive to voltage resolution);
  - Wang 2025 (OCV-invariance fit of C and z0);
  - Krupp 2021 (4S pack ICA superposition);
  - Cornejo 2026 (per-cell alignment on cumulative Ah);
  - Zhou 2025 (a fixed BoL OCV makes OCV drift look like resistance).
- **Environment.**
  - Research: `python3` (3.13, numpy/pandas/scipy/matplotlib). For OCP sourcing you may create a research-only venv in the study's git-ignored `cache/venv_ocp` (Python 3.11 or 3.12) and `pip install pybamm`.
  - Candidate classes: numpy/pandas only, and they must also run in Python 3.11. Create a venv in `cache/venv311` from `/opt/homebrew/bin/python3.11` with `pip install numpy pandas`.

## 4. Rules carried over from earlier rounds

1. **No artificial endpoints.** Never invent values beyond a measured curve. Either stop at the measured range and report the point as unavailable, or use a registered, bounded extension and report how far it extends.
2. **No real results before the selection is committed.** Never compute or print real-data CK1–CK7 proxy errors of a stage before its `protocol.json` is committed. Exclude k = 2 from any pseudo scenario used for a decision.
3. **Implement registered formulas exactly.** Register any deviation before running, or report it as a deviation.
4. **Cache keys contain every parameter** that changes the cached result.
5. **Causality checks compare exact floats** (future-noise and fit-on-prefix).
6. **6–7 anchors give diagnostics, not validation.**
7. **10-s voltage samples are strongly autocorrelated.** Any confidence or profile width must use an effective sample size from the residual autocorrelation, n_eff = n / (1 + 2 Σ ρ_k), never the raw point count.

## 5. Evaluation rules

- **Proxies, scenarios, metrics.** Same as V2 and rounds 3–4: P_k = Q_fc,k + ε0 + Δ, Δ ∈ {0, 0.4, 0.8}; PG1/PG2 for k = 4..7; PC5/PC10 for k = 3..7 in decisions, k = 2..7 only in final reporting; MAE, MAX, RMSE per Δ; ε-free CK2–7 MAE; per-checkup errors.
- **Common gates against V2:**

| Gate | Rule |
|---|---|
| G-causal | exact-float identity under future noise and fit-on-CK1-prefix |
| G-proxy | MAE < V2's MAE for every Δ, and MAX ≤ V2's MAX + 0.10 pp |
| G-epsfree | ε-free CK2–7 MAE ≤ V2's − 0.02 pp |
| G-robust | beats V2's MAE (Δ = 0.4) in ≥ 5 of 6 step variants |
| G-pseudo | mean MAE over PG1, PG2, PC5, PC10 (k ≥ 3) not worse than V2's by more than 0.02 pp |
| G-regress | no checkup's absolute error grows by more than 0.30 pp against V2 (Δ = 0.4) |
| G-impl | a numpy/pandas-only class with the `MyModel` interface (`fit(dataset)`, `estimate_soh(dataset, at_date)`) reproduces the research implementation within 0.001 pp, passes the sample_data smoke test in the 3.11 venv, and finishes the full run in under 30 min |

- **Pre-registration.** Before any evaluation in a stage, write `stage_X/protocol.json` (main configuration, all variants, gates, exit or selection rule), store its SHA256 in `stage_X/protocol.sha256`, and commit. Amend only before that stage's evaluation runs, with a reason. Never change the main configuration after seeing its results. The best variant is never reported as the main result.

## 6. Stages

### Stage 0 — Setup (cap 0.5 h)

- Create the study directory, `notes/STATUS.md`, `notes/DECISIONS.md`, `.gitignore` (`cache/`).
- Import the harness and confirm every cache write lands inside this worktree.
- Reproduce V2 (0.215726 / 0.669052 at Δ = 0.4) and M4 (0.291265) exactly. If either fails, stop the whole run and record why.

### Stage 1 — Half-cell OCPs, electrode model and synthetic identifiability (cap 2 h; no proxy metric)

**1a. OCP sourcing.**

- Obtain an LFP positive-electrode OCP and a graphite negative-electrode OCP from an open, licensed source. Main choice: the LFP OCP of PyBaMM's `Prada2013` parameter set, and a graphite OCP that shows staging plateaus (PyBaMM `Chen2020` or `Ecker2015` graphite).
- Function and set names may differ by version: find them by inspecting the installed PyBaMM, and record the PyBaMM version, function names and licence (BSD-3).
- Tabulate each OCP on a stoichiometry grid of 0.001 and store the tables as CSV in `ocp/` with a `SOURCES.md`.
- Register one alternative graphite OCP as a variant.
- **If no LFP and graphite OCP can be obtained from an open, licensed source:** record "blocked: no OCP source", skip stages 2–4, do stage 5 only for what is possible, and write the final report.

**1b. Model (implement exactly).** Per cell i and per event, with q the charged Ah from the event start (discharge: q decreases):

- graphite lithiation θ_n = θ_n,0 + q/Q_n;
- LFP lithiation θ_p = θ_p,0 − q/Q_p;
- cyclable lithium Q_Li = θ_n·Q_n + θ_p·Q_p (Ah), constant within an event;
- terminal voltage V = U_p(θ_p) − U_n(θ_n) + η, with η = R·I + h·sign(I) (I > 0 on charge).

Health parameters per cell are (Q_n, Q_p, Q_Li). Event parameters are the start lithiation θ_n,0 (θ_p,0 then follows from Q_Li) and the overpotential (R, h). Every θ must stay within [0, 1] over the event; reject parameter sets that leave it.

- **Degradation modes** relative to the reference (BoL) fit: LLI = Q_Li,ref − Q_Li, LAM_NE = Q_n,ref − Q_n, LAM_PE = Q_p,ref − Q_p (Ah).
- **Simulated quantities** for a health state:
  - **Q_fc,sim**: Ah charged from the anchor's start state to the CCCV end at 14.0 V pack / 5.1 A. Use the measured pack current profile of that anchor. The CV phase follows from V = U + R·I at the measured current.
  - **D_prog,sim**: the depth of the graphite step on a simulated ~10 A discharge from the CCCV end. Locate it on the simulated curve with the same midpoint-crossing rule (`events.MAIN_STEP`) as the real programs.
  - **Q_C20,sim**: from the CCCV-end state, after a rest (η → discharge-side η_dis), discharge at 5.1 A until the first time Σ_i V_i + c_pack = 11.2 V. c_pack is the constant pack-minus-cell-sum offset measured on the CK0 curve. If no root lies within the model's valid θ range, report "unavailable"; never extrapolate.

**1c. Fitting (main).**

- Fit each anchor and each cell independently over the whole charge (CC + CV), excluding the first 2 Ah (onset transient). Minimise the voltage residual, robust to outliers (soft-L1 with scale 2 mV), by bounded least squares.
- Variant: add a dV/dQ residual on the CC part (1 Ah smoothing, weight registered in 1c).
- Report the per-cell residual RMS and its autocorrelation.

**1d. Synthetic identifiability (exit rule, register before running).**

- Generate synthetic anchors with the model from a realistic BoL state (stage 2 gives one; until then use mid-range literature stoichiometries). Use the measured current profile of anchor 1 and 10-s sampling.
- Add 2 mV white noise plus 2 mV AR(1) noise with ρ = 0.9, and a constant per-cell offset of ±3 mV.
- Apply 30 random degradation states: LLI 0–8 Ah, LAM_NE 0–5 %, LAM_PE 0–5 %, and a start state drawn from the observed start-voltage range.
- Refit each. Report recovery errors for Q_fc, Q_C20, β_E (defined in stage 4), LLI, LAM_NE and LAM_PE.
- **Pass:** median |Q_C20 error| ≤ 0.2 Ah and median |β_E error| ≤ 0.10. Otherwise mark stages 3–4 "diagnostic only": still run stage 2 and stage 5, but evaluate no model.

### Stage 2 — BoL calibration and the CK0 check (cap 1 h; the only true-label check)

- **Reference health.** Fit health parameters per cell on anchor 0 (main; it is at 45 °C, so record that the OCPs are at 25 °C). Variant: anchor 1 (25 °C, one month older).
- **Discharge-side overpotential.** Fix the health parameters and fit η_dis,i (one constant per cell) and the start state on the CK0 curve from 5 Ah up to (end − 15 Ah). **The last 15 Ah of the CK0 curve are never used in any fit.**
- **CK0 prediction.**
  - Predict the cell voltages over the last 15 Ah and the pack 11.2 V root. Compare the root with 100.41 Ah and with the bounded-extension root 100.416854 Ah.
  - Also report the per-cell residuals over the last 15 Ah, which cell reaches its end first, and whether the model's graphite step on the CK0 curve lies within 1 Ah of `events.ck0_reference_step`.
- **Credibility rule (register before running).** The C/20 mapping is called *credible* only if |Q_C20,sim − 100.41| ≤ 0.5 Ah **and** the step position matches within 1 Ah. If it is not credible, the ε_E output of stage 4 is not produced. β_E does not need the C/20 mapping and stays allowed.

### Stage 3 — Identifiability audit on real anchors 1–7 (cap 1.5 h; no proxy metric)

- Fit every anchor (0–7) per cell (stage 1c main). Report per anchor and cell: residual RMS, LLI, LAM_NE, LAM_PE, R, h and start θ_n.
- **Profiles.** For each anchor and cell, fix LLI on a grid and refit the rest. From the profile with n_eff (rule 7), derive the 95 % range of:
  - the pack Q_C20,sim (combine cells by re-solving the pack root over the per-cell profile envelopes);
  - Q_fc,sim − Q_fc,obs (a fit check);
  - the local β_E.
- **Start-state confound.** Report the correlation between fitted LLI and start pack voltage across anchors 1–7. This is a diagnostic: round 3 found r = −0.975 for the bottom section.
- **Exit rule (register before the audit).** Stage 4 proceeds only if all of these hold:
  1. stage 1d passed;
  2. the 95 % range of pack Q_C20,sim is ≤ 0.6 Ah for ≥ 5 of 7 anchors (1–7);
  3. the 95 % range of β_E is ≤ 0.3 for ≥ 5 of 7 anchors;
  4. the fitted LLI trajectory over anchors 1–7 is monotone non-decreasing within its 95 % ranges.

  Otherwise mark stage 4 "diagnostic only".

### Stage 4 — Uses (cap 1.5 h; registered after the stage 3 audit, before any real-data proxy result)

**E1 — V2 with mechanistic β (proxy-gated; main).**

- At cutoff k, take the visible 25 °C anchors 1..k−1. Define the degradation direction as Δθ = θ_{k−1} − θ_1 in health-parameter space (four cells, fitted values).
- β_E,k = [Q_fc,sim(θ_1 + Δθ) − Q_fc,sim(θ_1)] / [D_prog,sim(θ_1 + Δθ) − D_prog,sim(θ_1)], averaged over the four cells by the pack definition, i.e. simulate the pack, not single cells.
- If k − 1 < 2, or the denominator's 95 % range includes zero, use β = 1 (as V2).
- Replace V2's β_k by β_E,k in the phase-matched branch only. Everything else is V2.
- Assumption to record: the ratio is computed at 25 °C OCPs and applied to 45 °C program steps; the temperature offset cancels in V2's phase-matched difference.
- Variants (report only): β_E with V2's shrinkage towards 1 (τ = 1); β_E from the reference fit on anchor 1 instead of 0; the alternative graphite OCP; the dV/dQ-residual fit.
- **Gates:** all common gates.

**E3 — mechanistic ε (leaderboard-only; only if the C/20 mapping is credible).**

- ε_sim(j) = Q_C20,sim(θ_j) − Q_fc,j for each visible anchor j.
- V2_epsE: Q̂_k = V2_k + [ε_sim(k−1) − ε_sim(1)] for k ≥ 2 (V2 otherwise). This keeps V2's calibration through anchor 1 and adds only the model's *change* in ε.
- Output an SOH table and the differences from V2. Proxies use the same constant-ε assumption, so never claim a proxy improvement.
- Also report the raw ε_sim(0) against the observed ε0 = 100.41 − Q_fc,0, as a model check.

**Order of work.**

1. Commit `stage_4/protocol.json`.
2. Run PG1, PG2, PC5 and PC10 (k ≥ 3) first and commit them.
3. Run the real scenario and all step variants.
4. Compute the gates.

### Stage 5 — Degradation-mode diagnostics (cap 0.75 h; descriptive, runs even if earlier exits fired)

- Per-cell LLI, LAM_NE and LAM_PE over anchors 0–7, with 95 % ranges, in a figure and a table.
- For each checkup date, which cell limits the simulated C/20 discharge, and by how many Ah the second cell would follow. Round 3's per-cell maps are a comparison.
- Compare the LLI share of the total loss with V2's empirical 68–79 % step → top share, and with literature expectations for LFP/graphite (LLI dominant: Yagci 2025, Bilfinger 2024).
- Comment on whether the model can say anything about the post-checkup recovery (0.02 → 0.87 Ah). Fit the first ~5-day CCCV charge after each anchor only if its range allows it; otherwise state that it cannot.
- Label every number with its identifiability status from stage 3.

### Stage 6 — Final report and candidate (cap 1 h)

- **`FINAL_REPORT.md`** (bilingual, conclusions first):
  1. the OCP source and the stage 1d synthetic result;
  2. the CK0 check (stage 2), stated plainly; it is the only true-label number of the round;
  3. the identifiability audit and its exit decision;
  4. a table of E1 (main and variants) against M4 and V2 (MAE per Δ, MAX, ε-free MAE, pseudo MAE, gates), with per-checkup errors;
  5. the E3 leaderboard-only table, if produced;
  6. the degradation-mode diagnostics;
  7. risks: exposure; single pack; literature OCPs that are not from these cells; the 45 °C anchor 0 against 25 °C OCPs; the unknown CK0 temperature; the assumption that the checkup full charge matches the anchor CCCV; ε and recovery;
  8. exact reproduction commands.
- **`README.md`** (bilingual).
- **Candidate class.** Only for a model that passes every gate: put it in `candidate_model/`.
  - Embed the OCP tables as numpy arrays in the module (no external files).
  - Implement the fit with numpy only (e.g. a bounded Levenberg–Marquardt). It must reproduce the research fit within the G-impl tolerance; if the research used scipy, prove the numpy version matches.
  - Provide G-causal and G-impl evidence.
  - Nothing is wired into `my_model/`.

## 7. Order and caps

| Order | Stage | Cap |
|---|---|---|
| 0 | Setup + reproduce V2 | 0.5 h |
| 1 | OCPs, model, synthetic identifiability | 2 h |
| 2 | BoL calibration, CK0 check | 1 h |
| 3 | Identifiability audit on real anchors | 1.5 h |
| 4 | E1 (proxy-gated), E3 (leaderboard-only) | 1.5 h |
| 5 | Degradation-mode diagnostics | 0.75 h |
| 6 | Final report + candidate | 1 h |

**Stop rules.**

- If stage 0 cannot reproduce V2, stop everything.
- If no OCP source is available, follow the 1a rule.
- Exit rules in 1d and stage 3 skip stage 4 but not stages 2, 5 and 6.
- A candidate failing G-causal is rejected outright. A round with no passing model is still a valid result.

## 8. Prohibitions (summary)

- **Causality.** No data after CK_k for CK_k. This covers fits, reference states, overpotentials, β, ε, thresholds and selection.
- **Pre-registration.** No change of a registered main configuration after its results; no real-data proxy results before the protocol commit; the best variant is never the main result.
- **Endpoints.** No invented curve values; unavailable roots are reported as unavailable.
- **Proxies.** Never present proxies as hidden truth; never reconstruct CK1–CK7 from external sources.
- **Files and git.** Do not edit the submission package or earlier studies. Push only to this branch, never force-push, do not touch other checkouts.
- **No questions.** Never ask the user anything; record decisions and continue.

---

<a id="zh"></a>

# 第五轮 B：电极级退化模式模型——无人值守执行 Prompt

> **语言：** [English](#en) · 中文

编写日期：2026-10-14。本文自成一体。英文部分是执行文本，中文部分是给读者的翻译；两者不一致时以英文为准。另一份 prompt（第五轮 A，应力历史模型）可以同时在另一个 worktree 里运行，两者互不共享任何东西。

## 0. 工作方式

- **无人值守运行。** 不要停下来提问。遇到未定的决策，选择遵守本文全部规则前提下最保守的方案，记入 `notes/DECISIONS.md`，然后继续。
- **上下文可能被压缩或重启。** 每一步之后都更新 `notes/STATUS.md`：阶段、已完成、下一步、最近一次提交。重启后先读 `notes/STATUS.md` 和 `notes/DECISIONS.md` 再接着做，不要重做已完成的阶段。
- **时间预算。** 全程约 8 小时，每个阶段有上限（第 7 节）。到上限时，把已有结果（包括"无定论"）写成报告、提交，然后进入下一阶段。
- **完成的标准**（必须全部满足）：
  1. 第 6 节每个阶段都已完成、到达上限或按登记的退出规则跳过，且 `notes/STATUS.md` 写明是哪一种；
  2. 研究目录里有 `FINAL_REPORT.md` 和 `README.md`，双语、结论在前；
  3. 每份预登记协议的 `protocol.sha256` 都在其评估提交之前提交；
  4. 所有提交都已推送到 `origin exp/phase2-r5b-electrode-model-20261014`；
  5. worktree 里 `git status` 没有未提交的研究文件。

## 1. 工作区、隔离与 git

- **worktree 与分支（已建好）。**
  - 只在 worktree `/Users/shane/Desktop/Arena_1014_r5b_electrode` 的分支 `exp/phase2-r5b-electrode-model-20261014` 上工作。该分支从 `exp/phase2-round4-signals-20261014` 的 `a6bc61f` 创建。
  - 不要 `cd` 到任何其他检出目录（`/Users/shane/Desktop/Arena_1013_model`、`Arena_1014_round4`、`Arena_1014_r5a_stress` 或归档目录）。
  - 所有新工作放在 `research/phase2_r5b_electrode_model_20261014/`（下称"研究目录"）。
- **并发防护。**
  - 开始时以及每次提交前，运行 `git log --oneline -5`，与自己最近一次提交对照。
  - 如果出现不是你做的提交，或有你没改过的已跟踪文件发生变化：停止编辑共享文件，记入 `notes/DECISIONS.md`，此后只按明确路径添加文件。
  - 不要使用 `git add -A` 或 `git add .`，不要撤销或改写别人的工作，不要使用裸 `git stash`。
- **提交与推送。**
  - 把本 prompt 作为第一个提交。
  - 每个阶段结束时提交，有意义的子步骤完成后也提交。
  - 每次阶段提交后运行 `git push -u origin exp/phase2-r5b-electrode-model-20261014`。不要推送到其他地方，不要强制推送。
  - 提交信息结尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **不要修改：**
  - `TechArena_Challenge2_Team_Package/`（框架、`run_model.py`、`validate_submission.py`、`my_model/`、`data/`）；
  - 之前任何研究目录（`phase2_anchor_step_20261013`、`phase2_v2_phase_matched_20261013`、`phase2_round3_models_20261014`、`phase2_round4_signals_20261014`）。

  可以导入它们的代码，但不要编辑。
- **文档语言。** 你写的每个 Markdown 文档都是英文在前、中文在后，格式与本文件相同（`<a id="en"></a>`、语言切换行、`---`、`<a id="zh"></a>`）。代码注释和 docstring 只用英文。
- **字节码。** 用 `python3 -B` 运行 Python。

## 2. 任务、现状与本轮的理由

**任务（TechArena 2026 Challenge 2）。** 估计 4 × 102 Ah LFP 串联电池组在每个检查日的 SOH。

- **目标量。** SOH = C/20 容量 ÷ 102 Ah。C/20 容量是满充后以 5.1 A 放电、直到组端电压首次达到 11.2 V 时放出的 Ah。
- **标签。** 只公开 CK0 = 100.41 Ah；CK1–CK7 隐藏，用于评分（多项误差指标，含最差误差，各自除以官方基线归一）。
- **检查日：** CK0 2025-01-14，CK1 02-08，CK2 03-11，CK3 04-14，CK4 05-16，CK5 06-16，CK6 07-25，CK7 08-28。
- **因果截断。** 预测 CK_k 只能用 `load_dataset(data, until=CK_k)`，截断点是该日 00:00。

**数据（2026-10-14 已核实）。**

- 13 个运行段，10 s 采样。第 1 段为 45 °C（01-19 → 02-08）；之后每月先是一个短的 25 °C 段，再是一个长的 45 °C 段。第 3 段（45 °C，02-19 → 03-11）缺失。
- 列：`timestamp`、`elapsed_s`、`segment`、`chamber_temperature_C`、`current_A`（充电为正）、`charge_Ah_cum`、`discharge_Ah_cum`、`cell1_V`..`cell4_V`、`pack_voltage_V`、`temp_mean_C`/`min`/`max`。
- 计数器把 20 A 脉冲记为充电，所以要按真实时间步长积分 `current_A`；Δt > 600 s 或 Δt ≤ 0 不积分。
- **CK0 参考放电**（`data/checkups/CK0_reference_discharge.csv.gz`，记录于 2025-01-15）：恒流 5.1 A，列为 `timestamp`、`current_A`、`voltage_V`、`cell1_V`..`cell4_V`、`discharged_Ah`。四芯电压和结束于 11.203 V；第三轮的有界延伸把组端 11.2 V 根定在 100.416854 Ah。没有温度列，按 25 °C 假设并记录。

**锚点（本轮的主要数据）。** 每次检查之后，电池组静置 2 h、从近空（组压约 11.6–12.0 V）开始，以约 20 A 恒流充电，再在 14.0 V 恒压到 5.1 A。每次约充入 95 Ah，有 10 s 的逐芯电压，并在充电方向越过石墨分阶台阶。锚点 0 在第 1 段、45 °C（2025-01-19）；锚点 1–7 在 25 °C 段 2、4、6、8、10、12、14，在 CK_j 之后 2–5 天。这是整个试验中仅有的全范围曲线；第三、四轮证明，除了约每 5 天一次的程序放电（约 10 A，从 CV 末端开始，在 45 °C 越过台阶），没有其他事件能从顶端到达台阶区域。

**当前领先候选：V2**（`research/phase2_v2_phase_matched_20261013/src/v2.py`）。分支 `exp/phase2-anchor-step-20261013` 上的提交包目前指向 V2（提交 `1f7deb3`），不要动它。

- Q_anchor = Q_fc + ε，ε = ε0 + Δ，ε0 = 100.41 − Q_fc,0。
- 月内更新：Q̂ = Q_anchor(k−1) + β_k·[E45(k−1) − E45(k−2) + r·(d(k−1) − d(k−2))]。E45 是一个月中最后一次 45 °C 程序放电的台阶深度。
- β_k 是一个*经验*比值。锚点之间的损失只有 68–79 % 体现在充电侧"台阶 → 顶端"的距离里，所以 β > 1（拟合值 1.06–1.51；CK7 的 1.51 超出了全程的比值范围）。
- ε 是一个*假定的常数*，把运行中的锚点充电（20 A 恒流 + 恒压，充电方向）映射到 C/20 放电至组端 11.2 V。
- CK1–CK3 回退到 M4。
- **代理结果**（代理 P_k = Q_fc,k + ε0 + Δ，Δ = 0.4）：MAE **0.215726 pp**，MAX **0.669052 pp**（CK2）。各检查点：CK1 +0.217、CK2 +0.669、CK3 +0.080、CK4 +0.228、CK5 +0.150、CK6 −0.163、CK7 −0.004。M4：MAE 0.291265。

**第三、四轮已确立的结论（要用上）。**

- **第三轮 A** 用两个唯象尺度（底部和顶部）把每次锚点充电配准到模板，结果被拒（MAE 0.242，稳健性零胜）。
  - 电压干扰项有界时，底部 / 顶部 / 电压分别只在 40 % / 80 % / 20 % 的拟合中可辨识。
  - 底部区段的变化与起始电压相关（r = −0.975）：起始状态是混杂因素。
- **第三轮 E** 把因果的逐芯充电映射套到 CK0 放电上。105 个情形中 90 个有有限的 11.2 V 根，max |ε − ε0| = 0.023 pp；另有 15 个根不可得，所以结论是无定论。
- **第四轮**证明 V2 的剩余误差不是台阶噪声。
  - 检查后恢复到 CK7 时增长到约 0.87 Ah（τ ≈ 2.5 天）。代理是恢复之后的充电量。
  - ε 和恢复状态主导了真实得分的不确定性，而代理检验不了它们。

**为什么做本轮。** 之前的配准模型是对经验模板做缩放。本轮用**物理的电极模型**：文献中 LFP 和石墨的半电池开路电位（OCP），加逐芯的化学计量对齐。它把 V2 中两个经验量换成机理量：

- **β_E**：沿拟合出的退化方向（LLI / LAM_NE / LAM_PE），d(满充 Ah) / d(程序台阶深度) 的比值。可用代理检验。
- **ε_E**：模型给出的、每个锚点从锚点充电到 C/20 放电至组端 11.2 V 的映射。只用于排行榜，因为代理和 V2 共用 ε 假设。
- **诊断**：逐芯 LLI、LAM_NE、LAM_PE 轨迹，以及每个检查点在 11.2 V 时由哪一芯限制电池组。这对应可解释性和创新两项评分（各 10 %）。

不需要辨识每个电极参数。只要所有能拟合数据的参数组在目标量（Q_C20、β_E）上一致就够了。审计就是围绕这一点设计的。

**曝光。** 所有 CK1–CK7 代理值都已看过，所以每个结果都是**已曝光的探索性结果**。每份报告都要写明，并且绝不把代理当成隐藏真值。

## 3. 可复用的代码与数据

- **共享评估框架：** `research/phase2_round3_models_20261014/src/harness.py`。
  - 提供 `run`、`metrics`、`per_ck`、`gates_vs_v2`、`candidate_checks`、`SCENARIOS`（`real`、`PG1`、`PG2`、`PC5`、`PC10`）、`BASELINES`（M4、V2）、`QFC`、`EPS0`、`cut_op`、`full_op`。
  - 预测器是 `f(ctx) -> Q_hat_Ah` 或 `(Q_hat, info)`。`ctx` 含 `k`、`at_date`、`ck`、`op`、`fc`、`steps`、`step`、`a4`、`a4s`、`eps`、`eps0`、`delta`、`scenario`、`key`。
  - 导入 `harness` 会把缓存写到本 worktree 里的 `research/phase2_round3_models_20261014/cache/`（被 git 忽略、私有）。你自己的缓存放在研究目录被忽略的 `cache/` 下，键名包含所有参数。
- **事件提取：** `research/phase2_anchor_step_20261013/src/events.py`：
  - `full_charges` 给出带 `_seg_index`（段内起止行）的锚点行；
  - `step_programs`、`STEP_VARIANTS` 和 `_locate`（中点穿越与 dV/dQ 峰两种台阶定位）；
  - `charge_step_split`（充电侧"底部 → 台阶"和"台阶 → 顶端"）；
  - `ck0_reference_step`；
  - `segment_arrays`。
- **V2 函数：** `research/phase2_v2_phase_matched_20261013/src/v2.py`（`anchors_by_checkup`、`month_steps`、`end45`、`phase_diff`、`beta_a4`、`shrink`、`m4`、`v2`）。V2 参考类是 `research/phase2_v2_phase_matched_20261013/candidate_model/anchor_step_v2_model.py`。
- **第三轮映射代码**（`research/phase2_round3_models_20261014/stage_E/`）展示了逐芯映射和首个 11.2 V 根的算法。写自己的求根之前先读它，并遵守第 4 节规则 1。
- **文献背景**（卡片见 `/Users/shane/Desktop/Arena 阶段 2 官方材料/research/phase2_literature_reassessment/outputs/LFP_SOH_核心论文精读与证据附册.md`）：
  - Yagci 2025 第 2.4 节（用半电池曲线做五参数 dV/dQ 拟合，LFP 中 LLI 主导）；
  - Bilfinger 2024（在 106 串 LFP 整车上追踪石墨 stage-2；LFP 的 IC 对电压分辨率敏感）；
  - Wang 2025（用 OCV 不变性拟合 C 和 z0）；
  - Krupp 2021（四串电池组 ICA 的叠加关系）；
  - Cornejo 2026（在累计 Ah 上做逐芯对齐）；
  - Zhou 2025（固定 BoL OCV 会把 OCV 漂移误认成电阻）。
- **环境。**
  - 研究用 `python3`（3.13，numpy/pandas/scipy/matplotlib）。为获取 OCP，可以在研究目录被忽略的 `cache/venv_ocp`（Python 3.11 或 3.12）里建一个仅供研究的 venv，`pip install pybamm`。
  - 候选类只用 numpy/pandas，且必须能在 Python 3.11 下运行：在 `cache/venv311` 里用 `/opt/homebrew/bin/python3.11` 建 venv，`pip install numpy pandas`。

## 4. 沿用自前几轮的规则

1. **不得人造端点。** 不得编造测量曲线之外的值。要么停在测量范围内并把该点报告为不可得，要么用登记过的有界延伸并报告延伸了多远。
2. **选择提交之前不得出真实结果。** 某阶段的 `protocol.json` 提交之前，不得计算或打印真实数据上 CK1–CK7 的代理误差。任何用于决策的伪场景都要排除 k = 2。
3. **严格按登记的公式实现。** 偏离要在运行前登记，否则作为偏离报告。
4. **缓存键必须包含**所有会改变缓存结果的参数。
5. **因果检查比较精确浮点数**（未来加噪与前缀拟合）。
6. **6–7 个锚点只能给出诊断，不是验证。**
7. **10 s 电压采样高度自相关。** 任何置信区间或剖面宽度都要用由残差自相关得到的有效样本量 n_eff = n / (1 + 2 Σ ρ_k)，绝不能用原始点数。

## 5. 评估规则

- **代理、场景、指标。** 与 V2 和第三、四轮相同：P_k = Q_fc,k + ε0 + Δ，Δ ∈ {0, 0.4, 0.8}；PG1/PG2 用 k = 4..7；PC5/PC10 在决策中用 k = 3..7，只在最终报告中用 k = 2..7；每个 Δ 下的 MAE、MAX、RMSE；与 ε 无关的 CK2–7 MAE；各检查点误差。
- **对 V2 的通用门槛：**

| 门槛 | 规则 |
|---|---|
| G-causal | 未来数据加噪、仅用 CK1 前缀拟合时，输出的浮点数完全一致 |
| G-proxy | 每个 Δ 下 MAE 都低于 V2，且 MAX ≤ V2 的 MAX + 0.10 pp |
| G-epsfree | 与 ε 无关的 CK2–7 MAE ≤ V2 的值 − 0.02 pp |
| G-robust | 在 6 种台阶检测方法中至少 5 种上 MAE（Δ = 0.4）优于 V2 |
| G-pseudo | PG1、PG2、PC5、PC10（k ≥ 3）的平均 MAE 比 V2 差不超过 0.02 pp |
| G-regress | 任何检查点的绝对误差相对 V2 的增幅不超过 0.30 pp（Δ = 0.4） |
| G-impl | 只依赖 numpy/pandas、接口为 `MyModel`（`fit(dataset)`、`estimate_soh(dataset, at_date)`）的类，与研究实现相差 ≤ 0.001 pp，在 3.11 venv 中通过 sample_data 冒烟测试，且完整运行在 30 分钟内完成 |

- **预登记。** 每个阶段在任何评估之前写 `stage_X/protocol.json`（主配置、所有变体、门槛、退出或选择规则），把 SHA256 存进 `stage_X/protocol.sha256` 并提交。只能在该阶段评估运行之前修订，并写明理由。看到结果之后不得更改主配置。最佳变体永远不能作为主结果报告。

## 6. 各阶段

### 第 0 阶段——准备（上限 0.5 小时）

- 建研究目录、`notes/STATUS.md`、`notes/DECISIONS.md`、`.gitignore`（`cache/`）。
- 导入 harness，确认所有缓存写入都落在本 worktree 内。
- 精确复现 V2（Δ = 0.4 时 0.215726 / 0.669052）和 M4（0.291265）。任何一个复现不了，就停止整轮并记录原因。

### 第 1 阶段——半电池 OCP、电极模型与合成数据可辨识性（上限 2 小时；不算代理指标）

**1a. 获取 OCP。**

- 从开放且有许可证的来源获取 LFP 正极 OCP 和石墨负极 OCP。主选：PyBaMM `Prada2013` 参数集中的 LFP OCP，以及一个能显示分阶平台的石墨 OCP（PyBaMM 的 `Chen2020` 或 `Ecker2015` 石墨）。
- 函数名和参数集名可能随版本变化：通过检查已安装的 PyBaMM 找到它们，并记录 PyBaMM 版本、函数名和许可证（BSD-3）。
- 把每条 OCP 在 0.001 的化学计量网格上列表，以 CSV 存进 `ocp/`，并写 `SOURCES.md`。
- 另登记一条备选石墨 OCP 作为变体。
- **如果拿不到开放且有许可证的 LFP 和石墨 OCP：** 记录"受阻：无 OCP 来源"，跳过第 2–4 阶段，第 5 阶段只做能做的部分，然后写最终报告。

**1b. 模型（严格按此实现）。** 对每一芯 i、每个事件，q 为从事件开始累计的充入 Ah（放电时 q 减小）：

- 石墨嵌锂度 θ_n = θ_n,0 + q/Q_n；
- LFP 嵌锂度 θ_p = θ_p,0 − q/Q_p；
- 可循环锂 Q_Li = θ_n·Q_n + θ_p·Q_p（Ah），在一个事件内为常数；
- 端电压 V = U_p(θ_p) − U_n(θ_n) + η，其中 η = R·I + h·sign(I)（充电时 I > 0）。

每芯的健康参数是 (Q_n, Q_p, Q_Li)；事件参数是起始嵌锂度 θ_n,0（θ_p,0 由 Q_Li 决定）和过电位 (R, h)。整个事件中每个 θ 都必须在 [0, 1] 内；越界的参数组一律拒绝。

- **退化模式**相对参考（BoL）拟合定义：LLI = Q_Li,ref − Q_Li，LAM_NE = Q_n,ref − Q_n，LAM_PE = Q_p,ref − Q_p（Ah）。
- 给定健康状态时的**模拟量**：
  - **Q_fc,sim**：从锚点起始状态充到组端 14.0 V / 5.1 A 的 CCCV 末端所充入的 Ah。用该锚点实测的组电流曲线；恒压段由 V = U + R·I 在实测电流下求出。
  - **D_prog,sim**：从 CCCV 末端以约 10 A 模拟放电时的石墨台阶深度。在模拟曲线上用与真实程序相同的中点穿越规则（`events.MAIN_STEP`）定位。
  - **Q_C20,sim**：从 CCCV 末端状态出发，静置后（η 换成放电侧的 η_dis），以 5.1 A 放电，直到 Σ_i V_i + c_pack 首次等于 11.2 V。c_pack 是在 CK0 曲线上测得的"组压 − 芯压和"常数偏差。如果在模型的有效 θ 范围内找不到根，报告"不可得"，绝不外推。

**1c. 拟合（主配置）。**

- 每个锚点、每一芯独立拟合整个充电过程（恒流 + 恒压），排除前 2 Ah（起始暂态）。以有界最小二乘最小化电压残差，用对离群点稳健的损失（soft-L1，尺度 2 mV）。
- 变体：在恒流段加入 dV/dQ 残差（1 Ah 平滑，权重在 1c 中登记）。
- 报告逐芯残差 RMS 及其自相关。

**1d. 合成数据可辨识性（退出规则，运行前登记）。**

- 从一个现实的 BoL 状态出发用模型生成合成锚点（第 2 阶段会给出一个；在那之前用文献中的中间化学计量）。用锚点 1 的实测电流曲线和 10 s 采样。
- 加 2 mV 白噪声、ρ = 0.9 的 2 mV AR(1) 噪声，以及每芯 ±3 mV 的常数偏差。
- 施加 30 个随机退化状态：LLI 0–8 Ah、LAM_NE 0–5 %、LAM_PE 0–5 %，起始状态从实测的起始电压范围中抽取。
- 逐个重新拟合。报告 Q_fc、Q_C20、β_E（第 4 阶段定义）、LLI、LAM_NE、LAM_PE 的恢复误差。
- **通过条件：** |Q_C20 误差| 中位数 ≤ 0.2 Ah，且 |β_E 误差| 中位数 ≤ 0.10。否则把第 3–4 阶段标为"仅诊断"：第 2 阶段和第 5 阶段照常做，但不评估任何模型。

### 第 2 阶段——BoL 标定与 CK0 检查（上限 1 小时；唯一的真实标签检查）

- **参考健康状态。** 用锚点 0 逐芯拟合健康参数（主配置；它在 45 °C，要记录 OCP 是 25 °C 的）。变体：锚点 1（25 °C，老化一个月）。
- **放电侧过电位。** 固定健康参数，在 CK0 曲线 5 Ah 到（末端 − 15 Ah）的区间上拟合每芯的 η_dis,i（每芯一个常数）和起始状态。**CK0 曲线最后 15 Ah 在任何拟合中都不使用。**
- **CK0 预测。**
  - 预测最后 15 Ah 的各芯电压和组端 11.2 V 的根。把根与 100.41 Ah 以及有界延伸根 100.416854 Ah 比较。
  - 同时报告最后 15 Ah 上的逐芯残差、哪一芯先到末端，以及模型在 CK0 曲线上的石墨台阶是否与 `events.ck0_reference_step` 相差不超过 1 Ah。
- **可信度规则（运行前登记）。** 只有当 |Q_C20,sim − 100.41| ≤ 0.5 Ah **且**台阶位置相差不超过 1 Ah 时，C/20 映射才算*可信*。不可信时，第 4 阶段不产出 ε_E；β_E 不需要 C/20 映射，仍然允许。

### 第 3 阶段——真实锚点 1–7 的可辨识性审计（上限 1.5 小时；不算代理指标）

- 逐芯拟合每个锚点（0–7）（第 1c 主配置）。按锚点、按芯报告：残差 RMS、LLI、LAM_NE、LAM_PE、R、h、起始 θ_n。
- **剖面。** 对每个锚点、每一芯，把 LLI 固定在一组网格值上，其余参数重新拟合。由剖面并按 n_eff（规则 7）得出以下量的 95 % 范围：
  - 组的 Q_C20,sim（在逐芯剖面包络上重新求组端根来合成）；
  - Q_fc,sim − Q_fc,obs（拟合检查）；
  - 局部 β_E。
- **起始状态混杂。** 报告锚点 1–7 上拟合 LLI 与起始组压的相关。这只是诊断：第三轮在底部区段发现 r = −0.975。
- **退出规则（审计前登记）。** 只有以下条件全部满足，才进入第 4 阶段：
  1. 1d 已通过；
  2. 7 个锚点（1–7）中至少 5 个的组 Q_C20,sim 95 % 范围 ≤ 0.6 Ah；
  3. 7 个锚点中至少 5 个的 β_E 95 % 范围 ≤ 0.3；
  4. 锚点 1–7 上拟合的 LLI 轨迹在其 95 % 范围内单调不减。

  否则把第 4 阶段标为"仅诊断"。

### 第 4 阶段——应用（上限 1.5 小时；在第 3 阶段审计之后、任何真实数据代理结果之前登记）

**E1——带机理 β 的 V2（受代理门槛约束；主模型）。**

- 截断 k 时，取可见的 25 °C 锚点 1..k−1。把退化方向定义为健康参数空间中的 Δθ = θ_{k−1} − θ_1（四芯，用拟合值）。
- β_E,k = [Q_fc,sim(θ_1 + Δθ) − Q_fc,sim(θ_1)] / [D_prog,sim(θ_1 + Δθ) − D_prog,sim(θ_1)]，四芯按电池组定义合成，即模拟整个电池组而不是单芯。
- 若 k − 1 < 2，或分母的 95 % 范围包含零，则 β = 1（与 V2 相同）。
- 只在同相位分支中用 β_E,k 替换 V2 的 β_k，其余与 V2 完全相同。
- 要记录的假设：比值用 25 °C 的 OCP 计算，用于 45 °C 程序台阶；温度偏差在 V2 的同相位差分中相互抵消。
- 变体（只报告）：对 β_E 施加 V2 的向 1 收缩（τ = 1）；以锚点 1 而非锚点 0 为参考拟合的 β_E；备选石墨 OCP；加 dV/dQ 残差的拟合。
- **门槛：** 全部通用门槛。

**E3——机理 ε（只用于排行榜；仅当 C/20 映射可信时才做）。**

- 对每个可见锚点 j，ε_sim(j) = Q_C20,sim(θ_j) − Q_fc,j。
- V2_epsE：k ≥ 2 时 Q̂_k = V2_k + [ε_sim(k−1) − ε_sim(1)]（其他情况用 V2）。这样保留了 V2 经由锚点 1 的标定，只加入模型给出的 ε *变化量*。
- 输出 SOH 表及其与 V2 的差。代理与 V2 共用常数 ε 假设，所以绝不声称代理上有改进。
- 另外报告原始的 ε_sim(0) 与观测到的 ε0 = 100.41 − Q_fc,0 的对比，作为模型检查。

**工作顺序。**

1. 提交 `stage_4/protocol.json`。
2. 先跑 PG1、PG2、PC5、PC10（k ≥ 3）并提交。
3. 再跑真实场景和所有台阶变体。
4. 计算门槛。

### 第 5 阶段——退化模式诊断（上限 0.75 小时；描述性，即使前面的退出规则触发也照做）

- 锚点 0–7 上逐芯的 LLI、LAM_NE、LAM_PE，附 95 % 范围，给出图和表。
- 每个检查日，模拟的 C/20 放电由哪一芯限制，第二个到达的芯晚多少 Ah。可与第三轮的逐芯映射对比。
- 把 LLI 占总损失的份额与 V2 经验上的 68–79 % "台阶 → 顶端"份额比较，也与文献对 LFP/石墨的预期（LLI 主导：Yagci 2025、Bilfinger 2024）比较。
- 讨论模型能否对检查后恢复（0.02 → 0.87 Ah）给出任何结论。只有当每个锚点之后第一次约 5 天的 CCCV 充电的范围允许时才拟合它；否则直接说明做不到。
- 每个数字都标注第 3 阶段给出的可辨识性状态。

### 第 6 阶段——最终报告与候选（上限 1 小时）

- **`FINAL_REPORT.md`**（双语，结论在前）：
  1. OCP 来源和 1d 的合成数据结果；
  2. CK0 检查（第 2 阶段），直白写出；这是本轮唯一的真实标签数字；
  3. 可辨识性审计及其退出决定；
  4. E1（主配置和变体）对 M4、V2 的表（各 Δ 的 MAE、MAX、与 ε 无关的 MAE、伪场景 MAE、门槛），附各检查点误差；
  5. E3 的排行榜专用表（如果产出）；
  6. 退化模式诊断；
  7. 风险：曝光；单个电池组；文献 OCP 并非来自这些电芯；45 °C 的锚点 0 对 25 °C 的 OCP；CK0 温度未知；"检查时的满充与锚点 CCCV 相同"的假设；ε 与恢复；
  8. 精确的复现命令。
- **`README.md`**（双语）。
- **候选类。** 只对通过所有门槛的模型，在 `candidate_model/` 下给出：
  - OCP 表以 numpy 数组嵌入模块（不读外部文件）；
  - 拟合只用 numpy 实现（例如有界 Levenberg–Marquardt），必须在 G-impl 容差内复现研究拟合；如果研究中用了 scipy，要证明 numpy 版本与之一致；
  - 附 G-causal 和 G-impl 证据；
  - 不接入 `my_model/`。

## 7. 顺序与上限

| 顺序 | 阶段 | 上限 |
|---|---|---|
| 0 | 准备 + 复现 V2 | 0.5 小时 |
| 1 | OCP、模型、合成数据可辨识性 | 2 小时 |
| 2 | BoL 标定、CK0 检查 | 1 小时 |
| 3 | 真实锚点可辨识性审计 | 1.5 小时 |
| 4 | E1（代理门槛）、E3（排行榜专用） | 1.5 小时 |
| 5 | 退化模式诊断 | 0.75 小时 |
| 6 | 最终报告 + 候选 | 1 小时 |

**停止规则。**

- 第 0 阶段复现不了 V2，就停止一切。
- 没有 OCP 来源时，按 1a 的规则处理。
- 1d 和第 3 阶段的退出规则只跳过第 4 阶段，不跳过第 2、5、6 阶段。
- 未通过 G-causal 的候选直接拒绝。没有任何模型通过的一轮同样是有效结果。

## 8. 禁止事项（汇总）

- **因果性。** 预测 CK_k 不得用 CK_k 之后的数据，包括拟合、参考状态、过电位、β、ε、阈值和选择。
- **预登记。** 看到结果后不得更改登记的主配置；协议提交之前不得出真实数据代理结果；最佳变体永远不作为主结果。
- **端点。** 不得编造曲线值；不可得的根报告为不可得。
- **代理。** 绝不把代理当成隐藏真值；绝不从外部来源重建 CK1–CK7。
- **文件与 git。** 不修改提交包和之前的研究。只推送到本分支，不强制推送，不碰其他检出目录。
- **不提问。** 绝不向用户提问；记录决策并继续。
