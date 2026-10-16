<a id="en"></a>

# Round 7: Literature-Driven Checks — Final Report

> **Language:** English · [中文](#zh)

- **Run:** 2026-10-16/17, following [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md); work packages WP0–WP5, each registered before its results.
- **Where:** branch `exp/phase2-r7-lit-checks-20261016`, worktree `/Users/shane/Desktop/Arena_1016_r7_lit`, based on round 6's final commit `e144086`.
- **Reference:** the submitted model **SUB = V2 + √t gap branch** (submission commit `21a7a55`).
- **Exposure:** all real-proxy numbers are exposed-exploratory. Selection used only causal hold-out scenarios or the registered hypothesis grid.
- **Untouched:** no submission package was modified, and nothing was wired.

## Conclusions first

1. **CK2: switching to temperature-weighted √t (T_main) is recommended, and it is a small change.**
   - T_main replaces the √t time axis with Arrhenius-weighted 45 °C-equivalent days (Ea 20.6 kJ/mol), following the "virtual time" result of Naumann 2018.
   - It passes every registered gate: one-month causal hold-out MAE 0.105 vs 0.113 pp; pseudo 0.144 vs 0.148; cold start 0.170 vs 0.174; grid max regret within tolerance; bit-identical under future-noise; the Python 3.11 package validates.
   - It changes only CK2: **94.451 → 94.507 % SOH**. Calendar time with a lower exponent (p = 0.44) is worse on every causal metric (WP2).
   - **Not wired.** Adopting it means replacing one file (see WP2).
2. **The overhang explanation of the post-anchor step offset is not supported (WP1).**
   - The offset does not grow with the near-empty dwell or the start state; all three registered correlations have the wrong sign.
   - With the memory effect excluded by the literature and homogenisation disfavoured, the offset stays a reproducible charge-path effect. It does not affect SUB.
   - The pack enters every checkup charged (13.1–13.3 V), so the hidden C/20 most likely has no preceding near-empty rest.
3. **The ε-drift sign is not robust (WP3).**
   - The Yagci 180 Ah cycling cells give −0.057 Ah/Ah at 50 °C (agreeing with LIC −0.035 and Gotion −0.031) but +0.18 at 35 °C. The 35 °C value is driven by the first checkup; without it, neither group shows a consistent drift.
   - The pooled median is −0.033, so d stays at −0.031. By the registered rule, **P_drift moves to the end of the probe order: P_stress_early → P_start → P_drift**.
4. **Reichert 2013 was not available (WP4 skipped).**
5. **Report material:** [report_material/risk_addendum.md](report_material/risk_addendum.md) holds bilingual risk paragraphs with DOIs, ready to paste into the package REPORT.

## Work packages

| WP | Content | Outcome | Report |
|---|---|---|---|
| 0 | setup, re-baselining, √t inventory | SUB, round-6 grid (max regret 0.027) and audits reproduced; sqrt_gap fires in 5 distinct causal one-month cases | [wp0](wp0/REPORT.md) |
| 1 | overhang state effect | not supported: P1 ρ −0.29, P2 −0.18, P3 +0.61 (all opposite); H_ov adds little to the grid | [wp1](wp1/REPORT.md) |
| 2 | temperature-weighted √t | T_main passes all gates → recommend switching (CK2 +0.057 pp); not wired | [wp2](wp2/REPORT.md) |
| 3 | ε drift on Yagci | sign not robust (50 °C −0.057, 35 °C +0.178); d = −0.031 kept; P_drift probed last | [wp3](wp3/REPORT.md) |
| 4 | Reichert 2013 | skipped (no full text) | [wp4](wp4/REPORT.md) |
| 5 | synthesis | decision table, SOH tables, risk addendum | [wp5](wp5/REPORT.md) |

## Key numbers

| Model | Proxy MAE Δ0 / .4 / .8 | MAX Δ0 / .4 / .8 | Gap cases (k 3–7) | Pseudo | Cold start | CK2 SOH |
|---|---|---|---|---|---|---|
| SUB | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.113 | 0.148 | 0.174 | 94.451 |
| **T_main** | 0.197 / 0.126 / 0.146 | 0.609 / 0.228 / 0.228 | **0.105** | **0.144** | **0.170** | 94.507 |
| T_ea37 | 0.192 / 0.131 / 0.151 | 0.609 / 0.228 / 0.254 | 0.101 | 0.142 | 0.168 | 94.541 |
| R_p044 (non-causal) | 0.177 / 0.145 / 0.162 | 0.609 / 0.228 / 0.338 | 0.142 | 0.162 | 0.184 | 94.639 |

## Risks and limits

- **Seven anchors.** WP1 statistics are descriptive, and P1's inputs were seen before registration (D1.1).
- **WP2 rests on 5 distinct causal cases.** They are one-month extrapolations at k = 3..7, not the two-month CK2 gap. It also assumes segment 3 ran at 45 °C (at 25 °C, CK2 would be 94.84 %).
- **WP3's estimand is an analogue.** It compares a 50 A RPT at 20 °C with operating charges at 35/50 °C, from 2 cells per temperature.
- **Deviations** are recorded in [notes/DECISIONS.md](notes/DECISIONS.md): D0.1 distinct gap cases; D1.1 exposure of P1's inputs; D1.2 WP1 amendment (column f not measurable; Li-accounting signs).

## Reproduction

```bash
cd /Users/shane/Desktop/Arena_1016_r7_lit/research/phase2_r7_lit_checks_20261016
git -C /Users/shane/Desktop/Arena_1013_model archive 21a7a55 TechArena_Challenge2_Team_Package | tar -x -C cache/submitted_package
python3 -B wp0/run_wp0.py
python3 -B wp1/run_wp1.py
python3 -I -B wp3/eps_yagci.py /Users/shane/Desktop/Arena_1016_r6_robust/research/phase2_r6_robust_20261016/cache/downloads/yagci/unzipped/Data wp3/outputs
python3 -B wp3/run_wp3.py
python3 -B wp2/run_wp2.py causal && python3 -B wp2/run_wp2.py real
python3 -B wp2/check_candidate.py && sh wp2/check_package.sh
python3 -B wp5/run_wp5.py
```

**Environment:** research Python 3.13.0, numpy 2.4.2, pandas 3.0.0, scipy 1.18.0. Package check: Python 3.11.14, numpy 2.4.6, pandas 3.0.6 (`cache/venv311`).

---

<a id="zh"></a>

# 第七轮：文献驱动的检验——最终报告

> **语言：** [English](#en) · 中文

- **运行：** 2026-10-16/17，按 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) 执行；工作包 WP0–WP5，每个都在出结果之前登记。
- **位置：** 分支 `exp/phase2-r7-lit-checks-20261016`，worktree `/Users/shane/Desktop/Arena_1016_r7_lit`，基于第六轮的最终提交 `e144086`。
- **参照：** 提交的模型 **SUB = V2 + √t 缺口分支**（提交 `21a7a55`）。
- **曝光：** 所有真实代理的数字都是已曝光的探索性结果；选择只使用因果留出场景或登记的假设网格。
- **未改动：** 没有修改任何提交包，也没有接入任何东西。

## 结论先读

1. **CK2：建议切换到温度加权 √t（T_main），这是一个很小的改动。**
   - T_main 按 Naumann 2018 的“虚拟时间”结论，把 √t 的时间轴换成按 Arrhenius 加权的 45 °C 等效天数（Ea 20.6 kJ/mol）。
   - 它通过了全部登记门槛：一个月因果留出 MAE 0.105 对 0.113 pp；伪场景 0.144 对 0.148；冷启动 0.170 对 0.174；网格最大后悔值在容差之内；截断后数据换成噪声时输出逐位一致；Python 3.11 下提交包验证通过。
   - 它只改变 CK2：**94.451 → 94.507 % SOH**。改用更小指数的日历时间（p = 0.44）在所有因果指标上都更差（WP2）。
   - **未接入。** 采用时只需替换一个文件（见 WP2）。
2. **锚点后台阶偏移的 overhang 解释不被支持（WP1）。**
   - 偏移不随近空停放时长或起点状态增大，三条登记的相关性方向全部相反。
   - 记忆效应已被文献排除，均匀化也不利，所以偏移仍然是可重复的充电路径效应；它不影响 SUB。
   - 电池组每次进入检查时都是充电状态（13.1–13.3 V），因此隐藏的 C/20 之前很可能没有近空停放。
3. **ε 漂移的符号不稳健（WP3）。**
   - Yagci 180 Ah 循环芯在 50 °C 下给出 −0.057 Ah/Ah（与 LIC −0.035、Gotion −0.031 一致），在 35 °C 下却是 +0.18。35 °C 的结果由第一次检查主导；去掉它之后，两组都没有一致的漂移。
   - 合并中位数为 −0.033，所以 d 保持 −0.031。按登记规则，**P_drift 移到探测顺序的最后：P_stress_early → P_start → P_drift**。
4. **没有取得 Reichert 2013 的全文（WP4 跳过）。**
5. **报告材料：** [report_material/risk_addendum.md](report_material/risk_addendum.md) 中有附 DOI 的双语风险段落，可以直接粘贴进提交包的 REPORT。

## 风险与局限

- **只有 7 个锚点。** WP1 的统计都是描述性的，且 P1 的输入在登记前已见（D1.1）。
- **WP2 只依靠 5 个不同的因果案例。** 它们是 k = 3..7 的一个月外推，而不是 CK2 那样两个月的缺口。此外它假设段 3 在 45 °C 下运行（若为 25 °C，CK2 将是 94.84 %）。
- **WP3 的估计量只是类比量。** 它比较的是 20 °C 下的 50 A RPT 与 35/50 °C 下的运行充电，每个温度只有 2 只芯。
- **偏离记录**见 [notes/DECISIONS.md](notes/DECISIONS.md)。

复现命令与环境见英文部分。
