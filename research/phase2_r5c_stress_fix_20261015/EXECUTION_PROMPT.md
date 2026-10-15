<a id="en"></a>

# Round 5C: Fixing the Stress Model's Cold Start — Unattended Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-15. This document is self-contained. The English text is the execution text; the Chinese section is a translation for the reader, and if they differ the English governs.

## 0. Mode of work

- **Unattended run.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Context may be compacted or restarted.** Keep `notes/STATUS.md` current after every step: stage, done, next, last commit. On restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume. Never redo a finished stage.
- **Time budget.** About 9 hours in total, with a cap per stage (§7).
- **Ambition and honesty.** The targets in §5 are deliberately hard. Aim for all of them. Missing a target is a valid, reportable outcome. **Never chase a target with unregistered tuning on the real proxies.** The only legitimate route to a better model is a new registered design round (§6, at most three rounds).
- **Done means** (all must hold):
  1. every stage in §6 is finished, capped or skipped by a registered rule, and `notes/STATUS.md` says which;
  2. `FINAL_REPORT.md` and `README.md` exist in the study directory, bilingual, conclusions first, with an explicit target-by-target verdict (met / missed, with numbers);
  3. every registered protocol has its `protocol.sha256` committed before its evaluation commit;
  4. if any model passes every gate in §5, a candidate class exists in `candidate_model/` with G-causal and G-impl evidence and a passing `validate_submission.py` run on a **copy** of the package (never the real one);
  5. every commit is pushed to `origin exp/phase2-r5c-stress-fix-20261015`;
  6. `git status` in the worktree shows no uncommitted study files.

## 1. Workspace, isolation and git

- **Worktree and branch (already created).**
  - Work only in the worktree `/Users/shane/Desktop/Arena_1015_r5c_stressfix`, on branch `exp/phase2-r5c-stress-fix-20261015`. It starts from round 5A's final commit `f27cca7`.
  - Never `cd` into another checkout. All new work goes into `research/phase2_r5c_stress_fix_20261015/` (the "study directory").
- **Concurrency guard.**
  - At the start and before every commit, run `git log --oneline -5` and compare with your own last commit.
  - If a commit you did not make appears, or a tracked file changes that you did not change: stop editing shared files, record it in `notes/DECISIONS.md`, and only add files by explicit path from then on.
  - Never use `git add -A` / `git add .`, never revert or rewrite someone else's work, never use bare `git stash`.
- **Commits and pushes.**
  - Commit this prompt as the first commit.
  - Commit at the end of every stage. After each stage commit, run `git push -u origin exp/phase2-r5c-stress-fix-20261015`.
  - Never push anywhere else; never force-push.
  - Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify:**
  - `TechArena_Challenge2_Team_Package/`;
  - any earlier study directory, including `phase2_r5a_stress_model_20261014`;
  - the Challenge 1 data at `/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original/`, which is read only.

  Import and copy code; never edit it in place.
- **Language and bytecode.** Every Markdown document is English first, Chinese second, in this file's layout. Code comments are English only. Run Python with `python3 -B`.

## 2. Task and current state

**Task.** Estimate the SOH (C/20 capacity: 5.1 A discharge after a full charge until pack 11.2 V, divided by 102 Ah) of a 4 × 102 Ah LFP series pack on CK0..CK7 = 2025-01-14, 02-08, 03-11, 04-14, 05-16, 06-16, 07-25, 08-28. Only CK0 = 100.41 Ah is released. A prediction for CK_k may use only `load_dataset(data, until=CK_k)`.

**Calendar.**

- Month 0 (CK0 → CK1) is one 45 °C segment (seg 1).
- From month 1 on, each month is a short 25 °C segment followed by a long 45 °C segment.
- Segment 3 (45 °C, 02-19 → 03-11) is missing. Its counter jump becomes visible only after the CK2 cutoff.

**Anchors.** After each checkup the pack is charged from near empty (CC 20.4 A, CV 14.0 V to 5.1 A). Q_fc,j is anchor j. Anchor 0 is at 45 °C; anchors 1–7 are at 25 °C.

**Proxies** (all already seen, so every result is exposed-exploratory): P_k = Q_fc,k + ε0 + Δ, with ε0 = 100.41 − Q_fc,0 and Δ ∈ {0, 0.4, 0.8}.

**V2** (the submission package on `exp/phase2-anchor-step-20261013` points to it) combines the latest anchor + ε with a phase-matched 45 °C graphite-step difference × β; CK1–CK3 fall back to M4.

| | MAE Δ0 / .4 / .8 | MAX | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | +0.217 | **+0.669** | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| 5A S_main | 0.270 / 0.326 / 0.382 | 1.134 | **−1.134** | +0.565 | −0.025 | −0.004 | −0.156 | −0.370 | +0.029 |
| 5A ENS50 | 0.158 / 0.214 / 0.270 | 0.851 (Δ.8) | −0.459 | +0.617 | +0.027 | +0.112 | −0.003 | −0.266 | +0.013 |

