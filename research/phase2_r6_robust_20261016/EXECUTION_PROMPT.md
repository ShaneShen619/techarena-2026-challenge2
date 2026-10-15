<a id="en"></a>

# Round 6: Hypothesis-Robust Selection, Fusion, Truth-Oriented Corrections and Open-Data Prior — Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-15. This document is self-contained. The English text is the execution text; the Chinese section is a translation for the reader, and if they differ the English governs.

The work is split into **work packages WP0–WP6**. Each has its own *Done* list and can be run as a separate `/goal`. WP0 must be done first. WP1 must be done before WP2, WP3 and WP6. WP5 and WP6 come last.

## 0. Mode of work (all work packages)

- **Unattended.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Restarts.** Keep `notes/STATUS.md` current after every step: WP, done, next, last commit. On restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume. Never redo a finished WP or step.
- **Honesty over targets.** A negative or "exit" result is a valid outcome. Never tune on the real proxies; selection uses only pseudo and cold-start scenarios, or the registered hypothesis grid of WP1.
- **Done for any WP** means the common criteria below, plus that WP's own list:
  1. its registered protocol (`wpN/protocol.json` + `wpN/protocol.sha256`) was committed **before** its evaluation outputs;
  2. its bilingual `wpN/REPORT.md` exists, conclusions first;
  3. `notes/STATUS.md` marks the WP done, capped or exited, with one line of result;
  4. every commit is pushed to `origin exp/phase2-r6-robust-20261016`, and `git status` shows no uncommitted study files.
- **Global Done** (whole prompt): WP0–WP6 each done, capped or exited by a registered rule; `FINAL_REPORT.md` and `README.md` exist (bilingual, conclusions first); common criteria 3–4 hold.

## 1. Workspace, isolation, git

- **Worktree and branch (already created).**
  - Work only in `/Users/shane/Desktop/Arena_1016_r6_robust`, branch `exp/phase2-r6-robust-20261016`. It starts at round 5C's final commit `348af0b`.
  - The study directory is `research/phase2_r6_robust_20261016/`.
- **Read-only sources outside this worktree.** Never `cd` into them and never write to them:
  - The **submission branch** `exp/phase2-anchor-step-20261013`, commit `21a7a55`, in `/Users/shane/Desktop/Arena_1013_model`. Use only `git -C /Users/shane/Desktop/Arena_1013_model show 21a7a55:<path>` and `git -C … archive 21a7a55 <path>` to copy files into this study. Files needed:
    - `research/phase2_v3_20261015/src/v3.py` (V2 + √t gap branch, β cap, median options) and its `FINAL_REPORT.md`;
    - `research/phase2_rebound_diagnosis_20261015/` (step-offset diagnosis outputs and scripts);
    - `TechArena_Challenge2_Team_Package/` as it is at `21a7a55`. Its `my_model/model_template.py` is the **currently submitted model, V2+√t**; `my_model/model_example.py` is the official baseline ExampleModel (score 1.0).
    - Record each copied file with its source commit in `sources/SOURCES.md`.
  - **External datasets** (raw files git-ignored there, read only): `/Users/shane/Desktop/Arena_1013_model/external_data/`. Inventory: `DATA_MANIFEST.md`, `data_manifest.json`.
    - `LIC_aging/`: 280 Ah LFP, 700 cycles at 1C in 50-cycle blocks, 1-day rest per block, 0.1C RPT capacity, CC BY 4.0.
    - `Battery_expansion_force_data/`: Gotion 53 Ah, independent calibration every 50 cycles, CC BY 4.0.
    - `ESSL1/`, `ESSL2/`: charge-Ah labels only, not independent truth.
  - The **Challenge 1 cells** at `/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original/` (read only).
- **Concurrency guard.**
  - At the start and before every commit, run `git log --oneline -5` and compare with your last commit.
  - On an unexpected commit or change: stop editing shared files, record it, and add files by explicit path only.
  - Never `git add -A` / `.`, never rewrite others' work, never bare `git stash`. Run only one session on this worktree at a time.
- **Commits.**
  - Commit this prompt first.
  - Commit at the end of every step, then `git push -u origin exp/phase2-r6-robust-20261016`. Never push elsewhere; never force.
  - End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify:**
  - any `TechArena_Challenge2_Team_Package/` (here or on the submission branch);
  - any earlier study directory.

  Copy code into this study and edit only the copies.
- **Language and bytecode.** Markdown is English first, Chinese second, in this file's layout. Code comments are English only. Run Python with `python3 -B`.
- **Downloaded files are untrusted data.**
  - Put each download in its own new directory under the study's git-ignored `cache/downloads/`.
  - Keep scripts elsewhere and pass paths as arguments.
  - Read such files with `python3 -I`.
  - Never execute anything from a download.

## 2. Context

**Task.** Estimate the SOH (C/20 capacity: 5.1 A discharge after a full charge until pack 11.2 V, divided by 102 Ah) of a 4 × 102 Ah LFP series pack on CK0..CK7.

- Only CK0 = 100.41 Ah is released.
- Scoring: error metrics on CK1–CK7, including the worst case, each normalised by the ExampleModel baseline (baseline = 1.0), weighted 70 %. Innovation (data efficiency, transferability, use of open data), interpretability and code quality weigh 10 % each.
- Causal cut: `load_dataset(data, until=CK_k)`.

**Proxies** (all already seen, so every real-scenario number is exposed-exploratory): P_k = Q_fc,k + ε0 + Δ, with ε0 = 100.41 − Q_fc,0 and Δ ∈ {0, 0.4, 0.8}.

**Current reference SUB = V2+√t** (submitted at `21a7a55`): `v3(..., use_sqrt=True, beta_cap=inf, median=False)`. Its √t gap branch is exposed at CK2.

