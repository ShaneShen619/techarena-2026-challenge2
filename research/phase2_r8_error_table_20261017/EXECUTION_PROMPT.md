<a id="en"></a>

# Round 8: Error-Analysis Long Tables — Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-17. This document is self-contained. The English text is the execution text; the Chinese section is a translation for the reader, and if they differ the English governs.

**Goal of the round.** Build one consistent set of long tables (cases, events, anchors, optionally daily cycles), then slice the residuals by sample type, operating condition and value range to find where the submitted model fails systematically. The round produces **tables, figures and ranked hypotheses for the next round**. It builds no candidate, tunes nothing and never changes the submission.

The work is split into **work packages WP0–WP6**. Each has its own *Done* list and can be run as a separate `/goal`. WP0 must be done first. WP1, WP2 and WP3 are independent of each other; WP4 is optional; WP5 needs WP1–WP3; WP6 comes last.

## 0. Mode of work (all work packages)

- **Unattended.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Restarts.** Keep `notes/STATUS.md` current after every step: WP, done, next, last commit. On restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume. Never redo a finished WP or step.
- **Honesty over targets.** A null result ("no systematic pattern beyond noise") is a valid outcome. Every statistic in this round is descriptive.
- **Done for any WP** means the common criteria below, plus that WP's own list:
  1. for WP5, its registered protocol (`wp5/protocol.json` + `wp5/protocol.sha256`) was committed **before** any residual slice was computed;
  2. its bilingual `wpN/REPORT.md` exists, conclusions first;
  3. `notes/STATUS.md` marks the WP done, capped, skipped or exited, with one line of result;
  4. every commit is pushed to `origin exp/phase2-r8-error-table-20261017`, and `git status` shows no uncommitted study files.
- **Global Done:** WP0–WP6 each done, capped, skipped or exited by a registered rule; `FINAL_REPORT.md` and `README.md` exist (bilingual, conclusions first); `DATA_DICTIONARY.md` covers every column of every table; common criteria 3–4 hold.

## 1. Workspace, isolation, git

- **Worktree and branch (create in WP0 if missing; idempotent).**
  - Base: round 7's final commit on `exp/phase2-r7-lit-checks-20261016` (`c9658ad` at writing time; use the branch tip and record its hash). It already contains the round 3 harness, V2/V3, round 6 sources and round 7 `src/tsqrt.py`.
  - Create: `git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1017_r8_err -b exp/phase2-r8-error-table-20261017 <base>`. If it exists, check that its history contains `<base>` and reuse it.
  - Work only in `/Users/shane/Desktop/Arena_1017_r8_err`. The study directory is `research/phase2_r8_error_table_20261017/`.
- **Code to reuse (present on the base branch):**
  - round 3 harness `research/phase2_round3_models_20261014/src/harness.py` (scenarios real, PG1, PG2, PC5, PC10; `cut_op`, `scenario_op`, `proxies`, `run`);
  - V2 `research/phase2_v2_phase_matched_20261013/src/v2.py`, events `research/phase2_anchor_step_20261013/src/events.py`, V3 `research/phase2_r7_lit_checks_20261016/sources/v3/v3.py`;
  - round 7 `research/phase2_r7_lit_checks_20261016/src/` (`tsqrt.py` with design `T_main`, `common6.py`, `runner5c.py`, the CS/CSE cold-start scenarios);
  - existing diagnostic tables (start from these; recompute only what is missing):
    - `research/phase2_r6_robust_20261016/sources/rebound_diagnosis/outputs/events_merged.csv` (41 deep programs: charge Ah, CV Ah/h, end current, rest before charge, per-cell pulse R, V/I/T at 15/25/35/45 Ah depth, step depth for 6 variants, days since checkup);
    - `research/phase2_r7_lit_checks_20261016/wp0/outputs/wp0_3a_start_state.csv`, `wp0_3c_path_offsets.csv`, `wp0_branch_by_case.csv`;
    - `research/phase2_r7_lit_checks_20261016/wp1/outputs/anchor_state_table.csv`.
  - Copy what you change into this study and edit only the copies.
- **Read-only source outside this worktree.** The **submission branch** `exp/phase2-anchor-step-20261013`, commit `5cd305c`, in `/Users/shane/Desktop/Arena_1013_model`. Use only `git -C … show` / `git -C … archive`; never `cd` into it or write to it. `TechArena_Challenge2_Team_Package/my_model/model_template.py` there is the **submitted model SUB = T_main** (V2 + temperature-weighted √t gap branch). Extract it into `cache/submitted_package/`. Also read `EXPECTED_SOH` from `research/phase2_v3_20261015/package_submission.py` at that commit. Record copied files with SHA256 in `sources/SOURCES.md`.
- **Concurrency guard.** At the start and before every commit, run `git log --oneline -5` and compare with your last commit. On an unexpected commit, stop editing shared files, record it, and add files by explicit path only. Never `git add -A` / `.`, never bare `git stash`, never rewrite others' work. The untracked `research/phase2_round3_models_20261014/` leftovers in the submission worktree are not yours; ignore them.
- **Commits.** Commit this prompt first, copied from `/Users/shane/Desktop/Arena_1013_model/research/phase2_r8_error_table_20261017/EXECUTION_PROMPT.md` to the same relative path. Commit at the end of every step, then `git push -u origin exp/phase2-r8-error-table-20261017`. Never push elsewhere; never force. End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify:** any `TechArena_Challenge2_Team_Package/`, any earlier study directory, any file outside this worktree.
- **Language and bytecode.** Markdown is English first, Chinese second, in this file's layout. Code comments are English only. Run Python with `python3 -B`. No downloads are needed.