Errors are in pp at Δ = 0.4. V2's ε-free CK2–7 MAE is 0.216 and S_main's is 0.192; their pseudo MAEs (k ≥ 3) are 0.240 and 0.131.

**Round 5A's stress model S** (`research/phase2_r5a_stress_model_20261014/`, read its `FINAL_REPORT.md` first):

- Law: L = A_cal·(τ_eff)^z + A_cyc·ah_eff, with Arrhenius-weighted time and throughput (Ea 37.3 kJ/mol, z = 0.2). It is fitted by MAP on consecutive visible anchor pairs.
- Prediction: Q̂_k = base − ΔL, where base = Q_CK0 if the latest anchor is anchor 0, else Q_fc,k−1 + ε.

**Diagnosed problems of S (what this round must fix):**

1. **Cold start.** At CK1 no anchor pair exists, so S is the prior alone. The Yagci-derived prior over-predicts month-0 loss by about 1.2 Ah, giving −1.13 pp. This one point also causes S's MAE to grow with Δ, because only CK1's base lacks Δ. That is the whole reason ENS50 failed G-proxy at Δ = 0.8.
2. **Law shape.** A single t^z term conflates the fast first-month break-in with storage ageing (stage 2 of 5A: Challenge 1 cells show jumps of 1.5–2.5 Ah during idle gaps that z = 0.2 cannot produce). At CK2, z = 0.2 under-predicts month 1 (+0.57 pp) and z = 0.5 over-predicts slightly (−0.21 pp).
3. **Unused in-month information.** S ignores the ~5-day 45 °C program steps, which V2 uses. At the CK1 cutoff, four such steps from segment 1 are already visible (01-20, 01-24, 01-29, 02-03; step depth 32.81 → 30.31 Ah). They measure month-0 loss directly, but S never sees them.

## 3. Code and data to reuse

- **Round 5A modules:** copy `research/phase2_r5a_stress_model_20261014/src/stress.py` and `src/smodel.py` into this study's `src/` and extend the copies.
  - `stress_table(op, until, ck, horizon)` builds the stress history with the registered rules for checkups, the missing segment and the hidden tail.
  - `cumulative()` gives Arrhenius-weighted τ_eff and ah_eff.
  - `StressFit` uses a numpy-only LM.
  - 5A's `stage_2/prior.json` and `stage_2/c1_cycles.py` hold the Challenge 1 cycle summaries and prior rules.
- **Round 3 harness:** `research/phase2_round3_models_20261014/src/harness.py`.
  - It provides `run`, `metrics`, `per_ck`, `gates_vs_v2`, `candidate_checks`, `SCENARIOS`, `BASELINES`, `QFC`, `EPS0` and `cut_op`.
  - `ctx["steps"][variant]` holds the program steps (`t_cv_end`, `step_mean`, `setpoint_C`, per-cell steps) for the six step-detection variants.
  - Its cache stays inside this worktree.
- **V2 functions:** `research/phase2_v2_phase_matched_20261013/src/v2.py` (`anchors_by_checkup`, `month_steps`, `beta_a4`, `v2`, `m4`).
- **Environment:** research uses `python3` (3.13, numpy, pandas, scipy, matplotlib). Candidate classes must be numpy/pandas only and must also run under Python 3.11, in a venv at the study's git-ignored `cache/venv311` built from `/opt/homebrew/bin/python3.11`.

## 4. Rules

1. **No real results before the protocol commit.** In every design round, register first, then run pseudo and cold-start scenarios and commit, then run the real scenario once. Exclude k = 2 from any scenario used for a decision.
2. **Selection uses only pseudo and cold-start scenarios.** The real CK1–CK7 proxies are evaluated once per round and never used to choose between designs, weights or parameters. Report the real results of every registered design, including losers.
3. **Implement registered formulas exactly.** Register any deviation before running.
4. **Cache keys contain every parameter** that changes the cached result.
5. **Causality checks compare exact floats.**
6. **6–7 points are diagnostics, not validation.** Word correlations that way.
7. **The real CK1 error of 5A is known.** Any design whose only effect is at CK1 (for example "use V2 at CK1") must be labelled `exposed-CK1`. It may be reported and gated, but its CK1 improvement cannot be claimed as evidence.

## 5. Evaluation, gates and targets

**Scenarios.**

- *Real*: k = 1..7.
- *Pseudo*: PG1/PG2 (k = 4..7) and PC5/PC10 (k = 3..7), as in rounds 3–5A.
- ***New: cold-start scenarios CS*** (register in stage 0, before any design). They imitate CK1's situation at later months. For k = 3..7:
  - the model may use only anchor k−1 and later data, so every earlier anchor is removed from `fc`. Its prior and parameter fits must therefore come from the cold-start information alone (prior + in-month data);
  - the proxy is P_k as usual.

  Variant CS-early: additionally cut the operation data 10 days before CK_k. CS scenarios test exactly the mechanism CK1 depends on.