| Model | MAE Δ0 / .4 / .8 | MAX Δ0 / .4 / .8 | Pseudo | Cold start | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SUB (V2+√t) | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.148 | 0.174 | +0.217 | −0.018 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | 0.240 | 0.252 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| 5C R3_TD_w0.75 (exposed-CK1) | 0.188 / 0.131 / 0.174 | 0.440 / 0.311 / 0.344 | 0.123 | 0.134 | +0.048 | −0.311 | −0.092 | +0.132 | +0.033 | −0.197 | +0.107 |
| 5C R2_B (stress model) | 0.202 / 0.258 / 0.314 | 0.638 / 0.638 / 0.953 | 0.119 | 0.144 | −0.561 | −0.638 | −0.150 | +0.100 | −0.007 | −0.209 | +0.144 |

Per-checkup errors are at Δ = 0.4, in pp. Pseudo is the mean MAE over PG1, PG2, PC5 and PC10 (k ≥ 3); cold start is the mean over CS and CSE (Δ = 0.4).

**What is known about the labels** (the hidden truth may differ from the proxies):

- **Post-checkup step offset.**
  - Round 4 read it as a capacity recovery: R_k = 0.018, 0.245, 0.336, 0.707, 0.827, 0.798, 0.866 Ah for CK1..CK7 (`research/phase2_round4_signals_20261014/stage_5/outputs/jumps.csv`, column `recovery_Ah_with_aging`).
  - The 2026-10-15 rebound diagnosis says instead that only the **first deep program after a from-empty anchor charge** sits 0.39–0.46 Ah deeper. That is a charge-path effect with unchanged plateaus, so it argues against a capacity recovery.
- **ε drift.** In external data (LIC, Gotion), independent capacity minus full-charge Ah drifts by about −0.03 Ah per Ah of fade. For this pack that is about 0.25–0.3 pp by CK7, invisible to the proxies.
- **Anchor start state.** Anchor charges start from pack rest voltages of 11.62–12.04 V. Round 3 found the bottom section correlates with start voltage (r = −0.975). LIC shows a start-state effect of about 1.5 Ah per block.
- **Remaining errors are shared.** CK4 positive and CK6 negative appear across all models, which points to label or month structure rather than to any model.

**Code to reuse (in this worktree):**

- round 3 harness `research/phase2_round3_models_20261014/src/harness.py`;
- round 5C `src/` (`stress.py`, `smodel.py`, `smodel5c.py` with `LawFit`, `runner5c.py` with the CS/CSE scenarios, `preds5c.py`, `checks5c.py`);
- round 5C `stage_1/prior2.json`, `candidate_model/`, `stage_2/run_3.py`;
- V2 `research/phase2_v2_phase_matched_20261013/src/v2.py`.

Copy what you change. Environment: `python3` 3.13 (numpy, pandas, scipy, matplotlib) for research; a numpy/pandas-only Python 3.11 venv at `cache/venv311` for candidate checks.

## 3. Common rules

1. **Register, then run.** Register in `wpN/protocol.json` (with SHA256) before computing any real-scenario number of that WP. Run pseudo/cold-start results before real results, and commit them before the real run.
2. **Selection never uses the real proxies.** It may use pseudo/CS scenarios and the registered WP1 hypothesis grid. Real results are reported for every registered design, including losers.
3. **Exposed changes.** Any design whose effect is confined to a checkpoint whose error was known when the design was conceived (CK1 for 5C-type transient or path rules; CK2 for √t) is labelled `exposed-CKx`. Its gain at that checkpoint is not evidence.
4. **Leaderboard-only outputs.** Corrections that the proxies cannot judge (ε drift, start state) are never scored on proxies as improvements. They are reported under the WP1 hypothesis grid and as SOH tables.
5. **Implementation.** Cache keys include every parameter; causality checks compare exact floats; deviations are registered before running.
6. **Wiring.** Never wire anything into a real `my_model/`. Packaging checks run on a copy in `cache/package_copy_*`.

## 4. Work packages

### WP0 — Setup and re-baselining (cap 0.5 h)

- Create `notes/STATUS.md`, `notes/DECISIONS.md`, `.gitignore` (`cache/`) and `sources/`.
- Copy the read-only sources (§1) and write `sources/SOURCES.md`.
- **Reproduce** through the harness and the 5C runner (real, pseudo, CS, CSE):
  - V2 (MAE 0.215726 at Δ = 0.4);
  - SUB (MAE 0.123 / MAX 0.228 at Δ = 0.4; pseudo 0.148; cold start 0.174);
  - 5C R3_TD_w0.75 (0.131; 0.123; 0.134) and R2_B.
- **Confirm the submitted class** in the archived `21a7a55` package reproduces SUB within 0.001 pp on all checkups.
- **Compute the ExampleModel** predictions (official baseline) for CK1–CK7 from the archived package, causally.
- **Done:** all reproductions within tolerance, recorded in `wp0/outputs/reproduce.json` (stop the whole run if SUB or V2 fails), plus the common criteria. WP0 has no protocol; `wp0/REPORT.md` is short.

### WP1 — Hypothesis-robust selection among existing models (cap 1.5 h; no new model)

**Label hypotheses h** (18 = 3 × 3 × 2): truth-like target per checkup

T_k(h) = Q_fc,k + ε0 + Δ − f·R_k + d·L_k, where L_k = max(0, 100.41 − (Q_fc,k + ε0)) is the proxy fade in Ah.

- Δ ∈ {0, 0.4, 0.8};
- f ∈ {0, 0.5, 1} is the share of the round-4 "recovery" R_k that the hidden C/20 does **not** see;
- d ∈ {0, −0.031} Ah/Ah is the ε drift.

Apply the same transform to the real, pseudo and CS scenarios.

