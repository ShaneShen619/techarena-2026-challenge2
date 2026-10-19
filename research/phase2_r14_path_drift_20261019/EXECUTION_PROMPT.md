<a id="en"></a>

# Round 14: Path Drift on Our Own Pack — Does the From-Empty vs Top-Up Top Difference Change with Age? — Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-19. This document is self-contained. The English text is the execution text. The Chinese section is a translation for the reader; where the two differ, the English governs.

The work is split into **work packages WP0–WP3**. Each has its own *Done* list and can be run as a separate `/goal`.
- WP0, WP1, WP2 and WP3 run in this order. `FINAL_REPORT.md` comes last.
- This round is independent of rounds 12 and 13 and may run in parallel with them, in its own worktree. Where it reuses their registered code or results, the rules below say how.

## 0. Mode of work (all work packages)

- **Unattended.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Restarts.** Keep `notes/STATUS.md` current after every step: WP, done, next, last commit. On a restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume from there. Never redo a finished WP or step.
- **Honesty over targets.** "Not identifiable" and "inconclusive" are valid outcomes. This round produces **a pack-native estimate of the path drift, a decision and a recommendation**. It never changes the submission, and it never computes an error against the Challenge 2 proxy labels P_k.
- **Done for any WP** means the common criteria below, plus that WP's own list:
  1. the registered protocol (`wp1/protocol.json` + `wp1/protocol.sha256`, plus the registered code) was committed **before** any evaluation output;
  2. its bilingual `wpN/REPORT.md` exists, conclusions first;
  3. `notes/STATUS.md` marks the WP done or exited, with a one-line result;
  4. every commit is pushed to `origin exp/phase2-r14-path-drift-20261019`, and `git status` shows no uncommitted study files.
- **Global Done:** WP0–WP3 are each done or exited by a registered rule; `FINAL_REPORT.md`, `README.md` and `wp3/R14_RESULT.json` exist (Markdown bilingual, conclusions first); common criteria 3–4 hold.

## 1. Workspace, isolation, git

- **Worktree and branch.** Create them in WP0 if missing; the step is idempotent.
  - Base: `6525edf` on `exp/phase2-anchor-step-20261013`. If the branch tip is newer, use the tip and record its hash.
  - Create: `git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1019_r14_path_drift -b exp/phase2-r14-path-drift-20261019 <base>`. If it already exists, check that its history contains `<base>` and reuse it.
  - Work only in `/Users/shane/Desktop/Arena_1019_r14_path_drift`. The study directory is `research/phase2_r14_path_drift_20261019/`.
- **This prompt** lives, uncommitted, at `/Users/shane/Desktop/Arena_1013_model/research/phase2_r14_path_drift_20261019/R14_EXECUTION_PROMPT.md`. Copy it to `research/phase2_r14_path_drift_20261019/EXECUTION_PROMPT.md` in your worktree and commit it first. Do not commit, move or delete the original.
- **Read-only sources.** Read earlier rounds with `git -C /Users/shane/Desktop/Arena_1013_model show <ref>:<path>`, copy what you use into `sources/`, and record each copy's ref, path and SHA256 in `sources/SOURCES.md`:
  - round 11 `exp/phase2-r11-eps-transfer-20261018`, under `research/phase2_r11_eps_transfer_20261018/`: `FINAL_REPORT.md`, `wp2/REPORT.md` (LIC T_path), `wp4/pack_drivers.csv`, `src/drift.py` ("SUB + drift d");
  - round 8 `exp/phase2-r8-error-table-20261017`, under `research/phase2_r8_error_table_20261017/`: `DATA_DICTIONARY.md`, `outputs/table_events.csv`, `outputs/table_anchors.csv`, `outputs/table_cycles.csv`;
  - on the base branch (in your worktree): `research/phase2_rebound_diagnosis_20261015/` (first-program offset, `outputs/events_merged.csv`).
  - **Optional, if present on origin:**
    - round 12 `exp/phase2-r12-eps-level-20261019`: `research/phase2_r12_eps_level_20261019/src/ahchain.py` (registered Ah-chain code) and `wp3/pairs.csv`;
    - round 13 `exp/phase2-r13-top-tail-20261019`: `research/phase2_r13_top_tail_20261019/wp3/R13_RESULT.json`.
    
    Run `git -C /Users/shane/Desktop/Arena_1013_model fetch origin` first. If a file is absent, record "not available" and continue.
