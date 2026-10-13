<a id="en"></a>

# Round 3: Alternative Capacity Models (B → D → A → C → E → F) — Unattended Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-14. This document is self-contained: hand it to an executor that has no access to the earlier chat. The English text is the execution text. The Chinese section below is a translation for the reader; if the two differ, the English governs.

## 0. Mode of work: you are running unattended overnight

- **No one will answer questions.** Never stop to ask. Whenever a decision is open, take the most conservative option that keeps every rule in this document, write the decision and its reason to `notes/DECISIONS.md`, and continue.
- **Your context may be compacted or restarted.** Keep `notes/STATUS.md` current after every step: the stage you are in, what is done, what is next, and the last commit. On any restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume from there. Never redo a finished stage.
- **Time budget.** The whole run has about 9 hours. Each stage has a cap (§6). If a stage hits its cap, stop it, write up whatever it has (including "inconclusive"), commit, and move on.
- **Done means.** All six stages are finished or capped, `FINAL_REPORT.md` is written, and every commit is pushed (§1). Then stop.

## 1. Workspace, branch and git rules

- **Repository and worktree.** Work in `/Users/shane/Desktop/Arena_1013_model`, a git worktree. Do not `cd` into any other checkout.
- **Branch.** Start from branch `exp/phase2-anchor-step-20261013` (HEAD `886bfc1` or later) and create `exp/phase2-round3-models-20261014`. All work goes into `research/phase2_round3_models_20261014/` (the "study directory").
- **First commit.** Commit this prompt as the first commit of the new branch.
- **Commit and push.** Commit at the end of every stage, and whenever a meaningful sub-step finishes. After each stage commit, push the new branch: `git push -u origin exp/phase2-round3-models-20261014`. Never push to `main` or to `exp/phase2-anchor-step-20261013`, and never force-push.
- **Commit messages** end with:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
- **Do not modify:**
  - `TechArena_Challenge2_Team_Package/` in any way, including `framework/`, `run_model.py`, `validate_submission.py`, `my_model/` and `data/`;
  - the earlier studies `research/phase2_anchor_step_20261013/` and `research/phase2_v2_phase_matched_20261013/`.

  Import code from them; do not edit it.
- **Git stash.** Do not use bare `git stash`. The stash stack is shared with other sessions.
- **Documentation language.** Every Markdown document you write in this branch has an English version first and a Chinese version after it. Use the same layout as this file: an anchor `<a id="en"></a>`, a language-switch line, `---`, `<a id="zh"></a>`. Code comments and docstrings are English only.

## 2. Task and background

**The task.** This is TechArena 2026 Challenge 2, Topic 1. Estimate the SOH of a 4 × 102 Ah LFP series pack on each checkup date.

- SOH = C/20 capacity ÷ 102 Ah. The C/20 capacity is the Ah from a 5.1 A discharge, after a full charge, until the pack voltage first reaches 11.2 V.
- Only CK0 = 100.41 Ah (98.44 %) is released. CK1–CK7 are hidden and scored.
- Checkup dates: CK0 2025-01-14, CK1 02-08, CK2 03-11, CK3 04-14, CK4 05-16, CK5 06-16, CK6 07-25, CK7 08-28.
- The score is error metrics normalised by the official ExampleModel; lower is better.
- **Causal cut.** A prediction for CK_k may use only `load_dataset(data, until=CK_k)`, which cuts at 00:00 of the date.

**The data.** Operating data are 13 segments at 10-s sampling.

- Segments alternate 25 °C (short) and 45 °C (long).
- Month m runs from the post-CK_m anchor charge to the next checkup. It is a 25 °C segment followed by a 45 °C segment, except month 0, which is segment 1 at 45 °C only.
- Segment 3 (19 Feb – 11 Mar, 45 °C) is missing, so in month 1 only one 45 °C step (17 Feb) is visible before CK2.

**Current models.** The first two are on this branch:

- **V1 / M4** (`research/phase2_anchor_step_20261013/`, report `FINAL_REPORT.md`). This is the active submission model.
  - **Anchor:** every month opens with a post-checkup charge from near empty to the end of the 14.0 V CV phase (Q_fc). Q_fc = 100.122, 97.003, 95.670, 94.642, 93.747, 93.082, 92.636, 91.954 Ah after CK0–CK7.
  - **Offset:** Q_anchor = Q_fc + ε, with ε = ε0 + 0.4 Ah, where ε0 = 100.41 − 100.122.
  - **In-month update:** + (last step depth − first step depth after the anchor). The step depth is the graphite staging step, measured in Ah below the CV end on the ~5-day deep discharge.
- **V2** (`research/phase2_v2_phase_matched_20261013/`). This is the current best candidate and is not wired into the submission.
  - It compares only month-end 45 °C step depths of consecutive months.
  - β comes from the charge-side LLI share (A4) of the visible 25 °C anchors, shrunk towards 1.
  - CK1–CK3 fall back to M4.
  - Proxy results at ε0+0.4:

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | MAE | max |
|---|---|---|---|---|---|---|---|---|---|
| M4 | +0.22 | +0.67 | +0.08 | +0.28 | −0.11 | −0.40 | −0.28 | 0.291 | 0.669 |
| V2 | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 | 0.216 | 0.669 |

- V2's β by checkup: 1.06 (CK4), 1.24, 1.41, 1.51 (CK7).

**Known structure of the step signal.** Use it, and test it.

- At every 25 → 45 °C switch the step depth jumps up by about +0.18 Ah. The jump is +0.60 in month 1.
- The step depth drops fast in the 25 °C segment right after each checkup (0.07–0.13 Ah/day) and slowly at 45 °C (0.02–0.04 Ah/day). This looks like a transient (overhang / rehomogenisation), not ageing.
- 68–79 % of the anchor-to-anchor loss lies above the step (LLI-dominated). This implies β ≈ 1.3–1.45.

**Proxy labels and their limit.** P_k = Q_fc,k + ε, scored for ε ∈ {ε0, ε0+0.4, ε0+0.8}.