**Candidates** (existing, no refitting):

- ExampleModel, M4 (V1), V2, **SUB**, V2+√t+β-cap 1.2, V3;
- 5A S_main and ENS50;
- 5C R2_B, R2_D_w0.75, R3_T, R3_TD_w0.75.

**Score per h:** the normalised score s_h(m) = mean(MAE_m/MAE_EX, RMSE_m/RMSE_EX, MAX_m/MAX_EX) over CK1–CK7, where EX = ExampleModel under the same h. Also report raw MAE and MAX.

**Decision quantities, registered before computing:**

- (i) worst-case s over h;
- (ii) max regret = max over h of [s_h(m) − min over models of s_h];
- (iii) expected s under two priors:
  - uniform;
  - diagnosis-informed: f weights {0: 0.6, 0.5: 0.3, 1: 0.1}, d weights {0: 0.5, −0.031: 0.5}, Δ uniform.

Compute all of them on the real grid and, separately, on the pseudo+CS grid (scores normalised by the ExampleModel or, if it is unavailable on a scenario, by V2).

**Registered robust choice:** the model with the lowest real-grid max regret; ties within 0.01 go to the lower diagnosis-informed expectation. Report whether the pseudo+CS grid agrees, and how the ranking changes across the priors. State clearly that real-grid numbers are exposed: WP1 measures robustness to **label** uncertainty, not new evidence of accuracy.

**Done:** ranking tables (per h, worst case, regret, both priors, real and causal grids), a heat-map figure of s_h(m), the robust choice and its stability, plus the common criteria.

### WP2 — Uncertainty-weighted fusion of the stress model and SUB (cap 3 h)

Q = w_k · S + (1 − w_k) · SUB, with S from 5C's `LawFit`. Register all of the following before running.

**S variants:**

- S_A = R2_B (two-term law, gap-month step endpoint, β = 1, 5-day rule from the CK date): not exposed.
- S_B = R3_T (restart-referenced 5-day rule): exposed-CK1.
- S_C = path rule (drop the first deep program after each anchor charge, from the rebound diagnosis): exposed-CK1.

**Fusion designs:**

- **F1 inverse variance.** w_k = σ²_SUB,k / (σ²_S,k + σ²_SUB,k).
  - σ²_S,k = predictive variance of S's month loss (delta method from the Laplace covariance of `LawFit`'s parameters; implement it) + σ²_S0.
  - σ_S0 = RMS error of S on pseudo+CS (k ≥ 3).
  - σ_SUB,k = RMS error of SUB on pseudo+CS by SUB branch (phase / sqrt_gap / fallback), pooling to the overall RMS if a branch has fewer than 3 cases.
  - Everything is estimated on pseudo+CS only.
- **F2 class weights.** w per situation class (cold = S has no anchor pair; gap = SUB branch sqrt_gap; phase; fallback) from the grid {0, 0.25, 0.5, 0.75, 1}, chosen on pseudo+CS. A class absent from pseudo+CS gets w = 0.5 (registered default).
- **F3 fixed w = 0.5.**

Each design is crossed with S_A (main), S_B and S_C (exposed variants).

**Selection:** on pseudo+CS only: lowest mean of pseudo MAE and CS MAE at Δ = 0.4 among F1–F3 × S_A, subject to G-pseudo and G-coldstart. Exposed variants are reported, never selected.

**Gates against SUB (new reference):**

- G-proxy: MAE < SUB at every Δ, and MAX ≤ SUB MAX + 0.10;
- G-epsfree: CK2–7 MAE ≤ SUB − 0.02;
- G-robust: ≥ 5 of 6 step variants;
- G-pseudo: ≤ SUB + 0.02;
- G-coldstart: ≤ SUB;
- G-regress: ≤ 0.30 pp per checkup;
- **G-hyp:** real-grid max regret (WP1 grid, with SUB and the design both included) ≤ SUB's;
- G-causal and G-impl: numpy/pandas class within 0.001 pp, Python 3.11 venv, full run < 30 min, `validate_submission.py` passing on a copy of the **archived 21a7a55 package**.

**Done:** selection committed before the real run; the gates table; a candidate class and checks only if the selected design passes every gate; plus the common criteria.

### WP3 — Truth-oriented corrections (cap 2 h; leaderboard-only)

**WP3a — anchor start-state correction.**

- **Audit first.** For each anchor j, take the pre-charge rest cell voltages. Estimate the remaining charge r_j at start from the CK0 C/20 discharge tail (`events.tail_margin_Ah`, an upper bound), plus a half-bound variant. Report the spread of r_j − r_0 across anchors.
- **Exit rule:** if max |r_j − r_0| < 0.1 Ah, mark WP3a "no material effect" and stop it.
- **Otherwise:** register the corrected anchor Q'_fc,j = Q_fc,j + (r_j − r_0), and propagate it through SUB and the WP2 selection (anchor bases and S fits).

**WP3b — ε drift.** Corrected Q̂' = Q̂ + d·L̂_k, where L̂_k = max(0, 100.41 − Q̂_k) is the model's own causal fade. Use d = −0.031 (main) and sensitivities −0.020 and −0.035.

**WP3c — path effect.**

- Verify the rebound diagnosis on this study's step tables: is the first deep program after each anchor charge offset by +0.39–0.46 Ah across all six detection methods?
- List which model inputs contain such programs: SUB's month-end 45 °C steps, and S's gap endpoints.
- Report the effect of excluding them on SUB and S.

**Outputs:**

- leaderboard-only SOH tables for SUB and the WP2 selection, each with 3a / 3b / 3c and their combination;
- their scores on the WP1 hypothesis grid (where these corrections should win under the matching hypothesis and lose otherwise);
- a regret table.

