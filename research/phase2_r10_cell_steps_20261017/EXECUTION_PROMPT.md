<a id="en"></a>

# Round 10: Robust Per-Cell Step Aggregation — Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-17. This document is self-contained. The English text is the execution text; the Chinese section is a translation for the reader, and if they differ the English governs.

**Goal of the round.** Round 8 found that the four cells of the pack carry persistent, slowly diverging step-depth offsets, and that the submitted model's 4-cell **mean** picks up this divergence (about −0.15 Ah at CK6). Round 9 showed that the obvious fix, the 4-cell **median**, passes the causal gates on the main detection method but is not robust across detection methods (dvdq_peak real MAE 0.257 → 0.361). This round tests three better-founded ideas **one at a time**, each registered before it is evaluated:

- **A — make the per-cell detection stable first:** average each cell's step location over the 6 detection variants, then combine the cells.
- **B — combine per-cell changes, not per-cell positions:** compute each cell's own month-to-month step change, then combine the four changes robustly (median, or drop one outlying cell).
- **C — remove the cells' top-state drift:** correct each cell's step depth for how full that cell was at the CV end, using a per-cell reference point, so that only ageing remains.

The round produces registered verdicts per idea and, only if one passes every gate, a candidate model class with a package check. **It never wires anything into the submission.**

Work packages WP0–WP5. WP0 comes first. WP1, WP2 and WP3 are tested one by one in this order (WP2's candidate B3 depends on WP1's result). WP4 needs WP1–WP3. WP5 comes last. Each WP can be run as a separate `/goal`.

## 0. Mode of work (all work packages)

- **Unattended.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Restarts.** Keep `notes/STATUS.md` current after every step: WP, done, next, last commit. On restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume. Never redo a finished WP or step.
- **Honesty over targets.** "No idea passes" is a valid outcome. A failed idea is reported as plainly as a passing one.
- **Done for any WP** means the common criteria below, plus that WP's own list:
  1. its registered protocol (`wpN/protocol.json` + `wpN/protocol.sha256`) was committed **before** any candidate of that WP was evaluated (WP0 and WP5 have no protocol);
  2. its bilingual `wpN/REPORT.md` exists, conclusions first;
  3. `notes/STATUS.md` marks the WP done, capped, skipped or exited, with one line of result;
  4. every commit is pushed to `origin exp/phase2-r10-cell-steps-20261017`, and `git status` shows no uncommitted study files.
- **Global Done:** WP0–WP5 each done, capped, skipped or exited by a registered rule; `FINAL_REPORT.md` and `README.md` exist (bilingual, conclusions first); common criteria 3–4 hold.

## 1. Workspace, isolation, git

- **Worktree and branch (create in WP0 if missing; idempotent).**
  - Base: round 9's final commit on the **local** branch `exp/phase2-r9-fixes-20261017` (`6749c63` at writing time; use the branch tip and record its hash). It contains round 8 (`research/phase2_r8_error_table_20261017/`) and round 9 (`research/phase2_r9_fixes_20261017/`). This branch was not pushed; pushing this round's branch also publishes those commits, which is intended.
  - Create: `git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1017_r10_cells -b exp/phase2-r10-cell-steps-20261017 <base>`. If it exists, check that its history contains `<base>` and reuse it.
  - Work only in `/Users/shane/Desktop/Arena_1017_r10_cells`. The study directory is `research/phase2_r10_cell_steps_20261017/`.
- **Code to reuse (present on the base branch; copy what you change into this study, edit only the copies):**
  - round 8 `research/phase2_r8_error_table_20261017/src/`:
    - `harness.py` (round 3 harness copy whose cache lives next to its study);
    - `common8.py` (asserts the worktree name `Arena_1017_r8_err`, so it must be copied as `common10.py` with the assertion changed);
    - `runner5c.py` (scenarios real, PG1, PG2, PC5, PC10, CS, CSE, PC5_all, PC10_all; `scenario_tables`, `run`, `scen_mean`);
    - `tsqrt.py` (T_main), `v3.py`, `internals.py` (instrumented replay of SUB with the events each prediction uses), `eventcurves.py`, `slicestats.py`, `checks5c.py` (candidate checks).
    - Outside `src/`: `wp2/run_wp2.py` function `add_residuals` (R_seg, R_anc, R_cell definitions) and `wp5/run_wp5.py` function `r_anc_b` (leave-month-out free-slope residual). Copy the functions you need into this study's `src/`.
    - Copy `harness.py`, `common8.py` → `common10.py` and `runner5c.py` into this study's `src/` (the copied harness then caches in this study's git-ignored `cache/`). Import everything else from the copies too, never from the round 8 directory, so no earlier study directory is written to.
  - round 9 `research/phase2_r9_fixes_20261017/`:
    - `src/variants.py`: SUB with switchable fixes; `make()` with defaults reproduces SUB; `aggregate()` replaces `step_mean` by the cell median or minimum;
    - `run_r9.py`: the gate code;
    - `robust_r9.py` and `outputs/r9_robust_variants.csv`: the per-variant robustness table.
  - round 8 tables: `outputs/table_events.csv` (per program × cell: `depth_<variant>`, `R_seg`, `R_cell`, `t_cv_end`, `month`, `setpoint`), `outputs/table_anchors.csv` (per anchor: `step_to_top_cell1_V..cell4_V`, `end_cell1_V..cell4_V`), `outputs/table_cases.csv`, `DATA_DICTIONARY.md`.
  - events `research/phase2_anchor_step_20261013/src/events.py` (`step_programs` returns per-cell `step_cell1_V..step_cell4_V` and `step_mean` for every variant in `STEP_VARIANTS`), V2 `research/phase2_v2_phase_matched_20261013/src/v2.py` (`end45`, `month_steps`, `phase_diff`, `beta_a4`, `theil_sen`).
- **Read-only source outside this worktree.** The **submission branch** `exp/phase2-anchor-step-20261013`, commit `5cd305c`, in `/Users/shane/Desktop/Arena_1013_model`. Use only `git -C … show` / `git -C … archive`; never `cd` into it or write to it. `TechArena_Challenge2_Team_Package/my_model/model_template.py` there is the **submitted model SUB = T_main**. Extract the package into `cache/submitted_package/`. Read `EXPECTED_SOH` from `research/phase2_v3_20261015/package_submission.py` at that commit. Record copied files with SHA256 in `sources/SOURCES.md`.
- **Concurrency guard.** At the start and before every commit, run `git log --oneline -5` and compare with your last commit. On an unexpected commit, stop editing shared files, record it, and add files by explicit path only. Never `git add -A` / `.`, never bare `git stash`, never rewrite others' work. Untracked leftovers in the submission worktree (`research/phase2_round3_models_20261014/`, other prompt folders) are not yours; ignore them.
- **Commits.** Commit this prompt first, copied from `/Users/shane/Desktop/Arena_1013_model/research/phase2_r10_cell_steps_20261017/EXECUTION_PROMPT.md` to the same relative path. Commit at the end of every step, then `git push -u origin exp/phase2-r10-cell-steps-20261017`. Never push elsewhere; never force. End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify:** any `TechArena_Challenge2_Team_Package/`, any earlier study directory (rounds 3–9 included), any file outside this worktree.
- **Language and bytecode.** Markdown is English first, Chinese second, in this file's layout. Code comments are English only. Run Python with `python3 -B`. No downloads are needed. The package check needs Python 3.11 (`python3.11 -m venv cache/venv311`, then `pip install -r` the package's `requirements.txt`).

