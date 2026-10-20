<a id="en"></a>

# Round 15: Leaderboard Probe Plan — The Only Source of Real Truth, Used Sparingly and Within the Rules — Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-19. This document is self-contained. The English text is the execution text. The Chinese section is a translation for the reader; where the two differ, the English governs.

The work is split into **work packages WP0–WP4**. Each has its own *Done* list and can be run as a separate `/goal`.
- WP0 can run at any time.
- WP1–WP3 should run **after rounds 12–14 have finished**. If one has not, WP1 uses the registered fallback.
- WP4 runs **only after the user has recorded new leaderboard results**. It may be repeated once per leaderboard evaluation.
- `FINAL_REPORT.md` is written at the end of WP3 and updated by WP4.

## 0. Mode of work (all work packages)

- **Unattended, but never outward-facing.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue. **You never upload, submit, e-mail or post anything.** The user does every action that leaves this machine. You prepare files and a hand-over note.
- **Restarts.** Keep `notes/STATUS.md` current after every step: WP, done, next, last commit. On a restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume from there. Never redo a finished WP or step.
- **Honesty over targets.** "No probe is worth it" is a valid outcome. This round produces **a rules audit, a registered probe plan, validated probe packages and reading rules**. It never wires a variant into `TechArena_Challenge2_Team_Package/`, and it never computes an error against the Challenge 2 proxy labels P_k.
- **Done for any WP** means the common criteria below, plus that WP's own list:
  1. the registered protocol (`wp1/protocol.json` + `wp1/protocol.sha256`) was committed **before** any WP2–WP4 output;
  2. its bilingual `wpN/REPORT.md` exists, conclusions first;
  3. `notes/STATUS.md` marks the WP done, exited or waiting, with a one-line result;
  4. every commit is pushed to `origin exp/phase2-r15-probe-plan-20261019`, and `git status` shows no uncommitted study files.
- **Global Done:** WP0–WP3 are done or exited by a registered rule; WP4 is done or "waiting for leaderboard"; `FINAL_REPORT.md`, `README.md` and `wp3/HANDOVER.md` exist (Markdown bilingual, conclusions first); common criteria 3–4 hold.

## 1. Workspace, isolation, git

- **Worktree and branch.** Create them in WP0 if missing; the step is idempotent.
  - Base: the tip of `exp/phase2-anchor-step-20261013` (at writing `6525edf`). Record its hash.
  - Create: `git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1019_r15_probe -b exp/phase2-r15-probe-plan-20261019 <base>`. If it already exists, check that its history contains `<base>` and reuse it.
  - Work only in `/Users/shane/Desktop/Arena_1019_r15_probe`. The study directory is `research/phase2_r15_probe_plan_20261019/`.
- **This prompt** lives, uncommitted, at `/Users/shane/Desktop/Arena_1013_model/research/phase2_r15_probe_plan_20261019/R15_EXECUTION_PROMPT.md`. Copy it to `research/phase2_r15_probe_plan_20261019/EXECUTION_PROMPT.md` in your worktree and commit it first. Do not commit, move or delete the original.
- **Read-only sources.** Run `git -C /Users/shane/Desktop/Arena_1013_model fetch origin` first. Read with `git … show <ref>:<path>`, copy into `sources/`, and record ref, path and SHA256 in `sources/SOURCES.md`:
  - round 6 `exp/phase2-r6-robust-20261016`, under `research/phase2_r6_robust_20261016/`: `wp1/protocol.json`, `wp1/run_wp1.py` (18-hypothesis grid h = (Δ, f, d) and the normalised score s), `wp6/run_wp6.py`, `wp6/REPORT.md`, `wp6/outputs/wp6_probe_plan.json`. Its probe vectors were built for the **older** SUB (V2+√t, `21a7a55`); they must be rebuilt on the current SUB before use;
  - round 11 `exp/phase2-r11-eps-transfer-20261018`: `research/phase2_r11_eps_transfer_20261018/src/drift.py` and `wp5/decision.json`;
  - **results of rounds 12–14, if present on origin:**
    - `exp/phase2-r12-eps-level-20261019`: `research/phase2_r12_eps_level_20261019/wp4/` (decision, `SOH_variants.csv`, `R13_HANDOFF.json`);
    - `exp/phase2-r13-top-tail-20261019`: `research/phase2_r13_top_tail_20261019/wp3/R13_RESULT.json` and `wp3/SOH_variants.csv`;
    - `exp/phase2-r14-path-drift-20261019`: `research/phase2_r14_path_drift_20261019/wp3/R14_RESULT.json` and `wp3/SOH_variants.csv`.
    
    Record each one as present (with commit) or absent;
  - the packaging script `research/phase2_v3_20261015/package_submission.py` (in your worktree).
  - **User files, read-only, listing and hashing only:** `/Users/shane/Desktop/Arena项目书面文件/提交包/` and `/Users/shane/Desktop/*Challenge2*.zip`. You may extract a zip into the git-ignored `cache/existing/` to read its `my_model/model_template.py`. Never modify, move or delete the originals.