- **Challenge data:** `TechArena_Challenge2_Team_Package/data/` in your own worktree, and `CHALLENGE2_DESCRIPTION.pdf`.
- **Concurrency guard.** Run `git log --oneline -5` at the start and before every commit. On an unexpected change, stop editing shared files, record it, and add files by explicit path only. Never use `git add -A` / `git add .`, never rewrite others' work, never use a bare `git stash`. One session per worktree.
- **Commits.** Commit at the end of every step, then `git push -u origin exp/phase2-r14-path-drift-20261019`. Never push elsewhere, never force. End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify** any `TechArena_Challenge2_Team_Package/` directory, any earlier study directory, or anything outside this worktree. Model variants are copies under the git-ignored `cache/variants/`.
- **Language and bytecode.** Markdown English first, Chinese second. Code comments in English. Run Python with `python3 -B`. No downloads.

## 2. Context

**Task.** Estimate the SOH of a 4 × 102 Ah LFP series pack on CK0..CK7. SOH is the C/20 capacity (5.1 A to pack 11.2 V "after a full charge"; the full-charge protocol is not stated) divided by 102 Ah. Only CK0 = 100.41 Ah is released. The causal cut is `load_dataset(data, until=CK_k)`.

**Where this round sits.** With charge contents in Ah:

```
ε_k = C20_k − Q_fc,k = (F^CK_k − F^A_k) + (B_k − S_k)
```

- F^CK is the checkup's top, F^A the anchor's top (14.0 V CV ended at ≈ 5.1 A), B the anchor's start and S the end of the C/20 discharge.
- The checkup reaches its top by charging from a part-charged state: the pack enters each checkup at 13.1–13.3 V, so this is a top-up-type path. The anchor reaches its top by charging from empty.
- **This round measures how the difference between the two paths' tops changes with age (the path drift d_path).** In round 11 this was the dominant term in LIC (T_path, 97 %).
- The pack-native analogue is
  - Term3_k = F^T_k − F^A_k, the top of the first top-up after anchor k minus the anchor's own top.
  - Both end at the same CV termination (14.0 V, ≈ 5.1 A) and are joined by an Ah balance.
- If the checkup charge behaves like our top-ups, F^CK_k − F^A_k = Term3_k + c with a constant c, and the path drift is the trend of Term3_k.
- **Out of scope here:**
  - the level of ε (round 12);
  - the CV-tail part (round 13);
  - a different checkup charge rate (unknown). A rate-related tail difference belongs to round 13's scenarios.

**Correction recorded on purpose.** An earlier suggestion was to compare charge-side and discharge-side graphite-step positions (a "mirror" check). That difference h cancels in the total capacity: in ε it enters the top section with +h and the bottom section with −h. So it is **not** a test of ε drift. Step-position indicators appear here only as descriptive path-memory signals (P3).

**Facts to re-verify in WP0** (exposed, from the 2026-10-15 rebound study):
- After a from-empty anchor, the rest voltage at the top is 7–8 mV lower than after the next top-up, and the next top-up needs ≈ +0.1 Ah.
- The first deep program after the anchor sits +0.39–0.46 Ah deeper on all 6 detection variants, and the offset is gone by the next program.
- Anchors run at 25 °C except anchor 0 (segment 1, 45 °C).
- The per-block Ah balance between consecutive CV ends does not close (−0.3 to −1.1 Ah per block), so a measurement bias exists and must be removed by the loss rule.
- The counters book the 20 A pulse as charge. Integrate `current_A` with the package convention `_integrated_ah`.

**SUB.** `my_model/model_template.py` at the base commit. "SUB + drift d" is round 11's `src/drift.py`. Copy it; do not re-derive it.

## 3. Work packages

### WP0 — Setup and fact sheet

1. Create or reuse the worktree; write `notes/STATUS.md`, `notes/DECISIONS.md` and `sources/SOURCES.md`; commit this prompt; fetch and copy the sources (including the optional ones, if present).
2. Run SUB with the package CLI and save `wp0/SUB_SOH.csv`.
3. Write `wp0/anchor_blocks.csv`, one row per anchor k = 0..7:
   - the anchor's CV end and the CV ends of the next two top-ups in the same segment (if any);
   - recording gaps (dt > 60 s) in between;
   - CV Ah, CV duration and end current of the anchor and of those top-ups;
   - the pack and cell voltages 30 min after each CV end.
