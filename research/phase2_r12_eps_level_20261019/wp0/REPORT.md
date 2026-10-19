<a id="en"></a>

# WP0 — Setup and fact sheet: report

> **Language:** English · [中文](#zh)

## Conclusions

1. **Workspace.**
   - Worktree `/Users/shane/Desktop/Arena_1019_r12_eps_level`, branch `exp/phase2-r12-eps-level-20261019`.
   - Base `6525edf`, which is also the tip of `exp/phase2-anchor-step-20261013`.
   - 32 source files are copied with their SHA256 (`sources/SOURCES.md`).
2. **SUB reproduces, and EPS_EXTRA behaves as described except at CK2.**
   - SUB via the package CLI: CK1..CK7 = 95.984, 94.507, 93.600, 92.821, 92.015, 91.426, 90.765 %.
   - The research copy with EPS_EXTRA = 0.4 reproduces SUB exactly. CK1 does not move.
   - CK3–CK7 move by 0.9804 pp/Ah.
   - **CK2 moves by 1.4465 pp/Ah, not 0.98.** The √t gap branch fits its loss slope to anchor 1 plus the same ε, so dQ/dε = √(t_CK2/t_CK1) = 1.475.
3. **Event catalogue.**
   - There are 41 CCCV charges that reach CV: 8 from-empty anchors and 33 top-ups.
   - All 41 have the same structure: 20.4 A CC to 14.0 V, CV to 5.09–5.10 A, 30.0 min rest, 30.0 min −20.4 A pulse (10.20 Ah), and a deep program 55.92 Ah below the CV end.
4. **Facts.** Of the 35 bullets of §2:
   - 23 are confirmed and 6 corrected. The corrections are small: the 264 mV and 88 → 52 mV spreads are CV-end values, Q_fc,2 = 95.67 Ah, and the CV Ah depends on the CV-start definition.
   - 2 are cited and 3 deferred to WP2/WP3, by the WP0 rule. 1 is recorded (scope change).
   - See `FACTS.md`.
5. **New facts with consequences for WP3.**
   - The AT pairs of anchor 3 (segment 6: gaps of 3.65 h and 16.64 h) and anchor 7 (segment 14: 0.49 h) contain recording gaps, and the counters stay flat across them, so the profile paused.
   - Under the registered pair rule these pairs are excluded, so Term3 cannot use k = 3 or k = 7 (DECISIONS D9).
   - The five chamber-switch idles have exactly flat counters, so the X pairs are admissible.
6. **Anchor 0's start.**
   - In its 0.5 h rest the pack is cooling (47.01 → 46.54 °C) while the voltage rises at +85 mV/h, 3.39 d after the C/20 ended.
   - This is input to WP2 B1. No interpretation is made here.

## What was done

| Step | Output |
|---|---|
| 1 | worktree, `notes/STATUS.md`, `notes/DECISIONS.md`, `.gitignore` (`cache/`), `EXECUTION_PROMPT.md` (SHA256 identical to the original) |
| 2 | `sources/` (round 11, round 8, round 5B, base-branch rebound, V2 and anchor-step files) + `sources/SOURCES.md` |
| 3 | `wp0/SUB_SOH.csv`, `wp0/eps_extra_sensitivity.csv`, `wp0/eps_extra_checks.json`; variants under `cache/variants/eps_*` (diff = the EPS_EXTRA_AH line only) |
| 4 | `wp0/events.csv` (41 rows) |
| 5 | `wp0/FACTS.md` + `facts.json`, `switches.csv`, `checkup_windows.csv`, `integration_check.csv`, `pulses_programs.csv`, `counter_booking_by_segment.csv`, `in_segment_gaps.csv` |

Scripts: `src/wp0_sub.py`, `src/data12.py`, `src/wp0_events.py`, `src/wp0_facts.py`. All were run with `python3 -B` (system Python 3.13, pandas 3.0, numpy 2.4).

## Rules kept

- No Ah balance, step location or ε-related estimate was computed (DECISIONS D6).
- No proxy P_k was used. No file outside this worktree and no `TechArena_Challenge2_Team_Package/` file was modified.

---

<a id="zh"></a>

# WP0 — 准备与事实清单：报告

> [English](#en) · 中文

## 结论

1. **工作区。**
   - 工作树 `/Users/shane/Desktop/Arena_1019_r12_eps_level`，分支 `exp/phase2-r12-eps-level-20261019`。
   - 基点 `6525edf`，它也是 `exp/phase2-anchor-step-20261013` 的末端。
   - 复制了 32 个来源文件，附 SHA256（`sources/SOURCES.md`）。
2. **SUB 可复现；EPS_EXTRA 除 CK2 外都与描述一致。**
   - 用包 CLI 运行 SUB：CK1..CK7 = 95.984、94.507、93.600、92.821、92.015、91.426、90.765 %。
   - EPS_EXTRA = 0.4 的研究副本与 SUB 完全一致；CK1 不动。
   - CK3–CK7 每 Ah 移动 0.9804 pp。
   - **CK2 每 Ah 移动 1.4465 pp，而不是 0.98。** √t 间隙分支用锚点 1 加同一个 ε 拟合损失斜率，因此 dQ/dε = √(t_CK2/t_CK1) = 1.475。
3. **事件目录。**
   - 共 41 次到达 CV 的恒流恒压充电：8 次从空充满的锚点，33 次补电。
   - 41 次结构完全相同：20.4 A 恒流到 14.0 V，恒压到 5.09–5.10 A，静置 30.0 min，−20.4 A 脉冲 30.0 min（10.20 Ah），然后是到 CV 结束以下 55.92 Ah 的深放电程序。
4. **事实。** 第 2 节的 35 条中：
   - 23 条已确认，6 条已更正。更正都很小：264 mV 和 88 → 52 mV 是 CV 结束时的压差；Q_fc,2 = 95.67 Ah；CV 电量取决于 CV 起点的定义。
   - 按 WP0 规则，2 条为引用，3 条推迟到 WP2/WP3；1 条已记录（范围调整）。
   - 见 `FACTS.md`。
5. **对 WP3 有影响的新事实。**
   - 锚点 3（第 6 段：3.65 h 和 16.64 h 的间隙）和锚点 7（第 14 段：0.49 h）的 AT 配对内有记录间隙，前后计数器不变，说明工况程序暂停了。
   - 按登记的配对规则，这些配对会被排除，所以 Term3 不能使用 k = 3 和 k = 7（DECISIONS D9）。
   - 五次换温箱停机期间计数器完全不变，所以 X 配对可用。
6. **锚点 0 的起点。**
   - 在 0.5 h 静置中，电池组在降温（47.01 → 46.54 °C），电压却以 +85 mV/h 上升；此时距 C/20 结束已 3.39 天。
   - 这是 WP2 B1 的输入，此处不作解释。

## 做了什么

| 步骤 | 输出 |
|---|---|
| 1 | 工作树、`notes/STATUS.md`、`notes/DECISIONS.md`、`.gitignore`（`cache/`）、`EXECUTION_PROMPT.md`（SHA256 与原文件相同） |
| 2 | `sources/`（第 11 轮、第 8 轮、第 5B 轮，以及基点分支上的回弹、V2、锚点台阶研究文件）+ `sources/SOURCES.md` |
| 3 | `wp0/SUB_SOH.csv`、`wp0/eps_extra_sensitivity.csv`、`wp0/eps_extra_checks.json`；变体位于 `cache/variants/eps_*`（与原文件的差别只有 EPS_EXTRA_AH 这一行） |
| 4 | `wp0/events.csv`（41 行） |
| 5 | `wp0/FACTS.md` + `facts.json`、`switches.csv`、`checkup_windows.csv`、`integration_check.csv`、`pulses_programs.csv`、`counter_booking_by_segment.csv`、`in_segment_gaps.csv` |

脚本：`src/wp0_sub.py`、`src/data12.py`、`src/wp0_events.py`、`src/wp0_facts.py`，全部用 `python3 -B` 运行（系统 Python 3.13、pandas 3.0、numpy 2.4）。

## 遵守的规则

- 没有计算任何电量对账、台阶位置或与 ε 相关的估计（DECISIONS D6）。
- 没有使用代理标签 P_k；没有修改本工作树之外的任何文件，也没有修改任何 `TechArena_Challenge2_Team_Package/` 文件。