**Common gates against V2** (as in 5A):

| Gate | Rule |
|---|---|
| G-causal | exact-float identity under future noise and fit-on-CK1-prefix |
| G-proxy | MAE < V2 for every Δ; MAX ≤ V2 MAX + 0.10 pp |
| G-epsfree | ε-free CK2–7 MAE ≤ V2 − 0.02 pp |
| G-robust | beats V2's MAE (Δ = 0.4) in ≥ 5 of 6 step variants, or for models without step input, in ≥ 75 % of their registered variant groups |
| G-pseudo | mean pseudo MAE (k ≥ 3) not worse than V2 + 0.02 pp |
| G-coldstart | mean CS MAE ≤ V2's mean CS MAE (V2 run on the same CS inputs) |
| G-regress | no checkup's absolute error grows by more than 0.30 pp vs V2 (Δ = 0.4) |
| G-impl | numpy/pandas `MyModel` class within 0.001 pp of research, sample_data smoke test in the 3.11 venv, full run < 30 min, `validate_submission.py` passes on a copied package |

**Bold targets** (proxy pp; reported met or missed for the best gate-passing model and for the registered main of each round):

| Target | Value | V2 today |
|---|---|---|
| T1 MAE at every Δ | ≤ 0.15 | 0.272 / 0.216 / 0.210 |
| T2 MAX at every Δ | ≤ 0.45 | 0.669 |
| T3 CK1 and CK2 | each \|error\| ≤ 0.30 at Δ = 0.4 | 0.217 / 0.669 |
| T4 ε-free CK2–7 MAE | ≤ 0.15 | 0.216 |
| T5 mean pseudo MAE (k ≥ 3) | ≤ 0.12 | 0.240 |
| T6 mean CS MAE | ≤ 0.20 | to be measured in stage 0 |

T3's CK1 part is exposed-CK1 for any design that changes only CK1 (rule 7).

## 6. Stages

### Stage 0 — Setup and cold-start harness (cap 1 h)

- Create the study directory, `notes/STATUS.md`, `notes/DECISIONS.md` and `.gitignore` (`cache/`).
- Reproduce V2 (0.215726 / 0.669052), M4 (0.291265), and 5A's S_main and ENS50 (MAE 0.326 / 0.214 at Δ = 0.4) through the copied modules. If they do not reproduce, stop and record why.
- Implement the CS and CS-early scenarios.
  - Register them in `stage_0/protocol.json`.
  - Commit before running them.
  - Then report V2, M4, S_main and ENS50 on them. These baselines set T6's reference and G-coldstart.

### Stage 1 — Design round 1 (cap 2.5 h)

Register **all** of the following in `stage_1/protocol.json` before running anything. Each design is a full predictor; components can be combined only as registered here.

**D1 — Step-informed S ("S+steps").** Add the visible in-month 45 °C program steps as observations in S's MAP fit.