4. Write `wp0/FACTS.md`, verifying the bullets of §2 with numbers from the data. Do not compute any Ah balance in WP0.

**Done:** worktree, notes, sources, `wp0/SUB_SOH.csv`, `wp0/anchor_blocks.csv` and `wp0/FACTS.md` are committed and pushed.

### WP1 — Registration (nothing computed on challenge data)

Register the following in `wp1/protocol.json` and commit it, its hash and the code before any WP2 output.

- **Ah chain.**
  - If round 12's `src/ahchain.py` is available, copy it unchanged and record its hash. Otherwise implement the same rule in `src/ahchain.py`:
    - N_ij = ∫ current_A dt over (t_i, t_j] between consecutive CV ends, with the package convention, and thr_ij = the discharged Ah between them;
    - exclude pairs with a recording gap (dt > 60 s);
    - λ_s = median of N/thr over the segment's top-up → top-up (TT) pairs. If the segment has none, use the pooled median of its set point; if that set point has fewer than 2 TT pairs, use the other set point's pooled median, and record it;
    - σ_TT,25 and σ_TT,45 are 1.4826·MAD of the TT residuals N − λ·thr, with λ computed without that pair.
  - Test it on synthetic series only: a known Ah offset must be recovered to within 0.005 Ah.
- **Signals.**
  - **P1 (primary): Term3_k = N(A_k → T1) − λ·thr**, for k = 1..7 (25 °C).
    - Robustness variant **P1b:** Term3'_k = N(A_k → T2) − λ·thr, to the second top-up's CV end.
    - The 45 °C analogue for anchor 0 is reported separately and is not in the trend.
  - **P2 (consistency): ΔV_k = V30(T1) − V30(A_k)** in mV, pack and per cell. It is converted to Ah with s_top = dV/dQ of the CK0 pack curve over discharged Ah ∈ [0.5, 2.0] (per cell: per-cell curves).
  - **P3 (descriptive path memory).** These do not enter the decision.
    - The first-program offset o_k = D1_k − D2_k and the absolute shift o_k + Term3_k, from the package's A3 step value and its dvdq variant (0.25 Ah grid, stated).
    - The anchor vs T1 differences in CV Ah, CV duration and end current.
- **Statistics.**
  - fade_k = Q_fc,1 − Q_fc,k. **d_path** = Theil–Sen slope of Term3_k against fade_k over k = 1..7 (at least 5 points needed). Also report the leave-one-anchor-out (LOO) range and the slope against days since CK0.
  - Compare models by BIC: (a) constant, (b) linear in fade. The registered margin is 2.
  - **Outliers:** flag points beyond 3 MAD of the residuals, keep them in the main estimate, and give a sensitivity analysis without them. Anchor 3 (segment 6, unrelaxed start) stays in the main estimate, because its top is not affected by its bottom; give a sensitivity analysis without it.
  - Apply the same statistics to P1b and P2 (in Ah).
- **Decision rules (copy verbatim).** Let E = d_path × 8.2 Ah, the effect at CK7.
  - **Noise gate:** σ_TT,25 ≤ 0.30 Ah. Otherwise the outcome is **"not identifiable"**: report and exit after WP3's write-up.
  - **Identifiability:** the LOO range of E is ≤ 0.30 Ah wide. Otherwise the outcome is **O3 "not identifiable"**.
  - **O1 "path drift small":** the LOO range of E lies within [−0.10, +0.10] Ah, and P1b's median E lies within ±0.15 Ah.
  - **O2 "path drift material":** the LOO range of E excludes 0, |median E| > 0.10 Ah, BIC prefers (b) by ≥ 2, and P1b has the same sign. Candidate "SUB + d_path" is leaderboard-only.
  - **O3 "inconclusive":** any other case.
  - **Combination with round 13** (only if `R13_RESULT.json` is available): d_top = d_tail + d_path, with medians added and ranges added endpoint-wise. Report it; it decides nothing in this round. It is passed to round 15.
  - No rule uses P_k or proxy errors.
- Write `wp1/REPORT.md` with a "what each outcome would mean" table.

**Done:** protocol, hash, registered code with passing synthetic test and `wp1/REPORT.md` are committed and pushed.

### WP2 — Measurements

