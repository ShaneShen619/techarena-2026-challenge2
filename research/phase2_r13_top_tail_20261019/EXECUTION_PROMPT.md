<a id="en"></a>

# Round 13: Top-of-Charge Drift Bound — How Much Can the Anchor's CV Tail Move ε? — Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-19. This document is self-contained. The English text is the execution text. The Chinese section is a translation for the reader; where the two differ, the English governs.

The work is split into **work packages WP0–WP3**. Each has its own *Done* list and can be run as a separate `/goal`.
- WP0, WP1, WP2 and WP3 run in this order. `FINAL_REPORT.md` comes last.
- This round is independent of rounds 12 and 14 and may run in parallel with them, in its own worktree.

## 0. Mode of work (all work packages)

- **Unattended.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Restarts.** Keep `notes/STATUS.md` current after every step: WP, done, next, last commit. On a restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume from there. Never redo a finished WP or step.
- **Honesty over targets.** "Not identifiable" is a valid outcome. This round produces **a bound, a decision and a recommendation**. It never changes the submission, and it never computes an error against the Challenge 2 proxy labels P_k.
- **Done for any WP** means the common criteria below, plus that WP's own list:
  1. the registered protocol (`wp1/protocol.json` + `wp1/protocol.sha256`, plus the registered code) was committed **before** any evaluation output;
  2. its bilingual `wpN/REPORT.md` exists, conclusions first;
  3. `notes/STATUS.md` marks the WP done or exited, with a one-line result;
  4. every commit is pushed to `origin exp/phase2-r13-top-tail-20261019`, and `git status` shows no uncommitted study files.
- **Global Done:** WP0–WP3 are each done or exited by a registered rule; `FINAL_REPORT.md`, `README.md` and `wp3/R13_RESULT.json` exist (Markdown bilingual, conclusions first); common criteria 3–4 hold.

## 1. Workspace, isolation, git

- **Worktree and branch.** Create them in WP0 if missing; the step is idempotent.
  - Base: `6525edf` on `exp/phase2-anchor-step-20261013`. If the branch tip is newer, use the tip and record its hash.
  - Create: `git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1019_r13_top_tail -b exp/phase2-r13-top-tail-20261019 <base>`. If it already exists, check that its history contains `<base>` and reuse it.
  - Work only in `/Users/shane/Desktop/Arena_1019_r13_top_tail`. The study directory is `research/phase2_r13_top_tail_20261019/`.
- **This prompt** lives, uncommitted, at `/Users/shane/Desktop/Arena_1013_model/research/phase2_r13_top_tail_20261019/R13_EXECUTION_PROMPT.md`. Copy it to `research/phase2_r13_top_tail_20261019/EXECUTION_PROMPT.md` in your worktree and commit it first. Do not commit, move or delete the original.
- **Read-only sources.** Read earlier rounds with `git -C /Users/shane/Desktop/Arena_1013_model show <ref>:<path>`, copy what you use into `sources/`, and record each copy's ref, path and SHA256 in `sources/SOURCES.md`:
  - round 11 `exp/phase2-r11-eps-transfer-20261018`, under `research/phase2_r11_eps_transfer_20261018/`: `FINAL_REPORT.md`, `wp4/pack_drivers.csv`, `src/wp4_pack.py` (CV fit), `src/drift.py` ("SUB + drift d", copied from round 7), `wp5/R12_HANDOFF.json`;
  - round 8 `exp/phase2-r8-error-table-20261017`, under `research/phase2_r8_error_table_20261017/`: `DATA_DICTIONARY.md`, `outputs/table_events.csv`, `outputs/table_anchors.csv`;
  - round 5B `exp/phase2-r5b-electrode-model-20261014`: `research/phase2_r5b_electrode_model_20261014/FINAL_REPORT.md`.
