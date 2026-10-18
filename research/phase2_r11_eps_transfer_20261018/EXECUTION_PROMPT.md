<a id="en"></a>

# Round 11: Does the ε Drift Transfer to Our Pack? — Mechanism Decomposition on Truth-Bearing Open Data — Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-18. This document is self-contained. The English text is the execution text. The Chinese section is a translation for the reader; where the two differ, the English governs.

The work is split into **work packages WP0–WP6**. Each has its own *Done* list and can be run as a separate `/goal`.
- WP0 comes first and WP1 second.
- WP2, WP3 and WP4 depend only on WP1 and are independent of each other.
- WP5 needs WP2–WP4. WP6 is optional and may run at any time after WP1.
- `FINAL_REPORT.md` comes last.

## 0. Mode of work (all work packages)

- **Unattended.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Restarts.** Keep `notes/STATUS.md` current after every step: WP, done, next, last commit. On a restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume from there. Never redo a finished WP or step.
- **Honesty over targets.** A negative, inconclusive or "exit" result is a valid outcome. This round produces **evidence, bounds and a recommendation**. It never changes the submission, and it never uses the Challenge 2 proxy labels to choose anything.
- **Done for any WP** means the common criteria below, plus that WP's own list:
  1. its registered protocol (`wpN/protocol.json` + `wpN/protocol.sha256`) was committed **before** any of its evaluation outputs;
  2. its bilingual `wpN/REPORT.md` exists, conclusions first;
  3. `notes/STATUS.md` marks the WP done, capped, skipped or exited, with a one-line result;
  4. every commit is pushed to `origin exp/phase2-r11-eps-transfer-20261018`, and `git status` shows no uncommitted study files.
- **Global Done** (whole prompt):
  - WP0–WP5 are each done, capped, skipped or exited by a registered rule;
  - WP6 is done or skipped;
  - `FINAL_REPORT.md`, `README.md` and `wp5/R12_HANDOFF.json` exist (Markdown bilingual, conclusions first);
  - common criteria 3–4 hold.

## 1. Workspace, isolation, git

- **Worktree and branch.** Create them in WP0 if missing; the step is idempotent.
  - Base: `6525edf` on `exp/phase2-anchor-step-20261013` ("Wire the robust multi-variant cell-median step (A3) into the submission"). If the branch tip is newer, use the tip and record its hash.
  - Create: `git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1018_r11_eps -b exp/phase2-r11-eps-transfer-20261018 <base>`. If the worktree or branch already exists, check that its history contains `<base>` and reuse it.
  - Work only in `/Users/shane/Desktop/Arena_1018_r11_eps`. The study directory is `research/phase2_r11_eps_transfer_20261018/`.
- **Read-only sources outside this worktree.** Never `cd` into them and never write to them. Record every copied file with its source path or commit and its SHA256 in `sources/SOURCES.md`.
  - **External datasets** (git-ignored, so absent from your worktree): `/Users/shane/Desktop/Arena_1013_model/external_data/`.
    - `DATA_MANIFEST.md`
    - `LIC_aging/` (raw CSV is 1.1 GB; read it in chunks, or cache a parquet copy under your git-ignored `cache/`)
    - `Battery_expansion_force_data/` (Gotion)
    - `_screening/scripts/` (`lic_segments.py`, `lic_eps.py`, `gotion_cycles.py`, `gotion_steps.py`) and `_screening/outputs/` (`lic_eps.csv`, `gotion_cell_cycles.csv`, `gotion_module_cycles.csv`)
  - **Yagci 180 Ah cycling cells:** `/Users/shane/Desktop/Arena项目书面文件/外部数据/yagci/` (`Data.zip`, `readme.md`). Unzip into your git-ignored `cache/yagci/`, never in place. Checkup sheet #1500 duplicates #1000; the real test dates are in the raw file headers.
  - **Earlier rounds, read with `git -C /Users/shane/Desktop/Arena_1013_model show <ref>:<path>`:**
    - round 7 `exp/phase2-r7-lit-checks-20261016`: `research/phase2_r7_lit_checks_20261016/wp3/` (`eps_yagci.py`, `run_wp3.py`, `REPORT.md`, `outputs/`), which holds the Yagci ε definition and the "SUB + drift d" construction;
    - round 6 `exp/phase2-r6-robust-20261016`: `research/phase2_r6_robust_20261016/wp1/` (18-hypothesis grid) and `wp3/` (3a start-state audit, 3b drift);
    - round 5B `exp/phase2-r5b-electrode-model-20261014`: `research/phase2_r5b_electrode_model_20261014/FINAL_REPORT.md`, a negative result for full electrode-model reconstruction (see §2).
  - **Challenge data:** `TechArena_Challenge2_Team_Package/data/` in your own worktree (`CK0_reference_discharge.csv.gz`, `operation/`, `DATA_DESCRIPTION.md`) and `CHALLENGE2_DESCRIPTION.pdf`.
- **Concurrency guard.**
  - At the start and before every commit, run `git log --oneline -5` and compare it with your last commit.
  - On an unexpected commit or change: stop editing shared files, record it, and add files by explicit path only.
  - Never use `git add -A` or `git add .`, never rewrite others' work, never use a bare `git stash`. Run only one session on this worktree at a time.