- Compute P1, P1b, P2 and P3, and save `wp2/pairs.csv`, `wp2/term3.csv`, `wp2/p2_voltage.csv` and `wp2/p3_memory.csv`.
- If round 12's `wp3/pairs.csv` is available, compare the shared pairs: N must agree to within 0.001 Ah. Record any mismatch; do not resolve it by editing either side.
- Make two figures:
  - Term3_k, Term3'_k and P2 (in Ah) against fade, with the fitted line and LOO band;
  - P3 against month.

**Done:** tables, figures and `wp2/REPORT.md` are committed and pushed.

### WP3 — Decision and hand-off

1. Apply the registered rules: noise gate, identifiability, O1/O2/O3, and the combination with round 13 if available.
2. Save `wp3/SOH_variants.csv` (leaderboard-only, never scored against proxies): SUB, SUB + d_path (median and LOO ends), and SUB + d_top if available, built with the copied `drift.py`.
3. Write `wp3/R14_RESULT.json` for round 15: outcome, d_path (median and LOO range), BIC, P1b and P2 agreement, d_top if available, and the per-anchor table.
4. Write `wp3/REPORT.md`, then `FINAL_REPORT.md` and `README.md`. Conclusions first, plus a per-checkup SOH table of SUB vs the variants.

**Done:** the decision, `wp3/SOH_variants.csv`, `wp3/R14_RESULT.json`, `wp3/REPORT.md`, `FINAL_REPORT.md` and `README.md` are committed and pushed.

---

<a id="zh"></a>

# 第 14 轮：本电池组上的路径漂移——"从空充满"与"补电"的顶部差会随老化变化吗？——执行 Prompt