## 2. Context

**Task.** Estimate the SOH (C/20 capacity / 102 Ah) of a 4 × 102 Ah LFP series pack on CK0..CK7. Only CK0 = 100.41 Ah is released. The framework cuts data at the checkup date (`load_dataset(data, until=CK_k)`).

**Proxies** (all seen, so every real-scenario number is exposed-exploratory): P_k = Q_fc,k + ε0 + Δ, where Q_fc,k is the post-CK_k empty→full anchor charge, ε0 = 100.41 − Q_fc,0 and Δ ∈ {0, 0.4, 0.8}. Treat differences below 0.25 pp in proxy MAE as unresolvable.

**SUB = T_main** (commit `5cd305c`). Proxy MAE Δ0/0.4/0.8 = 0.197/0.126/0.146 pp, MAX 0.609/0.228/0.228; pseudo 0.144; cold start 0.170; one-month causal gap cases 0.105. Real-scenario branches: CK1 and CK3 `fallback` (anchor + `after[-1] − after[0]`, β = 1); CK2 `sqrt_gap`; CK4–CK7 `phase` (phase-matched month-end 45 °C step difference × β).

**Known effects (do not re-test; record them as columns so the slices can control for them):**
- the first deep program after every anchor charge sits 0.41–0.56 Ah deeper (0.83 Ah for month 0 at 45 °C); dropping those programs contradicts the proxies (round 6 3c); the overhang explanation is not supported (round 7 WP1);
- the step depth jumps about +0.18 Ah at every 25→45 °C switch (V2 study);
- anchor start state differs by up to 1.29 Ah (upper bound from the CK0 C/20 tail, round 6 3a);
- ε drift of about −0.031 Ah per Ah of fade is plausible but its sign is not robust (round 7 WP3). Any residual trend of that size is **invisible to the proxies** and must be labelled as such, never "fixed";
- operation counters book the 20 A pulse as charge; integrate `current_A` instead.

## 3. Common rules

1. **Register slices before looking.** All slice variables, bins, residual definitions and hypotheses H1–H10 (WP5) are frozen in `wp5/protocol.json` before any residual is grouped, plotted or ranked. Building the tables (WP1–WP4) is allowed before registration; looking at residuals by slice is not. Add any extra slice only as `exploratory-unregistered` and report it separately.
2. **No model changes.** Never build, tune or wire a candidate. Counterfactual recomputations in WP5 (for example, "fallback increment with the second post-anchor program") are diagnostics, labelled `diagnostic-only`, and never compared as proxy MAE improvements.
3. **Small samples and dependence.** 7 real cases, about 48 causal cases, 41 events (164 with cells), 8 anchors. Events in the same month are not independent. For every association report the effect size, the sign count, a bootstrap 90 % CI **resampling months as blocks**, and a permutation p-value **permuting within setpoint and across month blocks** (exact when n ≤ 9). Never state significance alone.
4. **Units.** Store residuals in Ah and in pp (pp = 100 · Ah / 102). Sign convention everywhere: residual = predicted − reference.
5. **Causality.** The event and anchor tables are diagnostics built from the full operation data. Every case-table field must come from the scenario's cut data, exactly as the framework would hand it to the model.
6. **Determinism.** Cache keys include every parameter; reruns must be byte-identical. Seeds are fixed in the protocol.

## 4. Work packages

### WP0 — Setup and re-baselining (cap 0.5 h)

- Create the worktree, `notes/STATUS.md`, `notes/DECISIONS.md`, `.gitignore` (`cache/`), `sources/SOURCES.md`.
- Reproduce SUB = T_main with the round 7 research implementation: the real-scenario metrics above (within 0.001 pp), pseudo 0.144 and cold start 0.170.
- Run the extracted submitted class from `5cd305c` on the full data with the framework's cut and compare with the research implementation per checkup (within 0.0005 pp) and with `EXPECTED_SOH`.
- Rebuild `wp0_branch_by_case.csv` under T_main for every scenario (real, PG1, PG2, PC5, PC10, CS, CSE).
- **Done:** all reproductions pass (if SUB fails, stop the whole run and record why), plus the common criteria. `wp0/REPORT.md` is short.

### WP1 — Case table (cap 2 h)

`outputs/table_cases.csv`, one row per (scenario, k, Δ, model), for models SUB (T_main), V2+√t and V2.