- **Commits.**
  - Commit this prompt first, as `research/phase2_r11_eps_transfer_20261018/EXECUTION_PROMPT.md`.
  - Commit at the end of every step, then run `git push -u origin exp/phase2-r11-eps-transfer-20261018`. Never push elsewhere and never force.
  - End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify:** any `TechArena_Challenge2_Team_Package/` directory (anywhere), any earlier study directory, or any file outside this worktree.
- **Language and bytecode.**
  - Markdown is English first, Chinese second, in this file's layout. Code comments are English only.
  - Run Python with `python3 -B`. Use `python3 -I -B` for every script that reads external or downloaded files, and pass data paths as arguments.
- **Downloads** happen only in WP6.
  - Put each download in its own new directory under the git-ignored `cache/downloads/`.
  - Treat downloads as untrusted data and never execute anything from them.

## 2. Context

**Task.** Estimate the SOH of a 4 × 102 Ah LFP series pack on CK0..CK7. SOH is the C/20 capacity divided by 102 Ah. Per the challenge PDF, the C/20 capacity is a 5.1 A discharge to pack 11.2 V "after a full charge"; the full-charge protocol is not stated.
- Only CK0 = 100.41 Ah is released.
- The causal cut is `load_dataset(data, until=CK_k)`.
- The PDF states that a public leaderboard is updated weekly.

**Proxies** (all already seen):
- P_k = Q_fc,k + ε0 + Δ, where Q_fc,k is the first CCCV charge from near empty after CK_k.
- ε0 = 100.41 − Q_fc,0 = 0.29 Ah. Δ ∈ {0, 0.4, 0.8} is an assumed extra offset for the 25 °C anchors.
- Q_fc,0..7 = 100.12 (45 °C), 97.00, 95.66, 94.64, 93.75, 93.08, 92.64, 91.95 Ah. Proxy fade from CK0 to CK7 is about 8.2 Ah.

**What this round is about.** For any estimator c:

```
e_true(c,k) − e_proxy(c,k) = P_k − T_k =: g_k          (identical for every estimator)
g_k = −(ε_k − ε_0) − (Δ_true − Δ)                       if T_k = Q_fc,k + ε_k
```

The proxy-to-truth gap g_k is therefore the **same vector for every candidate**. Signed errors all shift together; MAE and MAX rankings can change only when candidates' errors straddle the shift. Round 6's 18-hypothesis grid h = (Δ, f, d) already handles that sensitivity.

What no previous round settled is **the size of the fade-proportional part, d = dε/d(fade), for this pack's protocol**. It decides whether "SUB + drift d" should be preferred, and how the leaderboard probe P_drift should be ordered.

**What earlier rounds found about d.** All are black-box slopes across mismatched protocols:

| Dataset | d (Ah per Ah of fade) | ε definition and protocol |
|---|---|---|
| LIC 280 Ah | −0.035 | 0.1C RPT discharge − first 1C CCCV charge after the RPT. Cycling at 1C, CV to 0.05C. RPT capacity test at 0.1C, CV to 0.05C. RPT k=5 hit the 10 h limit (excluded). |
| Gotion 53 Ah cell | −0.031 | charge Ah − independent calibration (protocol not stated, 0.1 Ah resolution) |
| Yagci 50 °C (cells 22, 28) | −0.057 | RPT 50 A CC-CV at 20 °C, operation at 50 °C |
| Yagci 35 °C (cells 19, 42) | +0.178 | the sign comes from checkup 0; without it there is no consistent drift |
| Pooled median | −0.033 | round 7; registered outcome "drift sign not robust" |

- The LIC ε series (from `_screening/outputs/lic_eps.csv`) is +0.22, +0.24, +0.25, +0.17, +0.11, [k5 truncated], −0.63, −0.04, −0.07, −0.10, −0.16, −0.81, −0.20, −0.23, −0.25. That pattern may be a **step at the truncated RPT plus a slow drift**, rather than one fade-proportional slope. This round tests that.
- **Protocol of our pack** (from the operating data and earlier rounds):
  - The anchor charge runs at 20.4 A (0.2C) CC to 14.0 V, then CV to 5.1 A (0.05C, the same current as the C/20 test).
  - CV Ah grows from 1.29 to 1.52 over the months.
  - Pack voltage 30 min after the CV end is 13.365–13.379 V. Cell temperature at the end of the charge is 26.9–27.2 °C.
  - Start voltages at rest are 11.80–11.95 V, except two unrelaxed starts: seg1 (45 °C, 11.53 V, rising +86 mV/h) and seg6 (11.47 → 11.62 V).
  - The pack enters each checkup charged (13.1–13.3 V). The CK0 C/20 curve starts at 13.59 V under load and ends with all four cells at 2.800–2.802 V.
  - The per-block Ah balance does not close (−0.3 to −1.1 Ah per block), so this pack's coulombic efficiency cannot be measured.
- **Round 5B negative result.** Reconstructing absolute Q_C20 from anchor curves with literature half-cell OCPs is not identifiable: admitted parameter spans are 8–10 Ah per anchor. Do not retry an absolute electrode-model reconstruction in this round.

**Submitted model SUB.** `my_model/model_template.py` at the base commit (T_main √t gap branch + A3 cell-median step). Record its SOH outputs by running the package's own CLI in WP0. "SUB + drift d" is defined exactly as in round 7 WP3 (`run_wp3.py`). Copy that function and do not re-derive it.

## 3. Work packages

### WP0 — Setup

