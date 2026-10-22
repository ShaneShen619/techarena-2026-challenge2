<a id="en"></a>

# Round 18: Does the anchor + graphite-step method transfer? A truth-bearing test on the Challenge 1 cells — Execution prompt

> **Language:** English · [中文](#zh)

Written 2026-10-22. This document is self-contained. The English text is the execution text; the Chinese section is a translation, and if they differ the English governs.

The registered protocol is [protocol.json](protocol.json). The registered code is `src/`, `tests/` and `run_wp*.py`. Their SHA-256 values are in [protocol.sha256](protocol.sha256). All of it was committed **before any Challenge 1 output of this study existed**. The self-tests (WP1) pass in the cloud session that wrote them; the real run below has not happened yet.

## Why this round (read first)

- **Every validation of SUB so far scores against proxies that share SUB's level.** The proxy is the post-checkup full charge + ε. The first leaderboard reading (SUB 0.1868, 2026-10-20) implies a real error of about 0.7–1.0 pp. Proxies show whether SUB is self-consistent. They cannot show whether its **mechanism** is right: does the graphite step track capacity, and does β convert it correctly?
- **The six Challenge 1 cells are the same 102 Ah LFP cell type as the pack.**
  - Every cycle has voltage, current and a discharge-capacity label (0.5C/1C to 2.5 V).
  - They cover 25/35/45/55 °C.
  - The rules allow Challenge 1 data to be used again.
- **So the method can be tested where truth exists.** On each cell, the pack's information structure is emulated, and the submitted decision logic runs **unchanged**.
- **What the result is for:**
  - the report's Technical Innovation criterion (transferability, use of open data);
  - SUB's risk statements (β, step noise, first month).
- **It does not change the submission in this round.**

## What is tested: claims of the submitted README → checks

Rules are quoted from `protocol.json` → `gates` / `mechanism_checks`. The unit is the physical cell, n = number of counted cells, and δ = the registered noise threshold.

| # | Claim in the submitted README / REPORT | Check | Registered rule |
|---|---|---|---|
| C1 | The in-month step update tracks the loss after the anchor | E2_SUB vs E0_anchor | supported: macro MAE ratio ≤ 0.70, E2 better on ≥ ⌈5n/6⌉ cells, every leave-one-cell-out ratio ≤ 0.80, and the shuffle control fails by ≥ δ on ≥ ⌈5n/6⌉ cells |
| C1b | … and it carries more than a trend | E2_SUB vs E5_trend | supported: gain ≥ δ and better on ≥ ⌈2n/3⌉ cells |
| C2 | Loss of lithium inventory shortens the step-to-top distance; β 1.06–1.51 | β_realised per cell | descriptive, against the pack (1.06–1.51; round 8 1/b = 1.34) |
| C3 | β from the charge-side anchors | E2_SUB vs E2_beta1; \|β_V2 − β_realised\| | supported: gain ≥ δ on ≥ ⌈2n/3⌉ cells; a mismatch > 0.30 is reported |
| C4 | Phase-matched month-end differences | E2_SUB vs E1_fallback on phase targets | supported: gain ≥ δ on ≥ ⌈2n/3⌉ cells |
| C5 | The six-variant median is robust | robust key vs each single variant | supported: ≤ median single and within δ of the best |
| C6 | Step noise is small (pack: 0.012–0.036 Ah) | within-window residual SD | descriptive |
| C7 | ε drift is small | ε_j vs fade | descriptive, against round 11 (−0.036 … +0.052 Ah/Ah) |
| C8 | Far better than the partial-charge baseline | E2 / E4 MAE per cell | supported: ≤ 0.30 on every cell |
| C9 | √t extrapolation over a coverage gap | gap scenario | report only (pack-specific choice) |
| C10–C12 | Sanity | truncation, C-rate, window overlap | descriptive |

## The emulation (protocol.json → `information_structure`, `model`)

| Pack | Emulated on a Challenge 1 cell |
|---|---|
| One month between checkups | A window of 30 days from B_0 (sensitivity: 20 and 45 days) |
| Post-checkup anchor: full CCCV charge from empty | The full charge of the first eligible cycle after each boundary. Its discharge stays hidden |
| A deep program about every 5 days, reaching 55.9 Ah below full | The first eligible cycle after every 5-day mark. Only the discharge down to 56 Ah and the top 21 Ah of its charge are visible |
| CK0 = 100.41 Ah, the only label | label0 = the label of the anchor-0 cycle, the only label the model receives |
| Hidden C/20 at CK1–CK7 | truth(B_k) = median of the 5 labels nearest B_k, all within ±2 days |
| CK2: last visible step 22 days before | gap scenario: programs in the last 22 days before B_k are hidden |
| 25/45 °C anchors, EPS_EXTRA 0.4 Ah | One temperature per cell, so EPS_EXTRA = 0. Setpoints become role labels (anchor 0 → 45, later anchors → 25, programs → 45) and the Arrhenius clock is uniform |

**"Submitted logic unchanged" means the following.**
- `src/model_adapter.TransferModel` subclasses the submitted `MyModel` and overrides only `diagnose` (events come from the view, not from pack rows).
- Thin wrappers record which branch fired, x and β.
- Ablations switch exactly one part off:
  - E0 sees no steps;
  - E1 disables the phase branch;
  - E2_beta1 fixes β = 1;
  - in the gap scenario, E1_fallback_no_sqrt also disables the √t rule.
- `src/steps.py` calls the submitted `_locate_step`, `_locate_dvdq` and `_charge_step_to_top` on the single cell, passed as four identical columns. Only the current bands are scaled, from ~10 A to |I_dis|.
- WP1 proves that the adapter equals the submitted `_robust_step` **bit for bit** on all of the pack's deep discharges.

**Two claim levels.**
- **`code_as_is`** (key `robust`): the submitted locators.
- **`method`** (key `robust_interp`): the midpoint crossings are interpolated between samples.
- **Why two:** at 30 s and 0.5C/1C one sample spans 0.43/0.85 Ah, against 0.03 Ah on the pack. In the synthetic self-test, the as-is step noise was 0.12–0.36 Ah and the interpolated noise 0.03–0.05 Ah. A failure at `code_as_is` alone is a sampling limit of these files, not of the method.

## What this round cannot test

- **The ε level of the C/20 pack test.** The Challenge 1 label is a 0.5C/1C discharge of one cell to 2.5 V. So the leaderboard's level question stays out of reach.
- **The 25/45 °C alternation and the post-checkup step offset.** Each cell runs at one temperature, and there are no checkups.
- **Calendar-like fade.** The cells cycle continuously; √t is a pack-specific choice, hence C9 is report only.
- **The 4-cell median.** Each test unit is a single cell.
- **Self-heating.** The "25 °C" cells run at 37–41 °C under cycling (round 5A, stage 2).
- **Exposure.** The Challenge 1 labels were used before (round 5A's prior, the phase-1 transfer routes), so their fade curves have been seen. The method's errors on them have never been computed. Label every number "labels exposed, method errors unexposed".

## Rough expectations, written before running

- **C1 at `method` level: likely supported.** In DVA studies of cycled LFP/graphite, the staging step tracks LLI.
- **C3: uncertain.** The external screen found the charge direction at 0.68–0.83 and the discharge direction at 1.19–1.44 on LIC, so a charge/discharge mismatch is plausible.
- **C6 (`robust_interp`):** 0.05–0.15 Ah.
- **C9:** √t is probably worse than the anchor trend on continuously cycled cells.
- **First window (the CK1 analogue):** the fallback with β = 1 under-reads a fast break-in, as round 8 found for CK1.

## 0. Mode of work

- **Unattended.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Restarts.** Keep `notes/STATUS.md` current after every step (WP, done, next, last commit). On restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first.
- **Honesty over targets.** Never choose a parameter, a cell, a window or a key after seeing Challenge 1 errors. WP4 runs once.
- **No package change, no zip, no upload.** Do not modify `TechArena_Challenge2_Team_Package/` or any earlier study. Never write into the Challenge 1 data folder.
- **Amendments.** An amendment may change only a **structural** assumption, and only before WP3:
  - step-type names;
  - sampling;
  - sign conventions;
  - an eligibility threshold that rejects most cycles.

  It must be a new protocol version (`protocol.json` `version` + 1, a `changelog` entry), re-hashed and committed before rerunning WP1–WP2. Labels or estimator errors never justify an amendment.

## 1. Workspace, isolation, git

- **Base.** Use the commit on `exp/phase2-anchor-step-20261013` that adds `research/phase2_r18_c1_transfer_20261022/`. Create a worktree on a new branch `exp/phase2-r18-c1-transfer-20261022` from it, or reuse an existing one whose history contains that commit. Record which in STATUS.md.
- **Data.**
  - The Challenge 1 folder is `protocol.json` → `data.c1_dir_default` (`/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original`). If it has moved, pass `--c1-dir` and record the path. Each of the six cell folders holds `<cell>_time_series_part*.csv`.
  - The pack data must be present at `TechArena_Challenge2_Team_Package/data/` for WP1.
- **Python.** Python 3.11+ with numpy and pandas only (flake8 optional). Use `python3 -B`, and `python3 -I -B` for the script that reads the external files (WP2).
- **Git.** Commit after every WP and push with `git push -u origin exp/phase2-r18-c1-transfer-20261022`.
  - Add files by explicit path only. Never `git add -A`, never force-push.
  - `cache/` is git-ignored; `outputs/` is committed (small CSV/JSON/MD).
  - End every commit message with the attribution lines your session specifies.

## 2. Work packages

Run them in order from the study folder (`research/phase2_r18_c1_transfer_20261022/`).

### WP0 — Setup (cap 0.5 h)

- `shasum -a 256 -c protocol.sha256` (or `sha256sum -c`) must report OK for every file. If any file differs from the registered version, stop and record it.
- Record Python, numpy and pandas versions and the machine in STATUS.md.
- Confirm that the six cell folders exist and list their files and sizes. Do not open them yet.

### WP1 — Self-tests (cap 0.5 h)

- Run `python3 -B run_wp1_selftest.py`. It must print `"passed": true` with 16 tests, 0 failures and 0 skipped. A skip means the pack data is missing; fix that first.
- The tests cover:
  - bit-identity of the step adapter with the submitted code on the pack;
  - the information structure;
  - causality (future rows replaced by noise give identical predictions);
  - hidden rows that never enter;
  - branch selection;
  - recovery of planted β on both sides;
  - the decision rules.
- If anything fails, stop. Do not run WP2.

### WP2 — Extraction, facts, causality on the real files (cap 1.5 h)

- Run `python3 -I -B run_wp2_extract.py`. It writes `outputs/wp2_facts.csv`, `outputs/wp2_qc.csv` and `outputs/wp2_causality.csv`, and caches the views.
- It must end with `causality: N/N identical`. If not, stop: no result may be reported.
- **Check these structural assumptions** against `wp2_facts.csv` / `wp2_qc.csv` and record each as holds / fails:
  1. the step types include `cccv_charge`, `cc_discharge` and `rest`;
  2. the median sampling interval is ≤ 60 s for both steps;
  3. charge and discharge currents are about 51 or 102 A (sign recorded; the code uses |I|);
  4. the maximum charge voltage is a CV plateau and the minimum discharge voltage is about 2.5 V;
  5. per cell `detected_share` ≥ 0.9 and `finite_robust` ≥ 0.9 in view `w30`;
  6. at least 3 truth targets per cell, inside the primary scope (truth ≥ 0.90 × label0) for most of them.
- **If an assumption fails,** apply the amendment rule (§0), or exclude the cell by rule if `detected_share` < 0.5 after a structural fix. Record it.
- Commit the outputs.

### WP3 — Mechanism checks (cap 1 h)

- Run `python3 -B run_wp3_mechanism.py`. It writes `outputs/wp3_windows.csv`, `outputs/wp3_per_cell.csv` and `outputs/wp3_summary.json`.
- Write `wp3/REPORT.md`, conclusions first, bilingual:
  - C2: β_realised per cell for both keys, with R² and residual SD, against the pack values;
  - C2b: charge-side β from anchors and from truth;
  - C3: the mismatch cells;
  - C6: noise for both keys and by C-rate;
  - C7: ε drift;
  - C10–C12.
- Interpretation is descriptive: no claim here is decided by a gate.

### WP4 — Emulation and registered gates (cap 1.5 h)

- Run `python3 -B run_wp4_emulation.py` **once**. It writes `outputs/wp4_errors.csv`, `outputs/wp4_decisions.json` and `outputs/wp4_tables.md`.
- The decisions are what the script computes. Never edit a rule or rerun with other parameters.
- If a bug is found afterwards:
  1. fix it and record the bug, the fix and the commit;
  2. rerun WP1–WP4;
  3. report the first and the corrected results side by side.
- Write `wp4/REPORT.md`, conclusions first, bilingual:
  - the decision table for both levels;
  - the per-cell MAE tables (all targets; phase targets with the oracle);
  - the shuffle control;
  - C9 (gap);
  - the first window (k = 1, the CK1 analogue);
  - the extended scope (≥ 0.85 × label0);
  - the sensitivity runs (w20, w45, all programs).

### WP5 — Synthesis (cap 1 h)

- **`FINAL_REPORT.md`**, bilingual, conclusions first:
  1. one decision table (claims × levels) with the key numbers;
  2. what transfers and what does not, with the domain-gap caveats of this prompt;
  3. what it means for SUB's risk list:
     - β: if C3 is not supported or a mismatch is flagged, state the sign of β_V2 − β_realised and what it implies for CK5–CK7 (β 1.24–1.51);
     - step noise;
     - first month;
  4. a **draft** "Transferability" paragraph and table for the package README/REPORT. It is not applied; applying it is a separate decision.
- **`README.md`**: update the status and the outputs list.
- **Global Done:**
  - WP0–WP5 done, capped or exited by a rule;
  - every output committed and pushed;
  - `git status` clean;
  - no file outside this study changed.

## 3. How to read the outcomes (written before running)

| Outcome | Meaning |
|---|---|
| C1 supported at `method`, not at `code_as_is` | The mechanism holds. The submitted sample-based crossing is a resolution limit on 30 s / high-rate data; the pack (10 s at ~0.1C) is not affected |
| C1 not supported at `method` | Under continuous 0.5C/1C cycling the step does not track capacity well enough. SUB's mechanism claim then rests on the pack's own consistency only. State this in the report |
| C1b not supported while C1 is | The step update helps, but no more than extrapolating the anchors. The step's value is then robustness (e.g. reduced data), not accuracy |
| C2: β_realised within 1.06–1.51 (near 1.34) | Consistent with SUB's β and with round 8's 1/b |
| C3 not supported, or mismatch > 0.30 | V2's charge-side β does not predict the discharge-side ratio on this cell type. SUB's late β (1.24–1.51) becomes an explicit risk, direction from the sign |
| C6 (interp) well above 0.036 Ah | Expected from 30 s at 0.5C/1C; not a failure of the method |
| C8 supported | The normalised error on truth-bearing data is ≤ 0.30 of the ExampleModel analogue on every cell |
| C9: √t worse than the trend | Expected on cycling cells; supports calling √t a pack-specific choice. It does not refute it for the pack |
| First window: E2 (fallback) ≫ phase-target errors | The β = 1 fallback under-reads a fast first-month loss, the CK1 risk of SUB |

## 4. Files

| File | Content |
|---|---|
| `protocol.json`, `protocol.sha256` | registered parameters and rules; hashes of every registered file |
| `src/common.py` | paths, protocol, access to the submitted module, `patched` |
| `src/c1io.py` | reading a cell, the per-cycle summary, structural eligibility, the label rule of the Challenge 1 framework |
| `src/steps.py` | the step adapter around the submitted locators |
| `src/view.py` | the emulated information structure and the event dataset |
| `src/model_adapter.py` | `TransferModel` (the submitted `MyModel`), `predict`, the oracle β |
| `src/baselines.py` | E4 (ExampleModel analogue), E5 (anchor trend) |
| `src/metrics.py` | per-cell summaries and the registered decision rules |
| `src/synth.py` | synthetic cells in the Challenge 1 format (self-test only) |
| `src/store.py` | cache/outputs folders and view specs |
| `tests/` | WP1 self-tests |
| `run_wp1_selftest.py` … `run_wp4_emulation.py` | the work packages |
| `notes/DECISIONS.md`, `notes/STATUS.md` | decisions and status |

---

<a id="zh"></a>

# 第 18 轮："锚点 + 石墨台阶"方法能否迁移？在 Challenge 1 单芯上的带真值检验——执行任务书

> **语言：** [English](#en) · 中文

2026-10-22 撰写。本文件自成一体。英文为执行文本，中文为译文；两者不一致时以英文为准。

登记的协议是 [protocol.json](protocol.json)，登记的代码是 `src/`、`tests/` 和 `run_wp*.py`，它们的 SHA-256 记录在 [protocol.sha256](protocol.sha256)。以上全部在**本研究任何 Challenge 1 输出产生之前**提交。自检（WP1）已在编写它们的云端会话里通过；下面的真实运行尚未进行。

## 为什么做这一轮（先读）

- **到目前为止，SUB 的所有验证打分用的代理都和 SUB 共用同一个水平。** 代理 = 检查后满充 + ε。第一次排行榜读数（SUB 0.1868，2026-10-20）意味着真实误差约 0.7–1.0 pp。代理能说明 SUB 自洽，但说明不了它的**机理**是否正确：石墨台阶是否跟住容量、β 的换算是否正确。
- **Challenge 1 的六个单芯和本题电池组是同一种 102 Ah LFP 电芯。**
  - 每个循环都有电压、电流和放电容量标签（0.5C/1C 放到 2.5 V）。
  - 覆盖 25/35/45/55 °C。
  - 规则允许再次使用 Challenge 1 数据。
- **所以可以在有真值的地方检验这套方法。** 在每个单芯上模拟电池组的信息结构，**原样**运行提交的决策逻辑。
- **结果的用途：**
  - 报告里的"技术创新"评分项（可迁移性、开放数据的使用）；
  - SUB 的风险说明（β、台阶噪声、第一个月）。
- **本轮不改动提交。**

## 检验什么：提交 README 中的论断 → 检验

规则摘自 `protocol.json` → `gates` / `mechanism_checks`。单位是物理电芯，n = 计入的电芯数，δ = 登记的噪声门槛。

| # | 提交 README / REPORT 中的论断 | 检验 | 登记规则 |
|---|---|---|---|
| C1 | 月内台阶更新能跟住锚点之后的损失 | E2_SUB 对 E0_anchor | 成立：宏 MAE 比 ≤ 0.70；E2 在 ≥ ⌈5n/6⌉ 个电芯上更好；每个留一芯比值 ≤ 0.80；洗牌对照在 ≥ ⌈5n/6⌉ 个电芯上差 ≥ δ |
| C1b | ……而且不只是一条趋势线 | E2_SUB 对 E5_trend | 成立：增益 ≥ δ，且在 ≥ ⌈2n/3⌉ 个电芯上更好 |
| C2 | 活性锂损失缩短台阶到满充端的距离；β 1.06–1.51 | 逐芯 β_realised | 描述性，与电池组的值比较（1.06–1.51；第 8 轮 1/b = 1.34） |
| C3 | β 来自充电侧锚点 | E2_SUB 对 E2_beta1；\|β_V2 − β_realised\| | 成立：增益 ≥ δ，且在 ≥ ⌈2n/3⌉ 个电芯上更好；失配 > 0.30 时报告 |
| C4 | 相位匹配的月末差分 | 相位目标上 E2_SUB 对 E1_fallback | 成立：增益 ≥ δ，且在 ≥ ⌈2n/3⌉ 个电芯上更好 |
| C5 | 六变体中位数稳健 | robust 对各单一变体 | 成立：≤ 单一变体的中位数，且与最好者相差在 δ 以内 |
| C6 | 台阶噪声很小（电池组 0.012–0.036 Ah） | 窗口内残差标准差 | 描述性 |
| C7 | ε 漂移很小 | ε_j 对衰减量 | 描述性，与第 11 轮（−0.036 … +0.052 Ah/Ah）比较 |
| C8 | 远好于部分充电基线 | 逐芯 E2 / E4 的 MAE 比 | 成立：每个电芯都 ≤ 0.30 |
| C9 | 覆盖缺口上的 √t 外推 | 缺口场景 | 只报告（针对本电池组的选择） |
| C10–C12 | 合理性检查 | 截断、倍率、窗口重叠 | 描述性 |

## 模拟方式（protocol.json → `information_structure`、`model`）

| 电池组 | 在 Challenge 1 单芯上的模拟 |
|---|---|
| 两次检查之间的一个月 | 从 B_0 起每 30 天一个窗口（敏感性：20 天和 45 天） |
| 检查后锚点：从空态开始的完整 CCCV 充电 | 每个边界之后第一个合格循环的完整充电；它的放电保持隐藏 |
| 约每 5 天一次深度程序，放到满充以下 55.9 Ah | 每个 5 天标记之后的第一个合格循环；只能看到放电到 56 Ah 为止的部分和充电最上面 21 Ah |
| CK0 = 100.41 Ah，唯一公开的标签 | label0 = 锚点 0 所在循环的标签，是模型唯一能拿到的标签 |
| CK1–CK7 处隐藏的 C/20 | truth(B_k) = 离 B_k 最近的 5 个标签的中位数，全部在 ±2 天内 |
| CK2：最后一个可见台阶在 22 天前 | 缺口场景：隐藏 B_k 之前最后 22 天内的程序 |
| 25/45 °C 锚点，EPS_EXTRA 0.4 Ah | 每个电芯只有一个温度，所以 EPS_EXTRA = 0；设定温度变成角色标签（锚点 0 → 45，后续锚点 → 25，程序 → 45），Arrhenius 时钟均匀 |

**"原样运行提交逻辑"的含义如下。**
- `src/model_adapter.TransferModel` 继承提交的 `MyModel`，只重写 `diagnose`（事件来自模拟视图，而不是电池组的数据行）。
- 几个很薄的包装只记录走了哪个分支、x 和 β。
- 消融实验每次只关掉一个部分：
  - E0 看不到任何台阶；
  - E1 关掉相位分支；
  - E2_beta1 把 β 固定为 1；
  - 缺口场景下的 E1_fallback_no_sqrt 另外关掉 √t 规则。
- `src/steps.py` 把单芯电压复制成四列，调用提交的 `_locate_step`、`_locate_dvdq` 和 `_charge_step_to_top`。只把电流带从约 10 A 按比例缩放到 |I_dis|。
- WP1 证明了：在电池组的全部深放电上，适配层与提交的 `_robust_step` **逐位一致**。

**两个论断层级。**
- **`code_as_is`**（键 `robust`）：提交的定位器。
- **`method`**（键 `robust_interp`）：中点穿越在两个样本之间线性插值。
- **为什么要分两层：** 30 s 采样、0.5C/1C 时，一个样本对应 0.43/0.85 Ah，而电池组上只有 0.03 Ah。合成自检中，原样定位的台阶噪声为 0.12–0.36 Ah，插值后为 0.03–0.05 Ah。只在 `code_as_is` 层失败，说明的是这些数据文件的采样极限，不是方法本身的问题。

## 本轮检验不了的

- **电池组 C/20 检查的 ε 水平。** Challenge 1 的标签是单芯 0.5C/1C 放到 2.5 V，所以排行榜的水平问题仍然够不着。
- **25/45 °C 交替和检查后台阶偏移。** 每个电芯只在一个温度下运行，也没有检查。
- **类似日历老化的衰减。** 这些电芯连续循环；√t 是针对本电池组的选择，所以 C9 只报告。
- **四芯中位数。** 每个检验单位都是单芯。
- **自发热。** 标称"25 °C"的电芯在循环中实际处于 37–41 °C（第 5A 轮第 2 阶段）。
- **曝光。** Challenge 1 的标签以前用过（第 5A 轮的先验、阶段 1 的迁移路线），衰减曲线已经看过；但本方法在它们上的误差从未计算过。所有数字都标注"标签已曝光，方法误差未曝光"。

## 运行前写下的大致预期

- **`method` 层的 C1：很可能成立。** 关于循环 LFP/石墨的 DVA 文献表明，分阶台阶跟踪活性锂损失。
- **C3：不确定。** 外部数据筛查在 LIC 上发现充电方向 0.68–0.83、放电方向 1.19–1.44，所以充放电方向的失配是可能的。
- **C6（`robust_interp`）：** 0.05–0.15 Ah。
- **C9：** 在连续循环的电芯上，√t 很可能不如锚点趋势。
- **第一个窗口（CK1 的类比）：** β = 1 的回退分支会低估快速磨合，与第 8 轮对 CK1 的发现一致。

## 0. 工作方式

- **无人值守。** 不停下来提问。遇到未定的决定时，选遵守本文全部规则的最保守做法，记入 `notes/DECISIONS.md`，然后继续。
- **重启。** 每一步之后更新 `notes/STATUS.md`（WP、已完成、下一步、最后一次提交）。重启时先读 `notes/STATUS.md` 和 `notes/DECISIONS.md`。
- **诚实优先于目标。** 看到 Challenge 1 误差之后，绝不再选参数、电芯、窗口或键。WP4 只运行一次。
- **不改提交包、不打 zip、不上传。** 不修改 `TechArena_Challenge2_Team_Package/` 和任何更早的研究；绝不往 Challenge 1 数据文件夹里写东西。
- **修订。** 修订只能改**结构性**假设，而且只能在 WP3 之前：
  - 步骤类型名称；
  - 采样；
  - 符号约定；
  - 会把大多数循环拒掉的资格门槛。

  修订必须形成新的协议版本（`protocol.json` 的 `version` + 1，加一条 `changelog`），重新计算哈希并提交，然后重跑 WP1–WP2。标签或估计误差永远不能作为修订的理由。

## 1. 工作区、隔离、git

- **基点。** 用 `exp/phase2-anchor-step-20261013` 上加入 `research/phase2_r18_c1_transfer_20261022/` 的那次提交。从它新建分支 `exp/phase2-r18-c1-transfer-20261022` 的工作树，或者复用一个历史里包含该提交的现有工作树，并在 STATUS.md 中记录用的是哪种。
- **数据。**
  - Challenge 1 文件夹为 `protocol.json` → `data.c1_dir_default`（`/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original`）。如果路径变了，用 `--c1-dir` 传入并记录。六个电芯文件夹里各有 `<cell>_time_series_part*.csv`。
  - WP1 需要 `TechArena_Challenge2_Team_Package/data/` 下的电池组数据。
- **Python。** Python 3.11+，只需 numpy 和 pandas（flake8 可选）。用 `python3 -B`；读取外部文件的脚本（WP2）用 `python3 -I -B`。
- **Git。** 每个 WP 之后提交，并用 `git push -u origin exp/phase2-r18-c1-transfer-20261022` 推送。
  - 只按明确路径添加文件。绝不 `git add -A`，绝不强推。
  - `cache/` 被 git 忽略；`outputs/` 要提交（小型 CSV/JSON/MD）。
  - 每条提交信息末尾加上会话指定的署名行。

## 2. 工作包

在研究文件夹（`research/phase2_r18_c1_transfer_20261022/`）里按顺序运行。

### WP0 — 准备（上限 0.5 h）

- `shasum -a 256 -c protocol.sha256`（或 `sha256sum -c`）必须对每个文件都报告 OK。任何文件与登记版本不同就停下并记录。
- 在 STATUS.md 中记录 Python、numpy、pandas 的版本和机器。
- 确认六个电芯文件夹存在，列出文件和大小。此时还不要打开它们。

### WP1 — 自检（上限 0.5 h）

- 运行 `python3 -B run_wp1_selftest.py`。它必须打印 `"passed": true`：16 项测试、0 失败、0 跳过。出现跳过说明缺电池组数据，先补上。
- 测试覆盖：
  - 适配层在电池组上与提交代码逐位一致；
  - 信息结构；
  - 因果性（未来数据换成噪声后预测不变）；
  - 隐藏数据确实没有进入输入；
  - 分支选择；
  - 两侧植入 β 的恢复；
  - 判定规则。
- 任何一项失败就停止，不运行 WP2。

### WP2 — 在真实文件上提取、记录事实、检查因果性（上限 1.5 h）

- 运行 `python3 -I -B run_wp2_extract.py`。它会写出 `outputs/wp2_facts.csv`、`outputs/wp2_qc.csv` 和 `outputs/wp2_causality.csv`，并缓存模拟视图。
- 最后必须打印 `causality: N/N identical`。否则停止：不得报告任何结果。
- **对照 `wp2_facts.csv` / `wp2_qc.csv` 检查下列结构性假设**，逐条记为成立 / 不成立：
  1. 步骤类型包含 `cccv_charge`、`cc_discharge` 和 `rest`；
  2. 两类步骤的采样间隔中位数都 ≤ 60 s；
  3. 充放电电流约为 51 或 102 A（记录符号；代码用的是 |I|）；
  4. 充电最高电压是 CV 平台，放电最低电压约为 2.5 V；
  5. 视图 `w30` 中每个电芯的 `detected_share` ≥ 0.9、`finite_robust` ≥ 0.9；
  6. 每个电芯至少有 3 个真值目标，其中大部分在主范围内（真值 ≥ 0.90 × label0）。
- **假设不成立时**，按修订规则（§0）处理；如果结构修正后某个电芯的 `detected_share` 仍 < 0.5，按规则排除该电芯。记录在案。
- 提交输出。

### WP3 — 机理检查（上限 1 h）

- 运行 `python3 -B run_wp3_mechanism.py`。它会写出 `outputs/wp3_windows.csv`、`outputs/wp3_per_cell.csv` 和 `outputs/wp3_summary.json`。
- 写 `wp3/REPORT.md`（结论在前，双语）：
  - C2：两个键的逐芯 β_realised，附 R² 和残差标准差，与电池组的值比较；
  - C2b：由锚点和由真值得到的充电侧 β；
  - C3：失配的电芯；
  - C6：两个键的噪声，并按倍率分组；
  - C7：ε 漂移；
  - C10–C12。
- 解读是描述性的：这里没有任何论断由门槛判定。

### WP4 — 模拟与登记门槛（上限 1.5 h）

- **只运行一次** `python3 -B run_wp4_emulation.py`。它会写出 `outputs/wp4_errors.csv`、`outputs/wp4_decisions.json` 和 `outputs/wp4_tables.md`。
- 判定结果以脚本算出的为准。绝不修改规则，也不换参数重跑。
- 如果事后发现程序错误：
  1. 修复，并记录错误、修复和提交；
  2. 重跑 WP1–WP4；
  3. 把初次结果和修正后的结果并列报告。
- 写 `wp4/REPORT.md`（结论在前，双语）：
  - 两个层级的判定表；
  - 逐芯 MAE 表（全部目标；含 oracle 的相位目标）；
  - 洗牌对照；
  - C9（缺口）；
  - 第一个窗口（k = 1，CK1 的类比）；
  - 扩展范围（≥ 0.85 × label0）；
  - 敏感性运行（w20、w45、全部程序）。

### WP5 — 综合（上限 1 h）

- **`FINAL_REPORT.md`**（双语，结论在前）：
  1. 一张判定表（论断 × 层级），附关键数字；
  2. 哪些能迁移、哪些不能，附本文列出的领域差异说明；
  3. 对 SUB 风险清单的含义：
     - β：如果 C3 不成立或检出失配，写明 β_V2 − β_realised 的符号，以及它对 CK5–CK7（β 1.24–1.51）意味着什么；
     - 台阶噪声；
     - 第一个月；
  4. 为提交包 README/REPORT 起草一段"可迁移性"文字和一张表。只是**草稿**，不应用；是否应用另行决定。
- **`README.md`**：更新状态和输出清单。
- **全局完成：**
  - WP0–WP5 均已完成、达到上限，或按规则退出；
  - 所有输出已提交并推送；
  - `git status` 干净；
  - 本研究之外没有任何文件被改动。

## 3. 怎样解读结果（运行前写下）

| 结果 | 含义 |
|---|---|
| `method` 层 C1 成立，`code_as_is` 层不成立 | 机理成立。提交代码按样本取穿越点，在 30 s / 高倍率数据上受分辨率限制；电池组（10 s、约 0.1C）不受影响 |
| `method` 层 C1 不成立 | 在 0.5C/1C 连续循环下，台阶跟踪容量的能力不够。SUB 的机理论断就只能依靠电池组自身的一致性，要在报告中写明 |
| C1 成立但 C1b 不成立 | 台阶更新有帮助，但不比外推锚点更好。那么台阶的价值在于稳健性（例如数据缩减时），而不在精度 |
| C2：β_realised 落在 1.06–1.51（接近 1.34） | 与 SUB 的 β 和第 8 轮的 1/b 一致 |
| C3 不成立，或失配 > 0.30 | 在这种电芯上，V2 的充电侧 β 预测不了放电侧比值。SUB 后期的 β（1.24–1.51）成为一项明确的风险，方向由符号决定 |
| C6（插值）明显高于 0.036 Ah | 30 s、0.5C/1C 条件下的预期结果，不是方法失败 |
| C8 成立 | 在有真值的数据上，每个电芯的归一化误差都 ≤ ExampleModel 类比的 0.30 |
| C9：√t 不如趋势 | 连续循环电芯上的预期结果；支持"√t 是针对本电池组的选择"这一说法，并不否定它在电池组上的适用 |
| 第一个窗口：E2（回退）远大于相位目标的误差 | β = 1 的回退分支低估了第一个月的快速损失，对应 SUB 的 CK1 风险 |

## 4. 文件

| 文件 | 内容 |
|---|---|
| `protocol.json`、`protocol.sha256` | 登记的参数和规则；每个登记文件的哈希 |
| `src/common.py` | 路径、协议、提交模块的访问、`patched` |
| `src/c1io.py` | 读取电芯、逐循环汇总、结构性资格、Challenge 1 框架的标签规则 |
| `src/steps.py` | 围绕提交定位器的台阶适配层 |
| `src/view.py` | 模拟的信息结构和事件数据集 |
| `src/model_adapter.py` | `TransferModel`（提交的 `MyModel`）、`predict`、oracle β |
| `src/baselines.py` | E4（ExampleModel 类比）、E5（锚点趋势） |
| `src/metrics.py` | 逐芯汇总和登记的判定规则 |
| `src/synth.py` | Challenge 1 格式的合成电芯（只用于自检） |
| `src/store.py` | cache/outputs 文件夹和视图规格 |
| `tests/` | WP1 自检 |
| `run_wp1_selftest.py` … `run_wp4_emulation.py` | 各工作包 |
| `notes/DECISIONS.md`、`notes/STATUS.md` | 决策和状态 |