- **Challenge data:** `TechArena_Challenge2_Team_Package/data/` in your own worktree, and `CHALLENGE2_DESCRIPTION.pdf`.
- **Concurrency guard.** Run `git log --oneline -5` at the start and before every commit. On an unexpected change, stop editing shared files, record it, and add files by explicit path only. Never use `git add -A` / `git add .`, never rewrite others' work, never use a bare `git stash`. One session per worktree.
- **Commits.** Commit at the end of every step, then `git push -u origin exp/phase2-r13-top-tail-20261019`. Never push elsewhere, never force. End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify** any `TechArena_Challenge2_Team_Package/` directory, any earlier study directory, or anything outside this worktree. Model variants are copies under the git-ignored `cache/variants/`.
- **Language and bytecode.** Markdown English first, Chinese second. Code comments in English. Run Python with `python3 -B`. No downloads.

## 2. Context

**Task.** Estimate the SOH of a 4 × 102 Ah LFP series pack on CK0..CK7. SOH is the C/20 capacity (5.1 A to pack 11.2 V "after a full charge"; the full-charge protocol is not stated) divided by 102 Ah. Only CK0 = 100.41 Ah is released. The causal cut is `load_dataset(data, until=CK_k)`.

**Where this round sits.** With charge contents in Ah:

```
ε_k = C20_k − Q_fc,k = (F^CK_k − F^A_k) + (B_k − S_k)
```

- F^CK is the checkup's top, F^A the anchor's top (14.0 V CV ended at ≈ 5.1 A), B the anchor's start and S the end of the C/20 discharge.
- The **level** of ε (EPS_EXTRA) is round 12. The **path** part of the top term (from-empty vs top-up charge) is round 14.
- **This round bounds the tail part of the top drift:** how much F^CK_k − F^A_k can change across anchors because the anchor's CV phase and top state change with ageing.
- Define fade_k = Q_fc,1 − Q_fc,k and d_tail = d(Δε_top,tail)/d(fade). Report the effect at CK7 as d_tail × 8.2 Ah, the pack's fade from CK0 to CK7, as in round 11.

**What round 11 found.**
- In LIC, the ε drift sits in T_path and tracks the top state of the 1C charge: CV duration (ρ −0.96), a lower end current and a higher relaxed top voltage.
- In our pack:
  - CV Ah rises from 1.17 to 1.44 Ah and the CV decay constant τ from 179 to 217 s;
  - but the end current is fixed at 5.094–5.100 A, and the relaxed top voltage 30 min after the CV end is flat (13.439 → 13.435 V).
  - The unregistered reading is that the drift is ≈ 0.
- The transfer bound is d ∈ [−0.036, +0.052] Ah/Ah (O3).
- The handoff constraints are: no absolute electrode model (round 5B: 8–10 Ah spans); model one Δε term at a time with the pack's own data; identifiability first, an envelope below 0.3 Ah or exit.

**Facts to re-verify in WP0.**
- **Round 11's CV fit.** It fitted I(t) = I∞ + A·e^(−t/τ). For anchor 1 it gave τ = 179 s with I∞ = 4.23 A, an asymptote close to the 5.1 A cutoff. So the observed CV window does not by itself show a decay to zero.
- **CV window.** The anchors' CV phase lasts about 7 min, i.e. about 40 samples at 10 s. Top-up CV phases last 2–9 min. Anchor 0 (45 °C) has a CV phase of only 36 s, where round 11's fit fails.
- **Events.** There are 41 full charges: 8 from empty, 33 top-ups.
- **CK0's start.** The CK0 C/20 discharge starts at 13.590 V under 5.1 A load, with cell3 at 3.511 V. Cell3 also sets anchor 0's top (3.53 V 30 min after the CV end). The pack enters each checkup at 13.1–13.3 V.
- **Back-of-envelope (exposed, from the conversation that wrote this prompt).**
  - If the CV current decayed exponentially to zero, the charge beyond 5.1 A would be I_end·τ ≈ 0.25 Ah (anchor 1) → 0.31 Ah (anchor 7). Even a checkup charged until I → 0 would then see only ≈ 0.05 Ah of tail drift.
  - This is a **hypothesis to test**, not a result. A diffusion-type tail (I ∝ t^(−1/2)) has no finite limit, so it needs time-limited scenarios.

**SUB.** `my_model/model_template.py` at the base commit. "SUB + drift d" is round 11's `src/drift.py` (copied from round 7 WP3). Copy it; do not re-derive it.