1. Create or reuse the worktree, write `notes/STATUS.md`, `notes/DECISIONS.md` and `sources/SOURCES.md`, and commit this prompt.
2. Copy the needed scripts and earlier-round files (see §1) into `sources/`, with their SHA256.
3. Run SUB on the full data and save `wp0/SUB_SOH.csv`.
   - **Reproduction check.** Round 7's table was computed for the *older* submission V2+√t at `21a7a55`, not for the current SUB. Extract that package with `git archive` into the git-ignored `cache/sub_21a7a55/`. Apply the copied "SUB + drift d" function to it, and check that the SUB and "SUB + drift −0.031" rows match round 7's table to within 0.001 pp.
   - If they do not match, record the reason and stop at WP0 with status "exit: cannot reproduce".
   - Then apply the same function to the current SUB and save the result as `wp0/SUB_drift_reference.csv`.
4. Write `wp0/PACK_PROTOCOL.md`, a fact sheet of our protocol variables:
   - charge rate and CV cutoff, reference rate and cutoff;
   - temperature at the anchor charge and at the checkup (CK temperature unknown, assumed 25 °C);
   - start-state definition and rest before the anchor charge;
   - pack vs single cell.
   
   Take each value from the data or from §2, and cite the source.

**Done:** worktree, notes, sources, `wp0/SUB_SOH.csv`, the reproduction check and `wp0/PACK_PROTOCOL.md` are committed and pushed.

### WP1 — Protocol audit and registration (no ε values computed)

1. For **LIC**, audit the step sequence of every RPT and of the first cycles after each RPT. Run `lic_segments.py` (or a copy) to segment the data, then list, in order, each segment's sign, median current, duration, Ah, start and end voltage, end current, rest before, and median temperature.
   - Answer explicitly:
     - Does each RPT contain a 0.1C CCCV **charge** as well as the 0.1C discharge?
     - In which order do they occur?
     - Does the first 1C charge after the RPT start from the 0.1C-empty state, and after how long a rest?
     - Which segments are pulse tests?
   - Write the result to `wp1/lic_sequence.csv` and summarise it in `wp1/AUDIT.md`.
2. Do the same for **Yagci**: which RPT steps exist, their rates and temperatures, and whether an RPT charge capacity can be read. Do the same for **Gotion**: what the calibration table gives, and whether raw calibration steps exist.
3. **Register the decomposition** that the audited sequences permit, in `wp1/protocol.json`. The default, to be adapted only if a quantity does not exist, is:

   ```
   ε_total(k) = Q_ref,dis(k) − Q_op,ch,first(k)
              = [Q_ref,dis(k) − Q_ref,ch(k)]          T_CE    same-rate charge/discharge mismatch inside the RPT
              + [Q_ref,ch(k)  − Q_op,ch,first(k)]     T_path  rate, start state, temperature between reference and operating charge
   ```

   - Further annotate T_path with:
     - its CC and CV parts;
     - the start voltage and the rest duration before each charge;
     - the end current and the relaxed end voltage, which show whether the two charges reach the same top state.
   - If an RPT charge does not exist, record T_CE as "not identifiable" for that dataset. Do not substitute a proxy for it.
4. **Register the statistics.** For each term X of each dataset:
   - Report the Theil–Sen slope dX/d(fade) and the OLS slope, with fade = Q_ref,dis(0) − Q_ref,dis(k). Report leave-one-RPT-out ranges.
   - Compare three models by BIC: (a) linear in fade; (b) constant with one step at a registered event (for LIC, the truncated RPT k=5; other datasets: none unless the audit finds a protocol change); (c) linear plus that step.
   - **Outlier rule** (fixed now): flag a point when the start voltage of its operating charge, or its preceding rest duration, lies more than 3 MAD from that dataset's median. Report flagged points but keep them in the main estimate. Give a sensitivity analysis without them.
5. **Register the transfer rules and the decision rule (§4)** before any ε value is computed. Commit `protocol.json` and `protocol.sha256` first.

**Done:** audit files, registered protocol and `wp1/REPORT.md` are committed and pushed. No ε value appears in any WP1 file.

### WP2 — LIC decomposition

- Compute T_CE, T_path and ε_total for every usable RPT, plus T_path's annotations. Save `wp2/lic_terms.csv`.
- Apply the registered statistics. Report:
  - the slope of each term and its share of the total slope;
  - the BIC comparison (step vs drift);
  - whether the two charges in T_path reach the same top state (end current, relaxed voltage) and start from the same bottom state (start voltage, rest).
- Add a figure of each term against fade.
- Name the **dominant term**: the one whose slope is more than 60 % of the total slope. If the step model wins, say so; it means the "drift" is event-driven, not fade-driven.

**Done:** terms table, statistics JSON, figure and `wp2/REPORT.md` are committed and pushed.

### WP3 — Gotion and Yagci decomposition

- Apply WP2's procedure to each terms table that the WP1 audit allows; mark the rest "not identifiable".
- For Yagci, keep round 7's ε definition for ε_total, so the totals reproduce round 7's d (−0.057, +0.178 by group). Check this to within 0.005 Ah/Ah.
- Report the results with and without checkup 0. "Without checkup 0" is registered here as a sensitivity analysis; it is not a post-hoc choice.

**Done:** per-dataset term tables, statistics, figure and `wp3/REPORT.md` are committed and pushed.

### WP4 — Our pack's own driver series (no proxies, no labels)

