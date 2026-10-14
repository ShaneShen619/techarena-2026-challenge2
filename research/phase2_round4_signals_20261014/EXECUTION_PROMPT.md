<a id="en"></a>

# Round 4: More and Cleaner Step Signals (Directions 1–7) — Unattended Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-14. This document is self-contained. The English text is the execution text; the Chinese section is a translation for the reader, and if they differ the English governs.

## 0. Mode of work

- **Unattended overnight run.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Context may be compacted or restarted.** Keep `notes/STATUS.md` current after every step: stage, done, next, last commit. On restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume. Never redo a finished stage.
- **Time budget.** About 8 hours in total, with a cap per stage (§7). At a cap, write up what exists (including "inconclusive"), commit, and move on.
- **Done means.**
  - Every stage in §6 is finished or capped.
  - `FINAL_REPORT.md` is written.
  - Every commit is pushed to the round-4 branch.

## 1. Workspace, isolation and git

- **Worktree and branch (already created).**
  - Work only in the worktree `/Users/shane/Desktop/Arena_1014_round4`, on branch `exp/phase2-round4-signals-20261014`. The branch starts from `exp/phase2-round3-models-20261014` at `e162fb6`.
  - Never `cd` into `/Users/shane/Desktop/Arena_1013_model` or any other checkout.
  - All new work goes into `research/phase2_round4_signals_20261014/` (the "study directory").
- **Concurrency guard.** Round 3 was disturbed by a second session writing to the same branch and cache.
  - At the start and before every commit, run `git log --oneline -5` and compare with your own last commit.
  - If a commit you did not make appears, or a tracked file changes that you did not change: stop editing shared files, record it in `notes/DECISIONS.md`, and only add files by explicit path from then on.
  - Never use `git add -A` or `git add .`, and never revert or rewrite someone else's work.
  - Never use bare `git stash`.
- **Commits and pushes.**
  - Commit this prompt as the first commit if it is not committed yet.
  - Commit at the end of every stage and after meaningful sub-steps.
  - After each stage commit, run `git push -u origin exp/phase2-round4-signals-20261014`. Never push anywhere else, and never force-push.
  - Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify:**
  - `TechArena_Challenge2_Team_Package/` (framework, `run_model.py`, `validate_submission.py`, `my_model/`, `data/`);
  - any earlier study directory (`phase2_anchor_step_20261013`, `phase2_v2_phase_matched_20261013`, `phase2_round3_models_20261014`).

  Import their code; do not edit it.
- **Documentation language.** Every Markdown document you write has the English version first and the Chinese version after it, in the same layout as this file (`<a id="en"></a>`, language-switch line, `---`, `<a id="zh"></a>`). Code comments and docstrings are English only.
- **Bytecode.** Run Python with `python3 -B`.

## 2. Task, current state and what limits it

**Task (TechArena 2026 Challenge 2).** Estimate the SOH of a 4 × 102 Ah LFP series pack on each checkup date.

- **Target.** SOH = C/20 capacity ÷ 102 Ah. The C/20 capacity is the Ah from a 5.1 A discharge after a full charge, until the pack voltage first reaches 11.2 V.
- **Labels.** Only CK0 = 100.41 Ah is released. CK1–CK7 are hidden and scored.
- **Checkup dates:** CK0 2025-01-14, CK1 02-08, CK2 03-11, CK3 04-14, CK4 05-16, CK5 06-16, CK6 07-25, CK7 08-28.
- **Causal cut.** A prediction for CK_k may use only `load_dataset(data, until=CK_k)`, which cuts at 00:00 of that date.

**Data.**

- 13 operating segments at 10-s sampling. Segments alternate 25 °C (short, right after each checkup) and 45 °C (long).
- Segment 3 (19 Feb – 11 Mar, 45 °C) is missing.
- Columns: `timestamp`, `elapsed_s`, `segment`, `chamber_temperature_C`, `current_A` (+ charge), `charge_Ah_cum`, `discharge_Ah_cum`, `cell1_V`..`cell4_V`, `pack_voltage_V`, `temp_mean_C`/`min`/`max`.
- The Ah counters book the 20 A pulse as charge. Integrate `current_A` over real time steps instead, and do not integrate Δt > 600 s or Δt ≤ 0.

**Current leading candidate: V2** (`research/phase2_v2_phase_matched_20261013/`, `src/v2.py`).

- **Anchor.** Q_anchor = post-checkup full charge Q_fc + ε, with ε = ε0 + 0.4 Ah and ε0 = 100.41 − Q_fc,0.
- **In-month update.** Q̂ = Q_anchor(k−1) + β_k·[E45(k−1) − E45(k−2) + r·(d(k−1) − d(k−2))].
  - E45(m) is the last 45 °C graphite-step depth in month m, in Ah below the CV end, from the ~5-day deep discharge programs.
  - d(m) is that step's distance in days to the checkup date.
  - r is the current month's 45 °C Theil–Sen rate.
  - β_k comes from the A4 charge-side LLI share of the visible 25 °C anchors, shrunk towards 1.
- **Fallback.** CK1–CK3 fall back to M4 (anchor + step change since the anchor, β = 1).
- **Proxy result** (proxy P_k = Q_fc,k + ε0 + Δ, Δ = 0.4):
  - MAE **0.215726 pp**, MAX **0.669052 pp** (CK2).
  - Per checkup: CK1 +0.217, CK2 +0.669, CK3 +0.080, CK4 +0.228, CK5 +0.150, CK6 −0.163, CK7 −0.004.
  - The active submission is V1/M4 (MAE 0.291).

**Round 3** (`research/phase2_round3_models_20261014/FINAL_REPORT.md`). Six alternatives were tested and none beat V2. Findings you must use:

- **Few in-month measurements.** Only the 8 post-checkup anchor charges cross the graphite step in the charge direction. The ~5-day CCCV charges cover only about 21 Ah below full.
- **Rate-based gap extrapolation over-corrects** CK2-like gaps.
- **The registered bottom section of anchor charges is confounded** with the start state (r = −0.975 with start voltage).
- **Two effects in the step-depth signal are real:**
  - the step is about +0.18 Ah deeper at 45 °C than at 25 °C;
  - right after each checkup there is a transient of about +0.6 Ah that decays.