> [English](#en) · 中文

写于 2026-10-19。本文档自成一体。英文部分是执行文本，中文部分是供读者阅读的译文；两者不一致时以英文为准。

工作分为**工作包 WP0–WP3**。每个工作包都有自己的"完成"清单，可以作为单独的 `/goal` 运行。
- WP0、WP1、WP2、WP3 按顺序运行。`FINAL_REPORT.md` 最后写。
- 本轮与第 12、13 轮互相独立，可以在各自的工作树中并行运行。凡是复用它们的登记代码或结果，按下文规则处理。

## 0. 工作方式（所有工作包）

- **无人值守。** 永远不要停下来提问。遇到未决问题时，选择符合本文全部规则的最保守做法，记入 `notes/DECISIONS.md`，然后继续。
- **重启。** 每完成一步就更新 `notes/STATUS.md`：当前工作包、已完成、下一步、最后一次提交。重启时先读 `notes/STATUS.md` 和 `notes/DECISIONS.md`，从断点继续。已完成的工作包或步骤不要重做。
- **诚实优先于目标。** "无法识别"和"无定论"都是有效结果。本轮产出的是**基于本电池组的路径漂移估计、一个决策和一条建议**。本轮不改动提交，也不针对 Challenge 2 代理标签 P_k 计算任何误差。
- **任一工作包的"完成"**指满足下列通用条件，以及该工作包自己的清单：
  1. 登记协议（`wp1/protocol.json` + `wp1/protocol.sha256`，以及登记的代码）在任何评估输出**之前**已提交；
  2. 有中英双语的 `wpN/REPORT.md`，结论在前；
  3. `notes/STATUS.md` 把该工作包标为完成或退出，并附一行结果；
  4. 每次提交都已推送到 `origin exp/phase2-r14-path-drift-20261019`，且 `git status` 中没有未提交的研究文件。
- **全局完成：** WP0–WP3 各自完成或按登记规则退出；`FINAL_REPORT.md`、`README.md` 和 `wp3/R14_RESULT.json` 均存在（Markdown 双语，结论在前）；通用条件 3–4 成立。

## 1. 工作区、隔离与 git

- **工作树和分支。** 在 WP0 中按需创建，此步骤可重复执行。
  - 基点：`exp/phase2-anchor-step-20261013` 上的 `6525edf`。如果分支末端更新，就用末端，并记录其哈希。
  - 创建：`git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1019_r14_path_drift -b exp/phase2-r14-path-drift-20261019 <base>`。如果已存在，确认其历史包含 `<base>` 后复用。
  - 只在 `/Users/shane/Desktop/Arena_1019_r14_path_drift` 中工作。研究目录为 `research/phase2_r14_path_drift_20261019/`。
- **本 prompt** 目前未提交，位于 `/Users/shane/Desktop/Arena_1013_model/research/phase2_r14_path_drift_20261019/R14_EXECUTION_PROMPT.md`。把它复制到你工作树中的 `research/phase2_r14_path_drift_20261019/EXECUTION_PROMPT.md`，并作为第一次提交。不要提交、移动或删除原文件。
- **只读来源。** 用 `git -C /Users/shane/Desktop/Arena_1013_model show <ref>:<path>` 读取之前各轮的文件，把用到的复制到 `sources/`，并在 `sources/SOURCES.md` 中记录每个副本的引用、路径和 SHA256：
  - 第 11 轮 `exp/phase2-r11-eps-transfer-20261018`，位于 `research/phase2_r11_eps_transfer_20261018/` 下：`FINAL_REPORT.md`、`wp2/REPORT.md`（LIC 的 T_path）、`wp4/pack_drivers.csv`、`src/drift.py`（"SUB + drift d"）；
  - 第 8 轮 `exp/phase2-r8-error-table-20261017`，位于 `research/phase2_r8_error_table_20261017/` 下：`DATA_DICTIONARY.md`、`outputs/table_events.csv`、`outputs/table_anchors.csv`、`outputs/table_cycles.csv`；
  - 基点分支上（你的工作树里已有）：`research/phase2_rebound_diagnosis_20261015/`（首个程序偏移，`outputs/events_merged.csv`）。
  - **可选，若 origin 上存在：**
    - 第 12 轮 `exp/phase2-r12-eps-level-20261019`：`research/phase2_r12_eps_level_20261019/src/ahchain.py`（登记的电量链代码）和 `wp3/pairs.csv`；
    - 第 13 轮 `exp/phase2-r13-top-tail-20261019`：`research/phase2_r13_top_tail_20261019/wp3/R13_RESULT.json`。
    
    先运行 `git -C /Users/shane/Desktop/Arena_1013_model fetch origin`。文件不存在时，记录"不可用"，然后继续。
- **赛题数据：** 你自己工作树中的 `TechArena_Challenge2_Team_Package/data/`，以及 `CHALLENGE2_DESCRIPTION.pdf`。
- **并发保护。** 开始时以及每次提交前运行 `git log --oneline -5`。遇到意外改动时，停止编辑共享文件，记录下来，之后只按明确路径添加文件。不要用 `git add -A` / `git add .`，不要改写他人的工作，不要用不带参数的 `git stash`。一个工作树同时只开一个会话。
- **提交。** 每一步结束时提交，然后运行 `git push -u origin exp/phase2-r14-path-drift-20261019`。不要推送到其他地方，不要强制推送。每条提交信息的末尾加上 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **不得修改**任何 `TechArena_Challenge2_Team_Package/` 目录、之前各轮的研究目录或本工作树之外的任何东西。模型变体以副本形式放在 git 忽略的 `cache/variants/` 下。
- **语言与字节码。** Markdown 先英文后中文。代码注释用英文。运行 Python 时用 `python3 -B`。不下载任何东西。

## 2. 背景

**任务。** 估计一个 4 × 102 Ah LFP 串联电池组在 CK0..CK7 的 SOH。SOH 是 C/20 容量（"满充后"以 5.1 A 放电到电池组 11.2 V；满充协议没有说明）除以 102 Ah。只公布了 CK0 = 100.41 Ah。因果截断为 `load_dataset(data, until=CK_k)`。

**本轮的位置。** 以 Ah 计的电荷量：

```
ε_k = C20_k − Q_fc,k = (F^CK_k − F^A_k) + (B_k − S_k)
```

- F^CK 是检查的顶部，F^A 是锚点的顶部（14.0 V CV 在约 5.1 A 处结束），B 是锚点的起点，S 是 C/20 放电的终点。
- 检查是从部分荷电的状态充到顶部的：电池组进入每次检查时为 13.1–13.3 V，所以这属于补电型路径。锚点则是从空充到顶部。
- **本轮测量两条路径到达的顶部之差随老化的变化（路径漂移 d_path）。** 第 11 轮中这是 LIC 的主导项（T_path，占 97 %）。
- 本电池组上的对应量是
  - Term3_k = F^T_k − F^A_k，即锚点 k 之后第一次补电的顶部减去锚点自己的顶部。
  - 两者结束于同样的 CV 终止条件（14.0 V，约 5.1 A），之间用电量对账连接。
- 如果检查的充电表现得像我们的补电，那么 F^CK_k − F^A_k = Term3_k + c（c 为常数），路径漂移就是 Term3_k 的趋势。
- **不在本轮范围内：**
  - ε 的水平（第 12 轮）；
  - CV 尾巴部分（第 13 轮）；
  - 检查的充电倍率不同（未知）。与倍率相关的尾巴差异属于第 13 轮的情景。

**特意记录的更正。** 之前曾建议比较充电侧与放电侧石墨台阶的位置（"镜像"检查）。这个差值 h 在总容量中相互抵消：它在 ε 的顶部区段以 +h 出现，在底部区段以 −h 出现。所以它**不是** ε 漂移的检验。台阶位置类指标在本轮只作为描述性的路径记忆信号（P3）出现。

**需在 WP0 重新核实的事实**（已曝光，来自 2026-10-15 回弹研究）：
- 从空充满的锚点之后，顶部静置电压比下一次补电之后低 7–8 mV，下一次补电要多充约 +0.1 Ah。
- 锚点之后第一个深放电程序的台阶深 +0.39–0.46 Ah，6 种检测变体都如此，到下一个程序就消失了。
- 除锚点 0（第 1 段，45 °C）外，锚点都在 25 °C。
- 相邻两次 CV 结束之间的逐块电量对账不闭合（每块 −0.3 到 −1.1 Ah），说明存在测量偏差，必须由损耗规则扣除。
- 计数器把 20 A 脉冲记作充电。要对 `current_A` 积分，并沿用包内约定 `_integrated_ah`。

**SUB。** 基点提交上的 `my_model/model_template.py`。"SUB + drift d"用第 11 轮的 `src/drift.py`。复制它，不要重新推导。

## 3. 工作包

### WP0 — 准备与事实清单

1. 创建或复用工作树；写 `notes/STATUS.md`、`notes/DECISIONS.md` 和 `sources/SOURCES.md`；提交本 prompt；fetch 并复制来源文件（可选来源若存在也复制）。
2. 用包的 CLI 运行 SUB，保存 `wp0/SUB_SOH.csv`。
3. 写 `wp0/anchor_blocks.csv`，每个锚点 k = 0..7 一行：
   - 锚点的 CV 结束时间，以及同一段内接下来两次补电（如有）的 CV 结束时间；
   - 其间的记录间隙（dt > 60 s）；
   - 锚点和这些补电的 CV 电量、CV 时长和末电流；
   - 每次 CV 结束 30 min 后的电池组电压和各电芯电压。
4. 写 `wp0/FACTS.md`，用数据中的数字核实第 2 节的各条事实。WP0 中不计算任何电量对账。

**完成：** 工作树、记录文件、sources、`wp0/SUB_SOH.csv`、`wp0/anchor_blocks.csv` 和 `wp0/FACTS.md` 均已提交并推送。

### WP1 — 登记（不在赛题数据上计算任何东西）

把以下内容登记到 `wp1/protocol.json`，并在任何 WP2 输出之前提交它、它的哈希和代码。

- **电量链。**
  - 若第 12 轮的 `src/ahchain.py` 可用，原样复制并记录其哈希。否则按同一规则实现 `src/ahchain.py`：
    - N_ij = 相邻两次 CV 结束之间在 (t_i, t_j] 上对 current_A 的积分，沿用包内约定；thr_ij = 两者之间的放电 Ah；
    - 排除带记录间隙（dt > 60 s）的配对；
    - λ_s = 该段所有补电 → 补电（TT）配对的 N/thr 的中位数。该段没有 TT 配对时，用其设定温度的合并中位数；若该设定温度的 TT 配对不足 2 个，就用另一个设定温度的合并中位数，并记录下来；
    - σ_TT,25 和 σ_TT,45 为 TT 残差 N − λ·thr 的 1.4826·MAD，计算 λ 时排除该配对本身。
  - 只在合成序列上测试：已知的电量偏移要在 0.005 Ah 以内找回。
- **信号。**
  - **P1（主信号）：Term3_k = N(A_k → T1) − λ·thr**，k = 1..7（25 °C）。
    - 稳健性变体 **P1b：** Term3'_k = N(A_k → T2) − λ·thr，算到第二次补电的 CV 结束。
    - 锚点 0 的 45 °C 对应值单独报告，不进入趋势。
  - **P2（一致性）：ΔV_k = V30(T1) − V30(A_k)**，单位 mV，分电池组和各电芯。用 s_top 换算成 Ah，s_top 为 CK0 电池组曲线在放电 Ah ∈ [0.5, 2.0] 上的 dV/dQ（各电芯用各自的曲线）。
  - **P3（描述性的路径记忆）。** 不进入决策。
    - 首个程序偏移 o_k = D1_k − D2_k，以及绝对位移 o_k + Term3_k，用包内 A3 台阶值及其 dvdq 变体计算（0.25 Ah 网格，需注明）。
    - 锚点与 T1 在 CV 电量、CV 时长和末电流上的差。
- **统计。**
  - fade_k = Q_fc,1 − Q_fc,k。**d_path** = 在 k = 1..7 上 Term3_k 对 fade_k 的 Theil–Sen 斜率（至少需要 5 个点）。同时报告留一锚点（LOO）范围，以及对距 CK0 天数的斜率。
  - 用 BIC 比较两个模型：(a) 常数，(b) 对衰减线性。登记的阈值为 2。
  - **离群点：** 标记残差超过 3 MAD 的点，主估计中保留，另做去掉它们的敏感性分析。锚点 3（第 6 段，起点未静置好）保留在主估计中，因为它的顶部不受底部影响；另做去掉它的敏感性分析。
  - 对 P1b 和 P2（换算成 Ah）做同样的统计。
- **决策规则（原样照抄）。** 令 E = d_path × 8.2 Ah，即 CK7 处的影响。
  - **噪声门：** σ_TT,25 ≤ 0.30 Ah。否则结果为**"无法识别"**：报告，写完 WP3 后退出。
  - **可识别性：** E 的 LOO 范围宽度 ≤ 0.30 Ah。否则结果为 **O3"无法识别"**。
  - **O1"路径漂移小"：** E 的 LOO 范围在 [−0.10, +0.10] Ah 之内，且 P1b 的 E 中位数在 ±0.15 Ah 之内。
  - **O2"路径漂移显著"：** E 的 LOO 范围不含 0，|E 中位数| > 0.10 Ah，BIC 对 (b) 的偏好 ≥ 2，且 P1b 同号。候选"SUB + d_path"只用于排行榜。
  - **O3"无定论"：** 其他所有情况。
  - **与第 13 轮合并**（仅当 `R13_RESULT.json` 可用时）：d_top = d_tail + d_path，中位数相加，范围按端点相加。报告它，但本轮不据此做任何决定，而是交给第 15 轮。
  - 以上规则都不使用 P_k 或代理误差。
- 写 `wp1/REPORT.md`，附"各结果意味着什么"表。

**完成：** 协议、哈希、通过合成测试的登记代码和 `wp1/REPORT.md` 均已提交并推送。

### WP2 — 测量

- 计算 P1、P1b、P2 和 P3，保存 `wp2/pairs.csv`、`wp2/term3.csv`、`wp2/p2_voltage.csv` 和 `wp2/p3_memory.csv`。
- 若第 12 轮的 `wp3/pairs.csv` 可用，比较双方共有的配对：N 必须在 0.001 Ah 以内一致。记录任何不一致；不要通过修改任何一方来消除不一致。
- 画两张图：
  - Term3_k、Term3'_k 和 P2（换算为 Ah）随衰减的变化，附拟合线和 LOO 带；
  - P3 随月份的变化。

**完成：** 各表、图和 `wp2/REPORT.md` 均已提交并推送。

### WP3 — 决策与交接

1. 应用登记的规则：噪声门、可识别性、O1/O2/O3，以及（可用时）与第 13 轮合并。
2. 保存 `wp3/SOH_variants.csv`（只用于排行榜，绝不与代理对比打分）：SUB、SUB + d_path（中位数和 LOO 两端），以及可用时的 SUB + d_top，用复制来的 `drift.py` 构造。
3. 写 `wp3/R14_RESULT.json` 供第 15 轮使用：结果、d_path（中位数和 LOO 范围）、BIC、P1b 与 P2 的一致性、可用时的 d_top，以及逐锚点表。
4. 写 `wp3/REPORT.md`，然后写 `FINAL_REPORT.md` 和 `README.md`。结论在前，并附 SUB 与各变体在每个检查点的 SOH 对比表。

**完成：** 决策、`wp3/SOH_variants.csv`、`wp3/R14_RESULT.json`、`wp3/REPORT.md`、`FINAL_REPORT.md` 和 `README.md` 均已提交并推送。