For every anchor charge k = 0..7 (and the seg14 anchor if present), measure from the operating data the drivers of each term. Save `wp4/pack_drivers.csv`:
- CC Ah, CV Ah, CV duration, and the CV current decay constant (fit I(t) = I_∞ + A·e^(−t/τ) over the CV phase);
- the relaxed pack voltage and each cell's voltage 30 min after the CV end;
- the start voltage, its slope over the last 30 min of rest, the rest duration, and each cell's start voltage;
- the median cell temperature during the charge, and the spread across cells at the top and at the start.

Flag seg1 (45 °C, unrelaxed) and seg6 (unrelaxed). For each driver, compare its trend over our fade with the trend of the same driver in LIC over a matching fade range. **Do not compute any quantity that uses 100.41 or P_k in this WP.**

**Done:** driver table, figure and `wp4/REPORT.md` are committed and pushed.

### WP5 — Transfer, bounds and decision

1. Apply the registered transfer rules (§4) to obtain a **bound interval** [d_lo, d_hi] for our pack, and a point value only where §4 allows one.
2. Apply the registered decision rule (§4) and state the outcome (O1/O2/O3) and the dominant term.
3. Produce `wp5/SOH_variants.csv`: SUB and "SUB + drift d" for d ∈ {d_lo, point if any, d_hi, −0.031}. These are **leaderboard-only** numbers; never score them against proxies.
4. Recommend the leaderboard probe order (current order from round 7: P_stress_early → P_start → P_drift) and say whether the outcome changes it.
5. Write `wp5/R12_HANDOFF.json` for the follow-up mechanism study (round 12). It must contain:
   - outcome, dominant term, [d_lo, d_hi];
   - for each term: identifiable or not, and which of our pack's drivers (WP4) it maps to;
   - which pack-specific terms this round could not assess (at minimum: cell imbalance under pack-voltage cutoffs, the Δ offset at 25 °C, CE of this pack);
   - the anchors flagged in WP4.

**Done:** interval, decision, variants table, handoff JSON and `wp5/REPORT.md` are committed and pushed.

### WP6 — Optional: Figgener home-storage data (zenodo 12091223)

- First query only the record's metadata (the Zenodo API file list and sizes, plus the readme). Do not download raw data until the screening below passes.
- Proceed only if all of these hold:
  - at least one system is LFP;
  - field capacity tests are included, with their protocol;
  - the operating charge data around those tests are included;
  - the total download needed is ≤ 3 GB.
- If so, compute ε_total and, where possible, its terms for those systems, using the WP1 statistics. Register the protocol before computing.
- Otherwise record "skipped: <reason>".

**Done:** `wp6/REPORT.md` (results, or the reason it was skipped) is committed and pushed.

## 4. Registered transfer and decision rules (copy into `wp1/protocol.json` verbatim)

- **Transfer.** The bounds are partial-identification bounds. No term is scaled by an invented factor.
  - **T_CE** transfers with factor 1, in Ah per Ah of fade. LFP-intrinsic side reactions are assumed protocol-independent to first order. This is a stated assumption.
  - **T_path** transfers with an unknown factor in [0, 1], because our anchor differs from LIC's operating charge in rate (0.2C vs 1C), start state and temperature. The factor is 1 only if WP4 shows our drivers trend like LIC's. It is 0 only if WP2 shows that T_path is carried entirely by drivers whose trend WP4 finds flat in our pack, for example the relaxed top voltage and the start voltage.
  - d_lo and d_hi are the minimum and maximum, over the factor range, of the combined slope from the datasets where each term is identifiable. Pooling across datasets uses the median, plus a leave-one-dataset-out range.
  - A step-type component (WP2 BIC model (b) or (c) winning) transfers **only** if our pack has an analogous event. Our candidates for such an event are the missing segment 3 and the seg1 45 °C anchor. Otherwise it is excluded from d and reported separately.
- **Decision** (with our fade ≈ 8.2 Ah by CK7):
  - **O1 "drift small":** [d_lo, d_hi] ⊂ [−0.012, +0.012] Ah/Ah, i.e. a CK7 shift of at most about 0.1 pp. Recommendation: keep SUB and move P_drift to last or drop it.
  - **O2 "drift transfers":** d_hi < −0.015. Recommendation: P_drift becomes the first probe, and the report states the bias.
  - **O3 "inconclusive":** any other case. Recommendation: keep round 7's order, and round 12 models the dominant term on our own data.
- **Dominant term:** the term whose slope is more than 60 % of the total in the pooled estimate. Otherwise the result is "mixed".

---

<a id="zh"></a>

# 第 11 轮：ε 漂移能否迁移到我们的电池组？——在有真值的公开数据上做机理分解——执行 Prompt