## 2. Context

**Task.** Estimate the SOH (C/20 capacity / 102 Ah) of a 4 × 102 Ah LFP series pack on CK0..CK7. Only CK0 = 100.41 Ah is released. The framework cuts data at the checkup date (`load_dataset(data, until=CK_k)`).

**Proxies** (all seen, so every real-scenario number is exposed-exploratory). P_k = Q_fc,k + ε0 + Δ, where:
- Q_fc,k is the post-CK_k empty→full anchor charge;
- ε0 = 100.41 − Q_fc,0;
- Δ ∈ {0, 0.4, 0.8}.

Treat differences below 0.25 pp in real proxy MAE as unresolvable. Selection therefore rests on the causal scenarios.

**SUB = T_main** (commit `5cd305c`).
- **Real proxy metrics:** MAE Δ0/0.4/0.8 = 0.1972/0.1257/0.1464 pp; MAX 0.6090/0.2277/0.2277.
- **Causal metrics:** pseudo (mean MAE over PG1, PG2, PC5, PC10 at Δ 0.4) 0.1439; cold start (CS, CSE) 0.1703.
- **Real errors at Δ 0.4 (pp):** CK1 +0.217, CK2 +0.039, CK3 +0.080, CK4 +0.228, CK5 +0.150, CK6 −0.163, CK7 −0.004.
- **Branches in the real scenario:** CK1, CK3 `fallback`; CK2 `sqrt_gap`; CK4–CK7 `phase`.

**How SUB uses the step** (main detection variant).
- **Per program.** For every deep program p, `step_programs` locates the graphite step on each cell: `loc_v(p, c)`, the depth in Ah below the CV end, for variant v and cell c. SUB uses `step_mean(p) = mean_c loc_main(p, c)`.
- **Phase branch.**
  - E(m) is the last 45 °C `step_mean` of month m, d(m) the days from that program to CK_m+1, and r(m) the Theil–Sen rate over month m's 45 °C programs (if ≥ 3).
  - x = E(k−1) − E(k−2) + r(k−1)·(d(k−1) − d(k−2)), and Q = Q_fc,k−1 + ε + β·x.
  - β comes from the charge-side step-to-top of the visible 25 °C anchors (`beta_a4`, prior 1, τ = 1).
- **Fallback.** Q = anchor term + `step_mean(after[-1]) − step_mean(after[0])` over the programs after the last anchor.
- **sqrt_gap** uses no step quantity except to decide that the coverage gap exceeds 10 days.

**What rounds 8 and 9 found** (all from the full data; diagnostic).
- **Per-cell offsets.** Each cell keeps a fixed sign of `R_cell = loc_main(p, c) − median_c loc_main(p, c)` in 8 of 8 months: cell1 −0.36, cell2 +0.13, cell3 +0.25, cell4 −0.13 Ah. This was seen before round 8's registration.
- **Divergence.** The spread (max − min over cells) grows 0.56 → 0.62 → 0.72 Ah over months 0–2 / 3–5 / 6–7. The weakest cell at maximum depth is cell1 in most months.
- **Effect on SUB.** The mean-versus-median difference moves SUB's increment by −0.15 Ah at CK6, +0.10 at CK5, −0.09 at CK4 and +0.05 at CK7.
- **Top state.** At the anchor CV end, the cell voltage spread falls 88 → 52 mV while cell3 stays highest. The per-cell rest voltages before the anchor charge spread from 7 to 35 mV. The per-cell charge-side step→top distance (`step_to_top_cellX_V`, 0.25 Ah grid, 2 Ah smoothing, anchors only, once per month) spreads 0.75–2.0 Ah.
- **Step scale.** The step moves 0.745 Ah per Ah of Q_fc fade (CI 0.674–0.765; 0.70–0.73 without month 0). This is not this round's subject; keep β as in SUB.
- **Round 9, median of cells** (P2a: `step_mean` → median, β unchanged).
  - It passes the causal gates on the main variant: pseudo 0.1385, cold 0.1511, changed non-real cases 0.217 → 0.195 pp with the worst case +0.057; real MAE Δ0.4 0.1135.
  - It is **not robust**: it wins on only 3 of 6 detection variants. On dvdq_peak, real MAE goes 0.2567 → 0.3608, pseudo 0.1506 → 0.1720 and cold 0.2165 → 0.2488. V3 (2026-10-15) found the same.
  - The 4-cell minimum (P2b) fails every gate.
- **SUB per detection variant** (real MAE Δ0.4 / pseudo / cold, from `r9_robust_variants.csv`):

  | variant | real | pseudo | cold |
  |---|---|---|---|
  | main | 0.1257 | 0.1439 | 0.1703 |
  | band_narrow | 0.1243 | 0.1352 | 0.1606 |
  | windows_minus3 | 0.1815 | 0.1405 | 0.2071 |
  | windows_plus3 | 0.2142 | 0.1435 | 0.2192 |
  | dvdq_peak | 0.2567 | 0.1506 | 0.2165 |
  | ir_corrected | 0.1532 | 0.1295 | 0.1930 |

**Known effects (do not re-test):**
- the first deep program after every anchor sits 0.41–0.56 Ah deeper (0.83 Ah in month 0);
- the step jumps about +0.18 Ah at every 25→45 °C switch;
- the 6 A CV tail and the anchor start state do not explain ΔQ_fc scatter;
- pulse resistance is flat and quantised (0.049 mΩ);
- operation counters book the 20 A pulse as charge, so integrate `current_A` instead.

## 3. Common rules

1. **Register before evaluating.** Each of WP1–WP4 writes `wpN/protocol.json` (candidates with exact formulas, fixed constants with their numeric values, gates, the adoption rule and the diagnostics) and commits it with its SHA256 before any candidate of that WP is run on any scenario. Anything added after registration is labelled `exploratory-unregistered`, reported separately and **never adoptable**.
2. **Branch freeze.** A candidate changes only the per-program step quantities inside the phase and fallback branches, and how they are combined. The branch chosen at every case, the programs selected (E_cur, E_prev, the rate-fit set, after[0], after[-1]), n, d and β are taken from SUB unchanged. Implement this by replaying SUB's selection (`internals.decompose` already returns the selected programs as `ev_*` timestamps). If a candidate's per-cell value is NaN for a selected program, use the available cells, and record every such case.
3. **Causality.** Every candidate input must come from the scenario's cut data: per-cell locations of visible programs, per-cell voltages of visible samples, visible anchors only. A quantity fitted across time (for example a coefficient in WP3) is fitted at each cut on visible data only. The full-data round 8 tables are allowed for **diagnostics and for fixing registered constants** (WP0 noise scale). Each such use is named in the protocol.
4. **Robustness is a gate, not a footnote.** See G_robust in section 4. This is the lesson of round 9.
5. **No model changes outside this study.** Never edit the submission. A candidate class is built only in WP4, inside this study, and only for a candidate that passed.
6. **Small samples.** 7 real cases; 37–40 causal cases, many of them near-duplicates (PC5 = PC5_all for k ≥ 3; PG1/PG2/PC10 share sqrt cases). Report the counts with every metric. Statistics are descriptive.
7. **Units and signs.** Ah and pp (pp = 100·Ah/102); error = predicted − proxy.
8. **Determinism.** Cache keys include every parameter. Reruns must be byte-identical for CSV/JSON. Seeds are fixed in the protocols.