Columns:
- identity: scenario, k, checkup, ck_date, Δ, model, branch;
- prediction: Q_pred, SOH_pred, proxy P_k, err_Ah, err_pp;
- **error decomposition** (the core of this table): anchor_used (index and t_end), Q_fc_anchor_used, q_anchor_term (the anchor term the model used, including ε0 and `EPS_EXTRA_AH` where applied), increment_pred (β·x, `after[-1] − after[0]` or the √t term), **increment_obs = Q_fc,k − Q_fc_anchor_used**, **inc_resid = increment_pred − increment_obs**, offset_part = err_Ah − inc_resid. Assert that offset_part depends only on (branch family, Δ) and on whether the anchor was the 45 °C anchor 0, to 1e-9 Ah; record the assertion in the report. inc_resid is free of ε0 and Δ, so it is the primary case residual;
- branch internals: β and its shrinkage weight s, x, E_cur/E_prev, d_cur/d_prev, r (45 °C rate), n_45 steps per month, gap days from last deep program to CK, √t coefficient a and effective days (T_main);
- flags: `uses_first_post_anchor_program` (true when the increment uses `after[0]`), `anchor_setpoint`, `anchor_is_ck0_45C`;
- context: days from anchor to CK, effective 45 °C-equivalent days, cumulative fade at the anchor (100.41 − Q_fc_anchor_used − ε0), throughput since anchor (integrated `current_A`, discharge Ah), share of time at 45 °C since anchor.

Also write `outputs/table_cases_wide.csv` (one row per scenario × k, SUB only, Δ = 0.4).

- **Done:** both tables, the decomposition assertion, a per-branch summary (count, mean and median signed inc_resid, MAE) in `wp1/REPORT.md` (summary only, no slicing yet), plus the common criteria.

### WP2 — Event table (cap 2.5 h)

`outputs/table_events.csv`, one row per deep program (41) × cell (cell1..cell4 plus `pack_mean`), so about 205 rows. Start from `events_merged.csv` and add:
- identity: event_id, t_cv_end, segment, setpoint, month m (anchor index it follows), program index after anchor (1, 2, …), `is_first_after_anchor`, days since anchor, days since checkup;
- operating condition: measured T at CV end and at 15/25/35/45 Ah depth, T_measured − setpoint, days since the last 25↔45 °C switch, rest before the deep program, start-of-charge rest voltage (pack and cell), CV Ah, CV hours, CV end current, throughput since anchor and since campaign start (integrated `current_A`), `has_recording_gap` (any Δt > 600 s inside the program);
- step: depth for all 6 variants (main, band_narrow, dvdq_peak, ir_corrected, windows_minus3, windows_plus3), per-cell depth for `main` (use the per-cell `locs` before averaging), step sharpness per cell (dV/dQ peak height and FWHM on a 0.25 Ah grid with 2 Ah smoothing), upper/lower plateau medians;
- cell state: per-cell pulse resistance (from `events_merged`), cell voltage spread (max − min) at CV end and at maximum depth, rank of each cell by voltage at maximum depth;
- **use flags**: which SUB real-scenario predictions used this event and how (`end45_E_cur`, `end45_E_prev`, `rate_fit`, `after_first`, `after_last`), from WP1's internals.

**Residual definitions** (computed here, frozen in WP5 before slicing):
- **R_seg** (within-segment): depth minus a leave-one-out Theil–Sen line fitted to the other events of the same segment and cell; NaN if fewer than 3 others;
- **R_anc** (anchor tracking): depth minus [a_setpoint,cell + b · Q_interp(t)], where Q_interp is the linear interpolation in time of Q_fc between the anchors that bracket the event, with b = 1 fixed (pure LLI) and a_setpoint,cell fitted leaving the event's month out. Also report the b-free fit (b and its block-bootstrap CI) as a descriptive number;
- **R_cell** (cell dispersion): per-cell depth minus the pack median depth of the same event.

- **Done:** the table, a column-level check that 41 events and 6 variants match `events_merged.csv` exactly where columns overlap, plus the common criteria.

### WP3 — Anchor table (cap 1.5 h)

`outputs/table_anchors.csv`, one row per anchor 0..7. Start from round 7 `anchor_state_table.csv` and add:
- Q_fc as is, and **Q_fc at a common CV cut-off**: the charge integrated until the current first falls below I_cut = the largest end current among the 8 anchors (and, as a second column, 6.0 A); the difference from Q_fc;
- CV Ah and CV hours; measured temperature mean during the charge; per-cell start rest voltages; start-state residual charge r_upper/r_half (from 3a);
- ΔQ_fc to the next anchor, and the same with the common cut-off;
- per-cell charge-direction step → top distance (`_charge_step_to_top` per cell, before averaging) and its spread;
- nearest pulse resistance (mean and per cell) and its change from anchor 0;
- cell voltage spread at the CV end.

- **Done:** the table plus a one-page descriptive summary (no slicing against case errors yet), plus the common criteria.

### WP4 — Daily cycle table (optional, cap 1.5 h)

`outputs/table_cycles.csv`, one row per daily charge/discharge cycle: start/end rest voltages, Ah charged/discharged (integrated), CV reached or not, top-of-charge Ah relative to the last CV end, end-of-rest voltage after 1 h, cell spread at top and bottom, measured temperature. Residual R_cyc = value minus a leave-one-out rolling median (7 cycles, same setpoint). Skip with a recorded reason if the cap is reached; WP5 then drops H10.

### WP5 — Registered slicing and worst-20 % dossier (cap 3 h)

**Register first** (`wp5/protocol.json`): residual definitions; slice variables and bins (fixed edges written in the protocol, e.g. fade 0–3 / 3–6 / > 6 %; days since switch 0–2 / 2–5 / > 5; sharpness terciles fixed from the full event table *without* residuals); hypotheses; statistics; seeds; the worst-set definition (top 20 % by |residual|, ties included).