> **语言：** [English](#en) · 中文

2026-10-18 编写。本文件自成一体。英文是执行文本，中文是给读者的翻译；两者不一致时以英文为准。

工作分为 **WP0–WP6** 共七个工作包，每个都有自己的完成清单，可以作为单独的 `/goal` 运行。
- WP0 最先做，WP1 其次。
- WP2、WP3、WP4 只依赖 WP1，彼此独立。
- WP5 需要 WP2–WP4。WP6 可选，WP1 之后任何时候都可以做。
- `FINAL_REPORT.md` 最后写。

## 0. 工作方式（所有工作包）

- **无人值守。** 不要停下来提问。遇到未定的选择，取满足本文所有规则的最保守选项，记入 `notes/DECISIONS.md` 后继续。
- **重启。** 每完成一步就更新 `notes/STATUS.md`：当前 WP、已完成、下一步、最后一次提交。重启时先读 `notes/STATUS.md` 和 `notes/DECISIONS.md`，从断点继续。已完成的 WP 或步骤不要重做。
- **诚实优先于目标。** 阴性、无定论或"退出"都是有效结果。本轮产出**证据、区间和建议**。本轮不改动提交，也不用 Challenge 2 的代理标签做任何选择。
- **任一 WP 完成**的条件是下面的通用条件，加上该 WP 自己的清单：
  1. 登记协议（`wpN/protocol.json` + `wpN/protocol.sha256`）的提交**早于**该 WP 的任何评估输出；
  2. 双语的 `wpN/REPORT.md` 已写好，结论在前；
  3. `notes/STATUS.md` 已把该 WP 标为完成、封顶、跳过或退出，并附一行结果；
  4. 所有提交都已推送到 `origin exp/phase2-r11-eps-transfer-20261018`，`git status` 中没有未提交的研究文件。
- **全局完成**（整个 prompt）：
  - WP0–WP5 均已完成、封顶、跳过，或按登记规则退出；
  - WP6 已完成或跳过；
  - `FINAL_REPORT.md`、`README.md` 和 `wp5/R12_HANDOFF.json` 都已存在（Markdown 双语，结论在前）；
  - 通用条件 3–4 成立。

## 1. 工作区、隔离与 git

- **工作树与分支。** 缺失时在 WP0 创建；这一步可以重复执行。
  - 基点：`exp/phase2-anchor-step-20261013` 上的 `6525edf`（"Wire the robust multi-variant cell-median step (A3) into the submission"）。如果分支末端更新，就用末端，并记录哈希。
  - 创建命令：`git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1018_r11_eps -b exp/phase2-r11-eps-transfer-20261018 <base>`。如果工作树或分支已存在，检查其历史包含 `<base>` 后复用。
  - 只在 `/Users/shane/Desktop/Arena_1018_r11_eps` 中工作。研究目录是 `research/phase2_r11_eps_transfer_20261018/`。
- **工作树之外的只读来源。** 不要 `cd` 进去，也不要写入。每个复制过来的文件都要在 `sources/SOURCES.md` 中记录来源路径或提交，以及 SHA256。
  - **外部数据集**（被 git 忽略，所以你的工作树里没有）：`/Users/shane/Desktop/Arena_1013_model/external_data/`。
    - `DATA_MANIFEST.md`
    - `LIC_aging/`（原始 CSV 有 1.1 GB；分块读取，或在你被 git 忽略的 `cache/` 里缓存一份 parquet）
    - `Battery_expansion_force_data/`（国轩）
    - `_screening/scripts/`（`lic_segments.py`、`lic_eps.py`、`gotion_cycles.py`、`gotion_steps.py`）和 `_screening/outputs/`（`lic_eps.csv`、`gotion_cell_cycles.csv`、`gotion_module_cycles.csv`）
  - **Yagci 180 Ah 循环芯：** `/Users/shane/Desktop/Arena项目书面文件/外部数据/yagci/`（`Data.zip`、`readme.md`）。解压到你被 git 忽略的 `cache/yagci/`，不要原地解压。检查表 #1500 与 #1000 重复；真实测试日期在原始文件的表头里。
  - **之前各轮，用 `git -C /Users/shane/Desktop/Arena_1013_model show <ref>:<path>` 读取：**
    - 第 7 轮 `exp/phase2-r7-lit-checks-20261016`：`research/phase2_r7_lit_checks_20261016/wp3/`（`eps_yagci.py`、`run_wp3.py`、`REPORT.md`、`outputs/`），其中有 Yagci 的 ε 定义和"SUB + drift d"的构造；
    - 第 6 轮 `exp/phase2-r6-robust-20261016`：`research/phase2_r6_robust_20261016/wp1/`（18 假设网格）和 `wp3/`（3a 起点状态审查、3b 漂移）；
    - 第 5B 轮 `exp/phase2-r5b-electrode-model-20261014`：`research/phase2_r5b_electrode_model_20261014/FINAL_REPORT.md`，即完整电极模型重建的阴性结果（见 §2）。
  - **赛题数据：** 你自己工作树里的 `TechArena_Challenge2_Team_Package/data/`（`CK0_reference_discharge.csv.gz`、`operation/`、`DATA_DESCRIPTION.md`），以及 `CHALLENGE2_DESCRIPTION.pdf`。
- **并发保护。**
  - 开始时和每次提交前运行 `git log --oneline -5`，与你上一次的提交比对。
  - 发现意外的提交或改动时：停止编辑共享文件，记录下来，之后只按明确路径添加文件。
  - 不要用 `git add -A` 或 `git add .`，不要改写别人的工作，不要用不带参数的 `git stash`。同一时间只在这个工作树上运行一个会话。
- **提交。**
  - 先提交本 prompt，路径为 `research/phase2_r11_eps_transfer_20261018/EXECUTION_PROMPT.md`。
  - 每一步结束时提交，然后运行 `git push -u origin exp/phase2-r11-eps-transfer-20261018`。不推送到别处，也不强推。
  - 每条提交信息末尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **不得修改：** 任何位置的 `TechArena_Challenge2_Team_Package/` 目录、任何之前的研究目录、本工作树之外的任何文件。
- **语言与字节码。**
  - Markdown 先英文后中文，版式同本文件。代码注释只用英文。
  - 用 `python3 -B` 运行 Python。凡是读取外部或下载文件的脚本都用 `python3 -I -B`，数据路径作为参数传入。
- **下载**只在 WP6 中进行。
  - 每次下载放进被 git 忽略的 `cache/downloads/` 下的一个新目录。
  - 下载内容视为不可信数据，绝不执行其中任何东西。

## 2. 背景

**任务。** 估计一个 4 × 102 Ah LFP 串联电池组在 CK0..CK7 的 SOH。SOH 是 C/20 容量除以 102 Ah。按赛题 PDF，C/20 容量是"满充后"以 5.1 A 放电到电池组 11.2 V 的容量；满充协议没有说明。
- 只公布了 CK0 = 100.41 Ah。
- 因果截断为 `load_dataset(data, until=CK_k)`。
- PDF 写明公开排行榜每周更新。

**代理标签**（都已看过）：
- P_k = Q_fc,k + ε0 + Δ，其中 Q_fc,k 是 CK_k 之后第一次从接近放空开始的 CCCV 充电量。
- ε0 = 100.41 − Q_fc,0 = 0.29 Ah。Δ ∈ {0, 0.4, 0.8} 是对 25 °C 锚点假设的额外偏移。
- Q_fc,0..7 = 100.12（45 °C）、97.00、95.66、94.64、93.75、93.08、92.64、91.95 Ah。CK0 到 CK7 的代理衰减约 8.2 Ah。

**本轮研究的问题。** 对任意估计器 c：

```
e_true(c,k) − e_proxy(c,k) = P_k − T_k =: g_k          （对每个估计器都相同）
g_k = −(ε_k − ε_0) − (Δ_true − Δ)                       若 T_k = Q_fc,k + ε_k
```

因此代理与真值之间的差距 g_k 对**所有候选都是同一个向量**。有符号误差一起平移；只有当候选的误差分布在平移量两侧时，MAE 和 MAX 排名才会变。第 6 轮的 18 假设网格 h = (Δ, f, d) 已经处理了这种敏感性。

之前各轮都没有解决的是：**按本电池组的协议，随衰减成比例的那部分 d = dε/d(衰减) 有多大。** 它决定"SUB + drift d"是否应该优先，以及排行榜探测 P_drift 排在第几。

**之前各轮关于 d 的结果。** 都是在协议不匹配的数据上算出的黑箱斜率：

| 数据集 | d（每 Ah 衰减对应的 Ah） | ε 定义与协议 |
|---|---|---|
| LIC 280 Ah | −0.035 | 0.1C RPT 放电 − RPT 后第一次 1C CCCV 充电。循环为 1C，CV 截止 0.05C。RPT 容量测试为 0.1C，CV 截止 0.05C。RPT k=5 触发 10 h 上限（已排除）。 |
| 国轩 53 Ah 单芯 | −0.031 | 充电 Ah − 独立标定（协议未说明，精度 0.1 Ah） |
| Yagci 50 °C（芯 22、28） | −0.057 | RPT 为 20 °C 下 50 A CC-CV，运行在 50 °C |
| Yagci 35 °C（芯 19、42） | +0.178 | 正号来自第 0 次检查；去掉后没有一致的漂移 |
| 合并中位数 | −0.033 | 第 7 轮；登记结果为"漂移符号不稳健" |

- LIC 的 ε 序列（来自 `_screening/outputs/lic_eps.csv`）为 +0.22、+0.24、+0.25、+0.17、+0.11、[k5 被截断]、−0.63、−0.04、−0.07、−0.10、−0.16、−0.81、−0.20、−0.23、−0.25。这个形态可能是**截断 RPT 处的一个台阶加上缓慢漂移**，而不是一条随衰减成比例的斜率。本轮检验这一点。
- **本电池组的协议**（来自运行数据和之前各轮）：
  - 锚点充电以 20.4 A（0.2C）恒流到 14.0 V，然后恒压到 5.1 A（0.05C，与 C/20 测试电流相同）。
  - CV 段的 Ah 逐月从 1.29 增长到 1.52。
  - CV 结束 30 min 后电池组电压为 13.365–13.379 V。充电结束时电芯温度为 26.9–27.2 °C。
  - 静置起点电压为 11.80–11.95 V，有两次起点未弛豫：seg1（45 °C，11.53 V，以 +86 mV/h 上升）和 seg6（11.47 → 11.62 V）。
  - 电池组进入每次检查时都是充电态（13.1–13.3 V）。CK0 的 C/20 曲线在负载下从 13.59 V 开始，结束时四个电芯都在 2.800–2.802 V。
  - 每个循环块的 Ah 收支不闭合（每块 −0.3 到 −1.1 Ah），所以本电池组的库伦效率无法测量。
- **第 5B 轮的阴性结果。** 用文献半电池 OCP 从锚点曲线重建绝对 Q_C20 不可识别：每个锚点允许的参数范围相差 8–10 Ah。本轮不要再尝试绝对电极模型重建。

**提交模型 SUB。** 基点提交上的 `my_model/model_template.py`（T_main √t 缺口分支 + A3 电芯中位数台阶）。在 WP0 用包自带的 CLI 运行，记录它的 SOH 输出。"SUB + drift d"严格按第 7 轮 WP3（`run_wp3.py`）的定义构造。复制那个函数，不要重新推导。

## 3. 工作包

### WP0 — 准备

1. 创建或复用工作树，写好 `notes/STATUS.md`、`notes/DECISIONS.md` 和 `sources/SOURCES.md`，提交本 prompt。
2. 把需要的脚本和之前各轮的文件（见 §1）复制到 `sources/`，附 SHA256。
3. 在完整数据上运行 SUB，保存 `wp0/SUB_SOH.csv`。
   - **复现检查。** 第 7 轮的表是对*旧版*提交 V2+√t（`21a7a55`）算的，不是当前的 SUB。用 `git archive` 把那个包解到被 git 忽略的 `cache/sub_21a7a55/`，对它套用复制来的"SUB + drift d"函数，检查 SUB 行和"SUB + drift −0.031"行与第 7 轮的表在 0.001 pp 以内一致。
   - 如果不一致，记录原因，以"exit: cannot reproduce"状态停在 WP0。
   - 然后对当前 SUB 套用同一个函数，结果保存为 `wp0/SUB_drift_reference.csv`。
4. 写 `wp0/PACK_PROTOCOL.md`，列出本题协议变量：
   - 充电倍率和 CV 截止、参考倍率和截止；
   - 锚点充电时的温度和检查时的温度（检查温度未知，假设 25 °C）；
   - 起点状态的定义和锚点充电前的静置；
   - 电池组还是单芯。
   
   每个值都取自数据或 §2，并注明来源。

**完成：** 工作树、记录文件、sources、`wp0/SUB_SOH.csv`、复现检查和 `wp0/PACK_PROTOCOL.md` 均已提交并推送。

### WP1 — 协议审查与登记（不计算任何 ε 值）

1. 对 **LIC**，审查每次 RPT 以及每次 RPT 之后前几个循环的工步序列。先运行 `lic_segments.py`（或其副本）分段，然后按顺序列出每段的符号、电流中位数、时长、Ah、起止电压、结束电流、之前的静置时长和温度中位数。
   - 明确回答：
     - 每次 RPT 除了 0.1C 放电，是否还有 0.1C CCCV **充电**？
     - 两者的顺序是什么？
     - RPT 后第一次 1C 充电是否从 0.1C 放空状态开始，之前静置多久？
     - 哪些段是脉冲测试？
   - 结果写入 `wp1/lic_sequence.csv`，并在 `wp1/AUDIT.md` 中总结。
2. 对 **Yagci** 做同样的事：有哪些 RPT 工步、倍率和温度，能否读出 RPT 的充电容量。对**国轩**：标定表给了什么，有没有原始标定工步。
3. 在 `wp1/protocol.json` 中**登记审查出的序列允许的分解**。默认形式如下，只有某个量不存在时才调整：

   ```
   ε_total(k) = Q_ref,dis(k) − Q_op,ch,first(k)
              = [Q_ref,dis(k) − Q_ref,ch(k)]          T_CE    RPT 内同倍率充放电之差
              + [Q_ref,ch(k)  − Q_op,ch,first(k)]     T_path  参考充电与运行充电之间的倍率、起点状态和温度差异
   ```

   - T_path 还要附上：
     - 它的 CC 和 CV 两部分；
     - 每次充电前的起点电压和静置时长；
     - 结束电流和弛豫后的结束电压，用来判断两次充电是否到达同一个顶部状态。
   - 如果某个数据集没有 RPT 充电，就把它的 T_CE 记为"不可识别"，不要用代理量替代。
4. **登记统计方法。** 对每个数据集的每一项 X：
   - 报告 Theil–Sen 斜率 dX/d(衰减) 和 OLS 斜率，其中衰减 = Q_ref,dis(0) − Q_ref,dis(k)。报告逐一剔除 RPT 后的范围。
   - 用 BIC 比较三个模型：(a) 随衰减线性；(b) 常数，在一个登记的事件处有一个台阶（LIC 为被截断的 RPT k=5；其他数据集没有，除非审查发现协议变化）；(c) 线性加该台阶。
   - **离群点规则**（现在定死）：如果某点对应的运行充电起点电压，或之前的静置时长，偏离该数据集中位数超过 3 MAD，就标记该点。被标记的点要报告，但保留在主估计中；另给剔除它们的敏感性分析。
5. 在计算任何 ε 值之前，**登记迁移规则和决策规则（§4）**。先提交 `protocol.json` 和 `protocol.sha256`。

**完成：** 审查文件、登记协议和 `wp1/REPORT.md` 均已提交并推送。WP1 的任何文件中都不出现 ε 值。

### WP2 — LIC 分解

- 对每次可用的 RPT 计算 T_CE、T_path、ε_total，以及 T_path 的附注。保存 `wp2/lic_terms.csv`。
- 套用登记的统计方法。报告：
  - 各项的斜率及其占总斜率的比例；
  - BIC 比较（台阶 vs 漂移）；
  - T_path 中两次充电是否到达同一个顶部状态（结束电流、弛豫电压），是否从同一个底部状态开始（起点电压、静置）。
- 给出各项随衰减变化的图。
- 指出**主导项**：斜率超过总斜率 60% 的那一项。如果台阶模型胜出，要明确说出来；这意味着"漂移"是事件驱动的，而不是随衰减变化的。

**完成：** 分项表、统计 JSON、图和 `wp2/REPORT.md` 均已提交并推送。

### WP3 — 国轩与 Yagci 的分解

- 对 WP1 审查允许的每个分项表套用 WP2 的流程；其余标为"不可识别"。
- Yagci 的 ε_total 沿用第 7 轮的定义，使总量能复现第 7 轮按组得到的 d（−0.057、+0.178），误差在 0.005 Ah/Ah 以内。
- 结果给出含与不含第 0 次检查两个版本。"不含第 0 次检查"在这里登记为敏感性分析，不是事后选择。

**完成：** 各数据集的分项表、统计、图和 `wp3/REPORT.md` 均已提交并推送。

### WP4 — 本电池组自身的驱动量序列（不用代理，不用标签）

对每次锚点充电 k = 0..7（如果有 seg14 的锚点也算上），从运行数据中测量各项的驱动量，保存到 `wp4/pack_drivers.csv`：
- CC Ah、CV Ah、CV 时长，以及 CV 电流衰减常数（在 CV 段拟合 I(t) = I_∞ + A·e^(−t/τ)）；
- CV 结束 30 min 后的电池组弛豫电压和各电芯电压；
- 起点电压、静置最后 30 min 的电压斜率、静置时长和各电芯起点电压；
- 充电期间电芯温度的中位数，以及顶部和起点处各电芯之间的离散度。

标记 seg1（45 °C、未弛豫）和 seg6（未弛豫）。对每个驱动量，比较它在我们衰减过程中的趋势与它在 LIC 中相同衰减范围内的趋势。**本 WP 中不计算任何用到 100.41 或 P_k 的量。**

**完成：** 驱动量表、图和 `wp4/REPORT.md` 均已提交并推送。

### WP5 — 迁移、区间与决策

1. 套用登记的迁移规则（§4），得到本电池组的**区间** [d_lo, d_hi]；只有 §4 允许时才给点估计。
2. 套用登记的决策规则（§4），给出结果（O1/O2/O3）和主导项。
3. 生成 `wp5/SOH_variants.csv`：SUB 以及 d ∈ {d_lo, 点估计（如有）, d_hi, −0.031} 时的"SUB + drift d"。这些**仅供排行榜使用**，不要拿代理标签给它们打分。
4. 给出排行榜探测顺序的建议（第 7 轮的现行顺序：P_stress_early → P_start → P_drift），说明本轮结果是否改变这个顺序。
5. 为后续的机理研究（第 12 轮）写 `wp5/R12_HANDOFF.json`，内容包括：
   - 结果、主导项、[d_lo, d_hi]；
   - 每一项是否可识别，以及对应本电池组的哪些驱动量（WP4）；
   - 本轮无法评估的电池组特有项（至少包括：电池组电压截止下的电芯不一致、25 °C 的 Δ 偏移、本电池组的库伦效率）；
   - WP4 中被标记的锚点。

**完成：** 区间、决策、变体表、交接 JSON 和 `wp5/REPORT.md` 均已提交并推送。

### WP6 — 可选：Figgener 家储数据（zenodo 12091223）

- 先只查询记录的元数据（Zenodo API 的文件列表和大小，以及 readme）。下面的筛选通过之前，不要下载原始数据。
- 只有以下条件全部满足才继续：
  - 至少有一个系统是 LFP；
  - 包含现场容量测试及其协议；
  - 包含这些测试前后的运行充电数据；
  - 需要下载的总量不超过 3 GB。
- 满足时，用 WP1 的统计方法对这些系统计算 ε_total，能分项时也分项。计算之前先登记协议。
- 否则记录"skipped: <原因>"。

**完成：** `wp6/REPORT.md`（结果，或跳过的原因）已提交并推送。

## 4. 登记的迁移规则与决策规则（原样复制进 `wp1/protocol.json`）

- **迁移。** 区间是部分识别意义下的区间，任何一项都不乘编造的系数。
  - **T_CE** 按系数 1 迁移，单位为每 Ah 衰减对应的 Ah。这里假设 LFP 固有的副反应在一阶近似下与协议无关；这是一条明说的假设。
  - **T_path** 的迁移系数未知，取值在 [0, 1]，因为我们的锚点与 LIC 的运行充电在倍率（0.2C 对 1C）、起点状态和温度上都不同。只有当 WP4 显示我们的驱动量与 LIC 趋势相同时，系数才取 1。只有当 WP2 显示 T_path 完全由 WP4 在我们电池组中测出趋势平坦的驱动量承载时（例如弛豫后的顶部电压和起点电压），系数才取 0。
  - d_lo 和 d_hi 是在系数范围内，由各项可识别的数据集合成的总斜率的最小值和最大值。跨数据集合并用中位数，并给出逐一剔除数据集的范围。
  - 台阶型成分（WP2 中 BIC 模型 (b) 或 (c) 胜出）**只有**在我们的电池组有类似事件时才迁移。可能的类似事件是缺失的 segment 3 和 seg1 的 45 °C 锚点。否则把它排除在 d 之外，单独报告。
- **决策**（按 CK7 时衰减约 8.2 Ah 计）：
  - **O1"漂移小"：** [d_lo, d_hi] ⊂ [−0.012, +0.012] Ah/Ah，即 CK7 平移不超过约 0.1 pp。建议：保留 SUB，把 P_drift 放到最后或取消。
  - **O2"漂移可迁移"：** d_hi < −0.015。建议：P_drift 改为第一个探测，报告中写明这项偏差。
  - **O3"无定论"：** 其他情况。建议：保持第 7 轮的顺序，由第 12 轮在我们自己的数据上对主导项建模。
- **主导项：** 合并估计中斜率超过总斜率 60% 的项；否则结果为"混合"。