- For each pair of consecutive visible 45 °C steps i < j within the same month (main step method; steps less than 5 days after the month's checkup date are excluded because of the post-checkup transient, τ ≈ 2.5 d):

  β_k · (s_j − s_i) = −[L(t_j) − L(t_i)] + e, with e ~ N(0, σ_s²), σ_s = 0.05 Ah.

- β_k is V2's `beta_a4(β0 = 1, τ = 1)` at that cutoff, which is 1 at early cutoffs.
- These terms are added to the anchor-pair terms. At CK1 they are the only data besides the prior.
- Variants:
  - σ_s × 0.5 and × 2;
  - β free with prior N(1.3, 0.2²);
  - include the 25 °C steps with a free 25→45 °C offset per month.

**D2 — Two-term law ("S2").**

- Law: L = A_b·(1 − exp(−τ_eff/τ_b)) + A_cal·τ_eff^0.5 + A_cyc·ah_eff. This is a saturating break-in term, a √t calendar term and a linear cycle term.
- Priors come from refitting this law to the six Challenge 1 cells with 5A's stage 2 data and rules (`c1_cycles.py`), including idle gaps at nominal temperature. Use the jackknife SD; if a parameter is unidentified, fall back to Yagci-derived scales as in 5A's stage 2 rule. Register the refit procedure before running it.
- Free in the pack fit: log A_b, log A_cal, log A_cyc and o_45. τ_b is fixed at the prior mean; a variant leaves it free with its prior.

**D3 — D1 + D2 combined ("S2+steps").**

**D4 — Ensembles.** w·D + (1 − w)·V2 for each D in {D1, D2, D3}, with w chosen on pseudo + CS scenarios only from the grid {0, 0.25, 0.5, 0.75, 1}. Also register a variant with w fixed at 0.5.

**D5 — exposed-CK1 hybrid** (label it so). Use V2 at CK1 and D3 from CK2 on. Report it and gate it; under rule 7 it cannot be the selected main unless it also wins on CS scenarios.

**Selection rule** (register it): among D1–D4, choose the main of round 1 as the design with the lowest mean of the pseudo MAE and the CS MAE at Δ = 0.4, subject to passing G-pseudo and G-coldstart. Ties go to the simpler design.

**Order:** protocol commit → pseudo + CS runs, committed → selection committed → real run → gates, targets and per-checkup tables committed.

### Stage 2 — Design rounds 2 and 3 (cap 3 h in total; optional)

Run another round only if no model passed every gate, or if gates passed but targets T1–T5 were missed.

- Each round must start with a **written diagnosis** based only on pseudo and CS results and on physics, never on the real proxies. Examples: wrong β early on, transient leakage, law shape on CS.
- Then register at most four new designs, using the same order and selection rule as round 1.
- At most three rounds in total. Stop after round 3 whatever the result.

### Stage 3 — Candidate and packaging check (cap 1 h)

Do this only for the single best model that passes **every** gate; choose by the round's registered selection rule, and if several rounds pass, take the latest round's main.

- Write a numpy/pandas-only `MyModel` in `candidate_model/`.
- Run `harness.candidate_checks` (G-causal + G-impl) in Python 3.13 and in the 3.11 venv.
- Copy `TechArena_Challenge2_Team_Package/` to the study's git-ignored `cache/package_copy/`, wire the candidate there, and run `validate_submission.py`.
- Record the result. **Never touch the real package.**

### Stage 4 — Final report (cap 0.5 h)

**`FINAL_REPORT.md`** (bilingual, conclusions first) contains:

1. a table of every registered design and variant against V2, M4, S_main and ENS50 (MAE per Δ, MAX, ε-free, pseudo, CS, gates);
2. per-checkup errors;
3. the target-by-target verdict T1–T6;
4. what fixed the cold start, if anything, and why, separating causal evidence (pseudo/CS) from exposed results;
5. the candidate verdict and a leaderboard-only SOH table;
6. a recommendation on whether the user should consider replacing V2 in the submission. **Make no change yourself.**
7. risks: exposure, single pack, ε and the post-checkup recovery (round 4: up to ~0.9 Ah late), and prior transfer;
8. exact reproduction commands.

Also write a bilingual **`README.md`**.

## 7. Order and caps

| Order | Stage | Cap |
|---|---|---|
| 0 | Setup, reproduction, CS harness | 1 h |
| 1 | Design round 1 | 2.5 h |
| 2 | Design rounds 2–3 (optional) | 3 h |
| 3 | Candidate + packaging check | 1 h |
| 4 | Final report | 0.5 h |

**Stop rules.**

- If stage 0 cannot reproduce V2 or 5A, stop.
- A candidate failing G-causal is rejected outright.
- After round 3, stop designing even if no target is met.

## 8. Prohibitions (summary)

- **Causality.** No data after CK_k for CK_k. The public segment schedule is the only exception, as in 5A.
- **Selection.** Selection never uses real proxies. No change of a registered main after its results. No unregistered retries. At most three design rounds.
- **Proxies.** Never present proxies as hidden truth; never reconstruct CK1–CK7 from external sources.
- **Files and git.** Do not edit the submission package or earlier studies. Push only to this branch; never force-push.
- **No questions.** Never ask the user anything; record decisions and continue.

---

<a id="zh"></a>

# 第五轮 C：修复应力模型的冷启动问题——无人值守执行 Prompt

> **语言：** [English](#en) · 中文

编写日期：2026-10-15。本文自成一体。英文部分是执行文本，中文部分是给读者的翻译；两者不一致时以英文为准。

## 0. 工作方式

- **无人值守运行。** 不要停下来提问。遇到未定的决策，选择遵守本文全部规则前提下最保守的方案，记入 `notes/DECISIONS.md`，然后继续。
- **上下文可能被压缩或重启。** 每一步之后都更新 `notes/STATUS.md`：阶段、已完成、下一步、最近一次提交。重启后先读 `notes/STATUS.md` 和 `notes/DECISIONS.md` 再接着做，不要重做已完成的阶段。
- **时间预算。** 全程约 9 小时，每个阶段有上限（第 7 节）。
- **雄心与诚实。** 第 5 节的目标是故意定得很难的，要全力争取全部达成。没达成也是有效、可报告的结果。**绝不能为了达成目标而在真实代理上做未登记的调参。** 想得到更好的模型，唯一合规的途径是新开一轮登记过的设计轮次（第 6 节，最多三轮）。
- **完成的标准**（必须全部满足）：
  1. 第 6 节每个阶段都已完成、到达上限或按登记的规则跳过，且 `notes/STATUS.md` 写明是哪一种；
  2. 研究目录里有 `FINAL_REPORT.md` 和 `README.md`，双语、结论在前，并对每个目标逐条给出明确结论（达成 / 未达成，附数字）；
  3. 每份预登记协议的 `protocol.sha256` 都在其评估提交之前提交；
  4. 如果有模型通过第 5 节的全部门槛，`candidate_model/` 下要有候选类，附 G-causal 和 G-impl 证据，并在提交包的**副本**（绝不是真实提交包）上跑通 `validate_submission.py`；
  5. 所有提交都已推送到 `origin exp/phase2-r5c-stress-fix-20261015`；
  6. worktree 里 `git status` 没有未提交的研究文件。

## 1. 工作区、隔离与 git

- **worktree 与分支（已建好）。**
  - 只在 worktree `/Users/shane/Desktop/Arena_1015_r5c_stressfix` 的分支 `exp/phase2-r5c-stress-fix-20261015` 上工作。该分支从第 5 轮 A 的最终提交 `f27cca7` 创建。
  - 不要 `cd` 到任何其他检出目录。所有新工作放在 `research/phase2_r5c_stress_fix_20261015/`（下称"研究目录"）。
- **并发防护。**
  - 开始时以及每次提交前，运行 `git log --oneline -5`，与自己最近一次提交对照。
  - 如果出现不是你做的提交，或有你没改过的已跟踪文件发生变化：停止编辑共享文件，记入 `notes/DECISIONS.md`，此后只按明确路径添加文件。
  - 不要使用 `git add -A` / `git add .`，不要撤销或改写别人的工作，不要使用裸 `git stash`。
- **提交与推送。**
  - 把本 prompt 作为第一个提交。
  - 每个阶段结束时提交；每次阶段提交后运行 `git push -u origin exp/phase2-r5c-stress-fix-20261015`。
  - 不推送到其他地方，不强制推送。
  - 提交信息结尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **不要修改：**
  - `TechArena_Challenge2_Team_Package/`；
  - 之前任何研究目录，包括 `phase2_r5a_stress_model_20261014`；
  - `/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original/` 中的 Challenge 1 数据（只读）。

  可以导入和复制代码，但绝不原地编辑。
- **语言与字节码。** 每个 Markdown 文档都是英文在前、中文在后，格式与本文件相同。代码注释只用英文。用 `python3 -B` 运行 Python。

## 2. 任务与现状

**任务。** 估计 4 × 102 Ah LFP 串联电池组在 CK0..CK7 = 2025-01-14、02-08、03-11、04-14、05-16、06-16、07-25、08-28 的 SOH（C/20 容量：满充后以 5.1 A 放电至组端 11.2 V，除以 102 Ah）。只公开 CK0 = 100.41 Ah。预测 CK_k 只能用 `load_dataset(data, until=CK_k)`。

**日程。**

- 第 0 月（CK0 → CK1）只有一个 45 °C 段（第 1 段）。
- 从第 1 月起，每月先是一个短的 25 °C 段，再是一个长的 45 °C 段。
- 第 3 段（45 °C，02-19 → 03-11）缺失，它的计数器跳变要到 CK2 截断之后才可见。

**锚点。** 每次检查后，电池组从近空开始充电（恒流 20.4 A，恒压 14.0 V 到 5.1 A），Q_fc,j 就是锚点 j。锚点 0 在 45 °C，锚点 1–7 在 25 °C。

**代理**（都已看过，所以每个结果都是已曝光的探索性结果）：P_k = Q_fc,k + ε0 + Δ，其中 ε0 = 100.41 − Q_fc,0，Δ ∈ {0, 0.4, 0.8}。

**V2**（分支 `exp/phase2-anchor-step-20261013` 上的提交包指向它）由最新锚点 + ε，加上同相位 45 °C 石墨台阶差分 × β 组成；CK1–CK3 回退到 M4。

| | MAE Δ0 / .4 / .8 | MAX | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | +0.217 | **+0.669** | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| 5A S_main | 0.270 / 0.326 / 0.382 | 1.134 | **−1.134** | +0.565 | −0.025 | −0.004 | −0.156 | −0.370 | +0.029 |
| 5A ENS50 | 0.158 / 0.214 / 0.270 | 0.851（Δ.8） | −0.459 | +0.617 | +0.027 | +0.112 | −0.003 | −0.266 | +0.013 |

误差单位为 pp（Δ = 0.4）。V2 与 ε 无关的 CK2–7 MAE 为 0.216，S_main 为 0.192；伪场景 MAE（k ≥ 3）分别为 0.240 和 0.131。

**第五轮 A 的应力模型 S**（`research/phase2_r5a_stress_model_20261014/`，先读它的 `FINAL_REPORT.md`）：

- 定律：L = A_cal·(τ_eff)^z + A_cyc·ah_eff，时间和吞吐都经 Arrhenius 加权（Ea 37.3 kJ/mol，z = 0.2），在相邻可见锚点对上做 MAP 拟合。
- 预测：Q̂_k = 起点 − ΔL；如果最新锚点是锚点 0，起点 = Q_CK0，否则起点 = Q_fc,k−1 + ε。

**S 已诊断出的问题（本轮必须解决）：**

1. **冷启动。** CK1 时没有任何锚点对，S 只有先验。由 Yagci 推出的先验把第 0 月的损失多算了约 1.2 Ah，CK1 误差为 −1.13 pp。也正是这一个点让 S 的 MAE 随 Δ 增大，因为只有 CK1 的起点不含 Δ。这就是 ENS50 在 Δ = 0.8 时未通过 G-proxy 的全部原因。
2. **定律形状。** 单一的 t^z 项把首月的快速磨合和存储老化混在了一起（5A 第 2 阶段：Challenge 1 电芯在停测空档里损失跳升 1.5–2.5 Ah，z = 0.2 产生不了这种跳升）。在 CK2 处，z = 0.2 少算了第 1 月（+0.57 pp），z = 0.5 略微多算（−0.21 pp）。
3. **月内信息没有用上。** S 忽略了约每 5 天一次的 45 °C 程序台阶，而 V2 用了它们。CK1 截断时，第 1 段里已经能看到 4 次这样的台阶（01-20、01-24、01-29、02-03；台阶深度 32.81 → 30.31 Ah），它们直接测量了第 0 月的损失，但 S 从来没用过。

## 3. 可复用的代码与数据

- **第五轮 A 的模块：** 把 `research/phase2_r5a_stress_model_20261014/src/stress.py` 和 `src/smodel.py` 复制到本研究的 `src/`，在副本上扩展。
  - `stress_table(op, until, ck, horizon)` 按登记的检查、缺失段和隐藏尾段规则构建应力历史。
  - `cumulative()` 给出 Arrhenius 加权的 τ_eff 和 ah_eff。
  - `StressFit` 使用只依赖 numpy 的 LM。
  - 5A 的 `stage_2/prior.json` 和 `stage_2/c1_cycles.py` 存有 Challenge 1 的逐循环摘要和先验规则。
- **第三轮 harness：** `research/phase2_round3_models_20261014/src/harness.py`。
  - 提供 `run`、`metrics`、`per_ck`、`gates_vs_v2`、`candidate_checks`、`SCENARIOS`、`BASELINES`、`QFC`、`EPS0`、`cut_op`。
  - `ctx["steps"][variant]` 存有六种台阶检测方法下的程序台阶（`t_cv_end`、`step_mean`、`setpoint_C`、逐芯台阶）。
  - 它的缓存留在本 worktree 内。
- **V2 函数：** `research/phase2_v2_phase_matched_20261013/src/v2.py`（`anchors_by_checkup`、`month_steps`、`beta_a4`、`v2`、`m4`）。
- **环境：** 研究用 `python3`（3.13，numpy、pandas、scipy、matplotlib）。候选类只能用 numpy/pandas，并且必须能在 Python 3.11 下运行：在研究目录被忽略的 `cache/venv311` 里用 `/opt/homebrew/bin/python3.11` 建 venv。

## 4. 规则

1. **协议提交之前不得出真实结果。** 每一轮设计都要先登记，再跑伪场景和冷启动场景并提交，然后只跑一次真实场景。任何用于决策的场景都排除 k = 2。
2. **选择只用伪场景和冷启动场景。** 真实的 CK1–CK7 代理每轮只评估一次，绝不用来在设计、权重或参数之间做选择。每个登记过的设计的真实结果都要报告，包括落选的。
3. **严格按登记的公式实现。** 偏离要在运行前登记。
4. **缓存键必须包含**所有会改变缓存结果的参数。
5. **因果检查比较精确浮点数。**
6. **6–7 个点只能作诊断，不是验证。** 相关性要这样措辞。
7. **5A 在真实 CK1 上的误差是已知的。** 任何只在 CK1 起作用的设计（例如"CK1 用 V2"）必须标为 `exposed-CK1`。它可以报告、可以过门槛，但它在 CK1 上的改进不能作为证据。

## 5. 评估、门槛与目标

**场景。**

- *真实*：k = 1..7。
- *伪场景*：PG1/PG2（k = 4..7）和 PC5/PC10（k = 3..7），与第三轮至 5A 相同。
- ***新增：冷启动场景 CS***（在第 0 阶段、任何设计之前登记）。它们在后面的月份里模拟 CK1 的处境。对 k = 3..7：
  - 模型只能使用锚点 k−1 及之后的数据，更早的锚点都从 `fc` 中删除。因此先验和参数拟合只能来自冷启动时可用的信息（先验 + 月内数据）；
  - 代理照常取 P_k。

  变体 CS-early：另外把运行数据截到 CK_k 前 10 天。CS 场景检验的正是 CK1 所依赖的那套机制。

**对 V2 的通用门槛**（与 5A 相同）：

| 门槛 | 规则 |
|---|---|
| G-causal | 未来数据加噪、仅用 CK1 前缀拟合时，输出的浮点数完全一致 |
| G-proxy | 每个 Δ 下 MAE 都低于 V2；MAX ≤ V2 的 MAX + 0.10 pp |
| G-epsfree | 与 ε 无关的 CK2–7 MAE ≤ V2 − 0.02 pp |
| G-robust | 在 6 种台阶检测方法中至少 5 种上 MAE（Δ = 0.4）优于 V2；不用台阶输入的模型，则要在至少 75 % 的登记变体组上优于 V2 |
| G-pseudo | 伪场景平均 MAE（k ≥ 3）比 V2 差不超过 0.02 pp |
| G-coldstart | CS 场景平均 MAE ≤ V2 在相同 CS 输入上的平均 MAE |
| G-regress | 任何检查点的绝对误差相对 V2 的增幅不超过 0.30 pp（Δ = 0.4） |
| G-impl | 只依赖 numpy/pandas 的 `MyModel` 类与研究实现相差 ≤ 0.001 pp，在 3.11 venv 中通过 sample_data 冒烟测试，完整运行 < 30 分钟，并在提交包副本上通过 `validate_submission.py` |

**大胆目标**（代理 pp；对通过全部门槛的最佳模型以及每轮登记的主模型，都要报告达成或未达成）：

| 目标 | 数值 | V2 现状 |
|---|---|---|
| T1 每个 Δ 下的 MAE | ≤ 0.15 | 0.272 / 0.216 / 0.210 |
| T2 每个 Δ 下的 MAX | ≤ 0.45 | 0.669 |
| T3 CK1 和 CK2 | Δ = 0.4 时每个 \|误差\| ≤ 0.30 | 0.217 / 0.669 |
| T4 与 ε 无关的 CK2–7 MAE | ≤ 0.15 | 0.216 |
| T5 伪场景平均 MAE（k ≥ 3） | ≤ 0.12 | 0.240 |
| T6 CS 平均 MAE | ≤ 0.20 | 在第 0 阶段测出 |

对于只改动 CK1 的设计，T3 中 CK1 那部分属于 exposed-CK1（规则 7）。

## 6. 各阶段

### 第 0 阶段——准备、复现与冷启动 harness（上限 1 小时）

- 建研究目录、`notes/STATUS.md`、`notes/DECISIONS.md` 和 `.gitignore`（`cache/`）。
- 通过复制来的模块复现 V2（0.215726 / 0.669052）、M4（0.291265），以及 5A 的 S_main 和 ENS50（Δ = 0.4 时 MAE 0.326 / 0.214）。复现不了就停止并记录原因。
- 实现 CS 和 CS-early 场景。
  - 在 `stage_0/protocol.json` 中登记。
  - 运行之前先提交。
  - 然后报告 V2、M4、S_main 和 ENS50 在这些场景上的结果。这些基线确定 T6 的参照值和 G-coldstart。

### 第 1 阶段——第一轮设计（上限 2.5 小时）

在运行任何东西之前，把下列**全部**设计登记进 `stage_1/protocol.json`。每个设计都是完整的预测器；组件只能按这里登记的方式组合。

**D1——带台阶观测的 S（"S+steps"）。** 把可见的月内 45 °C 程序台阶作为观测加入 S 的 MAP 拟合。

- 对同一月内相邻的两个可见 45 °C 台阶 i < j（主台阶方法；由于检查后暂态 τ ≈ 2.5 天，距本月检查日不足 5 天的台阶排除）：

  β_k · (s_j − s_i) = −[L(t_j) − L(t_i)] + e，e ~ N(0, σ_s²)，σ_s = 0.05 Ah。

- β_k 取该截断下 V2 的 `beta_a4(β0 = 1, τ = 1)`，早期截断时等于 1。
- 这些项加在锚点对项之上。在 CK1 时，除了先验，它们是唯一的数据。
- 变体：
  - σ_s × 0.5 和 × 2；
  - β 自由，先验 N(1.3, 0.2²)；
  - 纳入 25 °C 台阶，每月带一个自由的 25→45 °C 偏差。

**D2——两项定律（"S2"）。**

- 定律：L = A_b·(1 − exp(−τ_eff/τ_b)) + A_cal·τ_eff^0.5 + A_cyc·ah_eff，即饱和的磨合项 + √t 日历项 + 线性循环项。
- 先验来自用 5A 第 2 阶段的数据和规则（`c1_cycles.py`），把这个定律重新拟合到六枚 Challenge 1 电芯上，包括按标称温度计入的停测空档。用 jackknife SD；参数无法辨识时，像 5A 第 2 阶段的规则那样回退到由 Yagci 推出的尺度。运行之前先登记重新拟合的流程。
- 电池组拟合中自由的参数：log A_b、log A_cal、log A_cyc、o_45。τ_b 固定为先验均值；变体让它带先验自由拟合。

**D3——D1 + D2 组合（"S2+steps"）。**

**D4——集成。** 对 D 属于 {D1, D2, D3} 的每一个，构造 w·D + (1 − w)·V2；w 只用伪场景 + CS 场景，从网格 {0, 0.25, 0.5, 0.75, 1} 中选。另登记一个 w 固定为 0.5 的变体。

**D5——exposed-CK1 混合**（必须这样标注）。CK1 用 V2，从 CK2 起用 D3。要报告并过门槛；按规则 7，除非它在 CS 场景上也胜出，否则不能被选为主模型。

**选择规则**（要登记）：在 D1–D4 中，选 Δ = 0.4 时伪场景 MAE 与 CS MAE 平均值最低、且通过 G-pseudo 和 G-coldstart 的设计，作为第一轮主模型。平局时选更简单的设计。

**顺序：** 提交协议 → 跑伪场景 + CS 场景并提交 → 提交选择结果 → 跑真实场景 → 提交门槛、目标和各检查点表。

### 第 2 阶段——第二、三轮设计（合计上限 3 小时；可选）

只有在没有模型通过全部门槛，或者通过了门槛但没达成 T1–T5 时，才开新的一轮。

- 每轮必须先写一份**书面诊断**，只依据伪场景和 CS 结果以及物理，绝不依据真实代理。例如：早期 β 不对、暂态泄漏、定律形状在 CS 上的表现。
- 然后最多登记四个新设计，顺序和选择规则与第一轮相同。
- 总共最多三轮。无论结果如何，第三轮之后停止。

### 第 3 阶段——候选与打包检查（上限 1 小时）

只对通过**全部**门槛的那一个最佳模型做；按该轮登记的选择规则选，如果多轮都有通过的，取最后一轮的主模型。

- 在 `candidate_model/` 中写一个只依赖 numpy/pandas 的 `MyModel`。
- 在 Python 3.13 和 3.11 venv 中运行 `harness.candidate_checks`（G-causal + G-impl）。
- 把 `TechArena_Challenge2_Team_Package/` 复制到研究目录被忽略的 `cache/package_copy/`，在副本中接入候选并运行 `validate_submission.py`。
- 记录结果。**绝不触碰真实的提交包。**

### 第 4 阶段——最终报告（上限 0.5 小时）

**`FINAL_REPORT.md`**（双语，结论在前）包含：

1. 每个登记设计和变体对比 V2、M4、S_main、ENS50 的表（各 Δ 的 MAE、MAX、与 ε 无关的 MAE、伪场景、CS、门槛）；
2. 各检查点误差；
3. T1–T6 逐条结论；
4. 冷启动问题是否被修复、靠什么修复的、为什么；把因果证据（伪场景 / CS）和已曝光的结果分开；
5. 候选结论和只用于排行榜的 SOH 表；
6. 对用户是否应考虑在提交中替换 V2 的建议。**自己不做任何改动。**
7. 风险：曝光、单个电池组、ε 与检查后恢复（第四轮：后期最多约 0.9 Ah）、先验迁移；
8. 精确的复现命令。

另写一份双语 **`README.md`**。

## 7. 顺序与上限

| 顺序 | 阶段 | 上限 |
|---|---|---|
| 0 | 准备、复现、CS harness | 1 小时 |
| 1 | 第一轮设计 | 2.5 小时 |
| 2 | 第二、三轮设计（可选） | 3 小时 |
| 3 | 候选 + 打包检查 | 1 小时 |
| 4 | 最终报告 | 0.5 小时 |

**停止规则。**

- 第 0 阶段复现不了 V2 或 5A，就停止。
- 未通过 G-causal 的候选直接拒绝。
- 第三轮之后停止设计，即使一个目标都没达成。

## 8. 禁止事项（汇总）

- **因果性。** 预测 CK_k 不得用 CK_k 之后的数据。公开的分段日程是唯一例外，与 5A 相同。
- **选择。** 选择绝不使用真实代理。看到结果后不得更改登记的主配置。不做未登记的重试。最多三轮设计。
- **代理。** 绝不把代理当成隐藏真值；绝不从外部来源重建 CK1–CK7。
- **文件与 git。** 不修改提交包和之前的研究。只推送到本分支，不强制推送。
- **不提问。** 绝不向用户提问；记录决策并继续。