**What limits V2.**

1. **CK2 is the largest error** (missing segment); round 3 found no causal fix.
2. **V2 subtracts two single step measurements** (one per month-end), so step noise of about 0.1–0.2 Ah enters directly.
3. **ε and the post-checkup recovery** cannot be tested on proxies; only the leaderboard can.

This round attacks point 2 (fewer noisy points, more measurements) and argues point 3 physically. CK2 is not a target.

**Exposure.** Every CK1–CK7 proxy value has been seen, so every result is **exposed-exploratory**. State this in every report, and never present proxies as hidden truth.

## 3. Code to reuse

- **Shared harness:** `research/phase2_round3_models_20261014/src/harness.py`.
  - It provides `run`, `metrics`, `per_ck`, `gates_vs_v2`, `candidate_checks`, `SCENARIOS` (`real`, `PG1`, `PG2`, `PC5`, `PC10`), `BASELINES` (M4, V2) and the causal cut/cache helpers.
  - `src/harness_extended.py` holds supplementary evaluation.
  - Import them by adding that `src/` to `sys.path`.
  - **Its cache.** Importing `harness` computes the proxies at import time and writes to `research/phase2_round3_models_20261014/cache/`. Inside this worktree that directory is git-ignored and private to this worktree, so using it is allowed. Any cache you add yourself goes into this study's git-ignored `cache/`, with keys that include every parameter (rule 4 in §4). Never write into the other checkout `/Users/shane/Desktop/Arena_1013_model`.
- **Event extraction:** `research/phase2_anchor_step_20261013/src/events.py` (`full_charges`, `step_programs`, `STEP_VARIANTS`, `charge_step_split`, `segment_arrays`, `iter_segments`).
- **V2 functions:** `research/phase2_v2_phase_matched_20261013/src/v2.py` (`anchors_by_checkup`, `month_steps`, `end45`, `phase_diff`, `beta_a4`, `shrink`, `theil_sen`, `m4`, `v2`).
- **Environment.**
  - Research: `python3` (3.13, numpy/pandas/scipy/matplotlib).
  - Candidate classes: numpy/pandas only, and they must also run in a Python 3.11 venv. Create one under `/tmp/arena-round4-py311` from `/opt/homebrew/bin/python3.11` with `pip install numpy pandas`.

## 4. Lessons from round 3 that are now rules

1. **No artificial endpoints.** When interpolating beyond a curve's end, never invent values (round 3 used "last value − 1 V", which produced unreliable roots). Either stop at the measured range and report the point as unavailable, or use a registered, bounded linear extension and report how far it extends.
2. **No real results before the selection is committed.** A pseudo-cut at CK2 (PC5/PC10, k = 2) contains exactly the real CK2 data. Exclude k = 2 from any scenario used for selection. Never print or compute real-data CK1–CK7 results of a stage before its selection or main configuration is committed.
3. **Implement registered formulas exactly.** If the code must deviate, register the deviation before running, or report it as a deviation.
4. **Cache keys must contain every parameter that changes the cached result.**
5. **Causality checks compare exact floats**, both future-noise and fit-prefix. Rounded output is not enough.
6. **Correlations in 6–7 anchors are diagnostics, not validation.** Word them that way.

## 5. Evaluation rules (all stages)

- **Proxies, scenarios, metrics.**
  - Same proxies as V2 (P_k = Q_fc,k + ε0 + Δ, Δ ∈ {0, 0.4, 0.8}).
  - Same pseudo scenarios as round 3: PG1/PG2 for k = 4..7; PC5/PC10 for k = 3..7 in selection steps, and k = 2..7 only in final reporting.
  - Same metrics: MAE, MAX, RMSE per Δ; ε-free CK2–7 MAE; per-checkup errors.
- **Robustness.** All six step-detection variants, and A4 smoothing 1/2/3 Ah where β is used.
- **Common gates against V2** (unless a stage says otherwise):

| Gate | Rule |
|---|---|
| G-causal | exact-float identity under future noise and fit-on-CK1-prefix |
| G-proxy | MAE < V2's MAE for every Δ, and MAX ≤ V2's MAX + 0.10 pp |
| G-epsfree | ε-free CK2–7 MAE ≤ V2's − 0.02 pp |
| G-robust | beats V2's MAE (Δ = 0.4) in ≥ 5 of 6 step variants |
| G-pseudo | mean MAE over PG1, PG2, PC5 and PC10 (k ≥ 3) is not worse than V2's by more than 0.02 pp |
| G-regress | no checkup's absolute error grows by more than 0.30 pp against V2 (Δ = 0.4) |
| G-impl | a numpy/pandas-only class with the `MyModel` interface reproduces the research implementation within 0.001 pp, and passes the sample_data smoke test in the 3.11 venv |

- **Audits before evaluation.** Directions 2, 3 and 4 start with a data audit that computes **no proxy metric**. Only directions that pass their audit get a registered evaluation.
- **Pre-registration.** Before any evaluation in a stage, write `stage_X/protocol.json` with: the main configuration, all variants, the gates and the selection rule. Record its SHA256 in `stage_X/protocol.sha256` and commit it.
  - Amend it only before that stage's evaluation runs, and give the reason.
  - Never change the main configuration after seeing its proxy results.
- **Cumulative baseline.** If a stage passes all gates, later stages may also report "previous passing model + this direction" as a registered variant. The main comparison stays against V2.

## 6. Stages

### Stage 0 — Setup (cap 0.5 h)

- Create the study directory, `notes/STATUS.md`, `notes/DECISIONS.md` and `.gitignore` (`cache/`).
- Import the harness and confirm that every cache write lands inside this worktree.
- Reproduce V2 exactly (0.215726 / 0.669052 at Δ = 0.4) and M4 (0.291265). If either does not reproduce, stop the whole run and record why.