- Anchor-based predictions for CK2–CK7 have errors that do not depend on ε (the "ε-free" metric).
- Every CK1–CK7 proxy value has already been seen, so every result in this round is **exposed-exploratory**. Say so in every report.
- Proxies are not the hidden truth. Never present them as "true CK values".

**Literature.** The literature behind this plan is two documents on branch `research-archive-20261010`, under `research/phase2_literature_reassessment/outputs/`:

- `LFP_SOH_第二阶段文献综述与技术路线_深度重评.md` (review and routes R01–R09);
- `LFP_SOH_核心论文精读与证据附册.md` (33 paper cards).

Read them with `git show research-archive-20261010:<path>`. They predate the anchor finding, so their route ranking is outdated. Their constraints on identifiability, temperature layering, pack cutoff and information paths still apply.

**Do not retry these.** They failed before or have no labels to support them:

- plateau-window local-Ah capacity;
- joint SOC/SOH ECM on mid-plateau windows;
- ICA peak position → capacity;
- pulse or relaxation features → capacity regression;
- deep, self-supervised or transfer models;
- knee detection.

## 3. Code you must reuse

- `research/phase2_anchor_step_20261013/src/events.py`:
  - `full_charges(op)` (anchors; columns include `t_start`, `t_end`, `Q_Ah`, `setpoint_C`, `_seg_index`, start/end cell voltages);
  - `step_programs(op, **STEP_VARIANTS[v])` (discharge-direction steps; six variants);
  - `charge_step_split(op, fc, smooth_Ah)` (A4);
  - `segment_arrays`;
  - `ck0_reference_step`.
- `research/phase2_v2_phase_matched_20261013/src/v2.py`: `anchors_by_checkup`, `month_steps`, `end45`, `phase_diff`, `beta_a4`, `m4`, `v2`.
- `research/phase2_v2_phase_matched_20261013/stage_v2_eval.py` (evaluation loop and proxies) and `stage_v2_candidate.py` (causality and reimplementation checks). Copy their patterns.
- **Data and framework:** `TechArena_Challenge2_Team_Package/data/` and `framework/data.py`. `Dataset.eval_points` holds all checkup dates.
- **Integration rules:** charge is positive; integrate `current_A` over real time steps; do not integrate Δt > 600 s or Δt ≤ 0. The Ah counters book the 20 A pulse as charge, so never use them for depth.

**Environment.**

- **Research scripts:** use `python3` (3.13, with numpy/pandas/scipy/matplotlib).
- **Candidate classes:** they must use only numpy/pandas, and must also run in a Python 3.11 venv. Create it in the session scratchpad or in `/tmp`, from `/opt/homebrew/bin/python3.11` with `pip install numpy pandas`.

## 4. Shared evaluation harness (build first, in stage 0)

Write `src/harness.py` in the study directory. It is used by every stage.

1. **Per-checkup data.** For k = 1..7, run `load_dataset(data, until=CK_k)` and extract fc, steps for all six variants, and A4 for smoothing windows 1/2/3 Ah. Cache the results to disk under `cache/`, git-ignored.
2. **Proxies.** Use exactly the V2 definition: P_k = Q_fc,k(full data) + ε0 + Δ, with Δ ∈ {0, 0.4, 0.8}.
3. **Metrics.**
   - MAE, MAX and RMSE (pp) for each Δ;
   - the ε-free CK2–7 MAE;
   - per-checkup errors;
   - a comparison table against M4 and V2, recomputed through the harness. It must reproduce V2's 0.216 / 0.669 at Δ = 0.4, or you stop and fix the harness.
4. **Pseudo-cutoff and pseudo-gap scenarios.** These give more test cases than the seven proxies. Implement them as functions that return a cut operation DataFrame:
   - **PG1 "CK2-like gap":** for k = 4..7, in month k−1, keep the 25 °C segment and only the operation rows of the 45 °C segment up to the end of its first deep discharge (first 45 °C step). Delete the rest of that 45 °C segment, then predict CK_k.
   - **PG2:** same as PG1, but keep the first two 45 °C steps.
   - **PC5 / PC10:** cut the data 5 / 10 days before CK_k, for k = 2..7.

   Score all of them against the same P_k. They are ε-free for k ≥ 2.
5. **Causality check.** Replace every row after the cutoff with noise; the prediction must be bit-identical. Also fit on data cut at CK1. Run this for every candidate class.
6. **Robustness.** Every stage reports results for the six step variants and the three A4 smoothing windows.

**Common acceptance gates against V2.** These apply unless a stage says otherwise.

| Gate | Rule |
|---|---|
| G-causal | the causality check is bit-identical |
| G-proxy | MAE < V2's MAE for every Δ, and MAX ≤ V2's MAX + 0.10 pp |
| G-epsfree | ε-free CK2–7 MAE ≤ V2's − 0.02 pp |
| G-robust | beats V2's MAE (Δ = 0.4) in ≥ 5 of 6 step variants |
| G-regress | no checkup's absolute error grows by more than 0.30 pp against V2 (Δ = 0.4) |
| G-impl | a numpy/pandas-only candidate class with the `MyModel` interface (`fit`, `estimate_soh`) reproduces the research implementation within 0.001 pp and passes the sample_data smoke test in the 3.11 venv |

**Pre-registration.** Before running any evaluation in a stage, write `stage_X/protocol.json`: the main configuration, every variant, the gates and the selection rule. Record its SHA256 in `stage_X/protocol.sha256` and commit it.

- You may amend it only before that stage's evaluation code is run, and every amendment must state its reason.
- After evaluation you may not change the main configuration. Report variants as variants.

## 5. Stages

### Stage B — Charge-direction step measurements (cap 1 h)

**Goal.** Get a second, independent step-depth channel from the charge direction, which could double the number of measurements.