## 4. Common gates (all at Δ = 0.4, against SUB on the same detection variant unless stated)

- **G_pseudo:** mean MAE over PG1, PG2, PC5, PC10 ≤ SUB + 0.005 pp (main variant).
- **G_cold:** mean MAE over CS, CSE ≤ SUB + 0.005 pp (main variant).
- **G_changed (main variant):** take the non-real cases whose prediction changes by > 1e-9 Ah. Their mean |err| must fall by ≥ 0.02 pp, and no single one may worsen by > 0.10 pp. If none changes, the candidate is untestable and not adoptable.
- **G_robust:** recompute the candidate and SUB on each of the 6 detection variants (for WP1 ensembles: on each leave-one-variant-out ensemble, see WP1).
  - Let causal = the mean of pseudo and cold.
  - The candidate must satisfy causal ≤ SUB_v + 0.005 on at least 5 of 6, and causal ≤ SUB_v + 0.03 and real MAE ≤ SUB_v + 0.05 pp on all 6.
  - Round 9's median fails this (dvdq_peak: causal +0.027, real +0.104).
- **G_event (non-proxy evidence, main variant, diagnostic tables).** Build the candidate's pack-level step for every program of the full data and fit depth = a_setpoint + b·Q_interp, leaving each month out (round 8's R_anc_b, `wp5/run_wp5.py::r_anc_b`). The SD of these residuals over the 40 bracketed events must not exceed SUB's by more than 2 %. Here the anchors serve only as a smooth reference for the step series, not as scored proxies.
- **G_real_safety:** real MAX at each Δ not worse than SUB by > 0.10 pp. Real MAE is reported but not used for selection.
- **Adoption rule (within a WP):**
  - a candidate is *passing* if it passes all gates;
  - among passing candidates, take the lowest causal mean on the main variant; ties within 0.002 pp go to the simpler candidate (fewer constants);
  - otherwise the WP's verdict is "no candidate".

## 5. Work packages

### WP0 — Setup and re-baselining (cap 0.5 h)

- Create the worktree, `notes/STATUS.md`, `notes/DECISIONS.md`, `.gitignore` (`cache/`, `__pycache__/`, `*.pyc`), `sources/SOURCES.md`; copy the code listed in section 1.
- **Reproduce** (within 0.001 pp):
  - SUB's real MAE/MAX, pseudo, cold and the per-checkup errors in section 2;
  - round 9's P2a numbers and the SUB-per-variant table.
  - Confirm that the extracted `5cd305c` class equals the research SUB per checkup (≤ 0.0005 pp) and `EXPECTED_SOH`.
- **Build the per-cell location cache:** for every scenario cut and every variant, `loc_v(p, c)` with the program's `t_cv_end`, `setpoint`, `t_measured` and its SUB selection role. Also build the per-cell CV-end voltages `V_c(p)` at the program's CV end, and for every visible anchor `step_to_top_c` and `end_c` voltages.
- **Fix the detection-noise scale used by WP2 and WP3:**
  - σ_det = 1.4826·MAD of `R_seg` over the round 8 cell rows (`table_events.csv`, unit cell1_V..cell4_V, 45 °C segments with ≥ 4 programs, main variant), pooled over cells, plus the same per cell;
  - also σ_det for every variant, recomputing R_seg on that variant's per-cell depths with round 8's `wp2/run_wp2.py::add_residuals` rule.
  - Record the values in `wp0/outputs/noise_scale.json`. These values were seen in round 8 (exposure noted); they are a noise scale, not an outcome.
- **Done:** all reproductions pass (if SUB fails, stop the run and record why), the caches and `noise_scale.json` exist, plus the common criteria. `wp0/REPORT.md` is short.

### WP1 — Idea A: stabilise per-cell detection (cap 1.5 h)

**Idea.** The 4-cell median is fragile because each single detection is noisy, and the median of 4 is the mean of whichever two cells happen to be in the middle. Averaging each cell's location over detection variants should reduce that noise before the cells are combined.

**Candidates (register exactly):**
- **A1:** `loc_ens(p, c)` = mean over the 6 variants of `loc_v(p, c)` (NaN-aware, requiring ≥ 4 finite variants, else NaN); pack step = mean over cells.
- **A2:** same ensemble; pack step = median over cells.
- **A3:** `loc_ens(p, c)` = median over the 6 variants; pack step = median over cells.

**Robustness for ensembles.** G_robust is evaluated on the 6 leave-one-variant-out ensembles: each candidate is rebuilt from 5 variants, against SUB on the main variant. All three criteria of G_robust apply across these 6 rebuilds.

**Registered diagnostics (descriptive):**
- per-cell noise σ of `loc_ens` versus each single variant, with R_seg recomputed on `loc_ens`, 45 °C segments with ≥ 4 programs; expected lower;
- the R_cell sign pattern and spread trend recomputed on `loc_ens`, to check whether the round 8 cell offsets survive averaging;
- per-checkup real errors and SOH for each candidate.

- **Done:** protocol committed first, all gates and diagnostics computed, verdict per candidate, adoption rule applied, `wp1/REPORT.md`, plus the common criteria.

### WP2 — Idea B: combine per-cell changes (cap 1.5 h)

**Idea.** The model needs only a change between two programs. If one cell drifts in a given month, the change of the **other three** cells is a cleaner estimate than any combination of positions.

**Per-cell change** (main variant unless stated; the programs are SUB's selection):
- phase: `x_c = E_c(k−1) − E_c(k−2) + r_c(k−1)·(d(k−1) − d(k−2))`, with E_c the cell's location at SUB's E programs and r_c the Theil–Sen rate of the cell over SUB's rate-fit programs (0 if SUB's r is 0);
- fallback: `inc_c = loc(after[-1], c) − loc(after[0], c)`.

**Candidates (register exactly; τ is numeric, from WP0):**
- **B1:** x = median over cells of x_c (the same for the fallback increment).
- **B2:** one-cell rejection.
  - For each cell, dev_c = x_c − median of the other three.
  - If max_c |dev_c| > τ, drop that one cell and average the other three; else average all four.
  - τ = 3·√2·σ_det, with σ_det the pooled main-variant value from WP0. On variant v, use σ_det,v.
- **B3** (only if WP1 adopted a candidate; otherwise record "skipped by rule"): B2 computed on WP1's adopted `loc_ens`, with σ_det recomputed on `loc_ens` in WP1's diagnostics.