**Hypotheses** (each states the expected sign and what result counts as "systematic"; registered threshold: |effect| ≥ 0.10 Ah (≈ 0.1 pp) **and** a block-bootstrap 90 % CI excluding 0 **and** the sign holds in ≥ 70 % of month blocks):
- **H1 fallback and the first post-anchor program.** In cases with `uses_first_post_anchor_program`, inc_resid is shifted relative to the other cases by about the first-program offset (0.4–0.8 Ah). Diagnostic-only counterfactual: the increment with `after[0]` replaced by (a) the second program after the anchor, (b) the first program minus its 3c offset. Report the inc_resid of each; do not score as proxy MAE.
- **H2 temperature-switch transient.** R_seg and R_anc depend on days since the last 25↔45 °C switch, separately per setpoint.
- **H3 measured vs set temperature.** R_anc correlates with T_measured − setpoint at 45 Ah depth.
- **H4 fade-dependent bias.** Signed inc_resid (cases) and R_anc (events) trend with cumulative fade. Compare the slope with −0.031 Ah/Ah; if the CI contains it, label the pattern **"indistinguishable from ε drift, invisible to proxies"**.
- **H5 step quality.** |R_seg| is larger in the lowest sharpness tercile; the worst-20 % events are enriched in it (Fisher exact).
- **H6 cell heterogeneity.** R_cell has a persistent per-cell sign (one cell consistently deeper or shallower), and its spread grows with time; the weakest cell by voltage at maximum depth changes over the campaign or not.
- **H7 resistance.** Pulse resistance trends upward; anchor CV Ah and Q_fc − Q_fc(common cut-off) grow with it (anchor table, n = 8, exact permutation). This is the mechanism candidate for ε drift in the next round.
- **H8 extrapolation horizon.** |inc_resid| grows with gap days and with days from anchor to CK, by branch.
- **H9 anchor start state and CV cut-off.** ΔQ_fc month to month, before vs after the common cut-off, and its dependence on r_upper (n = 7). Report how much of the month-to-month scatter of ΔQ_fc the two corrections remove (variance ratio).
- **H10 (needs WP4) daily cycles.** R_cyc of top-of-charge Ah shows the same post-anchor and post-switch pattern as the events.

**Outputs:**
- `wp5/outputs/slice_summary.csv`: per hypothesis × slice × bin: n, n_months, mean, median, block-bootstrap CI, sign count, permutation p, verdict (`systematic` / `not systematic` / `inconclusive`);
- figures in `wp5/figures/`: each residual against each registered slice variable, coloured by setpoint, with month labels; per-branch inc_resid bars for every scenario;
- **worst-20 % dossier** `wp5/dossier/`: for the worst cases (by |inc_resid|, SUB, all scenarios) and the worst events (by |R_anc| and by |R_seg|), one panel each with per-cell voltage vs depth around the step, dV/dQ, current, measured temperature, and the event's slice values; plus `enrichment.csv` comparing the category shares of the worst set with the base rate (Fisher exact per category).

- **Done:** protocol committed before the first slice, all registered outputs, `wp5/REPORT.md` with a verdict per hypothesis, plus the common criteria.

### WP6 — Synthesis (cap 1 h)

`FINAL_REPORT.md` (bilingual, conclusions first):
1. **Failure map.** A ranked table of the systematic patterns: where (branch / condition / value range), size in pp of SOH at the affected checkups, evidence strength, and whether the proxies can see it at all.
2. **Error budget for SUB at Δ = 0.4.** The real-scenario error per checkup, split into inc_resid and offset_part, and, where H1–H9 apply, the share that each systematic pattern explains (descriptive).
3. **Next-round feature list.** For each `systematic` or strong `inconclusive` pattern: the physical mechanism, the feature or preprocessing step that targets it (for example anchor start-state correction from the CK0 tail, common CV cut-off, temperature-corrected step depth, sharpness weights, resistance-linked ε), the table columns that already hold it, and the registered test that a next-round candidate would have to pass (on inc_resid, R_anc or the causal scenarios, never only on the real proxies).
4. **Null results.** Hypotheses that did not hold, stated plainly.

Also write `README.md` (how to rebuild every table: one command per WP) and `DATA_DICTIONARY.md` (every column: table, name, unit, definition, source function or file, causal or diagnostic).

- **Done:** both files and the Global Done list.

---

<a id="zh"></a>

# 第 8 轮：误差分析长表 — 执行说明