1. **Coverage audit (no proxy metrics yet).**
   - Find every charge that ends in CV at the pack level (≥ 13.95 V, 0 < I < 6 A at the end), including the ~5-day CCCV charges and the anchors.
   - For each, trace back to the start of the continuous charge.
   - Record: depth below the CV end at the start, the dominant CC current, the setpoint, and whether the charge crosses the step region (start depth ≥ 45 Ah).
   - Write `stage_B/coverage.csv` and a short summary.
2. **Location method.** Mirror the discharge method on the charge, with depth = Ah(CV end) − Ah(t):
   - a current band around the dominant CC current;
   - an upper window near full and a lower window below the step;
   - the first crossing of the midpoint between the plateau medians, per cell.

   Fix the windows from the coverage audit and the CK0 curve, before any proxy evaluation, and register them.
3. **Channel quality.** Report:
   - the fraction of events located;
   - the median four-cell range;
   - the offset between charge-side and discharge-side steps of the same program, and how stable it is;
   - the 25/45 °C jump in this channel.
4. **Use the channel.** Register a "V2 + charge steps" variant: the month-end 45 °C value becomes the mean of the last discharge-side step and the last charge-side step, the charge-side one offset-corrected with causally estimated offsets. Evaluate it against the gates.
5. **Exit.** If fewer than half of the months have ≥ 2 usable charge-side events at 45 °C, or the median four-cell range is > 1 Ah, mark the channel as "diagnostic only". Do not build the variant, and pass the measurement table to stage C as an optional input.

### Stage D — Gap extrapolation with pseudo-gap selection (cap 1.5 h)

**Goal.** Reduce CK2's error (+0.67 pp, the maximum) without tuning on CK2.

**Candidate rules.** They extend the fallback (M4) when the current month's 45 °C segment is truncated. Each predicts the step change, or the capacity change, from the last visible step to the CK date.

- **D0** — no extrapolation (current M4).
- **D1** — rate × β × gap days. The rate is the Theil–Sen 45 °C step rate of the most recent complete visible 45 °C segment other than segment 1; β is V2's β_k. If no such segment exists, use segment 1's rate from its last three steps only.
- **D2** — a semi-empirical capacity model fitted causally on the visible anchors and steps (converted with β): dQ/dt = −a·f(T)·(1/(2√t)) − b·(dAh/dt).
  - f(T) is an Arrhenius factor with Ea fixed at 37.3 kJ/mol (Yagci 2025 prior) and referenced to 25 °C. Use the actual mean cell temperature.
  - t is days since CK0 and Ah is throughput.
  - Fit a and b by least squares with non-negativity.
  - For the missing segment, use the counter jump `charge_Ah_cum` / `discharge_Ah_cum` across the gap for throughput, and 45 °C for temperature.
- **D3** — anchor trend in Q space: fit Q_fc,j vs √t over the visible 25 °C anchors (needs ≥ 2), and add the fitted increment from the last visible step time to the CK date.

**Selection.**

- Evaluate D0–D3 on PG1 and PG2 (k = 4..7) and on PC5/PC10.
- Choose the main rule by the lowest PG1 + PG2 MAE among the rules that are defined for CK2.
- It must beat D0 by ≥ 0.10 pp on PG1 + PG2; otherwise keep D0.
- **Write the choice down and commit it before computing the CK2 result.** Then apply it to CK2 and report the CK2 error and the full metrics.
- If D3 is not defined for CK2, it may still be reported, but not selected.

**Gates.** G-causal, G-regress, G-impl, plus: CK2's absolute error decreases, and the PG1 + PG2 MAE improves. G-epsfree and G-proxy are reported but are not required.

**Also report.** How each rule behaves when the anchor of month k−1 is missing (a leave-one-anchor-out scenario). This feeds the reduced-data-budget question.

### Stage A — Full-curve registration of the anchor charges (cap 2 h)

**Goal.** Split each month's capacity change into a lithium-inventory part and an active-material part, using the near-complete anchor charge curves. This gives a physical β per month and, optionally, a physical estimate of the drift in ε.

1. **Template.**
   - Per cell, use the post-CK0 anchor charge (20.4 A, 45 °C) and the first 25 °C anchor (post-CK1) as references.
   - Compute dV/dQ on a 0.25 Ah grid with registered smoothing (1/2/3 Ah).
   - Identify the robust features: the main graphite step peak, the high-SOC feature near the top if present, and the low-SOC tail onset. Register the feature definitions.
2. **Registration model.**
   - For anchor j (25 °C, j ≥ 2), relative to anchor 1, fit a piecewise-linear Ah map with breakpoints at the features: bottom section, step → top section, and a top offset.
   - Free parameters: at most three (top-section length change = LLI, bottom-section scale = LAM_NE proxy, and one bounded voltage offset).
   - Use least squares on dV/dQ, or on V(q), over the CC part only.
   - **Identifiability gate:** compute the profile of the fit residual for each parameter. If the profile is flat (a parameter changes by > 50 % within +5 % residual), mark that parameter as not identified.
3. **β from registration.**
   - β_reg,k = cumulative ΔQ_fc / cumulative Δ(top-section length), using the visible anchors j = 2..k−1, shrunk towards 1 with τ = 1 Ah², as in V2.
   - Register "V2 with β_reg" as the main variant of this stage, and evaluate it against the gates.
4. **Optional, exploratory ε drift.**
   - Apply each anchor's map to the CK0 C/20 reference discharge, per cell.
   - Sum the cell voltages and take the first 11.2 V root, which gives a modelled C/20 capacity per anchor.
   - Report ε_j(model) − ε0. This is not scored. It goes to stage E.
5. **Exit.** If the step → top length is not identified in most anchors, report it and keep V2's β.

### Stage C — Forward state-space fusion (cap 2.5 h)

**Goal.** One model that uses every visible observation, handles CK1–CK7 without special fallbacks, and gives an uncertainty.

**Structure (register it before fitting; do not tune it on the proxy).**