**Registered diagnostics:**
- the rejection log: for every case, whether a cell was dropped, which cell, |dev| and month;
- the share of rejections per cell, compared with round 8's pattern (cell1, cell3);
- per-checkup real errors and SOH.

- **Done:** protocol committed first, all gates and diagnostics computed, verdicts, adoption rule, `wp2/REPORT.md`, plus the common criteria.

### WP3 — Idea C: remove the cells' top-state drift (cap 3 h)

**Idea.** The step depth is measured downward from the CV end. The CV end is triggered by the **pack** voltage, so a cell that ends the CCCV less full than the others shows a shallower step without any ageing. The cell voltages at the CV end differ (spread 52–88 mV, cell3 highest) and change over time. If this top-state drift drives part of the per-cell divergence, correcting it should leave the ageing signal.

**WP3a — mechanism check (registered before computing; no proxies used).** Two covariates, each tested independently on the round 8 event table plus WP0's per-cell voltages (diagnostic, full data, main variant):
- **u_c(p)** = V_c − mean over cells of V at program p's CV end (mV);
- **w_c(m)** = `step_to_top_c` − mean over cells of `step_to_top` at anchor m, assigned to every program of month m (Ah).

For each covariate:
- regress R_cell(p, c) on it **within cell** (de-mean both per cell, so the fixed offsets drop), pooled over cells;
- report the slope, a block-bootstrap 90 % CI over months (2000 resamples, fixed seed), the within-cell R², and the sign per cell.

Expected sign: positive (a fuller top gives a deeper step).

**Pass rule:** CI excludes 0 with the expected sign, the sign holds in ≥ 3 of 4 cells, and within-cell R² ≥ 0.30. A covariate that fails is not used. If both fail, WP3 **exits** with "top-state mechanism not supported", and no WP3b candidate is built.

**WP3b — candidates (only for covariates that passed WP3a; register after WP3a and before evaluating):**
- **C1 (u, causal coefficient):** `loc_c − k·u_c`. k is the within-cell OLS slope of R_cell on u_c, fitted at each cut on the visible programs only (needs ≥ 2 visible months, else k = 0). Pack step = mean over cells.
- **C2 (w, fixed coefficient 1):** `loc_c − w_c(m)` for programs of month m. This is a pure Ah-for-Ah re-referencing to the month's own anchor, with no fitted constant. Pack step = mean over cells.
- **C3:** the passing covariate's correction followed by B2's rejection rule instead of the mean (only if WP2 B2 passed; otherwise skipped by rule).

u and w do not depend on the detection variant, so G_robust is computed by applying the same correction to each variant's per-cell locations.

**Registered diagnostics:**
- the per-cell spread trend and R_cell sign pattern after correction (does the divergence shrink?);
- per-checkup real errors and SOH.

- **Done:** WP3a verdicts, WP3b gates and verdicts or a recorded exit, `wp3/REPORT.md`, plus the common criteria.

### WP4 — Combination and candidate class (cap 2 h)

- If no candidate in WP1–WP3 passed: mark WP4 **skipped** with that reason and go to WP5.
- **Combination.** Otherwise, register **one** combination in `wp4/protocol.json` before evaluating it: the adopted candidates of the passing WPs, composed in the order A → C → B. Evaluate it with all gates. The final candidate is the combination if it passes and has a lower causal mean than every single adopted candidate. Otherwise it is the single adopted candidate with the lowest causal mean.
- **Candidate class.** Write `wp4/candidate_model/model_template.py`: a copy of the submitted `5cd305c` class with the minimal change.
  - The package must compute everything itself with numpy/pandas only, without the research harness. This includes per-cell locations; for idea A, all 6 detection variants (the dvdq_peak grid method and the ir_corrected pulse-resistance correction included); and for idea C, per-cell CV-end voltages or per-cell anchor step→top.
  - Keep the class's public interface, constants style and docstring style.
- **Checks:**
  - **G_causal:** `checks5c.candidate_checks`. Future rows replaced by noise must give identical outputs at all 8 checkups, and fitting on CK1-cut data must give identical outputs.
  - **G_impl:** class versus research per checkup ≤ 0.001 pp.
  - **Package:** a package copy in `cache/` with the candidate class; `validate_submission.py` under Python 3.11 with the package's `requirements.txt`; a full `run_model.py` train + test run with timing.
- **Output:** a SOH table, SUB versus candidate, CK0–CK7, Δ 0.4, with the per-checkup change.
- **Never copy the class into the submission package.**
- **Done:** combination verdict, candidate class, all checks passed (if a check fails, fix the class, not the research numbers; if it cannot be fixed within the cap, record "capped"), `wp4/REPORT.md`, plus the common criteria.

### WP5 — Synthesis (cap 1 h)

`FINAL_REPORT.md` (bilingual, conclusions first):
1. **Verdict per idea.**
   - A, B and C, each with its gates table: G_pseudo, G_cold, G_changed, G_robust (per variant), G_event, G_real_safety.
   - For C, WP3a's mechanism result.
   - State plainly which ideas failed and why.
2. **What changed and where.** Per-checkup real errors and SOH, SUB versus the final candidate (if any), with the branch at each checkup. Note that differences below 0.25 pp in real MAE are unresolvable.
3. **Cell picture after this round.** Do the round 8 per-cell offsets and the divergence survive ensemble detection and top-state correction? Is the divergence detection noise, top-state drift or something else (unexplained)?
4. **Recommendation.** Wire or not, with the exact file change. The decision to wire is the user's; this round only recommends.
5. **Risks and limits.** Exposure, near-duplicate cases, the full-data constants used (σ_det), anything recorded in `notes/DECISIONS.md`.

Also write `README.md`: what the round did, and how to rebuild every output, with one command per WP.

- **Done:** both files and the Global Done list.

---

<a id="zh"></a>

# 第 10 轮：稳健的单体台阶合并——执行说明