### Stage 1 — Direction 1: month-end denoising by in-segment regression (cap 1.5 h)

**Idea.** V2's month-end value E45(m) is a single step measurement. Replace it with a robust line fitted to all 45 °C steps of that month's 45 °C segment, evaluated at the checkup date.

**Main configuration (register exactly).**

- For month m with ≥ 3 visible 45 °C steps (main step method): fit a Theil–Sen line s(t) over (days, step_mean), with intercept = median of (s_i − slope·t_i).
- L_m = s(CK_{m+1} date). For the current month k−1 this is the extrapolation to CK_k from visible steps only.
- Phase-matched branch: same validity conditions as V2 (previous month has a complete 45 °C segment with ≥ 3 steps and d(k−2) ≤ 10 days; current month has d(k−1) ≤ 10 days or ≥ 3 steps). If the current month has fewer than 3 steps, use V2's E45 + r·d for that month.
- Q̂ = Q_anchor(k−1) + β_k·[L_{k−1} − L_{k−2}], with β_k exactly as in V2.
- The fallback (CK1–CK3) is unchanged.

**Variants (report only).**

- OLS line instead of Theil–Sen.
- Only the last 3 steps of each segment.
- Evaluate at each segment's last step time plus V2's rate term (separates denoising from extrapolation).
- β = 1.

**Note.** V1 found "mean of the last two steps" worse than the last step, because averaging lags a trend. The regression keeps the trend. Report whether the slope estimate or the intercept noise dominates the change.

**Gates:** common gates against V2.

### Stage 2 — Direction 2: step crossings in daily dynamic operation (cap 2 h)

**Idea.** After every pack-level CV end (pack ≥ 13.95 V, 0 < I < 6 A, last such sample), the depth below that CV end is known by integrating current. Every later pass through the graphite-step region during normal daily cycling, until the next CV end, is a potential step measurement.

**2a. Audit (no proxy metric).**

- **Coulomb-counting drift.** For every pair of consecutive CV ends, compare the integrated net Ah (should be about 0, as both are full) with the counter difference. Report the distribution.
- **Candidate crossings.** Monotonic current intervals (constant sign, |I| within a registered band) whose depth range spans at least [step − 6, step + 6] Ah around the expected step depth. The expected depth is the most recent visible program step depth.
- **Location.** Per cell, a midpoint-threshold crossing as in `events.step_programs`. The threshold is computed from medians in an upper and a lower depth window, both within the same interval. Alternative: dV/dQ peak with 2 Ah smoothing.
- **Validation against the programs.** Apply the new detector to the existing ~5-day program discharges and report the median and P90 absolute difference from `step_programs`.
- **Counts.** Per month, temperature, direction and current band: candidate and located crossings, median four-cell range.
- **Exit rule (register before the audit).** Continue only if all of these hold:
  - the median |program reproduction difference| is ≤ 0.3 Ah;
  - the median |coulomb drift| per CV-to-CV interval is ≤ 0.2 Ah;
  - at least 5 of the 7 months have ≥ 3 additional located 45 °C crossings in one direction/current band.

  Otherwise mark "diagnostic only" and skip 2b.

**2b. Use (registered after the audit, before evaluation).**

- Treat located dynamic crossings as additional step measurements.
- Compare only the same direction and current band; for discharge crossings the program steps may be merged if the audit shows an offset ≤ 0.1 Ah.
- Apply them in direction 1's month-end regression (or in V2's E45 if direction 1 failed). Per-direction offsets must be estimated causally.
- Gates: common gates.

### Stage 3 — Direction 3: rest-point pseudo-OCV step (cap 1.5 h)

**Idea.** Rest periods with a known depth below the last CV end give polarisation-free (pseudo-OCV) points. The graphite step appears as a voltage step in pseudo-OCV versus depth.

**3a. Audit (no proxy metric).**

- **Rest periods.** |I| < 0.5 A for ≥ 10 min (main) or ≥ 30 min (variant), per cell, with voltage at the end of the rest and depth from the last CV end (with the coulomb-drift check from 2a).
- **Density.** Rest points per month and temperature within 15–45 Ah depth. Also report the direction of the last current before each rest, because hysteresis matters.
- **Fit.** Per month, temperature and pre-rest direction, a logistic step function V(d) = a + b/(1 + exp((d − s)/w)) with w bounded in [0.5, 3] Ah. Report the profile width of s.
- **Exit rule.** Continue only if ≥ 5 months at 45 °C have ≥ 8 rest points spanning the step and the profile 95 % width of s is ≤ 1.0 Ah. Otherwise "diagnostic only".

**3b. Use.** If the audit passes, register a variant where the month-end 45 °C step value is the pseudo-OCV step location of the last N days of the month (N registered), with an offset to the program steps estimated causally. Gates: common gates.

### Stage 4 — Direction 4: a feature inside the top 21 Ah of the ~5-day CCCV charges (cap 0.75 h)

**Audit only, unless it clearly passes.**

- For every ~5-day CCCV charge, at the 20.4 A CC part, compute per-cell dV/dQ against depth below the final CV end (0.25 Ah grid, 1/2/3 Ah smoothing).
- Search 2–20 Ah below the CV end for a reproducible peak or valley.
- Report its prominence, location noise within months, and drift across months.
- **Exit rule.** Continue only if a feature is located in ≥ 90 % of charges with within-month SD ≤ 0.3 Ah, and moves monotonically across months. If it passes, register its use as an additional in-month measurement (as in 2b) and evaluate it against the gates; otherwise "diagnostic only".

### Stage 5 — Direction 5: physics of the post-checkup recovery (cap 1 h, descriptive, nothing tuned)

**Goal.** Judge which state the hidden C/20 most likely reflects: before the post-checkup recovery, or after it.

1. **Estimate per month (descriptive).**
   - The jump from the last pre-checkup step to the first post-checkup step.
   - The decay of the step depth through the 25 °C segment: an exponential fit with time constant τ and its profile range.
   - If stage 2 or 3 passed, use their denser points.
   - Also report the 25 → 45 °C bridge.