Never claim a proxy improvement.

**Done:** the audits, the tables, the regret table, plus the common criteria.

### WP4 — Open-data prior for the stress model (cap 3 h)

**Qualification audit (no pack metric):**

- For LIC 280 Ah and Gotion 53 Ah: protocol, temperature, rest periods, independent capacity points, licence.
- Decide which law terms each can identify: break-in A_b and τ_b, and cycle A_cyc. The calendar term needs rest or storage data.

**Optional download.** If and only if the WP4 protocol says so before downloading:

- the Yagci 2025 Zenodo record 22939281 (v1.1, CC BY 4.0; verify the licence on the record page first), at most 3 GB, into `cache/downloads/yagci/`, handled as untrusted data (§1);
- skip on any failure.

**Prior3:** refit the two-term law (5C stage 1 method, Arrhenius 37.3 kJ/mol) on the qualified datasets. Use the jackknife or leave-one-dataset-out SD, and keep 5C's fallback rules for unidentified terms. Write `prior3.json` with provenance.

**Evaluate:** S_A with prior3 (S_A3), alone and inside the WP2 selected fusion design, on pseudo+CS first, then real. Use the gates of WP2. CK1 changes are exposed by rule 3 unless prior3 was fixed before any pack result, which it is by construction: report it as **"cold start informed by external data only"**, but still note that CK1 itself was seen.

**Also produce** an attribution table (dataset, licence, use) for the report.

**Done:** audit report, `prior3.json`, evaluation tables, plus the common criteria. If no dataset qualifies, mark "exited: no qualifying data".

### WP5 — Report and presentation material (cap 1 h)