> **语言：** [English](#en) · 中文

2026-10-17 编写。本文件自成一体。英文为执行文本，中文为供阅读的译文；两者不一致时以英文为准。

**本轮目标。** 建立一套口径一致的长表（预测案例、事件、锚点，可选日循环），再按样本类型、工况和数值区间切分残差，找出提交模型在哪里系统性失败。本轮产出的是**表格、图和为下一轮排好序的假设**。不构建候选模型，不调任何参数，也不改动提交。

工作分为 **WP0–WP6**，每个都有自己的 *Done* 清单，可作为单独的 `/goal` 运行。WP0 必须先做。WP1、WP2、WP3 相互独立；WP4 可选；WP5 依赖 WP1–WP3；WP6 最后做。

## 0. 工作方式（所有工作包）

- **无人值守。** 不要停下来提问。遇到未决事项时，选择满足本文所有规则的最保守方案，记入 `notes/DECISIONS.md`，然后继续。
- **重启。** 每一步完成后更新 `notes/STATUS.md`：WP、已完成、下一步、最近一次提交。重启时先读 `notes/STATUS.md` 和 `notes/DECISIONS.md` 再接着做。已完成的 WP 或步骤不要重做。
- **诚实优先。** "除噪声外没有系统性模式"也是有效结论。本轮所有统计量都是描述性的。
- **单个 WP 的 Done** 指下列通用条件加上该 WP 自己的清单：
  1. 对 WP5：注册协议（`wp5/protocol.json` + `wp5/protocol.sha256`）在计算任何残差切片**之前**已提交；
  2. 有双语的 `wpN/REPORT.md`，结论在前；
  3. `notes/STATUS.md` 把该 WP 标为 done、capped、skipped 或 exited，并附一行结果；
  4. 所有提交都已推送到 `origin exp/phase2-r8-error-table-20261017`，`git status` 中没有未提交的研究文件。
- **全局 Done：** WP0–WP6 各自 done、capped、skipped，或按注册规则 exited；`FINAL_REPORT.md` 和 `README.md` 存在（双语，结论在前）；`DATA_DICTIONARY.md` 覆盖每张表的每一列；通用条件 3–4 成立。

## 1. 工作区、隔离与 git

- **Worktree 和分支（在 WP0 中按需创建，可重复执行）。**
  - 基点：第 7 轮在 `exp/phase2-r7-lit-checks-20261016` 上的最终提交（编写时为 `c9658ad`；以分支末端为准并记录哈希）。其中已包含第 3 轮 harness、V2/V3、第 6 轮的 sources 和第 7 轮的 `src/tsqrt.py`。
  - 创建：`git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1017_r8_err -b exp/phase2-r8-error-table-20261017 <base>`。若已存在，确认其历史包含 `<base>` 后复用。
  - 只在 `/Users/shane/Desktop/Arena_1017_r8_err` 中工作。研究目录为 `research/phase2_r8_error_table_20261017/`。
- **可复用的代码（基点分支上已有）：**
  - 第 3 轮 harness `research/phase2_round3_models_20261014/src/harness.py`（场景 real、PG1、PG2、PC5、PC10；`cut_op`、`scenario_op`、`proxies`、`run`）；
  - V2 `research/phase2_v2_phase_matched_20261013/src/v2.py`，事件提取 `research/phase2_anchor_step_20261013/src/events.py`，V3 `research/phase2_r7_lit_checks_20261016/sources/v3/v3.py`；
  - 第 7 轮 `research/phase2_r7_lit_checks_20261016/src/`（含设计 `T_main` 的 `tsqrt.py`、`common6.py`、`runner5c.py`、CS/CSE 冷启动场景）；
  - 已有的诊断表（以它们为起点，只补缺的部分）：
    - `research/phase2_r6_robust_20261016/sources/rebound_diagnosis/outputs/events_merged.csv`（41 个深放电程序：充电 Ah、CV Ah/时长、截止电流、充电前静置、各 cell 脉冲内阻、15/25/35/45 Ah 深度处的 V/I/T、6 种 step 变体的深度、距 checkup 天数）；
    - `research/phase2_r7_lit_checks_20261016/wp0/outputs/wp0_3a_start_state.csv`、`wp0_3c_path_offsets.csv`、`wp0_branch_by_case.csv`；
    - `research/phase2_r7_lit_checks_20261016/wp1/outputs/anchor_state_table.csv`。
  - 需要修改的文件先复制到本研究目录，只改副本。
- **本 worktree 之外的只读来源。** **提交分支** `exp/phase2-anchor-step-20261013`，提交 `5cd305c`，位于 `/Users/shane/Desktop/Arena_1013_model`。只能用 `git -C … show` / `git -C … archive`；不要 `cd` 进去，也不要写入。那里的 `TechArena_Challenge2_Team_Package/my_model/model_template.py` 就是**提交模型 SUB = T_main**（V2 + 温度加权 √t 缺口分支）。把它解压到 `cache/submitted_package/`。同时读取该提交中 `research/phase2_v3_20261015/package_submission.py` 的 `EXPECTED_SOH`。在 `sources/SOURCES.md` 中记录所有复制的文件及其 SHA256。
- **并发保护。** 开始时和每次提交前运行 `git log --oneline -5`，与自己上一次的提交对比。发现意外提交时，停止编辑共享文件，记录下来，此后只按明确路径 add。不要 `git add -A` / `.`，不要裸 `git stash`，不要改写他人的工作。提交 worktree 中未跟踪的 `research/phase2_round3_models_20261014/` 残留不属于你，忽略即可。
- **提交。** 先提交本说明：从 `/Users/shane/Desktop/Arena_1013_model/research/phase2_r8_error_table_20261017/EXECUTION_PROMPT.md` 复制到相同的相对路径。每一步结束时提交，然后 `git push -u origin exp/phase2-r8-error-table-20261017`。不要推送到别处，不要 force。每条提交信息以 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` 结尾。
- **不得修改：** 任何 `TechArena_Challenge2_Team_Package/`、任何更早的研究目录、本 worktree 之外的任何文件。
- **语言与字节码。** Markdown 先英文后中文，版式同本文件。代码注释只用英文。用 `python3 -B` 运行 Python。不需要下载任何东西。

## 2. 背景

**任务。** 估计 4 × 102 Ah LFP 串联 pack 在 CK0..CK7 的 SOH（C/20 容量 / 102 Ah）。只公开了 CK0 = 100.41 Ah。框架在 checkup 日期截断数据（`load_dataset(data, until=CK_k)`）。

**Proxy**（都已看过，所以所有 real 场景的数字都属于 exposed-exploratory）：P_k = Q_fc,k + ε0 + Δ。其中 Q_fc,k 是 CK_k 之后从空到满的锚点充电量，ε0 = 100.41 − Q_fc,0，Δ ∈ {0, 0.4, 0.8}。proxy MAE 相差不到 0.25 pp 视为无法分辨。

**SUB = T_main**（提交 `5cd305c`）。proxy MAE Δ0/0.4/0.8 = 0.197/0.126/0.146 pp，MAX 0.609/0.228/0.228；pseudo 0.144；冷启动 0.170；单月因果缺口案例 0.105。real 场景的分支：CK1 和 CK3 走 `fallback`（锚点 + `after[-1] − after[0]`，β = 1）；CK2 走 `sqrt_gap`；CK4–CK7 走 `phase`（相位匹配的月末 45 °C step 差 × β）。

**已知效应（不要重新检验；作为列记录下来，让切片时可以控制它们）：**
- 每次锚点充电后的第一个深放电程序偏深 0.41–0.56 Ah（第 0 个月在 45 °C 下为 0.83 Ah）；去掉这些程序会与 proxy 矛盾（第 6 轮 3c）；overhang 解释不成立（第 7 轮 WP1）；
- 每次 25→45 °C 切换时 step 深度跳升约 +0.18 Ah（V2 研究）；
- 锚点起始状态最多相差 1.29 Ah（由 CK0 C/20 尾段给出的上界，第 6 轮 3a）；
- 约 −0.031 Ah/Ah 的 ε 漂移是可能的，但符号不稳健（第 7 轮 WP3）。这种量级的残差趋势**对 proxy 不可见**，必须如此标注，不能去"修正"；
- 运行计数器把 20 A 脉冲记为充电；应改为积分 `current_A`。

## 3. 通用规则

1. **先注册切片，再看结果。** 所有切片变量、分箱、残差定义和假设 H1–H10（WP5）都要在对残差做任何分组、作图或排序之前冻结到 `wp5/protocol.json`。在注册之前可以建表（WP1–WP4），但不能按切片查看残差。额外的切片只能标为 `exploratory-unregistered`，单独报告。
2. **不改模型。** 不构建、不调参、不接入任何候选。WP5 中的反事实重算（例如"用锚点后第二个程序计算 fallback 增量"）只是诊断，标为 `diagnostic-only`，不作为 proxy MAE 的改进来比较。
3. **小样本与相关性。** real 案例 7 个、因果案例约 48 个、事件 41 个（按 cell 拆为 164 个）、锚点 8 个。同一个月内的事件并不独立。每个关联都要报告：效应量、符号计数、**以月为块重采样**的 bootstrap 90 % 置信区间，以及**在同一设定温度内、跨月块置换**的置换检验 p 值（n ≤ 9 时用精确置换）。不能只给显著性结论。
4. **单位。** 残差同时以 Ah 和 pp 存储（pp = 100 · Ah / 102）。符号约定统一为：残差 = 预测 − 参照。
5. **因果性。** 事件表和锚点表是基于全部运行数据的诊断表。案例表的每个字段都必须来自该场景截断后的数据，与框架交给模型的数据完全一致。
6. **确定性。** 缓存键包含所有参数；重跑结果必须逐字节一致。随机种子固定在协议中。

## 4. 工作包

### WP0 — 准备与基线复现（上限 0.5 h）

- 创建 worktree、`notes/STATUS.md`、`notes/DECISIONS.md`、`.gitignore`（`cache/`）和 `sources/SOURCES.md`。
- 用第 7 轮的研究实现复现 SUB = T_main：上面列出的 real 场景指标（误差 0.001 pp 以内）、pseudo 0.144 和冷启动 0.170。
- 用框架的截断方式在全量数据上运行从 `5cd305c` 提取的提交类，逐个 checkup 与研究实现对比（误差 0.0005 pp 以内），并与 `EXPECTED_SOH` 对比。
- 在 T_main 下为所有场景（real、PG1、PG2、PC5、PC10、CS、CSE）重建 `wp0_branch_by_case.csv`。
- **Done：** 所有复现都通过（若 SUB 复现失败，停止整轮并记录原因），加上通用条件。`wp0/REPORT.md` 简短即可。

### WP1 — 案例表（上限 2 h）

`outputs/table_cases.csv`，每行对应一个（scenario, k, Δ, model）。模型包括 SUB（T_main）、V2+√t 和 V2。

列：
- 标识：scenario、k、checkup、ck_date、Δ、model、branch；
- 预测：Q_pred、SOH_pred、proxy P_k、err_Ah、err_pp；
- **误差分解**（这张表的核心）：anchor_used（索引和 t_end）、Q_fc_anchor_used、q_anchor_term（模型实际使用的锚点项，在适用时包括 ε0 和 `EPS_EXTRA_AH`）、increment_pred（β·x、`after[-1] − after[0]` 或 √t 项）、**increment_obs = Q_fc,k − Q_fc_anchor_used**、**inc_resid = increment_pred − increment_obs**、offset_part = err_Ah − inc_resid。断言 offset_part 只取决于（分支族, Δ）以及锚点是否为 45 °C 的锚点 0，误差在 1e-9 Ah 以内；把断言结果写进报告。inc_resid 不含 ε0 和 Δ，因此是首要的案例残差；
- 分支内部量：β 及其收缩权重 s、x、E_cur/E_prev、d_cur/d_prev、r（45 °C 速率）、每月的 45 °C step 数 n_45、最后一个深放电程序到 CK 的缺口天数、√t 系数 a 和有效天数（T_main）；
- 标志：`uses_first_post_anchor_program`（增量用到 `after[0]` 时为 true）、`anchor_setpoint`、`anchor_is_ck0_45C`；
- 背景量：锚点到 CK 的天数、45 °C 等效天数、锚点处的累计衰减（100.41 − Q_fc_anchor_used − ε0）、锚点以来的吞吐量（积分 `current_A` 得到的放电 Ah）、锚点以来处于 45 °C 的时间占比。

同时输出 `outputs/table_cases_wide.csv`（每个 scenario × k 一行，只含 SUB，Δ = 0.4）。

- **Done：** 两张表、分解断言，以及 `wp1/REPORT.md` 中按分支汇总的结果（数量、带符号 inc_resid 的均值和中位数、MAE；只汇总，暂不切片），加上通用条件。

### WP2 — 事件表（上限 2.5 h）

`outputs/table_events.csv`，每行对应一个深放电程序（41 个）× cell（cell1..cell4 加 `pack_mean`），共约 205 行。以 `events_merged.csv` 为起点，补充：
- 标识：event_id、t_cv_end、segment、setpoint、所属月份 m（跟在哪个锚点之后）、锚点后的程序序号（1, 2, …）、`is_first_after_anchor`、距锚点天数、距 checkup 天数；
- 工况：CV 结束时以及 15/25/35/45 Ah 深度处的实测温度、实测温度 − 设定温度、距上次 25↔45 °C 切换的天数、深放电程序前的静置时长、充电起点静置电压（pack 和各 cell）、CV Ah、CV 时长、CV 截止电流、锚点以来和整个试验以来的吞吐量（积分 `current_A`）、`has_recording_gap`（程序内是否有 Δt > 600 s）；
- step：全部 6 种变体的深度（main、band_narrow、dvdq_peak、ir_corrected、windows_minus3、windows_plus3）、`main` 变体的各 cell 深度（取平均之前的各 cell `locs`）、各 cell 的 step 锐度（在 0.25 Ah 网格、2 Ah 平滑下的 dV/dQ 峰高和半高宽）、上下平台的中位电压；
- cell 状态：各 cell 脉冲内阻（取自 `events_merged`）、CV 结束时和最大深度处的 cell 电压极差（max − min）、最大深度处各 cell 按电压的排名；
- **使用标志**：SUB 在 real 场景中的哪些预测用到了这个事件、怎么用的（`end45_E_cur`、`end45_E_prev`、`rate_fit`、`after_first`、`after_last`），取自 WP1 的内部量。

**残差定义**（在这里计算，在 WP5 切片前冻结）：
- **R_seg**（段内）：深度减去用同一 segment、同一 cell 的其他事件拟合的留一 Theil–Sen 直线；其他事件不足 3 个时为 NaN；
- **R_anc**（锚点跟踪）：深度减去 [a_setpoint,cell + b · Q_interp(t)]。Q_interp 是事件前后两个锚点的 Q_fc 按时间线性插值的结果；b = 1 固定（纯 LLI）；a_setpoint,cell 在去掉该事件所在月份后拟合。另外把 b 自由拟合的结果（b 及其块 bootstrap 置信区间）作为描述性数字报告；
- **R_cell**（cell 离散）：各 cell 的深度减去同一事件的 pack 中位深度。

- **Done：** 事件表，以及列级检查：41 个事件和 6 种变体在与 `events_merged.csv` 重叠的列上完全一致，加上通用条件。

### WP3 — 锚点表（上限 1.5 h）

`outputs/table_anchors.csv`，每个锚点 0..7 一行。以第 7 轮的 `anchor_state_table.csv` 为起点，补充：
- 原始 Q_fc，以及**统一 CV 截止下的 Q_fc**：积分到电流第一次低于 I_cut 为止，I_cut 取 8 个锚点中最大的截止电流（另设一列取 6.0 A）；以及它与 Q_fc 的差；
- CV Ah 和 CV 时长；充电期间的实测平均温度；各 cell 起始静置电压；起始状态残余电量 r_upper/r_half（取自 3a）；
- 到下一个锚点的 ΔQ_fc，以及统一截止下的同一量；
- 各 cell 充电方向 step → 顶部的距离（取平均之前对每个 cell 调用 `_charge_step_to_top`）及其极差；
- 最近一次脉冲的内阻（均值和各 cell）及其相对锚点 0 的变化；
- CV 结束时的 cell 电压极差。

- **Done：** 锚点表，加一页描述性总结（暂不对照案例误差做切片），加上通用条件。

### WP4 — 日循环表（可选，上限 1.5 h）

`outputs/table_cycles.csv`，每个日充放电循环一行：起止静置电压、积分得到的充/放电 Ah、是否到达 CV、相对上一次 CV 结束点的充电顶部 Ah、静置 1 h 后的电压、顶部和底部的 cell 极差、实测温度。残差 R_cyc = 该值减去留一滚动中位数（7 个循环，同一设定温度）。若达到上限，记录原因后跳过；此时 WP5 去掉 H10。

### WP5 — 注册切片与最差 20 % 档案（上限 3 h）

**先注册**（`wp5/protocol.json`）：残差定义；切片变量和分箱（固定边界写入协议，例如衰减 0–3 / 3–6 / > 6 %；距切换天数 0–2 / 2–5 / > 5；锐度三分位点由完整事件表确定，确定时*不看*残差）；假设；统计方法；随机种子；最差集合的定义（按 |残差| 取前 20 %，含并列）。

**假设**（每条都写明预期符号，以及什么结果算"系统性"。注册阈值：|效应| ≥ 0.10 Ah（约 0.1 pp），**且**块 bootstrap 90 % 置信区间不含 0，**且**符号在 ≥ 70 % 的月块中成立）：
- **H1 fallback 与锚点后第一个程序。** 在 `uses_first_post_anchor_program` 为真的案例中，inc_resid 相对其他案例偏移，幅度约为第一个程序的偏移量（0.4–0.8 Ah）。仅作诊断的反事实：把 `after[0]` 换成 (a) 锚点后第二个程序，(b) 第一个程序减去其 3c 偏移量，分别报告 inc_resid；不按 proxy MAE 评分。
- **H2 温度切换瞬态。** R_seg 和 R_anc 随距上次 25↔45 °C 切换的天数变化，按设定温度分别看。
- **H3 实测温度与设定温度。** R_anc 与 45 Ah 深度处的（实测温度 − 设定温度）相关。
- **H4 随衰减变化的偏差。** 带符号的 inc_resid（案例）和 R_anc（事件）随累计衰减呈趋势。把斜率与 −0.031 Ah/Ah 比较；若置信区间包含该值，标为**"与 ε 漂移无法区分，对 proxy 不可见"**。
- **H5 step 质量。** 锐度最低的三分位中 |R_seg| 更大；最差 20 % 的事件在该分位中富集（Fisher 精确检验）。
- **H6 cell 异质性。** R_cell 在各 cell 上有持续的符号（某个 cell 一直偏深或偏浅），且其离散随时间增大；看最大深度处电压最低的 cell 在试验过程中是否变化。
- **H7 内阻。** 脉冲内阻呈上升趋势；锚点的 CV Ah 以及 Q_fc − Q_fc(统一截止) 随之增大（锚点表，n = 8，精确置换）。这是下一轮 ε 漂移机理的候选。
- **H8 外推跨度。** |inc_resid| 随缺口天数和锚点到 CK 的天数增大，按分支分别看。
- **H9 锚点起始状态与 CV 截止。** 统一截止前后的月间 ΔQ_fc，以及它对 r_upper 的依赖（n = 7）。报告这两项修正能消除多少 ΔQ_fc 的月间离散（方差比）。
- **H10（需要 WP4）日循环。** 充电顶部 Ah 的 R_cyc 呈现与事件相同的锚点后、切换后模式。

**输出：**
- `wp5/outputs/slice_summary.csv`：每个假设 × 切片 × 分箱：n、n_months、均值、中位数、块 bootstrap 置信区间、符号计数、置换 p 值、结论（`systematic` / `not systematic` / `inconclusive`）；
- `wp5/figures/` 中的图：每种残差对每个注册切片变量的散点，按设定温度着色并标注月份；所有场景下按分支的 inc_resid 柱状图；
- **最差 20 % 档案** `wp5/dossier/`：对最差的案例（按 |inc_resid|，SUB，所有场景）和最差的事件（按 |R_anc| 和 |R_seg|），每个各出一张面板：step 附近各 cell 的电压–深度曲线、dV/dQ、电流、实测温度，以及该事件的切片取值。另附 `enrichment.csv`，把最差集合中各类别的占比与基准比例对比（每个类别做 Fisher 精确检验）。

- **Done：** 协议在第一次切片前已提交，所有注册的输出齐全，`wp5/REPORT.md` 对每条假设给出结论，加上通用条件。

### WP6 — 综合（上限 1 h）

`FINAL_REPORT.md`（双语，结论在前）：
1. **失败地图。** 把系统性模式排成表：发生在哪里（分支 / 工况 / 数值区间）、在受影响 checkup 上折合多少 pp SOH、证据强度，以及 proxy 是否看得见它。
2. **SUB 在 Δ = 0.4 下的误差预算。** real 场景每个 checkup 的误差拆成 inc_resid 和 offset_part；在 H1–H9 适用之处，给出各系统性模式解释的份额（描述性）。
3. **下一轮特征清单。** 对每个 `systematic` 或证据较强的 `inconclusive` 模式，写出：物理机理；针对它的特征或预处理步骤（例如基于 CK0 尾段的锚点起始状态修正、统一 CV 截止、温度校正的 step 深度、锐度权重、与内阻挂钩的 ε）；表中已有的对应列；下一轮候选模型必须通过的注册检验（基于 inc_resid、R_anc 或因果场景，不能只看 real proxy）。
4. **零结果。** 没有成立的假设，直接写明。

另外写 `README.md`（如何重建每张表：每个 WP 一条命令）和 `DATA_DICTIONARY.md`（每一列：所在表、列名、单位、定义、来源函数或文件、因果还是诊断）。

- **Done：** 两份文件齐全，且满足全局 Done 清单。