- **Latent capacity Q(t).** Piecewise-linear in time, with a separate rate for 25 °C and for 45 °C days in each month. Rates follow a random walk between months, with a prior SD of 0.02 Ah/day per month.
- **Anchor observations.** y_j = Q(t_anchor_j) − ε_j + noise, with SD 0.05 Ah. ε_j = ε0 for the post-CK0 anchor and ε0 + 0.4 for the 25 °C anchors.
- **Step observations.** In Ah below the CV end:
  - s = s0 + (Q(t) − Q0)/β + δ·[45 °C] + A_m·exp(−(t − t_anchor_m)/τ_tr)·[in month m] + noise.
  - Noise SD is 0.15 Ah, or from the four-cell spread.
  - β comes from stage A if stage A passed, else from V2.
  - δ has prior N(0.18, 0.1²) Ah.
  - A_m has prior N(0, 0.5²) per month.
  - τ_tr is fixed at 5 days. Variants are 3 and 8 days.
- **Optional charge-side observations** from stage B with their own offset, if stage B passed.

**Fitting.**

- At each cutoff, fit the model on the visible data only. The model is linear-Gaussian given β and τ_tr, so a batch weighted least-squares / MAP solve is enough.
- This batch fit is causal because only visible data are used. Never use data after the cutoff.
- Predict Q(CK_k) and its SD.

**Report.**

- Gates against V2.
- Calibration of the predicted SD against the proxy errors and the pseudo scenarios. With 7 points this is descriptive only.
- The fitted δ, A_m and rates per cutoff.

**Variants:** τ_tr ∈ {3, 5, 8}; with and without charge-side steps; β from V2 vs from A.

### Stage E — Four-cell pack-cutoff / ε-drift model (cap 1 h)

**Goal.** Quantify how much ε could drift because the cells drift apart. This is the biggest unverified risk for the real score. It is **not** scored on the proxies, because the proxies are the anchors.

- **Model.**
  - Per cell, map the CK0 C/20 reference discharge with that cell's state. The state is the stage A per-cell maps if they are available, else per-cell step offsets relative to the four-cell mean and per-cell top-section lengths from A4.
  - Compute the pack's first 11.2 V root over months, and compare it with the pack-level full charge.
- **Output.** A table of modelled ε_k − ε0 for k = 1..7, with ranges across the variants.
- **Decision.** If the maximum |ε_k − ε0| is < 0.10 pp, write "negligible". Otherwise register an "ε-drift-corrected" variant of the best model as a *leaderboard-only* option. Never claim it improves the proxy score.

### Stage F — Fixed-weight ensemble (cap 0.5 h)

- **Members.** Use only models that passed their stage gates (V2 always counts).
- **Weights.** Equal weights, fixed before evaluation.
- **When to report it.** Report the ensemble only if the members' per-checkup error correlation is < 0.8.
- **Gates.** The common gates against V2.

## 6. Order, caps and stop rules

| Order | Stage | Cap |
|---|---|---|
| 0 | Setup + harness, reproducing V2 | 0.5 h |
| 1 | B | 1 h |
| 2 | D | 1.5 h |
| 3 | A | 2 h |
| 4 | C | 2.5 h |
| 5 | E | 1 h |
| 6 | F + final report | 0.5–1 h |

**Stop rules.**

- If the harness cannot reproduce V2 (0.216 / 0.669), stop the whole run, write `notes/STATUS.md`, and commit.
- If a candidate fails G-causal, it is rejected outright.
- A stage that gets no passing variant is still a valid result. Write it up.

## 7. Outputs

```
research/phase2_round3_models_20261014/
  EXECUTION_PROMPT.md   (this file)
  README.md             (bilingual: layout, how to reproduce, environment)
  FINAL_REPORT.md       (bilingual, conclusions first)
  notes/STATUS.md  notes/DECISIONS.md
  src/harness.py  src/<stage modules>.py
  stage_B/ stage_D/ stage_A/ stage_C/ stage_E/ stage_F/
      protocol.json  protocol.sha256  run_*.py  outputs/*.csv|json  REPORT.md (bilingual, short)
  candidate_model/<name>_model.py   (one per passing model, MyModel interface, numpy/pandas only)
```

**`FINAL_REPORT.md` contents.**

1. A summary table of every candidate against M4 and V2: MAE for each Δ, MAX, ε-free MAE, per-checkup errors, pseudo-scenario MAE, gate results.
2. What each stage found, including negative results.
3. Which model, if any, should replace V2 as the leading candidate, and why.
4. Risks, including the exposure statement, ε, the post-checkup recovery and a single pack.
5. Exact reproduction commands.

**Do not wire anything into `my_model/`.** That is the user's decision.

## 8. Prohibitions (summary)

- Do not use data after CK_k for CK_k, including in thresholds, normalisation, feature definitions or selection.
- Do not change a registered main configuration after seeing its proxy results, and do not report the best variant as the main result.
- Do not tune anything on CK2 in stage D before the rule is committed.
- Do not present proxies as hidden truth, and do not reconstruct CK1–CK7 from external sources.
- Do not modify the submission package or the earlier studies. Do not push anywhere except the new branch. Do not force-push.
- Do not ask the user anything. Record decisions and continue.

---

<a id="zh"></a>

# 第三轮：备选容量模型（B → D → A → C → E → F）——无人值守执行 Prompt