2. **Compare with published mechanisms and time scales.** Cite each source with a link:
   - anode overhang (Lewerenz et al. 2018, J. Energy Storage 18:149–159: equalisation over days to hundreds of days; overhang-dominated float behaviour over about 5–30 days in LFP);
   - salt / lithium inhomogeneity and recovery after rest (Morales Torricos, Endisch, Lewerenz, Batteries 2023, and Batteries & Supercaps 2025; WEVJ 16(5) 2025);
   - capacity recovery in LFP/graphite (JES, doi 10.1149/1945-7111/ab7900).
3. **Write a reasoned argument** about whether a checkup (full charge, C/20 discharge, rests) measures a rehomogenised state that matches the post-checkup anchor (the proxy), and what that implies for V2. No model change and no parameter tuning are allowed in this stage.

### Stage 6 — Direction 6: temperature-based ε refinement (cap 0.5 h, leaderboard-only)

- **Physical reading.** The 25 → 45 °C bridge δ means a 45 °C full charge ends about δ Ah "fuller" above the step than a 25 °C one. If the bottom is unaffected, the 25 °C anchors need ε25 = ε0 + δ instead of ε0 + 0.4.
- **Estimate δ causally.** At each cutoff, take the mean of the visible bridges (25 °C last step → 45 °C first step in the same month, for months with both). Before any bridge is visible, use 0.4.
- **Output.** A leaderboard-only variant `V2_epsT`: an SOH table and its differences from V2. It cannot be judged on proxies, because the proxies use the same ε assumption, so never claim a proxy improvement. Report also the version with the best passing model from stages 1–4, if one exists.

### Stage 7 — Direction 7: round-3 leads (cap 1 h, only if time remains)

Each lead is registered separately before evaluation:

- **SS-fixed.** Round 3's state-space model (`round3/src/statespace.py`, imported unchanged and wrapped) with anchor 0 given its own free offset (prior N(0, 0.5²) Ah), and τ_tr = 8 d as the main setting.
- **β_reg-startcorr.** Round 3's registration β with the bottom-section change corrected for the start state:
  - Δbottom_corr = Δbottom − c·Δ(start mean cell voltage);
  - c is estimated causally by least squares over visible anchors j ≥ 2 (needs ≥ 3);
  - otherwise β0.

Gates: common gates. These are expected to be weak; negative results are fine.

### Stage 8 — Final report (cap 0.5 h)

- **`FINAL_REPORT.md`** (bilingual, conclusions first):
  1. a table of every candidate and variant against M4 and V2 (MAE per Δ, MAX, ε-free MAE, pseudo-scenario MAE, gates);
  2. per-checkup errors;
  3. what each audit found, including negative results;
  4. whether any model should replace V2, and why;
  5. the stage 5 argument and the stage 6 leaderboard-only table;
  6. risks, including exposure, ε, recovery, a single pack and any concurrency events;
  7. exact reproduction commands.
- **`README.md`** (bilingual).
- **Candidate class.** For each model that passes every gate, a candidate class in `candidate_model/` with G-causal and G-impl evidence.
- **Nothing is wired into `my_model/`.**

## 7. Order and caps

| Order | Stage | Cap |
|---|---|---|
| 0 | Setup + reproduce V2 | 0.5 h |
| 1 | Direction 1, month-end regression | 1.5 h |
| 2 | Direction 2, dynamic crossings (audit → use) | 2 h |
| 3 | Direction 3, rest pseudo-OCV (audit → use) | 1.5 h |
| 4 | Direction 4, top-21-Ah feature (audit) | 0.75 h |
| 5 | Direction 5, recovery physics (descriptive) | 1 h |
| 6 | Direction 6, ε temperature (leaderboard-only) | 0.5 h |
| 7 | Direction 7, round-3 leads (if time remains) | 1 h |
| 8 | Final report | 0.5 h |

**Stop rules.**

- If stage 0 cannot reproduce V2, stop everything.
- If a candidate fails G-causal, reject it outright.
- A stage without a passing variant is still a valid result.

## 8. Prohibitions (summary)

- **Causality.** No data after CK_k for CK_k, including thresholds, normalisation, feature definitions, windows, offsets and selection.
- **Pre-registration.**
  - No change of a registered main configuration after its proxy results.
  - The best variant is never reported as the main result.
  - No real-data results before the selection is committed.
- **Proxies.** Never present proxies as hidden truth, and never reconstruct CK1–CK7 from external sources.
- **Files and git.**
  - Do not edit the submission package or earlier studies.
  - Push only to the round-4 branch, and never force-push.
  - Do not touch other checkouts.
- **No questions.** Never ask the user anything; record decisions and continue.

---

<a id="zh"></a>

# 第四轮：更多、更干净的台阶信号（方向 1–7）——无人值守执行 Prompt

