<a id="en"></a>

# WP0 — Setup and fact sheet

> English · [中文](#zh)

**Conclusions first.**

- **Set-up is complete.** Worktree `/Users/shane/Desktop/Arena_1019_r13_top_tail`, branch `exp/phase2-r13-top-tail-20261019`, base `6525edf` (the branch tip). The sources are copied with their SHA256 in [../sources/SOURCES.md](../sources/SOURCES.md).
- **SUB is reproduced.** The package CLI (train, then test `--eval-point all`) on `6525edf` gives the SOH below, identical to round 11's WP0 ([SUB_SOH.csv](SUB_SOH.csv)).

| | CK0 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|
| SUB SOH % | 98.441 | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |

- **The CV catalogue has 41 rows**, one per full charge: 8 anchors and 33 top-ups (9 at 25 °C, 24 at 45 °C). All 41 match round 8's events ([cv_catalogue.csv](cv_catalogue.csv)).
- **Fact sheet** ([FACTS.md](FACTS.md)). Four of the six §2 facts hold as stated. Two are corrected:
  - the anchors' CV phase is 438–530 s (45–54 samples) and lengthens with ageing, not "≈ 7 min / 40 samples";
  - the top-ups' CV phase is 1.9–4.4 min, not 2–9 min.
- **The back-of-envelope reproduces only as arithmetic** (0.253 → 0.307 Ah, Δ 0.054 Ah). It uses round 11's τ, which comes from a model with I∞ ≈ 4.2 A, inside a zero-asymptote formula. WP2 must test it with M1's own τ.
- **Two facts matter for WP1.**
  - Cell3 is the highest cell at the CV end and at +30 min in **all 41** full charges. Its +30 min voltage falls by 7 mV over anchors 1–7 while the pack's is flat.
  - Every full charge has exactly 1800–1801 s of rest before the 20 A pulse, so V30 is well defined for every charge.
- No tail model was fitted, and no P_k or proxy error was used.

Catalogue columns: `segment`, `setpoint_C`, `type` (A/T), `anchor`; CV start/end (timestamp and elapsed s); `n_cv`, `cv_s`, `cv_Ah` (trapezoid), `cv_Ah_counter` (cycler counter), `I_cv_start`, `I_cv_end`; pack and cell voltages at the CV end (`*_end`) and +30 min (`*_30`, the last rest sample before the pulse); `top_cell_end` / `top_cell_30`; `T_cv_end`; round 8's `R_pulse_mOhm` per cell, as cell mean and as pack sum; a descriptive current at 1/3 and 2/3 of the CV time and 60 s before the end.

---

<a id="zh"></a>

# WP0 — 准备与事实清单

> [English](#en) · 中文

**结论先读。**

- **准备已完成。** 工作树 `/Users/shane/Desktop/Arena_1019_r13_top_tail`，分支 `exp/phase2-r13-top-tail-20261019`，基点 `6525edf`（即分支末端）。来源文件已复制，SHA256 见 [../sources/SOURCES.md](../sources/SOURCES.md)。
- **SUB 已复现。** 在 `6525edf` 上用包 CLI（先 train，再 test `--eval-point all`）得到下表 SOH，与第 11 轮 WP0 完全一致（[SUB_SOH.csv](SUB_SOH.csv)）。

| | CK0 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|
| SUB SOH % | 98.441 | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |

- **CV 目录共 41 行**，每次满充一行：8 个锚点和 33 次补电（25 °C 9 次，45 °C 24 次）。41 行全部与第 8 轮的事件对上（[cv_catalogue.csv](cv_catalogue.csv)）。
- **事实清单**（[FACTS.md](FACTS.md)）。第 2 节六条事实中四条如原文成立。两条需要修正：
  - 锚点 CV 段为 438–530 s（45–54 个样本），并随老化变长，而不是"约 7 min / 40 个样本"；
  - 补电 CV 段为 1.9–4.4 min，不是 2–9 min。
- **粗算只在算术上可复现**（0.253 → 0.307 Ah，差 0.054 Ah）。它把第 11 轮的 τ 代入一个渐近值为零的公式，而这个 τ 来自 I∞ ≈ 4.2 A 的模型。WP2 必须用 M1 自己的 τ 来检验。
- **有两条事实对 WP1 很重要。**
  - 在**全部 41 次**满充中，cell3 在 CV 结束时和 +30 min 时都是最高的电芯。在锚点 1–7 上，它在 +30 min 的电压下降了 7 mV，而电池组电压持平。
  - 每次满充后到 20 A 脉冲之前都恰好静置 1800–1801 s，因此每次充电的 V30 都有明确定义。
- 没有拟合任何尾巴模型，也没有使用任何 P_k 或代理误差。

目录各列：`segment`、`setpoint_C`、`type`（A/T）、`anchor`；CV 开始和结束（时间戳与 elapsed 秒）；`n_cv`、`cv_s`、`cv_Ah`（梯形积分）、`cv_Ah_counter`（循环仪计数器）、`I_cv_start`、`I_cv_end`；CV 结束时（`*_end`）和 +30 min 时（`*_30`，即脉冲前最后一个静置样本）的电池组与各电芯电压；`top_cell_end` / `top_cell_30`；`T_cv_end`；第 8 轮的分电芯 `R_pulse_mOhm`，以及其电芯均值和电池组总和；CV 时间 1/3、2/3 处和结束前 60 s 的电流（描述性）。