> **语言：** [English](#en) · 中文

2026-10-17 编写。本文件自成一体。英文为执行文本，中文为供阅读的译文；两者不一致时以英文为准。

**本轮目标。** 第 8 轮发现，电池组的四个单体各自带有持续存在、并在缓慢拉开的台阶深度偏移，而提交模型使用的四单体**均值**会把这种拉开计入增量（CK6 处约 −0.15 Ah）。第 9 轮表明，最直接的修正——四单体**中位数**——在主检测方法上通过了因果检验，但换检测方法就不稳健（dvdq_peak 真实 MAE 0.257 → 0.361）。本轮**逐个**检验三个更有依据的想法，每个都先登记、后评估：

- **A——先把单体检测做稳：** 每个单体的台阶位置在 6 种检测变体上取平均，再合并单体。
- **B——合并单体的变化量，而不是位置：** 先算每个单体自己的逐月台阶变化，再稳健地合并四个变化量（中位数，或剔除一个离群单体）。
- **C——消除单体顶部状态的漂移：** 用每个单体自己的参照点，按该单体在 CV 结束时有多满来修正它的台阶深度，只留下老化部分。

本轮给出每个想法的登记结论；只有当某个候选通过全部检验时，才构建候选模型类并做提交包检查。**本轮绝不把任何改动接入提交。**

工作包 WP0–WP5。WP0 最先。WP1、WP2、WP3 按此顺序逐个检验（WP2 的候选 B3 依赖 WP1 的结果）。WP4 需要 WP1–WP3。WP5 最后。每个 WP 可单独作为一个 `/goal` 运行。

## 0. 工作方式（所有工作包）

- **无人值守。** 不要停下来提问。遇到未决事项时，选择满足本文所有规则的最保守方案，记入 `notes/DECISIONS.md`，然后继续。
- **重启。** 每步完成后更新 `notes/STATUS.md`：WP、已完成、下一步、最近一次提交。重启时先读 `notes/STATUS.md` 和 `notes/DECISIONS.md` 再继续。已完成的 WP 或步骤不要重做。
- **诚实优先。** "没有想法通过"是有效结论。失败的想法与通过的想法同样直白地报告。
- **单个 WP 的 Done** 指下列通用条件加上该 WP 自己的清单：
  1. 该 WP 的登记协议（`wpN/protocol.json` + `wpN/protocol.sha256`）在评估该 WP 任何候选**之前**已提交（WP0 和 WP5 没有协议）；
  2. 有双语的 `wpN/REPORT.md`，结论在前；
  3. `notes/STATUS.md` 把该 WP 标为 done、capped、skipped 或 exited，并附一行结果；
  4. 所有提交都已推送到 `origin exp/phase2-r10-cell-steps-20261017`，`git status` 中没有未提交的研究文件。
- **全局 Done：** WP0–WP5 各自 done、capped、skipped，或按登记规则 exited；`FINAL_REPORT.md` 和 `README.md` 存在（双语，结论在前）；通用条件 3–4 成立。

## 1. 工作区、隔离与 git

- **Worktree 和分支（在 WP0 中按需创建，可重复执行）。**
  - 基点：第 9 轮在**本地**分支 `exp/phase2-r9-fixes-20261017` 上的最终提交（编写时为 `6749c63`；以分支末端为准并记录哈希）。其中包含第 8 轮（`research/phase2_r8_error_table_20261017/`）和第 9 轮（`research/phase2_r9_fixes_20261017/`）。该分支尚未推送；推送本轮分支时会一并公开这些提交，这是预期行为。
  - 创建：`git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1017_r10_cells -b exp/phase2-r10-cell-steps-20261017 <base>`。若已存在，确认其历史包含 `<base>` 后复用。
  - 只在 `/Users/shane/Desktop/Arena_1017_r10_cells` 中工作。研究目录为 `research/phase2_r10_cell_steps_20261017/`。
- **可复用的代码（基点分支上已有；要改的先复制到本研究，只改副本）：**
  - 第 8 轮 `research/phase2_r8_error_table_20261017/src/`：
    - `harness.py`（第 3 轮 harness 副本，缓存位于其所在研究目录）；
    - `common8.py`（断言 worktree 名为 `Arena_1017_r8_err`，因此必须复制为 `common10.py` 并修改断言）；
    - `runner5c.py`（场景 real、PG1、PG2、PC5、PC10、CS、CSE、PC5_all、PC10_all；`scenario_tables`、`run`、`scen_mean`）；
    - `tsqrt.py`（T_main）、`v3.py`、`internals.py`（SUB 的逐步重放，含每次预测所用的事件）、`eventcurves.py`、`slicestats.py`、`checks5c.py`（候选检查）。
    - `src/` 之外：`wp2/run_wp2.py` 中的函数 `add_residuals`（R_seg、R_anc、R_cell 的定义）和 `wp5/run_wp5.py` 中的函数 `r_anc_b`（逐月留出的自由斜率残差）。把需要的函数复制到本研究的 `src/`。
    - 把 `harness.py`、`common8.py` → `common10.py` 和 `runner5c.py` 复制到本研究的 `src/`（复制后的 harness 会把缓存写到本研究被 git 忽略的 `cache/`）。其余模块也都从副本导入，绝不从第 8 轮目录导入，以免写入任何较早的研究目录。
  - 第 9 轮 `research/phase2_r9_fixes_20261017/`：
    - `src/variants.py`：带可切换修正的 SUB，默认参数的 `make()` 复现 SUB，`aggregate()` 把 `step_mean` 换成单体中位数或最小值；
    - `run_r9.py`：检验代码；
    - `robust_r9.py` 和 `outputs/r9_robust_variants.csv`：逐变体稳健性表。
  - 第 8 轮的表：`outputs/table_events.csv`（每程序 × 单体：`depth_<variant>`、`R_seg`、`R_cell`、`t_cv_end`、`month`、`setpoint`），`outputs/table_anchors.csv`（每锚点：`step_to_top_cell1_V..cell4_V`、`end_cell1_V..cell4_V`），`outputs/table_cases.csv`，`DATA_DICTIONARY.md`。
  - events `research/phase2_anchor_step_20261013/src/events.py`（`step_programs` 对 `STEP_VARIANTS` 中每个变体返回单体列 `step_cell1_V..step_cell4_V` 和 `step_mean`），V2 `research/phase2_v2_phase_matched_20261013/src/v2.py`（`end45`、`month_steps`、`phase_diff`、`beta_a4`、`theil_sen`）。
- **本 worktree 之外的只读来源。** **提交分支** `exp/phase2-anchor-step-20261013` 的提交 `5cd305c`，位于 `/Users/shane/Desktop/Arena_1013_model`。只用 `git -C … show` / `git -C … archive`，绝不 `cd` 进去或写入。其中的 `TechArena_Challenge2_Team_Package/my_model/model_template.py` 就是**提交模型 SUB = T_main**。把提交包解压到 `cache/submitted_package/`，从该提交的 `research/phase2_v3_20261015/package_submission.py` 读取 `EXPECTED_SOH`。在 `sources/SOURCES.md` 中记录复制的文件及其 SHA256。
- **并发保护。** 开始时和每次提交前运行 `git log --oneline -5` 并与自己的上一次提交比对。若出现意外提交，停止编辑共享文件、记录下来，并只按明确路径添加文件。绝不 `git add -A` / `.`，绝不裸用 `git stash`，绝不改写他人的工作。提交 worktree 中未跟踪的残留（`research/phase2_round3_models_20261014/`、其他 prompt 文件夹）不属于你，忽略即可。
- **提交。** 先提交本 prompt：从 `/Users/shane/Desktop/Arena_1013_model/research/phase2_r10_cell_steps_20261017/EXECUTION_PROMPT.md` 复制到相同的相对路径。每一步结束都提交，然后 `git push -u origin exp/phase2-r10-cell-steps-20261017`。绝不推送到别处，绝不强推。每条提交信息都以 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` 结尾。
- **不得修改：** 任何 `TechArena_Challenge2_Team_Package/`、任何较早的研究目录（含第 3–9 轮）、本 worktree 之外的任何文件。
- **语言与字节码。** Markdown 先英文后中文，版式同本文件。代码注释只用英文。用 `python3 -B` 运行 Python。不需要下载任何东西。提交包检查需要 Python 3.11（`python3.11 -m venv cache/venv311`，然后 `pip install -r` 提交包的 `requirements.txt`）。

## 2. 背景

**任务。** 估计 4 × 102 Ah LFP 串联电池组在 CK0..CK7 的 SOH（C/20 容量 / 102 Ah）。只公开了 CK0 = 100.41 Ah。框架在检查日期截断数据（`load_dataset(data, until=CK_k)`）。

**代理真值**（都已看过，所以每个真实场景数字都是已曝光的探索性结果）。P_k = Q_fc,k + ε0 + Δ，其中：
- Q_fc,k 是 CK_k 之后从空到满的锚点充电量；
- ε0 = 100.41 − Q_fc,0；
- Δ ∈ {0, 0.4, 0.8}。

真实代理 MAE 中低于 0.25 pp 的差异视为无法分辨，因此选择依据是因果场景。

**SUB = T_main**（提交 `5cd305c`）。
- **真实代理指标：** MAE Δ0/0.4/0.8 = 0.1972/0.1257/0.1464 pp；MAX 0.6090/0.2277/0.2277。
- **因果指标：** 伪场景（Δ 0.4 下 PG1、PG2、PC5、PC10 的平均 MAE）0.1439；冷启动（CS、CSE）0.1703。
- **Δ 0.4 下的真实误差（pp）：** CK1 +0.217、CK2 +0.039、CK3 +0.080、CK4 +0.228、CK5 +0.150、CK6 −0.163、CK7 −0.004。
- **真实场景的分支：** CK1、CK3 为 `fallback`；CK2 为 `sqrt_gap`；CK4–CK7 为 `phase`。

**SUB 如何使用台阶**（主检测变体）。
- **逐程序。** 对每个深放程序 p，`step_programs` 在每个单体上定位石墨台阶：`loc_v(p, c)`，即变体 v、单体 c 在 CV 结束以下的深度（Ah）。SUB 使用 `step_mean(p) = mean_c loc_main(p, c)`。
- **phase 分支。**
  - E(m) 是第 m 月最后一个 45 °C 的 `step_mean`，d(m) 是该程序到 CK_m+1 的天数，r(m) 是第 m 月 45 °C 程序的 Theil–Sen 速率（≥ 3 个时）。
  - x = E(k−1) − E(k−2) + r(k−1)·(d(k−1) − d(k−2))，Q = Q_fc,k−1 + ε + β·x。
  - β 由可见 25 °C 锚点的充电侧台阶到顶部距离得到（`beta_a4`，先验 1，τ = 1）。
- **fallback。** Q = 锚点项 + `step_mean(after[-1]) − step_mean(after[0])`，取最后一个锚点之后的程序。
- **sqrt_gap** 除了判断覆盖缺口是否超过 10 天外，不使用任何台阶量。

**第 8、9 轮的发现**（都来自全量数据，属诊断）。
- **单体偏移。** 每个单体的 `R_cell = loc_main(p, c) − median_c loc_main(p, c)` 在 8 个月中 8 个月保持同号：cell1 −0.36、cell2 +0.13、cell3 +0.25、cell4 −0.13 Ah。这一点在第 8 轮登记前已被看到。
- **拉开。** 离散（单体最大值 − 最小值）在第 0–2 / 3–5 / 6–7 月从 0.56 增至 0.62、再到 0.72 Ah。大多数月份最大深度处最弱的单体是 cell1。
- **对 SUB 的影响。** 均值与中位数之差使 SUB 的增量在 CK6 移动 −0.15 Ah，CK5 +0.10，CK4 −0.09，CK7 +0.05。
- **顶部状态。** 锚点 CV 结束时，单体电压差从 88 降到 52 mV，cell3 始终最高。锚点充电前的单体静置电压差从 7 增到 35 mV。单体充电侧台阶→顶部距离（`step_to_top_cellX_V`，0.25 Ah 网格、2 Ah 平滑，仅锚点、每月一次）的单体间差为 0.75–2.0 Ah。
- **台阶比例。** 台阶随 Q_fc 衰减每 Ah 移动 0.745 Ah（CI 0.674–0.765；不含第 0 月为 0.70–0.73）。这不是本轮主题，β 保持与 SUB 相同。
- **第 9 轮，单体中位数**（P2a：`step_mean` → 中位数，β 不变）。
  - 在主变体上通过因果检验：伪场景 0.1385，冷启动 0.1511，变化的非真实案例 0.217 → 0.195 pp，最差案例 +0.057；真实 MAE Δ0.4 0.1135。
  - **不稳健**：6 种检测变体中只在 3 种上更好。dvdq_peak 上真实 MAE 0.2567 → 0.3608，伪场景 0.1506 → 0.1720，冷启动 0.2165 → 0.2488。V3（2026-10-15）也发现了同样的问题。
  - 四单体最小值（P2b）所有检验都不通过。
- **SUB 在各检测变体上的指标**（真实 MAE Δ0.4 / 伪场景 / 冷启动），见英文表格（来自 `r9_robust_variants.csv`）。

**已知效应（不再重复检验）：**
- 每个锚点后的首个深放程序深 0.41–0.56 Ah（第 0 月 0.83 Ah）；
- 每次 25→45 °C 切换时台阶跳变约 +0.18 Ah；
- 6 A CV 尾段和锚点起始状态不能解释 ΔQ_fc 的离散；
- 脉冲内阻平稳且量化（0.049 mΩ）；
- 运行计数器把 20 A 脉冲记为充电，所以改用对 `current_A` 积分。

## 3. 通用规则

1. **先登记，后评估。** WP1–WP4 各自写出 `wpN/protocol.json`（候选的精确公式、固定常数及其数值、检验、采用规则和诊断项），并在该 WP 的任何候选在任何场景上运行之前，连同 SHA256 一起提交。登记后新增的内容一律标为 `exploratory-unregistered`，单独报告，**永远不可采用**。
2. **分支冻结。** 候选只改变 phase 和 fallback 分支内部逐程序的台阶量及其合并方式。每个案例所走的分支、所选程序（E_cur、E_prev、速率拟合集、after[0]、after[-1]）、n、d 和 β 都沿用 SUB，不作改变。实现方式是重放 SUB 的选择（`internals.decompose` 已以 `ev_*` 时间戳返回所选程序）。若候选在某个所选程序上的单体值为 NaN，就用可用的单体，并记录每一次这样的情况。
3. **因果性。** 候选的每个输入都必须来自场景的截断数据：可见程序的单体位置、可见样本的单体电压、只用可见锚点。随时间拟合的量（例如 WP3 中的系数）在每个截断点上只用可见数据拟合。全量数据的第 8 轮表格可用于**诊断和确定登记常数**（WP0 的噪声尺度），每种用法都要在协议中写明。
4. **稳健性是检验门槛，不是脚注。** 见第 4 节的 G_robust。这是第 9 轮的教训。
5. **不在本研究之外改模型。** 绝不编辑提交。候选模型类只在 WP4、在本研究目录内、且只为通过检验的候选构建。
6. **样本少。** 7 个真实案例；37–40 个因果案例，其中很多近似重复（k ≥ 3 时 PC5 = PC5_all；PG1/PG2/PC10 共享 sqrt 案例）。每个指标都要附上样本数。统计量均为描述性。
7. **单位与符号。** Ah 和 pp（pp = 100·Ah/102）；误差 = 预测 − 代理。
8. **确定性。** 缓存键包含所有参数。重跑时 CSV/JSON 必须逐字节相同。随机种子在协议中固定。

## 4. 通用检验门槛（都在 Δ = 0.4 下，除非另有说明，均与同一检测变体上的 SUB 比较）

- **G_pseudo：** PG1、PG2、PC5、PC10 的平均 MAE ≤ SUB + 0.005 pp（主变体）。
- **G_cold：** CS、CSE 的平均 MAE ≤ SUB + 0.005 pp（主变体）。
- **G_changed（主变体）：** 取预测变化超过 1e-9 Ah 的非真实案例。它们的平均 |err| 必须下降至少 0.02 pp，且任何一个的变差不得超过 0.10 pp。若没有任何案例变化，则候选无法检验，不可采用。
- **G_robust：** 在 6 种检测变体上分别重算候选和 SUB（WP1 的集成候选则在每个留一变体集成上重算，见 WP1）。
  - 记因果指标 = 伪场景与冷启动的平均。
  - 候选至少在 6 个中的 5 个上满足 因果 ≤ SUB_v + 0.005，并且在全部 6 个上满足 因果 ≤ SUB_v + 0.03、真实 MAE ≤ SUB_v + 0.05 pp。
  - 第 9 轮的中位数不满足此条（dvdq_peak：因果 +0.027，真实 +0.104）。
- **G_event（非代理证据，主变体，诊断表）。** 为全量数据的每个程序构建候选的 pack 级台阶，拟合 depth = a_setpoint + b·Q_interp，逐月留出（第 8 轮的 R_anc_b，`wp5/run_wp5.py::r_anc_b`）。40 个被锚点夹住的事件上这些残差的标准差不得比 SUB 大超过 2 %。这里锚点只作为台阶序列的平滑参照，而不是计分用的代理真值。
- **G_real_safety：** 各 Δ 下真实 MAX 比 SUB 差不超过 0.10 pp。真实 MAE 只报告，不用于选择。
- **采用规则（WP 内）：**
  - 通过全部检验的候选为*通过*；
  - 在通过的候选中，取主变体上因果指标最低者；相差在 0.002 pp 以内时取更简单者（常数更少）；
  - 否则该 WP 的结论为"无候选"。

## 5. 工作包

### WP0——环境搭建与重新基线（上限 0.5 h）

- 创建 worktree、`notes/STATUS.md`、`notes/DECISIONS.md`、`.gitignore`（`cache/`、`__pycache__/`、`*.pyc`）、`sources/SOURCES.md`；复制第 1 节列出的代码。
- **复现**（误差 0.001 pp 以内）：
  - SUB 的真实 MAE/MAX、伪场景、冷启动以及第 2 节中逐检查点的误差；
  - 第 9 轮 P2a 的数字和 SUB 逐变体表。
  - 确认解压出的 `5cd305c` 类与研究版 SUB 逐检查点一致（≤ 0.0005 pp），并等于 `EXPECTED_SOH`。
- **构建单体位置缓存：** 对每个场景截断和每个变体，记录 `loc_v(p, c)` 及程序的 `t_cv_end`、`setpoint`、`t_measured` 和它在 SUB 选择中的角色。同时构建程序 CV 结束时的单体电压 `V_c(p)`，以及每个可见锚点的 `step_to_top_c` 和 `end_c` 电压。
- **确定 WP2 和 WP3 使用的检测噪声尺度：**
  - σ_det = 第 8 轮单体行 `R_seg` 的 1.4826·MAD（`table_events.csv`，单元 cell1_V..cell4_V，至少有 4 个程序的 45 °C 段，主变体），单体合并计算，同时给出每个单体的值；
  - 每个变体的 σ_det：用该变体的单体深度，按第 8 轮 `wp2/run_wp2.py::add_residuals` 的规则重算 R_seg。
  - 数值记入 `wp0/outputs/noise_scale.json`。这些值在第 8 轮已被看到（已记录曝光），它们是噪声尺度而不是结果。
- **Done：** 所有复现通过（若 SUB 复现失败，终止整轮并记录原因），缓存和 `noise_scale.json` 存在，加上通用条件。`wp0/REPORT.md` 简短即可。

### WP1——想法 A：先把单体检测做稳（上限 1.5 h）

**想法。** 四单体中位数之所以脆弱，是因为每次单独检测都有噪声，而 4 个数的中位数就是恰好排在中间的那两个单体的平均值。先在各检测变体上平均每个单体的位置，应能在合并单体之前降低这部分噪声。

**候选（按此精确登记）：**
- **A1：** `loc_ens(p, c)` = 6 个变体 `loc_v(p, c)` 的均值（忽略 NaN，至少需要 4 个有限变体，否则为 NaN）；pack 台阶 = 单体均值。
- **A2：** 同样的集成；pack 台阶 = 单体中位数。
- **A3：** `loc_ens(p, c)` = 6 个变体的中位数；pack 台阶 = 单体中位数。

**集成候选的稳健性。** G_robust 在 6 个留一变体集成上评估：每个候选用 5 个变体重建，与主变体上的 SUB 比较。G_robust 的三条标准都在这 6 次重建上适用。

**登记的诊断（描述性）：**
- `loc_ens` 与各单一变体的单体噪声 σ 对比：在 `loc_ens` 上重算 R_seg，取至少有 4 个程序的 45 °C 段；预期更低；
- 在 `loc_ens` 上重算 R_cell 符号模式和离散趋势，检查第 8 轮的单体偏移在平均后是否依然存在；
- 每个候选逐检查点的真实误差和 SOH。

- **Done：** 先提交协议，计算全部检验和诊断，逐个候选给出结论并应用采用规则，写 `wp1/REPORT.md`，加上通用条件。

### WP2——想法 B：合并单体的变化量（上限 1.5 h）

**想法。** 模型只需要两个程序之间的变化量。如果某个单体在某个月发生漂移，**其余三个**单体的变化量比任何对位置的合并都更干净。

**单体变化量**（除非另有说明用主变体；所用程序为 SUB 的选择）：
- phase：`x_c = E_c(k−1) − E_c(k−2) + r_c(k−1)·(d(k−1) − d(k−2))`，其中 E_c 是该单体在 SUB 的 E 程序上的位置，r_c 是该单体在 SUB 速率拟合程序上的 Theil–Sen 速率（SUB 的 r 为 0 时取 0）；
- fallback：`inc_c = loc(after[-1], c) − loc(after[0], c)`。

**候选（按此精确登记；τ 为来自 WP0 的数值）：**
- **B1：** x = 各单体 x_c 的中位数（fallback 增量同理）。
- **B2：** 单个单体剔除。
  - 对每个单体，dev_c = x_c − 其余三个的中位数。
  - 若 max_c |dev_c| > τ，剔除该单体，对其余三个取平均；否则四个全取平均。
  - τ = 3·√2·σ_det，σ_det 取 WP0 中主变体的合并值；在变体 v 上用 σ_det,v。
- **B3**（仅当 WP1 采用了候选时；否则记为"按规则跳过"）：在 WP1 采用的 `loc_ens` 上计算 B2，σ_det 用 WP1 诊断中在 `loc_ens` 上重算的值。

**登记的诊断：**
- 剔除日志：每个案例是否剔除了单体、剔除了哪个、|dev| 和月份；
- 各单体被剔除的比例，与第 8 轮的模式（cell1、cell3）对比；
- 逐检查点的真实误差和 SOH。

- **Done：** 先提交协议，计算全部检验和诊断，给出结论并应用采用规则，写 `wp2/REPORT.md`，加上通用条件。

### WP3——想法 C：消除单体顶部状态的漂移（上限 3 h）

**想法。** 台阶深度是从 CV 结束点往下量的。CV 结束由 **pack** 电压触发，所以一个在 CCCV 结束时比其他单体"没那么满"的单体，即使没有老化，台阶也会显得更浅。CV 结束时各单体电压不同（差值 52–88 mV，cell3 最高），并且随时间变化。如果这种顶部状态漂移造成了一部分单体间拉开，修正它就能只留下老化信号。

**WP3a——机制检查（计算前登记；不使用代理真值）。** 两个协变量，各自独立检验，使用第 8 轮事件表加上 WP0 的单体电压（诊断、全量数据、主变体）：
- **u_c(p)** = 程序 p 的 CV 结束时 V_c − 各单体 V 的均值（mV）；
- **w_c(m)** = 锚点 m 处 `step_to_top_c` − 各单体 `step_to_top` 的均值，赋给第 m 月的每个程序（Ah）。

对每个协变量：
- 在**单体内部**把 R_cell(p, c) 对它回归（两者都按单体去均值，固定偏移因此消掉），各单体合并；
- 报告斜率、按月块 bootstrap 的 90 % CI（2000 次重采样，固定种子）、单体内 R² 以及每个单体的符号。

预期符号为正（顶部更满 → 台阶更深）。

**通过规则：** CI 不含 0 且符号符合预期，至少 4 个单体中有 3 个符号一致，单体内 R² ≥ 0.30。未通过的协变量不使用。若两个都未通过，WP3 以"顶部状态机制不成立"**退出**，不构建任何 WP3b 候选。

**WP3b——候选（只针对通过 WP3a 的协变量；在 WP3a 之后、评估之前登记）：**
- **C1（u，因果系数）：** `loc_c − k·u_c`。k 是 R_cell 对 u_c 的单体内最小二乘斜率，在每个截断点只用可见程序拟合（至少需要 2 个可见月份，否则 k = 0）。pack 台阶 = 单体均值。
- **C2（w，固定系数 1）：** 对第 m 月的程序用 `loc_c − w_c(m)`。这是按 Ah 对 Ah 纯粹地以当月自己的锚点为参照重新定基，没有拟合常数。pack 台阶 = 单体均值。
- **C3：** 先做通过的协变量修正，再用 B2 的剔除规则代替均值（仅当 WP2 的 B2 通过时；否则按规则跳过）。

u 和 w 与检测变体无关，所以 G_robust 通过把同样的修正施加到每个变体的单体位置上来计算。

**登记的诊断：**
- 修正后的单体离散趋势和 R_cell 符号模式（拉开是否缩小？）；
- 逐检查点的真实误差和 SOH。

- **Done：** WP3a 结论，WP3b 的检验和结论或已记录的退出，写 `wp3/REPORT.md`，加上通用条件。

### WP4——组合与候选模型类（上限 2 h）

- 若 WP1–WP3 没有候选通过：把 WP4 标为 **skipped** 并写明原因，进入 WP5。
- **组合。** 否则在 `wp4/protocol.json` 中登记**一个**组合，并在评估前提交：由通过的各 WP 的采用候选按 A → C → B 的顺序组合。用全部检验评估它。若组合通过且因果指标低于每个单独采用的候选，则最终候选为该组合；否则为单独采用候选中因果指标最低者。
- **候选模型类。** 编写 `wp4/candidate_model/model_template.py`：提交的 `5cd305c` 类的副本，只做最小改动。
  - 提交包必须只用 numpy/pandas 自行完成所有计算，不能依赖研究用的 harness。这包括单体位置；对想法 A，还包括全部 6 种检测变体（包括 dvdq_peak 的网格方法和 ir_corrected 的脉冲内阻修正）；对想法 C，还包括单体 CV 结束电压或单体锚点台阶→顶部距离。
  - 保持该类的公开接口、常数写法和文档字符串风格。
- **检查：**
  - **G_causal：** `checks5c.candidate_checks`。把未来数据行替换为噪声后，8 个检查点的输出必须完全相同；用截至 CK1 的数据拟合，输出也必须完全相同。
  - **G_impl：** 模型类与研究实现逐检查点相差 ≤ 0.001 pp。
  - **提交包：** 在 `cache/` 中建立一个放入候选类的提交包副本；在 Python 3.11 下用提交包的 `requirements.txt` 运行 `validate_submission.py`；完整运行一次 `run_model.py` 的 train + test 并计时。
- **输出：** SOH 表，SUB 与候选对比，CK0–CK7，Δ 0.4，附逐检查点变化。
- **绝不把候选类复制进提交包。**
- **Done：** 组合结论、候选模型类、全部检查通过（某项检查失败时修正模型类，而不是研究数字；若在上限时间内无法修好，记为"capped"），写 `wp4/REPORT.md`，加上通用条件。

### WP5——综合（上限 1 h）

`FINAL_REPORT.md`（双语，结论在前）：
1. **每个想法的结论。**
   - A、B、C 各附检验表：G_pseudo、G_cold、G_changed、G_robust（逐变体）、G_event、G_real_safety。
   - C 还要附 WP3a 的机制检查结果。
   - 直白说明哪些想法失败、为什么失败。
2. **改了什么、改在哪里。** SUB 与最终候选（若有）的逐检查点真实误差和 SOH，并注明每个检查点的分支。注明真实 MAE 中低于 0.25 pp 的差异无法分辨。
3. **本轮之后的单体图景。** 第 8 轮的单体偏移和拉开在集成检测和顶部状态修正之后是否依然存在？拉开究竟来自检测噪声、顶部状态漂移，还是其他原因（未解释）？
4. **建议。** 是否接入，并给出确切的文件改动。是否接入由用户决定；本轮只提建议。
5. **风险与局限。** 曝光、近似重复的案例、使用的全量数据常数（σ_det），以及 `notes/DECISIONS.md` 中记录的所有内容。

另写 `README.md`：本轮做了什么，以及如何重建每个输出（每个 WP 一条命令）。

- **Done：** 两个文件都存在，并满足全局 Done 清单。