## 3. Work packages

### WP0 — Setup and fact sheet

1. Create or reuse the worktree; write `notes/STATUS.md`, `notes/DECISIONS.md` and `sources/SOURCES.md`; commit this prompt; copy the sources.
2. Run SUB with the package CLI and save `wp0/SUB_SOH.csv`.
3. Write `wp0/cv_catalogue.csv`, one row per full charge (anchors and top-ups):
   - segment, set point, type (A/T);
   - CV start (first sample with pack ≥ 13.95 V and I < 19.9 A) and CV end;
   - number of CV samples, CV duration, CV Ah, I at the CV end;
   - pack and cell voltages at the CV end and 30 min later (just before the pulse);
   - temperature at the CV end;
   - the pulse resistance (round 8's `R_pulse_mOhm` where available).
4. Write `wp0/FACTS.md`, verifying each bullet of §2 "Facts to re-verify" with a number from the data.

Do not fit any tail model in WP0.

**Done:** worktree, notes, sources, `wp0/SUB_SOH.csv`, `wp0/cv_catalogue.csv` and `wp0/FACTS.md` are committed and pushed.

### WP1 — Registration (no fits on challenge data)

Register the following in `wp1/protocol.json`, and implement it in `src/tail.py`.
- Test the code only on synthetic CV traces (`src/test_tail.py`): each model must recover its own generating parameters, and the tail charge must be recovered to within 0.01 Ah.
- Commit protocol, hash, code and test before any WP2 output.

- **Tail models,** fitted by least squares on I(t) over the CV phase, with t measured from the CV start:
  - **M1:** I = A·e^(−t/τ), decaying to zero;
  - **M2:** I = I∞ + A·e^(−t/τ), with I∞ ∈ [0, I_end];
  - **M3:** I = A·(t + t0)^(−1/2), a diffusion-like tail with t0 ≥ 0;
  - **M4:** I = A1·e^(−t/τ1) + A2·e^(−t/τ2), with τ2 ≥ 3·τ1.
- **Admission per charge:** RMSE ≤ 0.15 A, and the mean residual over the last third of the CV phase is ≤ 0.10 A in magnitude. Report non-admitted (charge, model) pairs.
- **Checkup-termination scenarios.** The CV stays at 14.0 V in all of them:
  - **C1:** the same termination as the anchor (5.1 A). The tail is 0 by construction.
  - **C2 / C3 / C4:** current cutoff at 2.55 A / 1.02 A / 0.51 A.
  - **C5 / C6 / C7:** a CV hold of 30 / 60 / 120 min beyond the anchor's 5.1 A point.
  - Q_tail(k; M, C) = ∫ I_M dt from the anchor's CV end to the scenario's end. If a current cutoff is never reached (M2 with I∞ > I_cut), that (M, C) pair is "undefined"; record it and use C5–C7 for that model.
- **Tail drift per anchor:** Δ_tail(k; M, C) = Q_tail(k) − Q_tail(1), for k = 2..7 (25 °C anchors). Anchor 0 is excluded (45 °C, 36 s CV).
  - d_tail(M, C) = Theil–Sen slope of Δ_tail(k) against fade_k, with leave-one-anchor-out (LOO) range.
- **Independent top-state estimators.** These test the "towards equilibrium" end directly.
  - **T2 (relaxed voltage).** ΔF^A_V(k) = (V30_k − V30_1)/s_top, contributing Δε = −ΔF^A_V(k).
    - s_top is the dV/dQ of the CK0 pack curve over discharged Ah ∈ [0.5, 2.0], with sensitivity windows [0.25, 1.0] and [1.0, 3.0].
    - Use per-cell versions with per-cell CK0 slopes. Report which cell is highest at each anchor's top.
  - **T3 (resistance).** ΔF^A_R(k) = −5.1·(R_k − R_1)/s_top, with R the pack pulse resistance at the top. This is a consistency check only.
  - d_T2 and d_T3: Theil–Sen slopes against fade_k, with LOO ranges.
- **Top-ups as a cross-check.** Fit M1–M4 to every 25 °C top-up as well. Report Q_tail per month (median over the month's top-ups) as a second, denser series. It is not used in the decision, because top-ups differ in path.
- **Descriptive CK0 comparison.** Compare CK0's initial per-cell voltages under 5.1 A with each anchor's per-cell voltages at the CV end and with the per-cell voltages under the 20 A pulse after rest: which cell limits the top in each case? Not gating.
- **Decision rules (copy verbatim):**
  - **Admitted set A** = all (M, C) pairs with at least 5 of the 6 anchors k = 2..7 admitted and defined, plus T2 (main window), plus C1 (≡ 0).
  - **Envelope** = max − min over A of the median d·8.2 Ah.
  - **Identifiability:** envelope ≤ 0.30 Ah. Otherwise the outcome is **O3 "not identifiable"**: report the envelope and exit WP3 after writing the result.
  - **O1 "tail drift small":** every member of A has |median d·8.2| ≤ 0.10 Ah, and every LOO range lies within ±0.15 Ah. This closes the tail part. SUB is unchanged, and the top-tail motivation for P_drift is removed.
  - **O2 "tail drift material":** identifiable, all members of A except C1 have the same sign, and their median |d·8.2| > 0.10 Ah. Candidate "SUB + d_tail" (d_tail = median over A without C1) is leaderboard-only.
  - **O3 "inconclusive":** any other case.
  - No rule uses P_k or proxy errors.

**Done:** protocol, hash, registered code with passing synthetic tests, and `wp1/REPORT.md` (with a "what each outcome would mean" table) are committed and pushed.

### WP2 — Measurements

- Fit all models to all anchors and top-ups. Save `wp2/fits.csv` (parameters, RMSE, admission), `wp2/tails.csv` (Q_tail and Δ_tail for every k, M, C) and `wp2/top_state.csv` (T2 and T3, per cell and pack).
- Make two figures:
  - the CV current of every anchor with each admitted model's fit and extrapolation;
  - Δ_tail(k) and −ΔF^A_V(k) against fade.
- **Answer the exposed back-of-envelope explicitly:** what is I_end·τ under M1 for anchors 1 and 7, and does M1 pass admission?

**Done:** fits, tails, top-state tables, figures and `wp2/REPORT.md` are committed and pushed.

### WP3 — Envelope, decision and hand-off

1. Apply the registered rules: envelope, identifiability, O1/O2/O3.
2. Save `wp3/SOH_variants.csv` (leaderboard-only, never scored against proxies): SUB, and SUB + d for d ∈ {min over A, median, max over A}, built with the copied `drift.py`.
3. Write `wp3/R13_RESULT.json` for rounds 14 and 15: outcome, admitted set, envelope, d_tail (median and range), T2/T3 slopes, and the per-anchor table.
4. Write `wp3/REPORT.md`, then `FINAL_REPORT.md` and `README.md`. Conclusions first, plus a per-checkup SOH table of SUB vs SUB + d_tail.

**Done:** the decision, `wp3/SOH_variants.csv`, `wp3/R13_RESULT.json`, `wp3/REPORT.md`, `FINAL_REPORT.md` and `README.md` are committed and pushed.

---

<a id="zh"></a>

# 第 13 轮：充电顶部漂移的上界——锚点的 CV 尾巴能让 ε 移动多少？——执行 Prompt

> [English](#en) · 中文

写于 2026-10-19。本文档自成一体。英文部分是执行文本，中文部分是供读者阅读的译文；两者不一致时以英文为准。

工作分为**工作包 WP0–WP3**。每个工作包都有自己的"完成"清单，可以作为单独的 `/goal` 运行。
- WP0、WP1、WP2、WP3 按顺序运行。`FINAL_REPORT.md` 最后写。
- 本轮与第 12、14 轮互相独立，可以在各自的工作树中并行运行。

## 0. 工作方式（所有工作包）

- **无人值守。** 永远不要停下来提问。遇到未决问题时，选择符合本文全部规则的最保守做法，记入 `notes/DECISIONS.md`，然后继续。
- **重启。** 每完成一步就更新 `notes/STATUS.md`：当前工作包、已完成、下一步、最后一次提交。重启时先读 `notes/STATUS.md` 和 `notes/DECISIONS.md`，从断点继续。已完成的工作包或步骤不要重做。
- **诚实优先于目标。** "无法识别"是有效结果。本轮产出的是**一个上界、一个决策和一条建议**。本轮不改动提交，也不针对 Challenge 2 代理标签 P_k 计算任何误差。
- **任一工作包的"完成"**指满足下列通用条件，以及该工作包自己的清单：
  1. 登记协议（`wp1/protocol.json` + `wp1/protocol.sha256`，以及登记的代码）在任何评估输出**之前**已提交；
  2. 有中英双语的 `wpN/REPORT.md`，结论在前；
  3. `notes/STATUS.md` 把该工作包标为完成或退出，并附一行结果；
  4. 每次提交都已推送到 `origin exp/phase2-r13-top-tail-20261019`，且 `git status` 中没有未提交的研究文件。
- **全局完成：** WP0–WP3 各自完成或按登记规则退出；`FINAL_REPORT.md`、`README.md` 和 `wp3/R13_RESULT.json` 均存在（Markdown 双语，结论在前）；通用条件 3–4 成立。

## 1. 工作区、隔离与 git

- **工作树和分支。** 在 WP0 中按需创建，此步骤可重复执行。
  - 基点：`exp/phase2-anchor-step-20261013` 上的 `6525edf`。如果分支末端更新，就用末端，并记录其哈希。
  - 创建：`git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1019_r13_top_tail -b exp/phase2-r13-top-tail-20261019 <base>`。如果已存在，确认其历史包含 `<base>` 后复用。
  - 只在 `/Users/shane/Desktop/Arena_1019_r13_top_tail` 中工作。研究目录为 `research/phase2_r13_top_tail_20261019/`。
- **本 prompt** 目前未提交，位于 `/Users/shane/Desktop/Arena_1013_model/research/phase2_r13_top_tail_20261019/R13_EXECUTION_PROMPT.md`。把它复制到你工作树中的 `research/phase2_r13_top_tail_20261019/EXECUTION_PROMPT.md`，并作为第一次提交。不要提交、移动或删除原文件。
- **只读来源。** 用 `git -C /Users/shane/Desktop/Arena_1013_model show <ref>:<path>` 读取之前各轮的文件，把用到的复制到 `sources/`，并在 `sources/SOURCES.md` 中记录每个副本的引用、路径和 SHA256：
  - 第 11 轮 `exp/phase2-r11-eps-transfer-20261018`，位于 `research/phase2_r11_eps_transfer_20261018/` 下：`FINAL_REPORT.md`、`wp4/pack_drivers.csv`、`src/wp4_pack.py`（CV 拟合）、`src/drift.py`（"SUB + drift d"，从第 7 轮复制而来）、`wp5/R12_HANDOFF.json`；
  - 第 8 轮 `exp/phase2-r8-error-table-20261017`，位于 `research/phase2_r8_error_table_20261017/` 下：`DATA_DICTIONARY.md`、`outputs/table_events.csv`、`outputs/table_anchors.csv`；
  - 第 5B 轮 `exp/phase2-r5b-electrode-model-20261014`：`research/phase2_r5b_electrode_model_20261014/FINAL_REPORT.md`。
- **赛题数据：** 你自己工作树中的 `TechArena_Challenge2_Team_Package/data/`，以及 `CHALLENGE2_DESCRIPTION.pdf`。
- **并发保护。** 开始时以及每次提交前运行 `git log --oneline -5`。遇到意外改动时，停止编辑共享文件，记录下来，之后只按明确路径添加文件。不要用 `git add -A` / `git add .`，不要改写他人的工作，不要用不带参数的 `git stash`。一个工作树同时只开一个会话。
- **提交。** 每一步结束时提交，然后运行 `git push -u origin exp/phase2-r13-top-tail-20261019`。不要推送到其他地方，不要强制推送。每条提交信息的末尾加上 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **不得修改**任何 `TechArena_Challenge2_Team_Package/` 目录、之前各轮的研究目录或本工作树之外的任何东西。模型变体以副本形式放在 git 忽略的 `cache/variants/` 下。
- **语言与字节码。** Markdown 先英文后中文。代码注释用英文。运行 Python 时用 `python3 -B`。不下载任何东西。

## 2. 背景

**任务。** 估计一个 4 × 102 Ah LFP 串联电池组在 CK0..CK7 的 SOH。SOH 是 C/20 容量（"满充后"以 5.1 A 放电到电池组 11.2 V；满充协议没有说明）除以 102 Ah。只公布了 CK0 = 100.41 Ah。因果截断为 `load_dataset(data, until=CK_k)`。

**本轮的位置。** 以 Ah 计的电荷量：

```
ε_k = C20_k − Q_fc,k = (F^CK_k − F^A_k) + (B_k − S_k)
```

- F^CK 是检查的顶部，F^A 是锚点的顶部（14.0 V CV 在约 5.1 A 处结束），B 是锚点的起点，S 是 C/20 放电的终点。
- ε 的**水平**（EPS_EXTRA）是第 12 轮的内容。顶部项中的**路径**部分（从空充满与补电的区别）是第 14 轮的内容。
- **本轮给顶部漂移中的尾巴部分定界：**由于锚点的 CV 段和顶部状态随老化变化，F^CK_k − F^A_k 在不同锚点之间能变化多少。
- 定义 fade_k = Q_fc,1 − Q_fc,k，d_tail = d(Δε_top,tail)/d(fade)。与第 11 轮一致，CK7 处的影响报告为 d_tail × 8.2 Ah，即电池组从 CK0 到 CK7 的衰减量。

**第 11 轮的发现。**
- 在 LIC 中，ε 漂移位于 T_path，并跟随 1C 充电的顶部状态：CV 时长（ρ −0.96）、更低的末电流、更高的静置顶部电压。
- 在我们的电池组中：
  - CV 电量从 1.17 升到 1.44 Ah，CV 衰减常数 τ 从 179 升到 217 s；
  - 但末电流固定在 5.094–5.100 A，CV 结束 30 min 后的静置顶部电压持平（13.439 → 13.435 V）。
  - 未登记的解读是漂移约为 0。
- 迁移得到的界为 d ∈ [−0.036, +0.052] Ah/Ah（O3）。
- 交接的约束是：不做绝对电极模型（第 5B 轮：范围 8–10 Ah）；每次只用电池组自身的数据为一个 Δε 分项建模；先过识别门，包络小于 0.3 Ah，否则退出。

**需在 WP0 重新核实的事实。**
- **第 11 轮的 CV 拟合。** 它拟合的是 I(t) = I∞ + A·e^(−t/τ)。锚点 1 得到 τ = 179 s、I∞ = 4.23 A，渐近值接近 5.1 A 的截止电流。所以单看观测到的 CV 窗口，并不能看出电流衰减到零。
- **CV 窗口。** 锚点的 CV 段约 7 min，即 10 s 采样下约 40 个样本。补电的 CV 段为 2–9 min。锚点 0（45 °C）的 CV 段只有 36 s，第 11 轮的拟合在这里失败。
- **事件。** 共 41 次满充：8 次从空开始，33 次补电。
- **CK0 的起点。** CK0 的 C/20 放电在 5.1 A 负载下从 13.590 V 开始，cell3 为 3.511 V。锚点 0 的顶部也是由 cell3 决定的（CV 结束 30 min 后为 3.53 V）。电池组进入每次检查时为 13.1–13.3 V。
- **粗算（已曝光，来自编写本 prompt 的对话）。**
  - 如果 CV 电流按指数衰减到零，5.1 A 之后还能充入的电量为 I_end·τ ≈ 0.25 Ah（锚点 1）→ 0.31 Ah（锚点 7）。那么即使检查一直充到 I → 0，尾巴漂移也只有约 0.05 Ah。
  - 这是一个**待检验的假设**，不是结果。扩散型尾巴（I ∝ t^(−1/2)）没有有限的极限，需要用限时情景来处理。

**SUB。** 基点提交上的 `my_model/model_template.py`。"SUB + drift d"用第 11 轮的 `src/drift.py`（从第 7 轮 WP3 复制而来）。复制它，不要重新推导。

## 3. 工作包

### WP0 — 准备与事实清单

1. 创建或复用工作树；写 `notes/STATUS.md`、`notes/DECISIONS.md` 和 `sources/SOURCES.md`；提交本 prompt；复制来源文件。
2. 用包的 CLI 运行 SUB，保存 `wp0/SUB_SOH.csv`。
3. 写 `wp0/cv_catalogue.csv`，每次满充一行（锚点和补电）：
   - 所在段、设定温度、类型（A/T）；
   - CV 开始（第一个电池组 ≥ 13.95 V 且 I < 19.9 A 的样本）和 CV 结束；
   - CV 样本数、CV 时长、CV 电量、CV 结束时的电流；
   - CV 结束时和 30 min 后（脉冲之前）的电池组电压与各电芯电压；
   - CV 结束时的温度；
   - 脉冲电阻（有第 8 轮的 `R_pulse_mOhm` 时取之）。
4. 写 `wp0/FACTS.md`，用数据中的数字核实第 2 节"需在 WP0 重新核实的事实"的每一条。

WP0 中不拟合任何尾巴模型。

**完成：** 工作树、记录文件、sources、`wp0/SUB_SOH.csv`、`wp0/cv_catalogue.csv` 和 `wp0/FACTS.md` 均已提交并推送。

### WP1 — 登记（不在赛题数据上做任何拟合）

把以下内容登记到 `wp1/protocol.json`，并实现为 `src/tail.py`。
- 只在合成 CV 曲线上测试代码（`src/test_tail.py`）：每个模型都要找回自己的生成参数，尾巴电量的误差要在 0.01 Ah 以内。
- 在任何 WP2 输出之前，提交协议、哈希、代码和测试。

- **尾巴模型**，在 CV 段上对 I(t) 做最小二乘拟合，t 从 CV 开始计：
  - **M1：** I = A·e^(−t/τ)，衰减到零；
  - **M2：** I = I∞ + A·e^(−t/τ)，I∞ ∈ [0, I_end]；
  - **M3：** I = A·(t + t0)^(−1/2)，扩散型尾巴，t0 ≥ 0；
  - **M4：** I = A1·e^(−t/τ1) + A2·e^(−t/τ2)，τ2 ≥ 3·τ1。
- **每次充电的准入条件：** RMSE ≤ 0.15 A，且 CV 段最后三分之一的平均残差绝对值 ≤ 0.10 A。报告未准入的（充电, 模型）组合。
- **检查终止情景。** 所有情景中 CV 都保持在 14.0 V：
  - **C1：** 与锚点相同的终止条件（5.1 A）。按定义尾巴为 0。
  - **C2 / C3 / C4：** 电流截止在 2.55 A / 1.02 A / 0.51 A。
  - **C5 / C6 / C7：** 在锚点 5.1 A 点之后再恒压 30 / 60 / 120 min。
  - Q_tail(k; M, C) = 从锚点 CV 结束到情景终点对 I_M 的积分。如果电流截止永远达不到（M2 且 I∞ > I_cut），该（M, C）组合记为"未定义"，记录下来，该模型改用 C5–C7。
- **每个锚点的尾巴漂移：** Δ_tail(k; M, C) = Q_tail(k) − Q_tail(1)，k = 2..7（25 °C 锚点）。锚点 0 排除（45 °C，CV 仅 36 s）。
  - d_tail(M, C) = Δ_tail(k) 对 fade_k 的 Theil–Sen 斜率，附留一锚点（LOO）范围。
- **独立的顶部状态估计。** 它们直接检验"趋向平衡"那一端。
  - **T2（静置电压）。** ΔF^A_V(k) = (V30_k − V30_1)/s_top，对 Δε 的贡献为 −ΔF^A_V(k)。
    - s_top 是 CK0 电池组曲线在放电 Ah ∈ [0.5, 2.0] 上的 dV/dQ，敏感性窗口为 [0.25, 1.0] 和 [1.0, 3.0]。
    - 同时做各电芯版本，用各电芯的 CK0 斜率。报告每个锚点顶部电压最高的是哪个电芯。
  - **T3（电阻）。** ΔF^A_R(k) = −5.1·(R_k − R_1)/s_top，R 为顶部的电池组脉冲电阻。只作一致性检查。
  - d_T2 和 d_T3：对 fade_k 的 Theil–Sen 斜率，附 LOO 范围。
- **用补电做交叉检验。** 对每次 25 °C 补电也拟合 M1–M4。按月报告 Q_tail（当月补电的中位数），作为第二条更密的序列。它不进入决策，因为补电的路径不同。
- **CK0 描述性对比。** 把 CK0 在 5.1 A 下的初始各电芯电压，与各锚点 CV 结束时的各电芯电压、以及静置后 20 A 脉冲下的各电芯电压对比：每种情况下由哪个电芯限制顶部？不作为门槛。
- **决策规则（原样照抄）：**
  - **准入集 A** = 在 k = 2..7 的 6 个锚点中至少 5 个准入且有定义的全部（M, C）组合，加上 T2（主窗口），再加上 C1（≡ 0）。
  - **包络** = A 中各成员 d·8.2 Ah 中位数的最大值减最小值。
  - **可识别性：** 包络 ≤ 0.30 Ah。否则结果为 **O3"无法识别"**：报告包络，写完结果后退出 WP3。
  - **O1"尾巴漂移小"：** A 中每个成员的 |d·8.2 中位数| ≤ 0.10 Ah，且每个 LOO 范围都在 ±0.15 Ah 以内。尾巴部分就此结案。SUB 不变，P_drift 来自顶部尾巴的动机被排除。
  - **O2"尾巴漂移显著"：** 可识别，除 C1 外 A 的所有成员同号，且其 |d·8.2| 的中位数 > 0.10 Ah。候选"SUB + d_tail"（d_tail = 不含 C1 的 A 的中位数）只用于排行榜。
  - **O3"无定论"：** 其他所有情况。
  - 以上规则都不使用 P_k 或代理误差。

**完成：** 协议、哈希、通过合成测试的登记代码，以及 `wp1/REPORT.md`（含"各结果意味着什么"表）均已提交并推送。

### WP2 — 测量

- 对所有锚点和补电拟合所有模型。保存 `wp2/fits.csv`（参数、RMSE、是否准入）、`wp2/tails.csv`（每个 k、M、C 的 Q_tail 和 Δ_tail）和 `wp2/top_state.csv`（T2 和 T3，分电芯和电池组）。
- 画两张图：
  - 每个锚点的 CV 电流，以及每个准入模型的拟合和外推；
  - Δ_tail(k) 与 −ΔF^A_V(k) 随衰减的变化。
- **明确回应已曝光的粗算：** 在 M1 下，锚点 1 和 7 的 I_end·τ 各是多少？M1 是否通过准入？

**完成：** 拟合表、尾巴表、顶部状态表、图和 `wp2/REPORT.md` 均已提交并推送。

### WP3 — 包络、决策与交接

1. 应用登记的规则：包络、可识别性、O1/O2/O3。
2. 保存 `wp3/SOH_variants.csv`（只用于排行榜，绝不与代理对比打分）：SUB，以及 d ∈ {A 中的最小值、中位数、A 中的最大值} 时的 SUB + d，用复制来的 `drift.py` 构造。
3. 写 `wp3/R13_RESULT.json` 供第 14、15 轮使用：结果、准入集、包络、d_tail（中位数和范围）、T2/T3 斜率，以及逐锚点表。
4. 写 `wp3/REPORT.md`，然后写 `FINAL_REPORT.md` 和 `README.md`。结论在前，并附 SUB 与 SUB + d_tail 在每个检查点的 SOH 对比表。

**完成：** 决策、`wp3/SOH_variants.csv`、`wp3/R13_RESULT.json`、`wp3/REPORT.md`、`FINAL_REPORT.md` 和 `README.md` 均已提交并推送。