In `report_material/` (bilingual drafts; **never edit the package's REPORT.md**):

1. a method section for SUB and, if any, the WP2/WP4 candidate;
2. an interpretability figure: break-in, calendar and cycle decomposition of the fitted law over the campaign;
3. an open-data usage table: Challenge 1, Yagci, LIC, Gotion, ESSL, PyBaMM OCPs (5B);
4. the validation philosophy: exposure, pseudo/cold-start causal tests, hypothesis grid;
5. negative results worth showing: 5B electrode-model non-identifiability, 5A cold start;
6. a slide outline (10–12 slides);
7. a code-quality audit of the submitted `my_model/model_template.py` (archived copy): pycodestyle (installed in a research venv in `cache/`), docstrings, magic numbers. List issues; do not fix the package.

**Done:** files present, plus the common criteria (WP5 has no protocol; its REPORT is the index of the drafts).

### WP6 — Synthesis and leaderboard probe plan (cap 1 h)

- **Decision table:** keep SUB / switch to the WP1 robust choice / switch to the WP2 or WP4 candidate, with the evidence class of each (causal, exposed, leaderboard-only).
- **Leaderboard probe plan.** Leaderboard evaluations are biweekly, so probes are scarce. Give an ordered list of at most 3 submissions. For each:
  - which hypothesis it discriminates (CK1 handling, ε drift, start state);
  - the expected score difference vs SUB under each relevant WP1 hypothesis;
  - how to read the result.
- **`FINAL_REPORT.md` and `README.md`** (bilingual): conclusions first; all WPs summarised; risks; reproduction commands.
- **Done:** the global Done (§0).

## 5. Caps and order

| WP | Content | Cap | Depends on |
|---|---|---|---|
| 0 | setup, re-baselining | 0.5 h | — |
| 1 | hypothesis-robust selection | 1.5 h | 0 |
| 2 | uncertainty-weighted fusion | 3 h | 0, 1 |
| 3 | truth-oriented corrections | 2 h | 0, 1 (2 for the combined table; otherwise SUB only) |
| 4 | open-data prior | 3 h | 0 (2 for the fusion variant) |
| 5 | report material | 1 h | 0 (uses 1–4 if done) |
| 6 | synthesis, probe plan | 1 h | 1–5 |

At a cap, write up what exists (including "inconclusive"), commit, push and mark the WP capped.

## 6. Prohibitions (summary)

- **Causality.** No data after CK_k for CK_k. The public segment schedule is the only exception.
- **Selection.** Selection never uses the real proxies. No change of a registered main after its results. Exposed changes are labelled and never selected.
- **Proxies.** Never present proxies as hidden truth; never reconstruct CK1–CK7 from external sources.
- **Files and git.** Do not edit any submission package, earlier study or external checkout. Push only to this branch; never force-push.
- **No questions.** Never ask the user; record decisions and continue.

---

<a id="zh"></a>

# 第六轮：多假设稳健选择、融合、真值导向修正与开放数据先验——执行 Prompt

> **语言：** [English](#en) · 中文

编写日期：2026-10-15。本文自成一体。英文部分是执行文本，中文部分是给读者的翻译；两者不一致时以英文为准。

工作分成 **WP0–WP6 七个工作包**。每个都有自己的"完成标准"，可以作为单独的 `/goal` 运行。WP0 必须最先完成；WP1 必须在 WP2、WP3、WP6 之前完成；WP5、WP6 放在最后。

## 0. 工作方式（所有工作包）

- **无人值守。** 不要停下来提问。遇到未定的决策，选择遵守本文全部规则前提下最保守的方案，记入 `notes/DECISIONS.md`，然后继续。
- **重启。** 每一步之后都更新 `notes/STATUS.md`：工作包、已完成、下一步、最近一次提交。重启后先读 `notes/STATUS.md` 和 `notes/DECISIONS.md` 再接着做，不要重做已完成的工作包或步骤。
- **诚实优先于目标。** 负面结果或"按规则退出"都是有效结果。绝不在真实代理上调参；选择只能用伪场景和冷启动场景，或 WP1 登记的假设网格。
- **任何工作包的"完成"** 都要满足下面的通用标准，再加上该工作包自己的清单：
  1. 登记的协议（`wpN/protocol.json` + `wpN/protocol.sha256`）在其评估输出**之前**提交；
  2. 有双语、结论在前的 `wpN/REPORT.md`；
  3. `notes/STATUS.md` 把该工作包标为完成、到达上限或已退出，并附一行结果；
  4. 所有提交都已推送到 `origin exp/phase2-r6-robust-20261016`，`git status` 没有未提交的研究文件。
- **整体完成**（整个 prompt）：WP0–WP6 都已完成、到达上限或按登记规则退出；`FINAL_REPORT.md` 和 `README.md` 已写好（双语，结论在前）；通用标准 3–4 成立。

## 1. 工作区、隔离与 git

- **worktree 与分支（已建好）。**
  - 只在 `/Users/shane/Desktop/Arena_1016_r6_robust` 的分支 `exp/phase2-r6-robust-20261016` 上工作。它从第五轮 C 的最终提交 `348af0b` 创建。
  - 研究目录为 `research/phase2_r6_robust_20261016/`。
- **本 worktree 之外的只读来源。** 绝不 `cd` 进去，也绝不写入：
  - **提交分支** `exp/phase2-anchor-step-20261013` 的提交 `21a7a55`，位于 `/Users/shane/Desktop/Arena_1013_model`。只能用 `git -C /Users/shane/Desktop/Arena_1013_model show 21a7a55:<路径>` 和 `git -C … archive 21a7a55 <路径>` 把文件复制到本研究中。需要的文件：
    - `research/phase2_v3_20261015/src/v3.py`（V2 + √t 缺口分支、β 上限、取中位数等选项）及其 `FINAL_REPORT.md`；
    - `research/phase2_rebound_diagnosis_20261015/`（台阶偏移诊断的输出和脚本）；
    - `21a7a55` 时的 `TechArena_Challenge2_Team_Package/`。其中 `my_model/model_template.py` 是**当前提交的模型 V2+√t**；`my_model/model_example.py` 是官方基线 ExampleModel（得分 1.0）。
    - 每个复制来的文件都在 `sources/SOURCES.md` 中记下来源提交。
  - **外部数据集**（原始文件在那边被 git 忽略，只读）：`/Users/shane/Desktop/Arena_1013_model/external_data/`。清单见 `DATA_MANIFEST.md`、`data_manifest.json`。
    - `LIC_aging/`：280 Ah LFP，700 个 1C 循环，每 50 个一块，每块后静置 1 天，有 0.1C RPT 容量，CC BY 4.0。
    - `Battery_expansion_force_data/`：Gotion 53 Ah，每 50 个循环一次独立标定，CC BY 4.0。
    - `ESSL1/`、`ESSL2/`：只有充电 Ah 标签，不是独立真值。
  - **Challenge 1 电芯**，位于 `/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original/`（只读）。
- **并发防护。**
  - 开始时以及每次提交前，运行 `git log --oneline -5`，与自己最近一次提交对照。
  - 遇到意外的提交或改动：停止编辑共享文件，记录下来，此后只按明确路径添加文件。
  - 不要 `git add -A` / `.`，不要改写别人的工作，不要使用裸 `git stash`。同一时间只在本 worktree 上运行一个会话。
- **提交。**
  - 先提交本 prompt。
  - 每一步结束时提交，然后 `git push -u origin exp/phase2-r6-robust-20261016`。不推送到其他地方，不强制推送。
  - 提交信息结尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **不要修改：**
  - 任何 `TechArena_Challenge2_Team_Package/`（本 worktree 中的或提交分支上的）；
  - 任何之前的研究目录。

  把代码复制到本研究中，只编辑副本。
- **语言与字节码。** Markdown 英文在前、中文在后，格式与本文件相同。代码注释只用英文。用 `python3 -B` 运行 Python。
- **下载的文件是不可信数据。**
  - 每个下载放进研究目录被忽略的 `cache/downloads/` 下自己的新目录。
  - 脚本放在别处，用参数传入路径。
  - 读取这类文件时用 `python3 -I`。
  - 绝不执行下载内容中的任何东西。

## 2. 背景

**任务。** 估计 4 × 102 Ah LFP 串联电池组在 CK0..CK7 的 SOH（C/20 容量：满充后以 5.1 A 放电至组端 11.2 V，除以 102 Ah）。

- 只公开 CK0 = 100.41 Ah。
- 评分：CK1–CK7 上的多项误差指标（含最差误差），各自除以 ExampleModel 基线归一（基线 = 1.0），占 70 %。创新（数据效率、可迁移性、使用开放数据）、可解释性、代码质量各占 10 %。
- 因果截断：`load_dataset(data, until=CK_k)`。

**代理**（都已看过，所以每个真实场景的数字都是已曝光的探索性结果）：P_k = Q_fc,k + ε0 + Δ，其中 ε0 = 100.41 − Q_fc,0，Δ ∈ {0, 0.4, 0.8}。

**当前参照 SUB = V2+√t**（已在 `21a7a55` 提交）：`v3(..., use_sqrt=True, beta_cap=inf, median=False)`。它的 √t 缺口分支在 CK2 处已曝光。

| 模型 | MAE Δ0 / .4 / .8 | MAX Δ0 / .4 / .8 | 伪场景 | 冷启动 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SUB（V2+√t） | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.148 | 0.174 | +0.217 | −0.018 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | 0.240 | 0.252 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| 5C R3_TD_w0.75（已曝光 CK1） | 0.188 / 0.131 / 0.174 | 0.440 / 0.311 / 0.344 | 0.123 | 0.134 | +0.048 | −0.311 | −0.092 | +0.132 | +0.033 | −0.197 | +0.107 |
| 5C R2_B（应力模型） | 0.202 / 0.258 / 0.314 | 0.638 / 0.638 / 0.953 | 0.119 | 0.144 | −0.561 | −0.638 | −0.150 | +0.100 | −0.007 | −0.209 | +0.144 |

各检查点误差为 Δ = 0.4 时的值，单位 pp。"伪场景"是 PG1、PG2、PC5、PC10（k ≥ 3）的平均 MAE；"冷启动"是 CS 和 CSE 的平均（Δ = 0.4）。

**关于标签已知的情况**（隐藏真值可能与代理不同）：

- **检查后的台阶偏移。**
  - 第四轮把它解读为容量恢复：CK1..CK7 的 R_k = 0.018、0.245、0.336、0.707、0.827、0.798、0.866 Ah（`research/phase2_round4_signals_20261014/stage_5/outputs/jumps.csv`，列 `recovery_Ah_with_aging`）。
  - 2026-10-15 的偏移诊断则认为：只有**从空充满的锚点充电之后的第一次深放电程序**偏深 0.39–0.46 Ah。这是充电路径效应，平台没有变化，所以它不支持"容量恢复"的解读。
- **ε 漂移。** 外部数据（LIC、Gotion）中，独立容量减去满充 Ah 的差值，每衰减 1 Ah 约漂移 −0.03 Ah。对本电池组来说，到 CK7 约为 0.25–0.3 pp，代理看不到。
- **锚点起点状态。** 锚点充电开始时的组端静置电压在 11.62–12.04 V 之间。第三轮发现底部区段与起始电压相关（r = −0.975）。LIC 显示每块约有 1.5 Ah 的起点效应。
- **剩下的误差是共有的。** 所有模型都是 CK4 偏正、CK6 偏负，这指向标签或月份本身的结构，而不是某个模型。

**可复用的代码（在本 worktree 中）：**

- 第三轮 harness `research/phase2_round3_models_20261014/src/harness.py`；
- 第五轮 C 的 `src/`（`stress.py`、`smodel.py`、含 `LawFit` 的 `smodel5c.py`、含 CS/CSE 场景的 `runner5c.py`、`preds5c.py`、`checks5c.py`）；
- 第五轮 C 的 `stage_1/prior2.json`、`candidate_model/`、`stage_2/run_3.py`；
- V2 `research/phase2_v2_phase_matched_20261013/src/v2.py`。

要改的先复制。环境：研究用 `python3` 3.13（numpy、pandas、scipy、matplotlib）；候选检查用 `cache/venv311` 中只装 numpy/pandas 的 Python 3.11 venv。

## 3. 通用规则

1. **先登记，再运行。** 在计算该工作包的任何真实场景数字之前，先在 `wpN/protocol.json`（附 SHA256）中登记。先跑伪场景 / 冷启动结果，在真实运行之前提交。
2. **选择绝不使用真实代理。** 可以用伪场景 / CS 场景和 WP1 登记的假设网格。每个登记设计的真实结果都要报告，包括落选的。
3. **已曝光的改动。** 任何设计，如果它的作用只限于某个在构思时误差已知的检查点（5C 类暂态或路径规则对应 CK1；√t 对应 CK2），就标为 `exposed-CKx`。它在该检查点上的收益不是证据。
4. **只用于排行榜的输出。** 代理无法评判的修正（ε 漂移、起点状态）绝不在代理上作为改进来评分。它们只在 WP1 假设网格下报告，并给出 SOH 表。
5. **实现。** 缓存键包含所有参数；因果检查比较精确浮点数；偏离要在运行前登记。
6. **接入。** 绝不接入任何真实的 `my_model/`。打包检查在 `cache/package_copy_*` 的副本上进行。

## 4. 工作包

### WP0——准备与重新确定基线（上限 0.5 小时）

- 建 `notes/STATUS.md`、`notes/DECISIONS.md`、`.gitignore`（`cache/`）和 `sources/`。
- 复制只读来源（第 1 节），写 `sources/SOURCES.md`。
- **复现**（通过 harness 和 5C 运行器，覆盖真实、伪场景、CS、CSE）：
  - V2（Δ = 0.4 时 MAE 0.215726）；
  - SUB（Δ = 0.4 时 MAE 0.123 / MAX 0.228；伪场景 0.148；冷启动 0.174）；
  - 5C 的 R3_TD_w0.75（0.131；0.123；0.134）和 R2_B。
- **确认提交的类**：归档的 `21a7a55` 提交包中的类在所有检查点上与 SUB 相差不超过 0.001 pp。
- **计算 ExampleModel**（官方基线）在 CK1–CK7 上的因果预测，用归档的提交包。
- **完成：** 所有复现都在容差内，记录在 `wp0/outputs/reproduce.json`（如果 SUB 或 V2 复现不了，停止整轮），并满足通用标准。WP0 没有协议，`wp0/REPORT.md` 写简短即可。

### WP1——在现有模型中做多假设稳健选择（上限 1.5 小时；不建新模型）

**标签假设 h**（共 18 个 = 3 × 3 × 2）：每个检查点的"类真值"目标为

T_k(h) = Q_fc,k + ε0 + Δ − f·R_k + d·L_k，其中 L_k = max(0, 100.41 − (Q_fc,k + ε0)) 是代理所示的衰减量（Ah）。

- Δ ∈ {0, 0.4, 0.8}；
- f ∈ {0, 0.5, 1}，表示第四轮"恢复量"R_k 中隐藏 C/20 **没有**测到的比例；
- d ∈ {0, −0.031} Ah/Ah，表示 ε 漂移。

对真实、伪场景和 CS 场景做同样的变换。

**候选**（现有模型，不重新拟合）：

- ExampleModel、M4（V1）、V2、**SUB**、V2+√t+β 上限 1.2、V3；
- 5A 的 S_main 和 ENS50；
- 5C 的 R2_B、R2_D_w0.75、R3_T、R3_TD_w0.75。

**每个 h 下的得分：** 归一化得分 s_h(m) = mean(MAE_m/MAE_EX, RMSE_m/RMSE_EX, MAX_m/MAX_EX)，在 CK1–CK7 上计算，EX 是同一 h 下的 ExampleModel。同时报告原始 MAE 和 MAX。

**决策量（计算前登记）：**

- (i) 所有 h 中最差的 s；
- (ii) 最大后悔值 = 对所有 h 取 [s_h(m) − 所有模型中 s_h 的最小值] 的最大值；
- (iii) 两种先验下 s 的期望：
  - 均匀先验；
  - 依据诊断的先验：f 的权重 {0: 0.6, 0.5: 0.3, 1: 0.1}，d 的权重 {0: 0.5, −0.031: 0.5}，Δ 均匀。

这些都在真实网格上算，另外在伪场景 + CS 网格上单独再算一遍（用 ExampleModel 归一；如果某场景上没有 ExampleModel，就用 V2 归一）。

**登记的稳健选择：** 真实网格上最大后悔值最低的模型；差距在 0.01 以内时，取依据诊断的先验下期望更低的那个。报告伪场景 + CS 网格是否给出相同结论，以及排名随先验如何变化。要明确说明真实网格的数字都已曝光：WP1 衡量的是对**标签**不确定性的稳健性，不是关于精度的新证据。

**完成：** 排名表（每个 h、最差情形、后悔值、两种先验、真实和因果网格）、s_h(m) 的热力图、稳健选择及其稳定性，并满足通用标准。

### WP2——应力模型与 SUB 的不确定度加权融合（上限 3 小时）

Q = w_k · S + (1 − w_k) · SUB，其中 S 来自 5C 的 `LawFit`。运行之前登记以下全部内容。

**S 的变体：**

- S_A = R2_B（两项定律、缺口月台阶首尾观测、β = 1、从 CK 日期起算的 5 天规则）：未曝光。
- S_B = R3_T（从恢复运行起算的 5 天规则）：已曝光 CK1。
- S_C = 路径规则（依据偏移诊断，去掉每次锚点充电后的第一次深放电程序）：已曝光 CK1。

**融合设计：**

- **F1 逆方差加权。** w_k = σ²_SUB,k / (σ²_S,k + σ²_SUB,k)。
  - σ²_S,k = S 的月损失预测方差（用 delta 方法从 `LawFit` 参数的拉普拉斯协方差得到；需要实现）+ σ²_S0。
  - σ_S0 = S 在伪场景 + CS（k ≥ 3）上的 RMS 误差。
  - σ_SUB,k = SUB 在伪场景 + CS 上按 SUB 分支（phase / sqrt_gap / fallback）计算的 RMS 误差；某分支少于 3 个情形时，用整体 RMS。
  - 这些全部只在伪场景 + CS 上估计。
- **F2 按类别定权重。** 每种情形类别（冷启动 = S 没有锚点对；缺口 = SUB 分支为 sqrt_gap；phase；fallback）从网格 {0, 0.25, 0.5, 0.75, 1} 中选一个 w，在伪场景 + CS 上选。伪场景 + CS 中没有出现的类别取 w = 0.5（登记的默认值）。
- **F3 固定 w = 0.5。**

每个设计分别与 S_A（主配置）、S_B 和 S_C（已曝光变体）组合。

**选择：** 只在伪场景 + CS 上进行：在 F1–F3 × S_A 中，选 Δ = 0.4 时伪场景 MAE 与 CS MAE 平均最低、且通过 G-pseudo 和 G-coldstart 的设计。已曝光变体只报告，绝不选。

**对 SUB（新参照）的门槛：**

- G-proxy：每个 Δ 下 MAE < SUB，且 MAX ≤ SUB 的 MAX + 0.10；
- G-epsfree：CK2–7 MAE ≤ SUB − 0.02；
- G-robust：6 种台阶方法中至少 5 种胜出；
- G-pseudo：≤ SUB + 0.02；
- G-coldstart：≤ SUB；
- G-regress：每个检查点 ≤ 0.30 pp；
- **G-hyp：** 真实网格上的最大后悔值（WP1 网格，SUB 和该设计都包含在内）≤ SUB 的；
- G-causal 与 G-impl：numpy/pandas 类与研究实现相差 ≤ 0.001 pp，Python 3.11 venv，完整运行 < 30 分钟，并在**归档的 21a7a55 提交包**副本上通过 `validate_submission.py`。

**完成：** 选择在真实运行之前提交；门槛表；只有当选出的设计通过全部门槛时才做候选类和检查；并满足通用标准。

### WP3——真值导向的修正（上限 2 小时；只用于排行榜）

**WP3a——锚点起点修正。**

- **先审计。** 对每个锚点 j，取充电前静置时的各芯电压，用 CK0 C/20 放电曲线的尾部（`events.tail_margin_Ah`，这是上界）估算起点处的残余电量 r_j；另做一个取上界一半的变体。报告各锚点 r_j − r_0 的离散程度。
- **退出规则：** 如果 max |r_j − r_0| < 0.1 Ah，把 WP3a 标为"无实质影响"并停止。
- **否则：** 登记修正后的锚点 Q'_fc,j = Q_fc,j + (r_j − r_0)，并把它传递到 SUB 和 WP2 的选中模型中（锚点起点和 S 的拟合）。

**WP3b——ε 漂移。** 修正后 Q̂' = Q̂ + d·L̂_k，其中 L̂_k = max(0, 100.41 − Q̂_k) 是模型自己因果估计的衰减。d = −0.031（主配置），敏感性取 −0.020 和 −0.035。

**WP3c——路径效应。**

- 在本研究的台阶表上核实偏移诊断：每次锚点充电之后的第一次深放电程序，是否在全部六种检测方法下都偏深 +0.39–0.46 Ah？
- 列出哪些模型输入包含这样的程序：SUB 的月末 45 °C 台阶、S 的缺口首尾台阶。
- 报告排除它们对 SUB 和 S 的影响。

**输出：**

- SUB 和 WP2 选中模型的排行榜专用 SOH 表，分别加上 3a / 3b / 3c 以及它们的组合；
- 它们在 WP1 假设网格上的得分（这些修正应在对应的假设下胜出、在其他假设下落败）；
- 一张后悔值表。

绝不声称代理上有改进。

**完成：** 审计、各表、后悔值表，并满足通用标准。

### WP4——为应力模型构建开放数据先验（上限 3 小时）

**资格审计（不算电池组指标）：**

- 对 LIC 280 Ah 和 Gotion 53 Ah：协议、温度、静置时段、独立容量点、许可证。
- 判断各自能辨识定律中的哪些项：磨合项 A_b 和 τ_b，以及循环项 A_cyc。日历项需要静置或存储数据。

**可选下载。** 当且仅当 WP4 协议在下载之前写明要下载时：

- Yagci 2025 的 Zenodo 记录 22939281（v1.1，CC BY 4.0；先在记录页面上核实许可证），不超过 3 GB，放进 `cache/downloads/yagci/`，按不可信数据处理（第 1 节）；
- 任何失败都跳过。

**Prior3：** 用 5C 第 1 阶段的方法（Arrhenius 37.3 kJ/mol），在合格的数据集上重新拟合两项定律。用 jackknife 或留一数据集的 SD，对无法辨识的项保留 5C 的回退规则。写出带来源说明的 `prior3.json`。

**评估：** 用 prior3 的 S_A（记为 S_A3），单独以及放进 WP2 选出的融合设计中，先在伪场景 + CS 上评估，再在真实场景上评估，门槛同 WP2。按规则 3，CK1 的变化本应算已曝光；但 prior3 是在得到任何电池组结果之前就确定的（按构造如此），所以可以报告为**"仅由外部数据驱动的冷启动"**，同时仍要注明 CK1 本身已经被看过。

**另外产出**一张来源说明表（数据集、许可证、用途），供报告使用。

**完成：** 审计报告、`prior3.json`、评估表，并满足通用标准。如果没有合格的数据集，标为"已退出：无合格数据"。

### WP5——报告与展示材料（上限 1 小时）

放在 `report_material/` 中（双语草稿；**绝不编辑提交包里的 REPORT.md**）：

1. SUB 的方法部分，以及 WP2/WP4 候选的方法部分（如果有）；
2. 可解释性图：拟合出的定律在整个试验期间按磨合、日历、循环分解；
3. 开放数据使用表：Challenge 1、Yagci、LIC、Gotion、ESSL、PyBaMM OCP（5B）；
4. 验证理念：曝光、伪场景 / 冷启动因果检验、假设网格；
5. 值得展示的负面结果：5B 电极模型不可辨识、5A 冷启动；
6. 演示大纲（10–12 页）；
7. 对已提交的 `my_model/model_template.py`（归档副本）做代码质量审计：pycodestyle（装在 `cache/` 中的研究 venv 里）、docstring、魔法数字。列出问题，不修改提交包。

**完成：** 文件齐全，并满足通用标准（WP5 没有协议；它的 REPORT 是这些草稿的索引）。

### WP6——综合与排行榜探测计划（上限 1 小时）

- **决策表：** 保留 SUB / 换成 WP1 的稳健选择 / 换成 WP2 或 WP4 的候选，并注明各自的证据类别（因果、已曝光、只用于排行榜）。
- **排行榜探测计划。** 排行榜每两周评估一次，探测机会很少。给出最多 3 次提交的有序清单。对每一次说明：
  - 它能区分哪个假设（CK1 的处理、ε 漂移、起点状态）；
  - 在每个相关的 WP1 假设下，相对 SUB 的预期得分差；
  - 结果出来后怎么解读。
- **`FINAL_REPORT.md` 和 `README.md`**（双语）：结论在前；概括所有工作包；风险；复现命令。
- **完成：** 满足整体完成标准（第 0 节）。

## 5. 上限与顺序

| WP | 内容 | 上限 | 依赖 |
|---|---|---|---|
| 0 | 准备、重新确定基线 | 0.5 小时 | — |
| 1 | 多假设稳健选择 | 1.5 小时 | 0 |
| 2 | 不确定度加权融合 | 3 小时 | 0、1 |
| 3 | 真值导向修正 | 2 小时 | 0、1（组合表需要 2；否则只用 SUB） |
| 4 | 开放数据先验 | 3 小时 | 0（融合变体需要 2） |
| 5 | 报告材料 | 1 小时 | 0（如已完成，用上 1–4） |
| 6 | 综合、探测计划 | 1 小时 | 1–5 |

到上限时，把已有结果（包括"无定论"）写成报告、提交、推送，并把该工作包标为到达上限。

## 6. 禁止事项（汇总）

- **因果性。** 预测 CK_k 不得用 CK_k 之后的数据。公开的分段日程是唯一例外。
- **选择。** 选择绝不使用真实代理。看到结果后不得更改登记的主配置。已曝光的改动必须标注，且绝不被选中。
- **代理。** 绝不把代理当成隐藏真值；绝不从外部来源重建 CK1–CK7。
- **文件与 git。** 不修改任何提交包、之前的研究或外部检出目录。只推送到本分支，不强制推送。
- **不提问。** 绝不向用户提问；记录决策并继续。