> **语言：** [English](#en) · 中文

编写日期：2026-10-14。本文自成一体，可交给看不到之前聊天记录的执行者。英文部分是执行文本，本中文部分是给读者的翻译；两者不一致时以英文为准。

## 0. 工作方式：通宵无人值守运行

- **没有人会回答问题。** 不要停下来提问。遇到未定的决策，选择在遵守本文全部规则前提下最保守的方案，把决策和理由写进 `notes/DECISIONS.md`，然后继续。
- **上下文可能被压缩或重启。** 每完成一步都更新 `notes/STATUS.md`：当前阶段、已完成内容、下一步、最近一次提交。任何重启后，先读 `notes/STATUS.md` 和 `notes/DECISIONS.md`，从那里接着做。不要重做已完成的阶段。
- **时间预算。** 全程约 9 小时，每个阶段有上限（第 6 节）。阶段到达上限时停止，把已有结果写成报告（包括"无定论"），提交，然后进入下一阶段。
- **完成的标准。** 六个阶段都已完成或到达上限，`FINAL_REPORT.md` 已写好，所有提交都已推送（第 1 节）。然后停止。

## 1. 工作区、分支与 git 规则

- **仓库与 worktree。** 在 git worktree `/Users/shane/Desktop/Arena_1013_model` 中工作，不要 `cd` 到其他检出目录。
- **分支。** 从 `exp/phase2-anchor-step-20261013`（HEAD `886bfc1` 或更新）创建 `exp/phase2-round3-models-20261014`。所有工作放在 `research/phase2_round3_models_20261014/`（下称"研究目录"）。
- **首次提交。** 新分支的第一个提交是本 prompt。
- **提交与推送。** 每个阶段结束时提交，有意义的子步骤完成时也提交。每次阶段提交后推送新分支：`git push -u origin exp/phase2-round3-models-20261014`。不要推送到 `main` 或 `exp/phase2-anchor-step-20261013`，不要强制推送。
- **提交信息**结尾加：
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
- **不要修改：**
  - `TechArena_Challenge2_Team_Package/` 的任何内容，包括 `framework/`、`run_model.py`、`validate_submission.py`、`my_model/` 和 `data/`；
  - 之前的研究目录 `research/phase2_anchor_step_20261013/` 和 `research/phase2_v2_phase_matched_20261013/`。

  可以导入其中的代码，但不要编辑。
- **git stash。** 不要使用裸 `git stash`，stash 栈与其他会话共享。
- **文档语言。** 本分支写的每个 Markdown 文档都是英文在前、中文在后，格式与本文件相同：锚点 `<a id="en"></a>`、语言切换行、`---`、`<a id="zh"></a>`。代码注释和 docstring 只用英文。

## 2. 任务与背景

**任务。** TechArena 2026 Challenge 2，Topic 1：估计 4 × 102 Ah LFP 串联电池组在每个检查日的 SOH。

- SOH = C/20 容量 ÷ 102 Ah。C/20 容量是满充后以 5.1 A 放电、直到组端电压首次达到 11.2 V 时放出的 Ah。
- 只公开 CK0 = 100.41 Ah（98.44 %）；CK1–CK7 隐藏，用于评分。
- 检查日：CK0 2025-01-14，CK1 02-08，CK2 03-11，CK3 04-14，CK4 05-16，CK5 06-16，CK6 07-25，CK7 08-28。
- 评分是以官方 ExampleModel 归一化的误差指标，越低越好。
- **因果截断。** 预测 CK_k 只能使用 `load_dataset(data, until=CK_k)`，截断点是该日 00:00。

**数据。** 运行数据共 13 段，10 s 采样。

- 各段在 25 °C（短）和 45 °C（长）之间交替。
- 第 m 月从检查 CK_m 后的锚点充电开始，到下一次检查为止，由一个 25 °C 段加一个 45 °C 段组成；第 0 月例外，只有第 1 段（45 °C）。
- 第 3 段（2 月 19 日 – 3 月 11 日，45 °C）缺失，所以第 1 月在 CK2 之前只能看到一次 45 °C 台阶（2 月 17 日）。

**现有模型。** 前两个都在本分支上：

- **V1 / M4**（`research/phase2_anchor_step_20261013/`，报告见 `FINAL_REPORT.md`）：当前提交包使用的模型。
  - **锚点：** 每月以一次检查后从近空到 14.0 V CV 末端的充电开始（Q_fc）。CK0–CK7 之后的 Q_fc = 100.122、97.003、95.670、94.642、93.747、93.082、92.636、91.954 Ah。
  - **偏置：** Q_anchor = Q_fc + ε，其中 ε = ε0 + 0.4 Ah，ε0 = 100.41 − 100.122。
  - **月内更新：** 加上（锚点后最后一次台阶深度 − 第一次台阶深度）。台阶深度指约每 5 天一次的深放电中，石墨分阶台阶位于 CV 末端以下的 Ah 数。
- **V2**（`research/phase2_v2_phase_matched_20261013/`）：目前最好的候选，尚未接入提交包。
  - 只比较相邻两个月的月末 45 °C 台阶深度。
  - β 由可见 25 °C 锚点的充电方向 LLI 份额（A4）求得，并向 1 收缩。
  - CK1–CK3 回退到 M4。
  - ε0+0.4 下的代理结果：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | MAE | 最大 |
|---|---|---|---|---|---|---|---|---|---|
| M4 | +0.22 | +0.67 | +0.08 | +0.28 | −0.11 | −0.40 | −0.28 | 0.291 | 0.669 |
| V2 | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 | 0.216 | 0.669 |

- V2 各检查点的 β：1.06（CK4）、1.24、1.41、1.51（CK7）。

**台阶信号的已知结构。** 要利用，也要检验：

- 每次 25 → 45 °C 切换，台阶深度上跳约 +0.18 Ah；第 1 月为 +0.60。
- 每次检查后的 25 °C 段里台阶深度下降很快（0.07–0.13 Ah/天），45 °C 段很慢（0.02–0.04 Ah/天）。这看起来是瞬态（overhang / 再均匀化），不是老化。
- 锚点间损失有 68–79 % 位于台阶以上（以 LLI 为主），对应 β ≈ 1.3–1.45。

**代理标签及其局限。** P_k = Q_fc,k + ε，在 ε ∈ {ε0, ε0+0.4, ε0+0.8} 下评分。

- 基于锚点的预测在 CK2–CK7 上的误差与 ε 无关（即"与 ε 无关"的指标）。
- CK1–CK7 的代理值都已看过，所以本轮所有结果都是**已曝光的探索性结果**，每份报告都要写明。
- 代理不是隐藏真值，绝不能把它们说成"真实 CK 值"。

**文献。** 本计划依据的文献是分支 `research-archive-20261010` 上 `research/phase2_literature_reassessment/outputs/` 下的两份文档：

- `LFP_SOH_第二阶段文献综述与技术路线_深度重评.md`（综述与路线 R01–R09）；
- `LFP_SOH_核心论文精读与证据附册.md`（33 篇论文卡）。

用 `git show research-archive-20261010:<path>` 读取。它们写于锚点发现之前，路线排序已经过时；但其中关于可辨识性、温度分层、组端截止、信息路径的约束仍然适用。

**不要重试以下方法**，它们以前失败过，或者没有标签支撑：

- 平台窗口局部 Ah 估容量；
- 平台中段窗口上的 SOC/SOH 联合 ECM；
- ICA 峰位 → 容量；
- 脉冲或弛豫特征 → 容量回归；
- 深度、自监督或迁移模型；
- 拐点检测。

## 3. 必须复用的代码

- `research/phase2_anchor_step_20261013/src/events.py`：
  - `full_charges(op)`（锚点；列包括 `t_start`、`t_end`、`Q_Ah`、`setpoint_C`、`_seg_index` 以及起止时的单体电压）；
  - `step_programs(op, **STEP_VARIANTS[v])`（放电方向台阶；6 种变体）；
  - `charge_step_split(op, fc, smooth_Ah)`（A4）；
  - `segment_arrays`；
  - `ck0_reference_step`。
- `research/phase2_v2_phase_matched_20261013/src/v2.py`：`anchors_by_checkup`、`month_steps`、`end45`、`phase_diff`、`beta_a4`、`m4`、`v2`。
- `research/phase2_v2_phase_matched_20261013/stage_v2_eval.py`（评估循环与代理）和 `stage_v2_candidate.py`（因果检查与重写一致性检查）：照着它们的写法做。
- **数据与框架：** `TechArena_Challenge2_Team_Package/data/` 和 `framework/data.py`。`Dataset.eval_points` 含全部检查日。
- **积分规则：** 充电为正；`current_A` 按真实时间步长积分；Δt > 600 s 或 Δt ≤ 0 不积分。Ah 计数器把 20 A 脉冲记为充电，所以计算深度时绝不能用计数器。

**环境。**

- **研究脚本：** 用 `python3`（3.13，含 numpy/pandas/scipy/matplotlib）。
- **候选类：** 只能依赖 numpy/pandas，还必须能在 Python 3.11 venv 中运行。venv 建在会话 scratchpad 或 `/tmp` 下，用 `/opt/homebrew/bin/python3.11` 创建并 `pip install numpy pandas`。

## 4. 共享评估框架（第 0 阶段先建好）

在研究目录写 `src/harness.py`，供每个阶段使用。

1. **逐检查点数据。** 对 k = 1..7，运行 `load_dataset(data, until=CK_k)`，提取 fc、全部 6 种变体的台阶、平滑窗口 1/2/3 Ah 下的 A4。结果缓存到 `cache/`，并加入 git 忽略。
2. **代理。** 完全沿用 V2 的定义：P_k = Q_fc,k（全量数据）+ ε0 + Δ，Δ ∈ {0, 0.4, 0.8}。
3. **指标。**
   - 每个 Δ 下的 MAE、MAX、RMSE（pp）；
   - 与 ε 无关的 CK2–7 MAE；
   - 逐检查点误差；
   - 与 M4、V2 的对比表，M4 和 V2 都通过框架重新计算。Δ = 0.4 时必须复现 V2 的 0.216 / 0.669，否则停下来修好框架。
4. **伪截止与伪缺口情景。** 它们提供比 7 个代理更多的测试情形。实现为返回截断后运行数据 DataFrame 的函数：
   - **PG1"类 CK2 缺口"：** 对 k = 4..7，在第 k−1 月保留 25 °C 段，45 °C 段只保留到其第一次深放电结束（第一次 45 °C 台阶）为止的数据，删掉该 45 °C 段其余部分，然后预测 CK_k。
   - **PG2：** 与 PG1 相同，但保留前两次 45 °C 台阶。
   - **PC5 / PC10：** 在 CK_k 前 5 / 10 天截断数据，k = 2..7。

   全部用同一套 P_k 评分；k ≥ 2 时都与 ε 无关。
5. **因果检查。** 截断点之后的每一行都换成噪声，预测必须逐位不变；另外用截断到 CK1 的数据做 fit。每个候选类都要做。
6. **稳健性。** 每个阶段都报告 6 种台阶变体和 3 种 A4 平滑窗口下的结果。

**相对 V2 的通用接纳门。** 各阶段另有规定的除外。

| 门 | 规则 |
|---|---|
| G-causal | 因果检查逐位一致 |
| G-proxy | 每个 Δ 下 MAE 都低于 V2，且 MAX ≤ V2 的 MAX + 0.10 pp |
| G-epsfree | 与 ε 无关的 CK2–7 MAE ≤ V2 − 0.02 pp |
| G-robust | 6 种台阶变体中至少 5 种的 MAE（Δ = 0.4）优于 V2 |
| G-regress | 与 V2 相比，任何检查点的绝对误差增加不超过 0.30 pp（Δ = 0.4） |
| G-impl | 有一个只依赖 numpy/pandas、具备 `MyModel` 接口（`fit`、`estimate_soh`）的候选类，与研究实现相差在 0.001 pp 以内，并在 3.11 venv 中通过 sample_data 冒烟测试 |

**预登记。** 每个阶段运行任何评估之前，先写 `stage_X/protocol.json`：主配置、全部变体、接纳门和选择规则。在 `stage_X/protocol.sha256` 记录其 SHA256 并提交。

- 只能在该阶段的评估代码运行之前修订，每次修订都要写明理由。
- 评估之后不得更改主配置；变体只能作为变体报告。

## 5. 各阶段

### 阶段 B——充电方向台阶测量（上限 1 小时）

**目标。** 从充电方向得到第二条独立的台阶深度通道，可能让测量次数翻倍。

1. **覆盖审计（先不算代理指标）。**
   - 找出所有以组端 CV 结束的充电（≥ 13.95 V，结束时 0 < I < 6 A），包括约每 5 天一次的 CCCV 充电和锚点充电。
   - 对每次充电，回溯到这段连续充电的起点。
   - 记录：起点位于 CV 末端以下的深度、主导 CC 电流、温度设定、是否越过台阶区（起点深度 ≥ 45 Ah）。
   - 写入 `stage_B/coverage.csv`，并附简短小结。
2. **定位方法。** 在充电上镜像放电方向的方法，深度 = Ah(CV 末端) − Ah(t)：
   - 围绕主导 CC 电流取电流带；
   - 取满充附近的上窗口和台阶下方的下窗口；
   - 每颗电芯取平台中位电压中点的首次穿越。

   窗口根据覆盖审计和 CK0 曲线确定，在任何代理评估之前登记。
3. **通道质量。** 报告：
   - 定位成功率；
   - 四芯极差中位数；
   - 同一程序中充电侧与放电侧台阶的偏移量及其稳定性；
   - 本通道中的 25/45 °C 跳变。
4. **使用通道。** 登记一个"V2 + 充电台阶"变体：月末 45 °C 值改为最后一次放电侧台阶与最后一次充电侧台阶的均值，充电侧台阶用因果估计的偏移量修正。按接纳门评估。
5. **退出条件。** 如果不到一半的月份在 45 °C 下有 ≥ 2 次可用的充电侧事件，或四芯极差中位数 > 1 Ah，就把该通道标为"仅诊断"，不构建该变体，把测量表作为可选输入交给阶段 C。

### 阶段 D——缺段外推与伪缺口选择（上限 1.5 小时）

**目标。** 在不对 CK2 调参的前提下降低 CK2 的误差（+0.67 pp，目前的最大误差）。

**候选规则。** 当本月 45 °C 段被截断时，在回退模型（M4）基础上外推，预测从最后一次可见台阶到检查日之间的台阶变化或容量变化。

- **D0**：不外推（即现在的 M4）。
- **D1**：速率 × β × 缺口天数。速率取最近一个完整可见、且不是第 1 段的 45 °C 段的 Theil–Sen 台阶速率；β 取 V2 的 β_k。没有这样的段时，只用第 1 段最后三次台阶计算速率。
- **D2**：用可见锚点和台阶（经 β 换算）因果拟合半经验容量模型：dQ/dt = −a·f(T)·(1/(2√t)) − b·(dAh/dt)。
  - f(T) 是 Arrhenius 因子，Ea 固定为 37.3 kJ/mol（Yagci 2025 先验），以 25 °C 为参考，使用实际单体平均温度。
  - t 为自 CK0 起的天数，Ah 为吞吐量。
  - a、b 用非负约束的最小二乘拟合。
  - 缺失段的吞吐量用 `charge_Ah_cum` / `discharge_Ah_cum` 在缺口前后的跳变，温度取 45 °C。
- **D3**：在 Q 空间做锚点趋势：用可见的 25 °C 锚点（至少 2 个）拟合 Q_fc,j 对 √t，加上从最后一次可见台阶时间到检查日之间的拟合增量。

**选择。**

- 在 PG1、PG2（k = 4..7）以及 PC5/PC10 上评估 D0–D3。
- 在对 CK2 有定义的规则中，选 PG1 + PG2 MAE 最低的作为主规则。
- 它在 PG1 + PG2 上必须比 D0 至少好 0.10 pp，否则保留 D0。
- **先把选择写下来并提交，再计算 CK2 的结果。** 然后应用到 CK2，报告 CK2 误差和完整指标。
- D3 若对 CK2 无定义，可以报告，但不能被选中。

**接纳门。** G-causal、G-regress、G-impl，另加：CK2 的绝对误差下降，且 PG1 + PG2 的 MAE 改善。G-epsfree 和 G-proxy 只报告，不作要求。

**另外报告。** 第 k−1 月的锚点缺失时各规则的表现（留一锚点情景），这对应数据削减评估的问题。

### 阶段 A——锚点充电的全曲线配准（上限 2 小时）

**目标。** 利用几乎完整的锚点充电曲线，把每月的容量变化拆成活性锂部分和活性物质部分，从而得到每月的物理 β，并可选地得到 ε 漂移的物理估计。

1. **模板。**
   - 每颗电芯以 CK0 后的锚点充电（20.4 A，45 °C）和第一次 25 °C 锚点（CK1 后）为参考。
   - 在 0.25 Ah 网格上计算 dV/dQ，平滑窗口（1/2/3 Ah）事先登记。
   - 识别稳健的特征：石墨主台阶峰、靠近顶端的高 SOC 特征（若存在）、低 SOC 尾部起点。特征定义事先登记。
2. **配准模型。**
   - 对锚点 j（25 °C，j ≥ 2），相对锚点 1 拟合分段线性的 Ah 映射，断点位于各特征处：底部段、台阶→顶部段，以及一个顶部偏移。
   - 自由参数最多三个：顶部段长度变化（即 LLI）、底部段缩放（LAM_NE 的代理量）、一个有界的电压偏置。
   - 只在 CC 部分，对 dV/dQ 或 V(q) 做最小二乘。
   - **可辨识性门：** 对每个参数计算拟合残差的剖面。剖面平坦（残差增加 5 % 以内、参数变化超过 50 %）时，把该参数标为不可辨识。
3. **由配准得到 β。**
   - β_reg,k = 累计 ΔQ_fc / 累计 Δ（顶部段长度），使用可见锚点 j = 2..k−1，并像 V2 一样以 τ = 1 Ah² 向 1 收缩。
   - 把"V2 改用 β_reg"登记为本阶段的主变体，按接纳门评估。
4. **可选的探索性 ε 漂移。**
   - 把每个锚点的映射逐芯应用到 CK0 C/20 参考放电曲线上。
   - 四芯电压相加，取首次 11.2 V 的根，得到每个锚点的模型 C/20 容量。
   - 报告 ε_j（模型）− ε0。这一项不评分，结果交给阶段 E。
5. **退出条件。** 如果多数锚点的台阶→顶部段长度不可辨识，就如实报告，保留 V2 的 β。

### 阶段 C——前向状态空间融合（上限 2.5 小时）

**目标。** 用一个模型利用所有可见观测，CK1–CK7 都不需要特殊回退，并给出不确定度。

**结构（拟合前登记，不得在代理上调参）。**

- **潜在容量 Q(t)。** 随时间分段线性，每个月的 25 °C 天和 45 °C 天各有一个速率。速率在月与月之间做随机游走，先验标准差为每月 0.02 Ah/天。
- **锚点观测。** y_j = Q(t_anchor_j) − ε_j + 噪声，噪声标准差 0.05 Ah。CK0 后的锚点取 ε_j = ε0，25 °C 锚点取 ε0 + 0.4。
- **台阶观测。** 以 CV 末端以下的 Ah 计：
  - s = s0 + (Q(t) − Q0)/β + δ·[45 °C] + A_m·exp(−(t − t_anchor_m)/τ_tr)·[属于第 m 月] + 噪声。
  - 噪声标准差 0.15 Ah，或由四芯离散度给出。
  - β：阶段 A 通过则取阶段 A 的值，否则取 V2 的值。
  - δ 的先验为 N(0.18, 0.1²) Ah。
  - A_m 的先验为每月 N(0, 0.5²)。
  - τ_tr 固定为 5 天，变体取 3 天和 8 天。
- **可选的充电侧观测。** 阶段 B 通过时加入，带各自的偏移量。

**拟合。**

- 每个截断点只用可见数据拟合。给定 β 和 τ_tr 时模型是线性高斯的，用批量加权最小二乘 / MAP 求解即可。
- 这样的批量拟合只用可见数据，所以是因果的。绝不能使用截断点之后的数据。
- 预测 Q(CK_k) 及其标准差。

**报告。**

- 相对 V2 的接纳门结果。
- 预测标准差相对于代理误差和伪情景的校准情况。只有 7 个点，仅作描述。
- 每个截断点拟合出的 δ、A_m 和速率。

**变体：** τ_tr ∈ {3, 5, 8}；有、无充电侧台阶；β 取自 V2 或取自阶段 A。

### 阶段 E——四芯组端截止 / ε 漂移模型（上限 1 小时）

**目标。** 量化电芯之间逐渐拉开会让 ε 漂移多少。这是真实分数上最大的未验证风险。代理标签本身就是锚点，所以本阶段**不**按代理评分。

- **模型。**
  - 每颗电芯用自己的状态映射 CK0 C/20 参考放电曲线。状态优先用阶段 A 的逐芯映射；没有时，用各芯台阶相对四芯均值的偏移，以及 A4 给出的各芯顶部段长度。
  - 逐月计算组端首次 11.2 V 的根，并与组端完整充电量比较。
- **产出。** k = 1..7 的模型 ε_k − ε0 表，附各变体之间的范围。
- **决策。** 若 |ε_k − ε0| 的最大值 < 0.10 pp，写"可忽略"。否则把最佳模型的"ε 漂移修正"变体登记为*只供排行榜检验*的选项，绝不声称它改善了代理分数。

### 阶段 F——固定权重集成（上限 0.5 小时）

- **成员。** 只用通过各自阶段接纳门的模型（V2 始终计入）。
- **权重。** 等权，评估前固定。
- **何时报告。** 只有成员间逐检查点误差的相关系数 < 0.8 时才报告集成结果。
- **接纳门。** 相对 V2 的通用接纳门。

## 6. 顺序、上限与停止规则

| 顺序 | 阶段 | 上限 |
|---|---|---|
| 0 | 准备 + 评估框架，并复现 V2 | 0.5 小时 |
| 1 | B | 1 小时 |
| 2 | D | 1.5 小时 |
| 3 | A | 2 小时 |
| 4 | C | 2.5 小时 |
| 5 | E | 1 小时 |
| 6 | F + 最终报告 | 0.5–1 小时 |

**停止规则。**

- 如果评估框架无法复现 V2（0.216 / 0.669），停止整个运行，写好 `notes/STATUS.md` 并提交。
- 候选未通过 G-causal 就直接淘汰。
- 某阶段没有任何变体通过，也是有效结果，照样写报告。

## 7. 输出

```
research/phase2_round3_models_20261014/
  EXECUTION_PROMPT.md   （本文件）
  README.md             （中英双语：结构、复现方法、环境）
  FINAL_REPORT.md       （中英双语，结论在前）
  notes/STATUS.md  notes/DECISIONS.md
  src/harness.py  src/<各阶段模块>.py
  stage_B/ stage_D/ stage_A/ stage_C/ stage_E/ stage_F/
      protocol.json  protocol.sha256  run_*.py  outputs/*.csv|json  REPORT.md（中英双语，简短）
  candidate_model/<name>_model.py   （每个通过的模型一个，MyModel 接口，只依赖 numpy/pandas）
```

**`FINAL_REPORT.md` 的内容。**

1. 所有候选相对 M4 和 V2 的汇总表：每个 Δ 下的 MAE、MAX、与 ε 无关的 MAE、逐检查点误差、伪情景 MAE、接纳门结果。
2. 每个阶段的发现，包括负面结果。
3. 是否有模型应取代 V2 成为领先候选，以及理由。
4. 风险，包括曝光声明、ε、检查后回弹、单一电池组。
5. 准确的复现命令。

**不要把任何东西接入 `my_model/`**，那由用户决定。

## 8. 禁止事项（汇总）

- 不得用 CK_k 之后的数据预测 CK_k，包括阈值、归一化、特征定义和选择。
- 看到代理结果后不得更改已登记的主配置，不得把最好的变体当作主结果报告。
- 阶段 D 中，规则提交之前不得对 CK2 调任何参数。
- 不得把代理说成隐藏真值，不得从外部来源重建 CK1–CK7。
- 不得修改提交包或之前的研究目录。除新分支外不推送到任何地方，不强制推送。
- 不向用户提问。记录决策，然后继续。
