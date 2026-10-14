<a id="en"></a>

# Round 4: More and Cleaner Step Signals — Final Report

> **Language:** English · [中文](#zh)

- **Run:** 2026-10-14, unattended, following [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md).
- **Where:** worktree `/Users/shane/Desktop/Arena_1014_round4`, branch `exp/phase2-round4-signals-20261014`.
- **Protocols:** every stage froze its protocol or audit protocol (with SHA256) before running.
- **Exposure:** all results are **exposed-exploratory**. All CK1–CK7 proxy values had been seen before, and proxies (post-checkup full charge + ε) are not hidden C/20 truth.
- **Untouched:** the active submission (V1/M4) and `my_model/`. No concurrency event occurred (`notes/DECISIONS.md`).

## Conclusions first

1. **No new model beats V2. V2 stays the leading *research* candidate.** Directions 1 and 7 were evaluated and failed the gates. Directions 2, 3 and 4 failed their data audits.
2. **V2's remaining error is not measurement noise.** Inside a 45 °C segment the graphite-step depths scatter by only 0.012–0.036 Ah around a straight line, an order of magnitude below V2's errors (about 0.2 Ah). More or cleaner step measurements therefore cannot fix it.
3. **The operation adds no new capacity information about the graphite step.**
   - The ~5-day charges stop about 21 Ah below full, above the step, and carry no usable feature in that top region.
   - Every rest lies 0–22 Ah below full.
   - Dynamic crossings occur only at day 4 of each cycle, and coulomb counting does not close between full charges (median 0.61 Ah).
   - The anchor charges and the program discharges remain the only capacity signals.
4. **The most important finding is about the hidden truth, not about the models.**
   - Each checkup restores capacity that cycling had made temporarily unavailable. This recovery grows from about 0.02 Ah (CK1) to about 0.87 Ah (CK7) and decays with τ ≈ 2.5 days once cycling resumes. This matches rest-driven rehomogenisation of cycling-induced inhomogeneity better than anode overhang.
   - The proxies are post-recovery charges. If the hidden C/20 sees only part of the recovery, every anchor-based model is biased high late in the campaign. **V1 then ranks above V2**: MAE 0.333 vs 0.434 at half recovery.
5. **Recommendation.**
   - Do not switch the submission from V1 to V2 on proxy evidence alone.
   - A leaderboard comparison of V1 and V2 is itself the most informative next experiment: it tells which recovery hypothesis holds.
   - `V2_epsT` (stage 6, −0.21 pp on CK3–CK7) is a further leaderboard-only probe.

## Summary table

Proxy error in pp, main step method, A4 smoothing 2 Ah. MAE is given for Δ = 0 / 0.4 / 0.8; MAX at Δ = 0.4. "Pseudo" is the mean MAE over PG1, PG2, PC5 and PC10 (k ≥ 3, Δ = 0.4).

| Model | Stage | MAE | MAX | ε-free CK2–7 | Pseudo | Gates |
|---|---|---|---|---|---|---|
| M4 (V1, submitted) | base | 0.347 / 0.291 / 0.285 | 0.669 | 0.304 | 0.247 | — |
| **V2** | base | **0.272 / 0.216 / 0.210** | 0.669 | **0.216** | 0.240 | reference |
| S1, Theil–Sen month-end line | 1 | 0.298 / 0.242 / 0.236 | 0.669 | 0.247 | 0.250 | fail (robust 1/6) |
| S1, last 3 steps (variant) | 1 | — / 0.229 / — | 0.669 | 0.231 | — | variant |
| S1, at last step + V2 rate (variant) | 1 | — / 0.226 / — | 0.669 | 0.227 | — | variant |
| SS_fixed (state space + level offset, τ 8 d) | 7 | 0.271 / 0.228 / 0.216 | 0.569 | not ε-free | 0.195 | fail (regress +0.34) |
| V2_startcorr (start-corrected registration β) | 7 | 0.282 / 0.226 / 0.220 | 0.669 | 0.227 | 0.239 | fail (robust 1/6) |
| Directions 2, 3, 4 | 2–4 | — | — | — | — | audit exit |
| V2_epsT (temperature ε) | 6 | leaderboard-only | — | — | — | not scored |

Per-checkup errors at Δ = 0.4 (pp):

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| M4 | +0.217 | +0.669 | +0.080 | +0.279 | −0.111 | −0.402 | −0.281 |
| V2 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| S1 | +0.217 | +0.669 | +0.080 | +0.364 | +0.149 | −0.209 | −0.008 |
| SS_fixed | +0.295 | −0.133 | −0.002 | +0.569 | +0.384 | −0.039 | −0.174 |
| V2_startcorr | +0.217 | +0.669 | +0.080 | +0.265 | +0.127 | −0.103 | +0.118 |

## What each stage found

- **Stage 0.** V2 (0.215726 / 0.669052) and M4 (0.291265) were reproduced exactly.
- **Stage 1** ([report](stage_1/REPORT.md)). The robust month-end line is worse than V2's single last step plus rate.
  - The change comes from extrapolating each line to its checkup date, not from denoising.
  - Within-segment residual SD is 0.012–0.036 Ah, so step noise is not V2's bottleneck.
- **Stage 2** ([report](stage_2/REPORT.md)). The new detector reproduces the program steps within 0.22 Ah (median).
  - Coulomb counting between consecutive full charges misses by a systematic −0.66 Ah per 4.8 days (about a −5 to −6 mA offset).
  - The extra crossings all sit at day 4 of each cycle, when that drift is largest.
  - Audit exit.
- **Stage 3** ([report](stage_3/REPORT.md)). All 110 rests lie 0–22 Ah below full, so no rest point lies near the step. Audit exit.
- **Stage 4** ([report](stage_4/REPORT.md)). The top 3–19 Ah of the ~5-day charges contain no reproducible, trending dV/dQ feature; the apparent peak is a window-edge artefact. Audit exit.
- **Stage 5** ([report](stage_5/REPORT.md)). Post-checkup recovery of 0.02 → 0.87 Ah with τ ≈ 2.5 d (95 % 0.5–9.8 d). Compared with anode overhang (weeks to months) and with rest-driven rehomogenisation (hours to days). The ranking sensitivity for the share f of recovery missing from the hidden C/20:

| f | M4 MAE | V2 MAE |
|---|---|---|
| 0 | 0.291 | 0.216 |
| 0.5 | 0.333 | 0.434 |
| 1 | 0.596 | 0.700 |

- **Stage 6** ([report](stage_6/REPORT.md)). The data-based temperature offset (δ ≈ 0.18 Ah instead of the assumed 0.4) lowers V2 by about 0.21 pp on CK3–CK7. Leaderboard-only.
- **Stage 7** ([report](stage_7/REPORT.md)).
  - The state space with a free level offset brings CK2 to −0.13 pp, but worsens CK4/CK5, still depends on ε, and is not robust.
  - The start-corrected registration β changes little.
  - Both fail.

## Risks and limits

- **Exposure.** Every proxy value was known. Pseudo scenarios reuse the same months, so they are not independent packs or labels.
- **ε and the recovery state of the hidden C/20 (stage 5).** These dominate the real-score uncertainty, at up to about 0.9 pp late in the campaign. They cannot be resolved without the checkup procedure or leaderboard feedback.
- **A single pack.** Correlations over 6–7 anchors are diagnostics, not validation.
- **Deviation.** Stage 7's SS_fixed uses a modified copy of round 3's `fit_predict`, registered before the run.
- **No concurrency events**, as recorded in `notes/DECISIONS.md`.

## Reproduction

```bash
cd /Users/shane/Desktop/Arena_1014_round4/research/phase2_round4_signals_20261014
python3 -B stage0_reproduce.py
python3 -B stage_1/run_1.py
python3 -B stage_2/audit_2.py
python3 -B stage_3/audit_3.py
python3 -B stage_4/audit_4.py
python3 -B stage_5/run_5.py
python3 -B stage_6/run_6.py
python3 -B stage_7/run_7.py
```

- **Environment:** Python 3.13 (numpy 2.4, pandas 3.0).
- **Code reused unchanged:**
  - round 3's `src/harness.py`, `registration.py` and `statespace.py`;
  - `events.py`;
  - `v2.py`.
- **Caches:** they live in the git-ignored `cache/` directories inside this worktree.
- **No candidate class** was produced, because no model passed every gate.

---

<a id="zh"></a>

# 第四轮：更多、更干净的台阶信号——最终报告

> **语言：** [English](#en) · 中文

- **运行：** 2026-10-14，无人值守，按 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) 执行。
- **位置：** worktree `/Users/shane/Desktop/Arena_1014_round4`，分支 `exp/phase2-round4-signals-20261014`。
- **协议：** 每个阶段都在运行前冻结了协议或审计协议（附 SHA256）。
- **曝光：** 全部结果都是**已曝光的探索性结果**。CK1–CK7 的代理值此前都已看过，而代理（检查后完整充电 + ε）不是隐藏的 C/20 真值。
- **未改动：** 当前提交（V1/M4）和 `my_model/`。本轮没有发生并发事件（见 `notes/DECISIONS.md`）。

## 结论先读

1. **没有新模型胜过 V2，V2 仍是领先的*研究*候选。** 方向 1 和 7 经评估未通过接纳门；方向 2、3、4 没通过数据审计。
2. **V2 的剩余误差不是测量噪声。** 在 45 °C 段内，石墨台阶深度相对直线的离散只有 0.012–0.036 Ah，比 V2 的误差（约 0.2 Ah）小一个数量级。所以更多、更干净的台阶测量修不了它。
3. **运行工况没有提供关于石墨台阶的新容量信息。**
   - 约每 5 天一次的满充只充到满充以下约 21 Ah 处，位于台阶之上，那段顶部区域也没有可用特征。
   - 所有静置都在满充以下 0–22 Ah。
   - 动态穿越只出现在每个周期的第 4 天，而两次满充之间的库仑计数闭合不上（中位数 0.61 Ah）。
   - 锚点充电和程序放电仍然是仅有的容量信号。
4. **最重要的发现关乎隐藏真值，而不是模型。**
   - 每次检查都会恢复一部分被循环暂时"锁住"的容量。这部分回弹从 CK1 的约 0.02 Ah 增长到 CK7 的约 0.87 Ah，恢复运行后以 τ ≈ 2.5 天衰减。这更符合"循环造成的不均匀在静置时再均匀化"，而不是负极 overhang。
   - 代理是回弹之后的充电量。如果隐藏的 C/20 只包含部分回弹，所有基于锚点的模型在试验后期都会偏高，而且**此时 V1 优于 V2**：回弹一半时 MAE 为 0.333 对 0.434。
5. **建议。**
   - 不要只凭代理证据就把提交从 V1 换成 V2。
   - V1 与 V2 在排行榜上的对比本身就是信息量最大的下一个实验，可以判断哪个回弹假设成立。
   - `V2_epsT`（阶段 6，CK3–CK7 下调 0.21 pp）是另一个只供排行榜检验的探测选项。

## 汇总表

代理误差（pp），主台阶检测方法，A4 平滑 2 Ah。MAE 依次对应 Δ = 0 / 0.4 / 0.8；MAX 取 Δ = 0.4。"伪情景"是 PG1、PG2、PC5、PC10（k ≥ 3，Δ = 0.4）的平均 MAE。

| 模型 | 阶段 | MAE | MAX | 与 ε 无关的 CK2–7 | 伪情景 | 接纳门 |
|---|---|---|---|---|---|---|
| M4（V1，已提交） | 基础 | 0.347 / 0.291 / 0.285 | 0.669 | 0.304 | 0.247 | — |
| **V2** | 基础 | **0.272 / 0.216 / 0.210** | 0.669 | **0.216** | 0.240 | 基准 |
| S1，Theil–Sen 月末直线 | 1 | 0.298 / 0.242 / 0.236 | 0.669 | 0.247 | 0.250 | 不通过（稳健性 1/6） |
| S1，只用最后 3 次台阶（变体） | 1 | — / 0.229 / — | 0.669 | 0.231 | — | 变体 |
| S1，最后一次台阶时刻 + V2 速率（变体） | 1 | — / 0.226 / — | 0.669 | 0.227 | — | 变体 |
| SS_fixed（状态空间 + 水平偏置，τ 8 天） | 7 | 0.271 / 0.228 / 0.216 | 0.569 | 与 ε 有关 | 0.195 | 不通过（回退 +0.34） |
| V2_startcorr（起点修正的配准 β） | 7 | 0.282 / 0.226 / 0.220 | 0.669 | 0.227 | 0.239 | 不通过（稳健性 1/6） |
| 方向 2、3、4 | 2–4 | — | — | — | — | 审计退出 |
| V2_epsT（温度 ε） | 6 | 只供排行榜 | — | — | — | 不评分 |

Δ = 0.4 下的逐检查点误差（pp）：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| M4 | +0.217 | +0.669 | +0.080 | +0.279 | −0.111 | −0.402 | −0.281 |
| V2 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| S1 | +0.217 | +0.669 | +0.080 | +0.364 | +0.149 | −0.209 | −0.008 |
| SS_fixed | +0.295 | −0.133 | −0.002 | +0.569 | +0.384 | −0.039 | −0.174 |
| V2_startcorr | +0.217 | +0.669 | +0.080 | +0.265 | +0.127 | −0.103 | +0.118 |

## 各阶段发现

- **阶段 0。** 精确复现了 V2（0.215726 / 0.669052）和 M4（0.291265）。
- **阶段 1**（[报告](stage_1/REPORT.md)）。稳健的月末直线不如 V2"最后一次台阶 + 速率"的做法。
  - 变化来自把直线外推到检查日，而不是去噪。
  - 段内残差标准差为 0.012–0.036 Ah，所以台阶噪声不是 V2 的瓶颈。
- **阶段 2**（[报告](stage_2/REPORT.md)）。新检测方法能把程序台阶复现到 0.22 Ah 以内（中位数）。
  - 但相邻两次满充之间的库仑计数系统性地差 −0.66 Ah / 4.8 天（约 −5 至 −6 mA 的偏置）。
  - 额外的穿越都在每个周期第 4 天，恰好是漂移最大的时候。
  - 审计退出。
- **阶段 3**（[报告](stage_3/REPORT.md)）。全部 110 个静置都在满充以下 0–22 Ah，台阶附近没有静置点。审计退出。
- **阶段 4**（[报告](stage_4/REPORT.md)）。约每 5 天一次的充电，其顶部 3–19 Ah 内没有可重复、有趋势的 dV/dQ 特征；看上去的"峰"是窗口边界的假象。审计退出。
- **阶段 5**（[报告](stage_5/REPORT.md)）。检查后回弹 0.02 → 0.87 Ah，τ ≈ 2.5 天（95 % 区间 0.5–9.8 天），已与负极 overhang（数周到数月）和静置驱动的再均匀化（数小时到数天）对照。隐藏 C/20 未包含的回弹比例 f 对排名的影响：

| f | M4 MAE | V2 MAE |
|---|---|---|
| 0 | 0.291 | 0.216 |
| 0.5 | 0.333 | 0.434 |
| 1 | 0.596 | 0.700 |

- **阶段 6**（[报告](stage_6/REPORT.md)）。用数据得到的温度偏移（δ ≈ 0.18 Ah，替代假定的 0.4），把 V2 在 CK3–CK7 上下调约 0.21 pp。只供排行榜检验。
- **阶段 7**（[报告](stage_7/REPORT.md)）。
  - 带自由水平偏置的状态空间模型把 CK2 拉到 −0.13 pp，但 CK4/CK5 变差、仍依赖 ε、而且不稳健。
  - 起点修正的配准 β 改变很小。
  - 两者都未通过。

## 风险与局限

- **曝光。** 每个代理值都已知；伪情景复用了相同的月份，不是独立的电池组或标签。
- **ε 与隐藏 C/20 的回弹状态（阶段 5）。** 它们主导了真实分数的不确定性，在试验后期最多约 0.9 pp；没有检查流程信息或排行榜反馈就无法解决。
- **单一电池组。** 6–7 个锚点上的相关性只是诊断，不是验证。
- **偏离。** 阶段 7 的 SS_fixed 使用了第三轮 `fit_predict` 的修改副本，已在运行前登记。
- **没有发生并发事件**，记录见 `notes/DECISIONS.md`。

## 复现

```bash
cd /Users/shane/Desktop/Arena_1014_round4/research/phase2_round4_signals_20261014
python3 -B stage0_reproduce.py
python3 -B stage_1/run_1.py
python3 -B stage_2/audit_2.py
python3 -B stage_3/audit_3.py
python3 -B stage_4/audit_4.py
python3 -B stage_5/run_5.py
python3 -B stage_6/run_6.py
python3 -B stage_7/run_7.py
```

- **环境：** Python 3.13（numpy 2.4，pandas 3.0）。
- **原样复用的代码：**
  - 第三轮的 `src/harness.py`、`registration.py`、`statespace.py`；
  - `events.py`；
  - `v2.py`。
- **缓存：** 位于本 worktree 内被 git 忽略的 `cache/` 目录。
- **没有候选类**：没有模型通过全部接纳门，因此没有生成。