> **语言：** [English](#en) · 中文

编写日期：2026-10-14。本文自成一体。英文部分是执行文本，中文部分是给读者的翻译；两者不一致时以英文为准。

## 0. 工作方式

- **通宵无人值守运行。** 不要停下来提问。遇到未定的决策，选择遵守本文全部规则前提下最保守的方案，记入 `notes/DECISIONS.md`，然后继续。
- **上下文可能被压缩或重启。** 每一步之后都更新 `notes/STATUS.md`：阶段、已完成、下一步、最近一次提交。重启后先读 `notes/STATUS.md` 和 `notes/DECISIONS.md` 再接着做，不要重做已完成的阶段。
- **时间预算。** 全程约 8 小时，每个阶段有上限（第 7 节）。到上限时，把已有结果（包括"无定论"）写成报告、提交，然后进入下一阶段。
- **完成的标准。**
  - 第 6 节的每个阶段都已完成或到达上限；
  - `FINAL_REPORT.md` 已写好；
  - 所有提交都已推送到第四轮分支。

## 1. 工作区、隔离与 git

- **worktree 与分支（已建好）。**
  - 只在 worktree `/Users/shane/Desktop/Arena_1014_round4` 的分支 `exp/phase2-round4-signals-20261014` 上工作。该分支从 `exp/phase2-round3-models-20261014` 的 `e162fb6` 创建。
  - 不要 `cd` 到 `/Users/shane/Desktop/Arena_1013_model` 或任何其他检出目录。
  - 所有新工作放在 `research/phase2_round4_signals_20261014/`（下称"研究目录"）。
- **并发防护。** 第三轮曾被另一个会话往同一分支和缓存写入。
  - 开始时以及每次提交前，运行 `git log --oneline -5`，与自己最近一次提交对照。
  - 如果出现不是你做的提交，或有你没改过的已跟踪文件发生变化：停止编辑共享文件，记入 `notes/DECISIONS.md`，此后只按明确路径添加文件。
  - 不要使用 `git add -A` 或 `git add .`，不要撤销或改写别人的工作。
  - 不要使用裸 `git stash`。
- **提交与推送。**
  - 本 prompt 如果还没提交，就作为第一个提交。
  - 每个阶段结束时提交，有意义的子步骤完成后也提交。
  - 每次阶段提交后运行 `git push -u origin exp/phase2-round4-signals-20261014`。不要推送到其他地方，不要强制推送。
  - 提交信息结尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **不要修改：**
  - `TechArena_Challenge2_Team_Package/`（框架、`run_model.py`、`validate_submission.py`、`my_model/`、`data/`）；
  - 之前任何研究目录（`phase2_anchor_step_20261013`、`phase2_v2_phase_matched_20261013`、`phase2_round3_models_20261014`）。

  可以导入它们的代码，但不要编辑。
- **文档语言。** 你写的每个 Markdown 文档都是英文在前、中文在后，格式与本文件相同（`<a id="en"></a>`、语言切换行、`---`、`<a id="zh"></a>`）。代码注释和 docstring 只用英文。
- **字节码。** 用 `python3 -B` 运行 Python。

## 2. 任务、现状及其限制

**任务（TechArena 2026 Challenge 2）。** 估计 4 × 102 Ah LFP 串联电池组在每个检查日的 SOH。

- **目标量。** SOH = C/20 容量 ÷ 102 Ah。C/20 容量是满充后以 5.1 A 放电、直到组端电压首次达到 11.2 V 时放出的 Ah。
- **标签。** 只公开 CK0 = 100.41 Ah；CK1–CK7 隐藏，用于评分。
- **检查日：** CK0 2025-01-14，CK1 02-08，CK2 03-11，CK3 04-14，CK4 05-16，CK5 06-16，CK6 07-25，CK7 08-28。
- **因果截断。** 预测 CK_k 只能用 `load_dataset(data, until=CK_k)`，截断点是该日 00:00。

**数据。**

- 13 个运行段，10 s 采样。各段在 25 °C（短，紧接每次检查之后）与 45 °C（长）之间交替。
- 第 3 段（2 月 19 日 – 3 月 11 日，45 °C）缺失。
- 列：`timestamp`、`elapsed_s`、`segment`、`chamber_temperature_C`、`current_A`（充电为正）、`charge_Ah_cum`、`discharge_Ah_cum`、`cell1_V`..`cell4_V`、`pack_voltage_V`、`temp_mean_C`/`min`/`max`。
- Ah 计数器把 20 A 脉冲记为充电。要按真实时间步长积分 `current_A`，Δt > 600 s 或 Δt ≤ 0 不积分。

**当前领先候选：V2**（`research/phase2_v2_phase_matched_20261013/`，`src/v2.py`）。

- **锚点。** Q_anchor = 检查后完整充电量 Q_fc + ε，其中 ε = ε0 + 0.4 Ah，ε0 = 100.41 − Q_fc,0。
- **月内更新。** Q̂ = Q_anchor(k−1) + β_k·[E45(k−1) − E45(k−2) + r·(d(k−1) − d(k−2))]。
  - E45(m) 是第 m 月最后一次 45 °C 石墨台阶的深度，以 CV 末端以下的 Ah 计，取自约每 5 天一次的深放电程序。
  - d(m) 是这次台阶测量距检查日的天数。
  - r 是本月 45 °C 台阶的 Theil–Sen 速率。
  - β_k 由可见 25 °C 锚点的 A4 充电侧 LLI 份额求得，并向 1 收缩。
- **回退。** CK1–CK3 回退到 M4（锚点 + 锚点后台阶变化，β = 1）。
- **代理结果**（代理 P_k = Q_fc,k + ε0 + Δ，Δ = 0.4）：
  - MAE **0.215726 pp**，MAX **0.669052 pp**（CK2）。
  - 各检查点：CK1 +0.217、CK2 +0.669、CK3 +0.080、CK4 +0.228、CK5 +0.150、CK6 −0.163、CK7 −0.004。
  - 当前提交是 V1/M4（MAE 0.291）。

**第三轮**（`research/phase2_round3_models_20261014/FINAL_REPORT.md`）。测试了六个备选方案，没有一个胜过 V2。必须用上的发现：

- **月内测量太少。** 只有 8 次检查后的锚点充电在充电方向越过石墨台阶；约每 5 天一次的 CCCV 充电只覆盖满充以下约 21 Ah。
- **基于速率的缺段外推**在类 CK2 缺口上修正过头。
- **锚点充电中配准出的底部段与起点状态混淆**（与起点电压 r = −0.975）。
- **台阶深度信号里有两个真实效应：**
  - 45 °C 时台阶比 25 °C 时深约 +0.18 Ah；
  - 每次检查后有一个约 +0.6 Ah 的瞬态，随后衰减。

**限制 V2 的因素。**

1. **CK2 是最大误差**（缺段），第三轮没找到因果的修正办法。
2. **V2 只用两次单点台阶测量相减**（每个月末各一次），约 0.1–0.2 Ah 的台阶噪声直接进入结果。
3. **ε 与检查后回弹**无法在代理上检验，只能靠排行榜。

本轮主攻第 2 点（降低单点噪声、增加测量次数），并从物理上论证第 3 点。CK2 不是本轮目标。

**曝光。** CK1–CK7 的每个代理值都已看过，所以全部结果都是**已曝光的探索性结果**。每份报告都要写明，绝不能把代理说成隐藏真值。

## 3. 复用的代码

- **共享评估框架：** `research/phase2_round3_models_20261014/src/harness.py`。
  - 提供 `run`、`metrics`、`per_ck`、`gates_vs_v2`、`candidate_checks`、`SCENARIOS`（`real`、`PG1`、`PG2`、`PC5`、`PC10`）、`BASELINES`（M4、V2）以及因果截断与缓存辅助函数。
  - `src/harness_extended.py` 是补充评估。
  - 把那个 `src/` 加入 `sys.path` 即可导入。
  - **它的缓存。** 导入 `harness` 时会立即计算代理，并写入 `research/phase2_round3_models_20261014/cache/`。在本 worktree 里，这个目录被 git 忽略、只属于本 worktree，所以可以使用。你自己新增的缓存放在本研究目录被 git 忽略的 `cache/` 中，缓存键要包含所有参数（见第 4 节第 4 条）。绝不能写入另一个检出目录 `/Users/shane/Desktop/Arena_1013_model`。
- **事件提取：** `research/phase2_anchor_step_20261013/src/events.py`（`full_charges`、`step_programs`、`STEP_VARIANTS`、`charge_step_split`、`segment_arrays`、`iter_segments`）。
- **V2 函数：** `research/phase2_v2_phase_matched_20261013/src/v2.py`（`anchors_by_checkup`、`month_steps`、`end45`、`phase_diff`、`beta_a4`、`shrink`、`theil_sen`、`m4`、`v2`）。
- **环境。**
  - 研究：`python3`（3.13，含 numpy/pandas/scipy/matplotlib）。
  - 候选类：只依赖 numpy/pandas，还必须能在 Python 3.11 venv 中运行。venv 建在 `/tmp/arena-round4-py311`，用 `/opt/homebrew/bin/python3.11` 创建并 `pip install numpy pandas`。

## 4. 第三轮的教训，本轮作为规则

1. **不得人为构造端点。** 插值超出曲线末端时不得编造数值（第三轮用了"末值 − 1 V"，导致求出的根不可靠）。要么停在实测范围内并把该点报告为"不可得"，要么使用登记过的有界线性延伸，并报告延伸了多远。
2. **选择提交之前不得出现真实结果。** CK2 处的伪截断（PC5/PC10，k = 2）与真实 CK2 数据完全相同。用于选择的情景必须排除 k = 2。某阶段的选择或主配置提交之前，绝不计算或打印该阶段在 CK1–CK7 上的真实数据结果。
3. **严格按登记的公式实现。** 代码如需偏离，要在运行前登记该偏离，或者作为偏离报告。
4. **缓存键必须包含所有会改变缓存结果的参数。**
5. **因果检查比较精确浮点值**，未来噪声检查和 fit 前缀检查都一样，只比较舍入后的输出不够。
6. **6–7 个锚点上的相关性只是诊断，不是验证。** 措辞上要体现这一点。

## 5. 评估规则（所有阶段）

- **代理、情景、指标。**
  - 代理与 V2 相同（P_k = Q_fc,k + ε0 + Δ，Δ ∈ {0, 0.4, 0.8}）。
  - 伪情景与第三轮相同：PG1/PG2 取 k = 4..7；PC5/PC10 在选择步骤中取 k = 3..7，只有在最终报告中才取 k = 2..7。
  - 指标相同：每个 Δ 下的 MAE、MAX、RMSE；与 ε 无关的 CK2–7 MAE；逐检查点误差。
- **稳健性。** 6 种台阶检测变体；用到 β 的地方还要报告 A4 平滑 1/2/3 Ah。
- **相对 V2 的通用接纳门**（各阶段另有规定的除外）：

| 门 | 规则 |
|---|---|
| G-causal | 未来噪声与 CK1 前缀 fit 下精确浮点一致 |
| G-proxy | 每个 Δ 下 MAE 都低于 V2，且 MAX ≤ V2 的 MAX + 0.10 pp |
| G-epsfree | 与 ε 无关的 CK2–7 MAE ≤ V2 − 0.02 pp |
| G-robust | 6 种台阶变体中至少 5 种的 MAE（Δ = 0.4）优于 V2 |
| G-pseudo | PG1、PG2、PC5、PC10（k ≥ 3）的平均 MAE 不比 V2 差 0.02 pp 以上 |
| G-regress | 与 V2 相比，任何检查点的绝对误差增加不超过 0.30 pp（Δ = 0.4） |
| G-impl | 有一个只依赖 numpy/pandas、具备 `MyModel` 接口的类，与研究实现相差在 0.001 pp 以内，并在 3.11 venv 中通过 sample_data 冒烟测试 |

- **先审计、后评估。** 方向 2、3、4 先做数据审计，审计中**不计算任何代理指标**。只有通过审计的方向才进入登记评估。
- **预登记。** 每个阶段在任何评估之前，写 `stage_X/protocol.json`：主配置、全部变体、接纳门和选择规则。在 `stage_X/protocol.sha256` 记录其 SHA256 并提交。
  - 只能在该阶段评估运行之前修订，并写明理由。
  - 看到代理结果后，绝不更改主配置。
- **累积基线。** 某阶段若通过全部接纳门，后续阶段可以另外报告"之前通过的模型 + 本方向"作为登记过的变体。主要比较对象仍是 V2。

## 6. 各阶段

### 阶段 0——准备（上限 0.5 小时）

- 建研究目录、`notes/STATUS.md`、`notes/DECISIONS.md` 和 `.gitignore`（`cache/`）。
- 导入评估框架，确认所有缓存写入都落在本 worktree 内。
- 精确复现 V2（Δ = 0.4 下 0.215726 / 0.669052）和 M4（0.291265）。任一无法复现，就停止整个运行并记录原因。

### 阶段 1——方向 1：用段内回归给月末值去噪（上限 1.5 小时）

**思路。** V2 的月末值 E45(m) 是单次台阶测量。改为对该月 45 °C 段内的全部 45 °C 台阶拟合一条稳健直线，取它在检查日的值。

**主配置（严格按此登记）。**

- 对第 m 月可见 45 °C 台阶 ≥ 3 次的情况（主台阶方法）：在（天数, step_mean）上拟合 Theil–Sen 直线 s(t)，截距取 (s_i − slope·t_i) 的中位数。
- L_m = s(CK_{m+1} 日期)。对当前月 k−1，这就是只用可见台阶外推到 CK_k。
- 同相位分支的有效条件与 V2 相同：上月有完整 45 °C 段（≥ 3 次台阶）且 d(k−2) ≤ 10 天；本月 d(k−1) ≤ 10 天或有 ≥ 3 次台阶。本月台阶不足 3 次时，该月用 V2 的 E45 + r·d。
- Q̂ = Q_anchor(k−1) + β_k·[L_{k−1} − L_{k−2}]，β_k 与 V2 完全相同。
- 回退分支（CK1–CK3）不变。

**变体（只报告）。**

- 用 OLS 直线代替 Theil–Sen。
- 每段只用最后 3 次台阶。
- 在各段最后一次台阶时刻取值，再加 V2 的速率项（用来区分去噪和外推的作用）。
- β = 1。

**注意。** V1 曾发现"取最后两次的平均"比只取最后一次更差，因为平均会滞后于趋势；回归保留了趋势项。要报告改变主要来自斜率估计还是截距噪声。

**接纳门：** 相对 V2 的通用接纳门。

### 阶段 2——方向 2：日常动态运行中的台阶穿越（上限 2 小时）

**思路。** 每次组端 CV 结束后（组端 ≥ 13.95 V、0 < I < 6 A 的最后一个采样点），对电流积分就知道当前位于该 CV 末端以下多深。从此直到下一次 CV 末端，日常循环每一次经过石墨台阶区，都是一次潜在的台阶测量。

**2a. 审计（不算代理指标）。**

- **库仑计数漂移。** 对每两次相邻的 CV 末端，比较积分得到的净 Ah（两端都是满充，应约为 0）与计数器差值，报告其分布。
- **候选穿越。** 单调电流区间（电流方向不变，|I| 在登记的电流带内），其深度范围至少覆盖预期台阶深度 ± 6 Ah。预期深度取最近一次可见的程序台阶深度。
- **定位。** 与 `events.step_programs` 一样，对每颗电芯取中点阈值的穿越。阈值由同一区间内上、下两个深度窗口的中位电压算出。备选方法：2 Ah 平滑的 dV/dQ 峰。
- **对照程序台阶验证。** 用新检测方法处理现有约每 5 天一次的程序放电，报告与 `step_programs` 差值绝对值的中位数和 P90。
- **计数。** 按月、温度、方向、电流带统计候选穿越数、成功定位数，以及四芯极差的中位数。
- **退出规则（审计前登记）。** 以下条件全部满足才继续：
  - 程序复现差值绝对值的中位数 ≤ 0.3 Ah；
  - 每个 CV 到 CV 区间的库仑漂移绝对值中位数 ≤ 0.2 Ah；
  - 7 个月里至少 5 个月，在同一方向和电流带上有 ≥ 3 次额外定位成功的 45 °C 穿越。

  否则标为"仅诊断"，跳过 2b。

**2b. 使用（审计之后、评估之前登记）。**

- 把定位成功的动态穿越作为额外的台阶测量。
- 只比较同方向、同电流带的测量；对放电方向的穿越，如果审计显示与程序台阶的偏移 ≤ 0.1 Ah，可以把程序台阶合并进来。
- 用在方向 1 的月末回归中（方向 1 若失败，则用在 V2 的 E45 中）。各方向的偏移量必须因果地估计。
- 接纳门：通用接纳门。

### 阶段 3——方向 3：静置点伪 OCV 台阶（上限 1.5 小时）

**思路。** 已知距上次 CV 末端深度的静置段，可以提供去极化的伪 OCV 点。石墨台阶在"伪 OCV 对深度"的曲线上表现为一个电压台阶。

**3a. 审计（不算代理指标）。**

- **静置段。** |I| < 0.5 A 持续 ≥ 10 分钟（主）或 ≥ 30 分钟（变体）。逐芯记录静置末端电压，以及距上次 CV 末端的深度（深度使用 2a 中的库仑漂移检查）。
- **密度。** 按月和温度统计 15–45 Ah 深度内的静置点数。还要报告每次静置之前最后一段电流的方向，因为滞后有影响。
- **拟合。** 按月、温度、静置前方向，拟合逻辑型台阶函数 V(d) = a + b/(1 + exp((d − s)/w))，w 限制在 [0.5, 3] Ah，并报告 s 的剖面宽度。
- **退出规则。** 只有 ≥ 5 个月在 45 °C 下有 ≥ 8 个跨越台阶的静置点，并且 s 的剖面 95 % 宽度 ≤ 1.0 Ah，才继续；否则"仅诊断"。

**3b. 使用。** 审计通过时，登记一个变体：月末 45 °C 台阶值改用该月最后 N 天（N 事先登记）静置伪 OCV 的台阶位置，它与程序台阶之间的偏移因果地估计。接纳门：通用接纳门。

### 阶段 4——方向 4：约每 5 天一次的 CCCV 充电顶部 21 Ah 内的特征（上限 0.75 小时）

**只做审计，除非明确通过。**

- 对每次约每 5 天一次的 CCCV 充电，在 20.4 A 的 CC 部分，逐芯计算 dV/dQ 对"最终 CV 末端以下深度"的曲线（0.25 Ah 网格，1/2/3 Ah 平滑）。
- 在 CV 末端以下 2–20 Ah 内寻找可重复出现的峰或谷。
- 报告其显著度、月内位置噪声和跨月漂移。
- **退出规则。** 只有特征在 ≥ 90 % 的充电中被定位、月内标准差 ≤ 0.3 Ah、并且跨月单调移动，才继续。通过时，登记把它作为额外月内测量的用法（同 2b），并按接纳门评估；否则"仅诊断"。

### 阶段 5——方向 5：检查后回弹的物理（上限 1 小时；只作描述，不调任何参数）

**目标。** 判断隐藏的 C/20 最可能反映回弹之前还是回弹之后的状态。

1. **逐月估计（描述性）。**
   - 从检查前最后一次台阶到检查后第一次台阶的跳变。
   - 台阶深度在 25 °C 段内的衰减：指数拟合的时间常数 τ 及其剖面范围。
   - 阶段 2 或 3 若通过，就用它们更密的数据点。
   - 同时报告 25 → 45 °C 的跳变。
2. **与已发表的机理和时间尺度比较。** 每个来源都附链接：
   - 负极 overhang（Lewerenz 等 2018，J. Energy Storage 18:149–159：平衡过程从数天到上百天；在 LFP 中，约 5–30 天由 overhang 主导浮充行为）；
   - 盐 / 锂分布不均与静置后的恢复（Morales Torricos、Endisch、Lewerenz，Batteries 2023 和 Batteries & Supercaps 2025；WEVJ 16(5) 2025）；
   - LFP/石墨的容量恢复（JES，doi 10.1149/1945-7111/ab7900）。
3. **写出论证：** 一次检查（满充、C/20 放电、静置）测到的是否是与检查后锚点（也就是代理）相同的再均匀化状态，以及这对 V2 意味着什么。本阶段不得修改模型，也不得调任何参数。

### 阶段 6——方向 6：基于温度细化 ε（上限 0.5 小时；只供排行榜检验）

- **物理解读。** 25 → 45 °C 的跳变 δ 意味着：45 °C 的满充比 25 °C 的满充在台阶以上多充约 δ Ah。如果底部不受影响，25 °C 锚点就应该用 ε25 = ε0 + δ，而不是 ε0 + 0.4。
- **因果地估计 δ。** 每个截断点取可见跳变的均值（同一个月内 25 °C 最后一次台阶 → 45 °C 第一次台阶，只用两种温度都有的月份）。尚无可见跳变时用 0.4。
- **产出。** 只供排行榜检验的变体 `V2_epsT`：SOH 表及其与 V2 的差值。代理用的是同一个 ε 假设，所以无法在代理上评判，绝不能声称它改善了代理分数。如果阶段 1–4 有通过的模型，也报告"该模型 + ε 细化"的版本。

### 阶段 7——方向 7：第三轮留下的线索（上限 1 小时，有剩余时间才做）

每条线索在评估之前单独登记：

- **SS-fixed。** 第三轮的状态空间模型（原样导入 `round3/src/statespace.py` 并包装），给锚点 0 一个自由偏置（先验 N(0, 0.5²) Ah），主设置 τ_tr = 8 天。
- **β_reg-startcorr。** 第三轮的配准 β，对底部段变化做起点状态修正：
  - Δbottom_corr = Δbottom − c·Δ（起点各芯平均电压）；
  - c 用可见锚点 j ≥ 2 的最小二乘因果地估计（至少需要 3 个）；
  - 否则用 β0。

接纳门：通用接纳门。预计效果较弱，负面结果也是有效结果。

### 阶段 8——最终报告（上限 0.5 小时）

- **`FINAL_REPORT.md`**（中英双语，结论在前）：
  1. 所有候选和变体相对 M4、V2 的汇总表（每个 Δ 的 MAE、MAX、与 ε 无关的 MAE、伪情景 MAE、接纳门结果）；
  2. 逐检查点误差；
  3. 每次审计的发现，包括负面结果；
  4. 是否有模型应取代 V2，以及理由；
  5. 阶段 5 的论证和阶段 6 的排行榜对照表；
  6. 风险：曝光、ε、回弹、单一电池组，以及任何并发事件；
  7. 准确的复现命令。
- **`README.md`**（中英双语）。
- **候选类。** 每个通过全部接纳门的模型，在 `candidate_model/` 中提供一个候选类，并附 G-causal 和 G-impl 的证据。
- **不得把任何东西接入 `my_model/`。**

## 7. 顺序与上限

| 顺序 | 阶段 | 上限 |
|---|---|---|
| 0 | 准备 + 复现 V2 | 0.5 小时 |
| 1 | 方向 1：月末回归 | 1.5 小时 |
| 2 | 方向 2：动态穿越（审计 → 使用） | 2 小时 |
| 3 | 方向 3：静置伪 OCV（审计 → 使用） | 1.5 小时 |
| 4 | 方向 4：顶部 21 Ah 特征（审计） | 0.75 小时 |
| 5 | 方向 5：回弹物理（描述） | 1 小时 |
| 6 | 方向 6：ε 温度细化（只供排行榜） | 0.5 小时 |
| 7 | 方向 7：第三轮线索（有剩余时间才做） | 1 小时 |
| 8 | 最终报告 | 0.5 小时 |

**停止规则。**

- 阶段 0 无法复现 V2 时，停止全部工作。
- 候选未通过 G-causal 就直接淘汰。
- 某阶段没有任何变体通过，也是有效结果。

## 8. 禁止事项（汇总）

- **因果性。** 不得用 CK_k 之后的数据预测 CK_k，包括阈值、归一化、特征定义、窗口、偏移量和选择。
- **预登记。**
  - 看到代理结果后，不得更改已登记的主配置。
  - 不得把最好的变体当作主结果报告。
  - 选择提交之前不得出现真实数据结果。
- **代理。** 不得把代理说成隐藏真值，不得从外部来源重建 CK1–CK7。
- **文件与 git。**
  - 不得修改提交包或之前的研究目录。
  - 只推送到第四轮分支，不得强制推送。
  - 不得碰其他检出目录。
- **不提问。** 不向用户提问；记录决策，然后继续。