- **Rules documents:** `TechArena_Challenge2_Team_Package/CHALLENGE2_DESCRIPTION.pdf` and `submission_instructions_2026.md` in your worktree.
- **User inputs** (in your study directory, filled by the user; create templates if missing):
  - `inputs/leaderboard_log.csv` with columns `board_date, package_file, package_sha256, model_commit, metrics_verbatim, rank, notes`;
  - `inputs/deadline.txt` (date, time and time zone, or "unknown");
  - `inputs/pptx_path.txt` (path of the team's current presentation, or "template").
- **Concurrency guard.** Run `git log --oneline -5` at the start and before every commit. On an unexpected change, stop editing shared files, record it, and add files by explicit path only. Never use `git add -A` / `git add .`, never rewrite others' work, never use a bare `git stash`. One session per worktree.
- **Commits.** Commit at the end of every step, then `git push -u origin exp/phase2-r15-probe-plan-20261019`. Never push elsewhere, never force. End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Zips are never committed; they live in the git-ignored `cache/packages/`.
- **Do not modify** any `TechArena_Challenge2_Team_Package/` directory, any earlier study directory, or anything outside this worktree. Variants are built from copies under `cache/`.
- **Language and bytecode.** Markdown English first, Chinese second. Code comments in English. Run Python with `python3 -B`. No downloads.

## 2. Context

**Task.** Estimate the SOH of a 4 × 102 Ah LFP series pack on CK1..CK7 (hidden C/20 capacities, 102 Ah nominal). Only CK0 = 100.41 Ah is released. Every local check uses proxies (P_k = Q_fc,k + ε0 + Δ), and the proxy–truth gap is common-mode: it is the same vector g_k for every estimator. Two scalars therefore cannot be judged locally at all:
- the ε level (EPS_EXTRA_AH = 0.4, an assumption; round 12 measures it);
- the ε drift d (rounds 13 and 14 bound it).

The leaderboard is the only place where truth enters.

**What the rules say (to be quoted verbatim in WP0).**
- **PDF.** "Package and submit as often as you like … a public leaderboard is updated weekly". There is a reduced-budget run that earns a data-efficiency bonus.
- **`submission_instructions_2026.md`:**
  - "Only CK0 is a target … Checkups CK1 to CK7 are hidden and scored … Do not attempt to reconstruct them from external sources."
  - "There is no limit on how many times you may resubmit before the deadline (<<TODO>>); **the last submission counts**."
  - "Submissions are evaluated **every two weeks** and the public leaderboard is updated accordingly." This conflicts with the PDF's "weekly"; record both.
  - Scoring: "error metrics of your SOH estimates (including the worst-case error), each normalised by the reference baseline — baseline = 1.0, lower is better. **The exact metric set is not published.**" Model performance is 70 % of the final score.
  - The final presentation inside the last submission is the one used at the final event.

**Compliance stance registered for this round.**
- Probing is not explicitly forbidden. Reconstructing hidden capacities is forbidden "from external sources", and per-checkup tuning against the leaderboard would reconstruct them in spirit. This plan therefore allows **at most two probe submissions**, under these conditions:
  - each probe is a **whole-model variant that changes one physically motivated scalar**, produced by a registered earlier round;
  - each probe and any adopted change are disclosed in the README and report;
  - the final model must remain justifiable from the physics alone.
- WP2 drafts a short question to the organisers. The user decides whether to send it.

**Earlier probe plan (round 6, for the older SUB).** P_drift (d = −0.031) → P_stress_early → P_start. Round 7 reordered it to P_stress_early → P_start → P_drift. Round 6 computed the expected Δs over an 18-hypothesis grid with a normalised score s (ExampleModel = 1). Reuse that machinery; do not re-derive it.

**Current SUB.** `my_model/model_template.py` at the base (A3). Its SOH: CK1 95.984, CK2 94.507, CK3 93.600, CK4 92.821, CK5 92.015, CK6 91.426, CK7 90.765 (the package script's `EXPECTED_SOH`). Re-verify in WP0.

## 3. Work packages

### WP0 — Setup, rules audit and inventory

1. Create or reuse the worktree; write `notes/STATUS.md`, `notes/DECISIONS.md` and `sources/SOURCES.md`; commit this prompt; fetch and copy the sources.
2. Write `wp0/RULES.md`.
   - Quote every rule sentence listed in §2 verbatim, with file and line or page.
   - List the open points: deadline, platform, cadence (weekly vs two-weekly), metric set, and whether the board shows one score or several.
3. Create the input templates if missing. Read whatever the user has filled in. If the leaderboard log is empty, record "no observations".
4. Write `wp0/existing_packages.csv`, an inventory of the existing zips:
   - name, size, SHA256;
   - SHA256 of the contained `model_template.py`;
   - the matching commit, found by comparing that file's hash with the history of `exp/phase2-anchor-step-20261013`;
   - its SOH vector from the package CLI (run from `cache/existing/`).
   
   Mark which zip, if any, the leaderboard log says was submitted.
5. Write `wp0/candidates.md`: which of rounds 12–14 are present and their outcomes (L1/L2/L3, O1/O2/O3), and which candidate SOH vectors exist.

**Done:** worktree, notes, sources, input templates, `wp0/RULES.md`, `wp0/existing_packages.csv`, `wp0/candidates.md` and `wp0/REPORT.md` are committed and pushed.

### WP1 — Registration

Write `wp1/protocol.json` (and its hash) and commit it before any WP2 output. It must contain the following.

- **Hypothesis grid.**
  - Start from round 6's grid h = (Δ, f, d), copied exactly.
  - Replace the Δ axis with round 12's EPS_EXTRA interval {lo, point, hi}, but only if round 12 reached L1 or L2. Otherwise keep {0, 0.4, 0.8}.
  - Replace the d axis with the combined d_top = d_tail + d_path {lo, median, hi}, but only if both rounds 13 and 14 are present and identifiable. If only one is present, combine it with round 11's [−0.036, +0.052] for the missing part. If neither is present, keep round 6's axis.
  - Truth vectors T_k(h) are built exactly as round 6 builds them.
- **Metric family.** Because the official metric set is unpublished, every reading rule must hold for all of:
  - round 6's s;
  - MAE, RMSE and MAX over CK1–CK7, each normalised by the same metric of ExampleModel (run locally through the package CLI) under the same h.
- **Eligible probes.** Each changes one scalar, is rebuilt on the current SUB, and is built as a research copy.
  - **P_level:** SUB with round 12's EPS_EXTRA point estimate. Eligible only if round 12 reached L2.
  - **P_A3fix:** round 12's anchor-3 correction. Eligible only if round 12's G_a3 passed.
  - **P_drift:** SUB + d with d = median d_top. Eligible if round 13 or round 14 reached O2. If both reached O1, P_drift is **ineligible**. If neither is present, round 6's d = −0.031 is used.
  - **P_stress_early:** round 6's F1_S_B fusion. Eligible only if it can be rebuilt on the current SUB from round 6/7 code without new fitting; otherwise dropped, with the reason recorded.
- **Free information first.** For every leaderboard observation whose package SOH vector is known (WP0), compute each hypothesis's predicted score under each metric. Keep the hypotheses whose prediction matches the displayed value within its display precision under at least one metric: this is the *surviving set*. This filters hypotheses only; it never selects a model by itself.
- **Probe selection.** For each eligible probe compute Δs(h, metric) against SUB over the surviving set (the full grid if there are no observations).
  - A probe is *readable* if sign(Δs) is the same under all four metrics for ≥ 80 % of the surviving hypotheses.
  - Rank the readable probes by expected Δs (uniform over the surviving set), then by worst-case Δs.
  - Choose **at most two**. If none is readable, the plan is "no probe; keep SUB".
- **Reading rules** (one table per chosen probe). tol = the board's display precision (from the log; default 0.005 if unknown).
  - Observed Δs < −tol: adopt the probe's scalar as the new submission candidate.
  - Observed Δs > +tol: revert to SUB and drop that hypothesis branch.
  - |Δs| ≤ tol: no information; revert to SUB.
  - If the board shows several metrics, the rule applies to each one, and a probe "wins" only if no shown metric gets worse by more than tol.
- **End-state rule.** The last submission before the deadline must be the best observed option (SUB by default). A probe is never left as the last submission unless it won. With evaluations every two weeks and an unknown deadline, assume at most two evaluation cycles remain.
- **Compliance rule.** These limits come from §2's stance: at most two probes, one scalar each, disclosure in the README and report, and no per-checkup edits.
- Write `wp1/REPORT.md` with a "what each outcome would mean" table.

**Done:** protocol, hash and `wp1/REPORT.md` are committed and pushed.

### WP2 — Plan

1. Rebuild every eligible probe's SOH vector on the current SUB. Save `wp2/probe_soh.csv`.
2. Compute the surviving set (if there are observations), Δs per probe × hypothesis × metric, readability and the ranking. Save `wp2/delta_s_long.csv` and `wp2/ranking.csv`.
3. Write `wp2/PROBE_PLAN.md`:
   - the chosen probes (or "no probe"), their SOH tables and reading tables;
   - a timeline against `inputs/deadline.txt`, with each evaluation cycle taken as two weeks;
   - the end-state rule.
4. Write `wp2/ORGANIZER_QUESTION.md`, a short English draft asking whether submitting a variant that differs in one physically motivated constant, to choose between two documented hypotheses, is acceptable. **It is a draft only; do not send it.**

**Done:** probe vectors, Δs tables, ranking, `wp2/PROBE_PLAN.md`, `wp2/ORGANIZER_QUESTION.md` and `wp2/REPORT.md` are committed and pushed.

### WP3 — Build probe packages and hand over (no upload)

1. For each chosen probe, stage a full copy of the package under `cache/pkg_<probe>/`.
   - Replace `my_model/model_template.py` with the probe's research copy. The diff against SUB must be the registered scalar, or the registered hook, plus a docstring line.
   - Add a short, honest README section describing the variant and why it is submitted.
2. Copy `package_submission.py` into `src/`, changing only three things: `PKG` points at the staged copy; `EXPECTED_SOH` is that probe's own CLI output; `--out` defaults to `cache/packages/`.
   - Build `Current State_Challenge2.zip` for each probe, in its own subfolder `cache/packages/<probe>/`, with `--members "Mona Zhu, Zhikuan Shen"` and `--pptx` from `inputs/pptx_path.txt`. If that file says "template", record a warning in the hand-over.
   - The script validates each zip in a fresh Python 3.11 venv; both checks must pass.
3. Record each zip's SHA256 in `wp3/packages.csv`.
4. Write `wp3/HANDOVER.md` for the user:
   - which zip to upload first, and when;
   - what to copy into `inputs/leaderboard_log.csv` afterwards, and how;
   - when to run WP4;
   - a reminder that the last submission counts, and that SUB's zip must be re-uploaded at the end unless a probe wins;
   - the pptx warning, if any.
5. Write `FINAL_REPORT.md` and `README.md` (conclusions first).

**Never upload, never copy zips to the Desktop, and never touch the existing zips.**

**Done:** validated zips in `cache/packages/`, `wp3/packages.csv`, `wp3/HANDOVER.md`, `wp3/REPORT.md`, `FINAL_REPORT.md` and `README.md` are committed and pushed (all except the zips).

### WP4 — Read leaderboard results (run after each evaluation the user has logged)

1. Read `inputs/leaderboard_log.csv`. If it has no new row since the last WP4 run, set the status to "waiting for leaderboard", commit and stop. This is an allowed end state.
2. Otherwise:
   - check that each logged package hash matches `wp3/packages.csv` or `wp0/existing_packages.csv`;
   - update the surviving set;
   - apply the registered reading rules;
   - state the decision and the next action under the end-state rule.
3. If the decision adopts a probe's scalar:
   - write the README and report text that discloses the probe and the physical justification;
   - build the final package the same way as in WP3 (not uploaded);
   - state clearly that wiring it into `TechArena_Challenge2_Team_Package/` is the user's call.
4. Update `FINAL_REPORT.md` and `wp4/REPORT.md`, adding one dated section per run.

**Done:** either the decision, any final package and the updated reports are committed and pushed, or the status is "waiting for leaderboard" and committed.

---

<a id="zh"></a>

# 第 15 轮：排行榜探针计划——唯一的真值来源，在规则之内节制地使用——执行 Prompt

> [English](#en) · 中文

写于 2026-10-19。本文档自成一体。英文部分是执行文本，中文部分是供读者阅读的译文；两者不一致时以英文为准。

工作分为**工作包 WP0–WP4**。每个工作包都有自己的"完成"清单，可以作为单独的 `/goal` 运行。
- WP0 随时可以运行。
- WP1–WP3 应在**第 12–14 轮完成之后**运行。若某一轮未完成，WP1 使用登记的备选方案。
- WP4 **只在用户记录了新的排行榜结果之后**运行，每次排行榜评估后可以再运行一次。
- `FINAL_REPORT.md` 在 WP3 结束时写，由 WP4 更新。

## 0. 工作方式（所有工作包）

- **无人值守，但绝不对外操作。** 永远不要停下来提问。遇到未决问题时，选择符合本文全部规则的最保守做法，记入 `notes/DECISIONS.md`，然后继续。**你永远不上传、不提交、不发邮件、不发布任何东西。**所有离开这台机器的操作都由用户完成。你只准备文件和一份交接说明。
- **重启。** 每完成一步就更新 `notes/STATUS.md`：当前工作包、已完成、下一步、最后一次提交。重启时先读 `notes/STATUS.md` 和 `notes/DECISIONS.md`，从断点继续。已完成的工作包或步骤不要重做。
- **诚实优先于目标。** "没有值得做的探针"是有效结果。本轮产出的是**规则审查、登记的探针计划、通过验证的探针包和解读规则**。本轮从不把变体接入 `TechArena_Challenge2_Team_Package/`，也不针对 Challenge 2 代理标签 P_k 计算任何误差。
- **任一工作包的"完成"**指满足下列通用条件，以及该工作包自己的清单：
  1. 登记协议（`wp1/protocol.json` + `wp1/protocol.sha256`）在任何 WP2–WP4 输出**之前**已提交；
  2. 有中英双语的 `wpN/REPORT.md`，结论在前；
  3. `notes/STATUS.md` 把该工作包标为完成、退出或等待，并附一行结果；
  4. 每次提交都已推送到 `origin exp/phase2-r15-probe-plan-20261019`，且 `git status` 中没有未提交的研究文件。
- **全局完成：** WP0–WP3 各自完成或按登记规则退出；WP4 完成或处于"等待排行榜"；`FINAL_REPORT.md`、`README.md` 和 `wp3/HANDOVER.md` 均存在（Markdown 双语，结论在前）；通用条件 3–4 成立。

## 1. 工作区、隔离与 git

- **工作树和分支。** 在 WP0 中按需创建，此步骤可重复执行。
  - 基点：`exp/phase2-anchor-step-20261013` 的末端（写作时为 `6525edf`）。记录其哈希。
  - 创建：`git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1019_r15_probe -b exp/phase2-r15-probe-plan-20261019 <base>`。如果已存在，确认其历史包含 `<base>` 后复用。
  - 只在 `/Users/shane/Desktop/Arena_1019_r15_probe` 中工作。研究目录为 `research/phase2_r15_probe_plan_20261019/`。
- **本 prompt** 目前未提交，位于 `/Users/shane/Desktop/Arena_1013_model/research/phase2_r15_probe_plan_20261019/R15_EXECUTION_PROMPT.md`。把它复制到你工作树中的 `research/phase2_r15_probe_plan_20261019/EXECUTION_PROMPT.md`，并作为第一次提交。不要提交、移动或删除原文件。
- **只读来源。** 先运行 `git -C /Users/shane/Desktop/Arena_1013_model fetch origin`。用 `git … show <ref>:<path>` 读取，复制到 `sources/`，并在 `sources/SOURCES.md` 中记录引用、路径和 SHA256：
  - 第 6 轮 `exp/phase2-r6-robust-20261016`，位于 `research/phase2_r6_robust_20261016/` 下：`wp1/protocol.json`、`wp1/run_wp1.py`（18 个假设的网格 h = (Δ, f, d) 和归一化得分 s）、`wp6/run_wp6.py`、`wp6/REPORT.md`、`wp6/outputs/wp6_probe_plan.json`。它的探针向量是为**旧的** SUB（V2+√t，`21a7a55`）构造的，使用前必须在当前 SUB 上重建；
  - 第 11 轮 `exp/phase2-r11-eps-transfer-20261018`：`research/phase2_r11_eps_transfer_20261018/src/drift.py` 和 `wp5/decision.json`；
  - **第 12–14 轮的结果，若 origin 上存在：**
    - `exp/phase2-r12-eps-level-20261019`：`research/phase2_r12_eps_level_20261019/wp4/`（决策、`SOH_variants.csv`、`R13_HANDOFF.json`）；
    - `exp/phase2-r13-top-tail-20261019`：`research/phase2_r13_top_tail_20261019/wp3/R13_RESULT.json` 和 `wp3/SOH_variants.csv`；
    - `exp/phase2-r14-path-drift-20261019`：`research/phase2_r14_path_drift_20261019/wp3/R14_RESULT.json` 和 `wp3/SOH_variants.csv`。
    
    逐一记录为存在（附提交）或不存在；
  - 打包脚本 `research/phase2_v3_20261015/package_submission.py`（你的工作树里已有）。
  - **用户文件，只读，只列出和算哈希：** `/Users/shane/Desktop/Arena项目书面文件/提交包/` 和 `/Users/shane/Desktop/*Challenge2*.zip`。可以把 zip 解压到 git 忽略的 `cache/existing/` 中，读取其中的 `my_model/model_template.py`。永远不要修改、移动或删除原文件。
- **规则文件：** 你工作树中的 `TechArena_Challenge2_Team_Package/CHALLENGE2_DESCRIPTION.pdf` 和 `submission_instructions_2026.md`。
- **用户输入**（放在你的研究目录中，由用户填写；缺失时创建模板）：
  - `inputs/leaderboard_log.csv`，列为 `board_date, package_file, package_sha256, model_commit, metrics_verbatim, rank, notes`；
  - `inputs/deadline.txt`（日期、时间和时区，或"unknown"）；
  - `inputs/pptx_path.txt`（团队当前演示文稿的路径，或"template"）。
- **并发保护。** 开始时以及每次提交前运行 `git log --oneline -5`。遇到意外改动时，停止编辑共享文件，记录下来，之后只按明确路径添加文件。不要用 `git add -A` / `git add .`，不要改写他人的工作，不要用不带参数的 `git stash`。一个工作树同时只开一个会话。
- **提交。** 每一步结束时提交，然后运行 `git push -u origin exp/phase2-r15-probe-plan-20261019`。不要推送到其他地方，不要强制推送。每条提交信息的末尾加上 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。zip 永远不提交，放在 git 忽略的 `cache/packages/` 中。
- **不得修改**任何 `TechArena_Challenge2_Team_Package/` 目录、之前各轮的研究目录或本工作树之外的任何东西。变体都从 `cache/` 下的副本构建。
- **语言与字节码。** Markdown 先英文后中文。代码注释用英文。运行 Python 时用 `python3 -B`。不下载任何东西。

## 2. 背景

**任务。** 估计一个 4 × 102 Ah LFP 串联电池组在 CK1..CK7 的 SOH（C/20 容量隐藏，标称 102 Ah）。只公布了 CK0 = 100.41 Ah。所有本地检查都用代理标签（P_k = Q_fc,k + ε0 + Δ），而代理与真值之差是共模的：对每个估计器都是同一个向量 g_k。因此有两个标量在本地完全无法判断：
- ε 的水平（EPS_EXTRA_AH = 0.4，是假设；第 12 轮测量它）；
- ε 的漂移 d（第 13、14 轮给它定界）。

排行榜是唯一引入真值的地方。

**规则原文（在 WP0 中逐字引用）。**
- **PDF。** "Package and submit as often as you like … a public leaderboard is updated weekly"。另有一次缩减数据量的运行，可获得数据效率加分。
- **`submission_instructions_2026.md`：**
  - "Only CK0 is a target … Checkups CK1 to CK7 are hidden and scored … Do not attempt to reconstruct them from external sources."
  - "There is no limit on how many times you may resubmit before the deadline (<<TODO>>); **the last submission counts**."
  - "Submissions are evaluated **every two weeks** and the public leaderboard is updated accordingly." 这与 PDF 的"weekly"矛盾；两者都要记录。
  - 评分："error metrics of your SOH estimates (including the worst-case error), each normalised by the reference baseline — baseline = 1.0, lower is better. **The exact metric set is not published.**" 模型表现占总分的 70 %。
  - 最后一次提交里的演示文稿就是决赛现场使用的版本。

**本轮登记的合规立场。**
- 规则没有明确禁止探测。但"从外部来源"重建隐藏容量是被禁止的，而逐个检查点对着排行榜调参，在精神上就等于重建它们。所以本计划**最多允许两次探针提交**，条件如下：
  - 每个探针都是**只改动一个有物理依据的标量的整体模型变体**，且由之前某一轮登记产出；
  - 每个探针以及任何最终采纳的改动，都在 README 和报告中披露；
  - 最终模型必须仅凭物理依据就能自圆其说。
- WP2 起草一个给主办方的简短问题。是否发送由用户决定。

**之前的探针计划（第 6 轮，针对旧 SUB）。** P_drift（d = −0.031）→ P_stress_early → P_start。第 7 轮把顺序改为 P_stress_early → P_start → P_drift。第 6 轮在 18 个假设的网格上，用归一化得分 s（ExampleModel = 1）计算了期望 Δs。复用这套方法，不要重新推导。

**当前 SUB。** 基点上的 `my_model/model_template.py`（A3）。其 SOH：CK1 95.984，CK2 94.507，CK3 93.600，CK4 92.821，CK5 92.015，CK6 91.426，CK7 90.765（即打包脚本中的 `EXPECTED_SOH`）。在 WP0 中重新核实。

## 3. 工作包

### WP0 — 准备、规则审查与清点

1. 创建或复用工作树；写 `notes/STATUS.md`、`notes/DECISIONS.md` 和 `sources/SOURCES.md`；提交本 prompt；fetch 并复制来源文件。
2. 写 `wp0/RULES.md`。
   - 逐字引用第 2 节列出的每条规则，注明文件和行号或页码。
   - 列出未决事项：截止时间、提交平台、评估频率（每周还是每两周）、指标集，以及排行榜显示一个分数还是多个。
3. 输入模板缺失时创建它们。读取用户已填写的内容。若排行榜记录为空，记为"无观测"。
4. 写 `wp0/existing_packages.csv`，清点已有的 zip：
   - 文件名、大小、SHA256；
   - 其中 `model_template.py` 的 SHA256；
   - 对应的提交（把该文件的哈希与 `exp/phase2-anchor-step-20261013` 的历史比对得出）；
   - 用包的 CLI 跑出的 SOH 向量（在 `cache/existing/` 中运行）。
   
   根据排行榜记录，标出哪个 zip（如有）已经提交过。
5. 写 `wp0/candidates.md`：第 12–14 轮中哪些已存在、各自的结果（L1/L2/L3、O1/O2/O3），以及有哪些候选 SOH 向量。

**完成：** 工作树、记录文件、sources、输入模板、`wp0/RULES.md`、`wp0/existing_packages.csv`、`wp0/candidates.md` 和 `wp0/REPORT.md` 均已提交并推送。

### WP1 — 登记

写 `wp1/protocol.json`（及其哈希），并在任何 WP2 输出之前提交。它必须包含以下内容。

- **假设网格。**
  - 以第 6 轮的网格 h = (Δ, f, d) 为起点，原样复制。
  - Δ 轴替换为第 12 轮的 EPS_EXTRA 区间 {下端, 点估计, 上端}，前提是第 12 轮得到 L1 或 L2。否则保留 {0, 0.4, 0.8}。
  - d 轴替换为合并的 d_top = d_tail + d_path {下端, 中位数, 上端}，前提是第 13、14 轮都存在且可识别。若只有一轮存在，缺失的部分用第 11 轮的 [−0.036, +0.052] 补上。若两轮都不存在，保留第 6 轮的轴。
  - 真值向量 T_k(h) 完全按第 6 轮的方法构造。
- **指标族。** 由于官方指标集未公布，每条解读规则都必须对以下所有指标成立：
  - 第 6 轮的 s；
  - CK1–CK7 上的 MAE、RMSE 和 MAX，各自除以同一 h 下 ExampleModel 的同一指标（ExampleModel 通过包的 CLI 在本地运行）。
- **合格探针。** 每个只改动一个标量，在当前 SUB 上重建，并以研究副本的形式构造。
  - **P_level：** EPS_EXTRA 取第 12 轮点估计的 SUB。仅当第 12 轮得到 L2 时合格。
  - **P_A3fix：** 第 12 轮的锚点 3 修正。仅当第 12 轮的 G_a3 通过时合格。
  - **P_drift：** SUB + d，d = d_top 的中位数。第 13 轮或第 14 轮得到 O2 时合格。若两者都得到 O1，P_drift **不合格**。若两者都不存在，使用第 6 轮的 d = −0.031。
  - **P_stress_early：** 第 6 轮的 F1_S_B 融合。仅当能用第 6/7 轮的代码在当前 SUB 上重建、且不需要重新拟合时合格；否则放弃，并记录原因。
- **先用免费的信息。** 对每条已知其包 SOH 向量（WP0）的排行榜观测，计算每个假设在每个指标下的预测得分。保留那些在至少一个指标下、预测值与显示值在显示精度内相符的假设：这就是*存活集*。它只用来筛选假设，本身从不用来选择模型。
- **探针选择。** 对每个合格探针，在存活集（没有观测时用整个网格）上计算相对 SUB 的 Δs(h, 指标)。
  - 若在 ≥ 80 % 的存活假设上，四个指标给出的 sign(Δs) 都相同，则该探针*可解读*。
  - 可解读的探针先按期望 Δs（在存活集上均匀加权）排序，再按最坏情况的 Δs 排序。
  - **最多选两个。**若没有可解读的探针，计划就是"不做探针，保留 SUB"。
- **解读规则**（每个选中的探针一张表）。tol = 排行榜的显示精度（取自记录；未知时默认 0.005）。
  - 观测到的 Δs < −tol：把该探针的标量作为新的提交候选。
  - 观测到的 Δs > +tol：退回 SUB，并排除那一支假设。
  - |Δs| ≤ tol：没有信息，退回 SUB。
  - 如果排行榜显示多个指标，规则对每个指标都适用；只有当显示的任何指标都没有变差超过 tol 时，探针才算"胜出"。
- **最终状态规则。** 截止前的最后一次提交必须是观测到的最佳选项（默认是 SUB）。除非探针胜出，否则绝不能让探针成为最后一次提交。评估每两周一次且截止时间未知时，假设最多还剩两个评估周期。
- **合规规则。** 这些限制来自第 2 节的立场：最多两个探针，每个只改一个标量，在 README 和报告中披露，不做逐个检查点的修改。
- 写 `wp1/REPORT.md`，附"各结果意味着什么"表。

**完成：** 协议、哈希和 `wp1/REPORT.md` 均已提交并推送。

### WP2 — 计划

1. 在当前 SUB 上重建每个合格探针的 SOH 向量，保存 `wp2/probe_soh.csv`。
2. 计算存活集（若有观测）、每个探针 × 假设 × 指标的 Δs、可解读性和排名。保存 `wp2/delta_s_long.csv` 和 `wp2/ranking.csv`。
3. 写 `wp2/PROBE_PLAN.md`：
   - 选中的探针（或"不做探针"）、它们的 SOH 表和解读表；
   - 对照 `inputs/deadline.txt` 的时间线，每个评估周期按两周计；
   - 最终状态规则。
4. 写 `wp2/ORGANIZER_QUESTION.md`，一份简短的英文草稿，询问：为了在两个有记录的假设之间做出选择，提交一个只在一个有物理依据的常数上不同的变体，是否可以接受。**只是草稿，不要发送。**

**完成：** 探针向量、Δs 表、排名、`wp2/PROBE_PLAN.md`、`wp2/ORGANIZER_QUESTION.md` 和 `wp2/REPORT.md` 均已提交并推送。

### WP3 — 构建探针包并交接（不上传）

1. 对每个选中的探针，在 `cache/pkg_<probe>/` 下放一份完整的包副本。
   - 把 `my_model/model_template.py` 换成该探针的研究副本。与 SUB 的差异只能是登记的那个标量或登记的钩子，外加一行文档字符串。
   - 在 README 中加一小节，如实说明这个变体是什么、为什么提交它。
2. 把 `package_submission.py` 复制到 `src/`，只改三处：`PKG` 指向暂存的副本；`EXPECTED_SOH` 设为该探针自己的 CLI 输出；`--out` 默认为 `cache/packages/`。
   - 为每个探针构建 `Current State_Challenge2.zip`，各放在自己的子目录 `cache/packages/<probe>/` 中，参数为 `--members "Mona Zhu, Zhikuan Shen"`，`--pptx` 取自 `inputs/pptx_path.txt`。若该文件写的是"template"，在交接说明中记录一条警告。
   - 脚本会在全新的 Python 3.11 venv 中验证每个 zip；两项检查都必须通过。
3. 在 `wp3/packages.csv` 中记录每个 zip 的 SHA256。
4. 为用户写 `wp3/HANDOVER.md`：
   - 先上传哪个 zip，什么时候上传；
   - 上传之后要把什么、以什么方式填进 `inputs/leaderboard_log.csv`；
   - 什么时候运行 WP4；
   - 提醒：最后一次提交才算数；除非探针胜出，最后必须重新上传 SUB 的 zip；
   - 如有 pptx 警告，也写进去。
5. 写 `FINAL_REPORT.md` 和 `README.md`（结论在前）。

**绝不上传，绝不把 zip 复制到桌面，绝不碰已有的 zip。**

**完成：** 通过验证的 zip 位于 `cache/packages/`；`wp3/packages.csv`、`wp3/HANDOVER.md`、`wp3/REPORT.md`、`FINAL_REPORT.md` 和 `README.md` 均已提交并推送（zip 除外）。

### WP4 — 读取排行榜结果（在用户记录了每次评估之后运行）

1. 读取 `inputs/leaderboard_log.csv`。若自上次运行 WP4 以来没有新行，把状态设为"等待排行榜"，提交并停止。这是允许的结束状态。
2. 否则：
   - 核对每个记录的包哈希与 `wp3/packages.csv` 或 `wp0/existing_packages.csv` 是否一致；
   - 更新存活集；
   - 应用登记的解读规则；
   - 按最终状态规则给出决策和下一步行动。
3. 若决策是采纳某个探针的标量：
   - 写出 README 和报告中披露该探针及其物理依据的文字；
   - 按 WP3 的方式构建最终的包（不上传）；
   - 明确说明是否接入 `TechArena_Challenge2_Team_Package/` 由用户决定。
4. 更新 `FINAL_REPORT.md` 和 `wp4/REPORT.md`，每次运行加一个带日期的小节。

**完成：** 要么决策、可能的最终包和更新后的报告均已提交并推送；要么状态为"等待排行榜"并已提交。
