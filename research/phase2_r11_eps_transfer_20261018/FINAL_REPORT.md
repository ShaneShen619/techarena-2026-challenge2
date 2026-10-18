<a id="en"></a>

# Round 11 — Does the ε drift transfer to our pack? Final report

> English · [中文](#zh)

**Keep SUB, and keep round 7's probe order. Registered outcome O3, "inconclusive": d ∈ [−0.036, +0.052] Ah/Ah, i.e. −0.29 to +0.42 pp at CK7.** The dominant term is **T_path**, the reference-charge vs operating-charge difference, not chemistry-intrinsic CE. In the one dataset that resolves the terms cleanly, the drift sits in a mechanism our pack does not show. This round changed nothing in the submission and used no Challenge 2 proxy label.

## What was asked

- The proxy–truth gap is the same vector g_k for every estimator, so the only open scalar is the fade-proportional slope d = dε/d(fade).
- Earlier rounds pooled black-box slopes (median −0.033, sign not robust).
- This round split ε into two terms on truth-bearing open data, measured our pack's own drivers, and bounded d by registered partial-identification rules:
  - T_CE: reference discharge − reference charge, at the same rate inside the RPT;
  - T_path: reference charge − first operating charge.

## Results

1. **LIC 280 Ah (WP2), the clean case.**
   - T_CE is flat: −0.0008 Ah/Ah, leave-one-out range −0.0011 … +0.0009.
   - T_path carries 97 % of the drift: −0.0287 (OLS −0.035).
   - **Step vs drift:** the step model at the registered event (an unrecorded charge plus an RPT temperature step from 29.7 to 35.1 °C) beats the linear model by only 1.2 BIC for T_path and 0.05 for ε_total. Both are below the registered margin of 2, so the drift model is kept. Within each temperature regime T_path still falls.
   - **Mechanism:** T_path tracks the **top state** of the 1C charge. As the cell ages, the CV phase gets longer (ρ = −0.96), the end current lower and the relaxed top voltage higher. The aged operating charge fills further than the reference charge. The start voltage is not a driver.
2. **Yagci and Gotion (WP3).**
   - Yagci reproduces round 7 exactly.
   - Its terms are unresolved: checkup 0 is a formation test, there are 4 points per cell, and cell slopes span ±0.15.
   - Gotion gives only a total, −0.028.
3. **Our pack (WP4, no labels).**
   - CV Ah rises like LIC's (1.17 → 1.44 Ah).
   - But the anchor ends at a fixed **5.10 A** and relaxes to the **same top voltage** (13.439 → 13.435 V). The top state does not move.
   - Neither registered factor condition holds, so f ∈ [0, 1].
   - Pack-only signals: the start voltage rises by 0.12 V, and the cell spread at the bottom grows from 22 to 35 mV.
4. **Transfer (WP5).**
   - The all-dataset medians give [−0.0065, −0.0008], which would be O1.
   - The registered leave-one-dataset-out pooling, driven by Yagci's noise, widens this to [−0.036, +0.052], so the outcome is O3. Every sensitivity gives the same pattern.
5. **Figgener (WP6)** was skipped: the test protocol is not in the data, and the download is 6.2 GB, above the 3 GB cap.

## What this means

- **For the submission:** nothing changes. The −0.25 to −0.3 pp "common bias" from the earlier screening is **not established for our protocol**.
- **The best-supported reading** (not registered) is a drift near zero. LIC's drift comes from the top state, and our top state is pinned by an exact 0.05C cutoff. The registered rule cannot confirm this without a direct test.
- **Probe order:** P_stress_early → P_start → P_drift, unchanged.
- **Round 12** ([wp5/R12_HANDOFF.json](wp5/R12_HANDOFF.json)):
  - Main task: a **top-of-charge model** that extrapolates each anchor's CV decay (τ 179 → 217 s) beyond 5.1 A, to see whether any Δε_top(k) exists.
  - Also needed: the **bottom/imbalance terms**, which no open dataset here can assess (rising start voltage, growing bottom spread).
  - Constraint: no absolute DMA (round 5B).
  - Gate: identifiability first, i.e. an envelope below 0.3 Ah.

## WP status

| WP | Status | One line |
|---|---|---|
| WP0 | done | reproduction of round 7 passed (0.0006 pp); current SUB CK7 90.765 |
| WP1 | done | registration `d183743`; LIC event = unrecorded charge + temperature step |
| WP2 | done | LIC T_path dominant (top state); step not distinguishable from drift |
| WP3 | done | Yagci reproduces; terms unresolved; Gotion total −0.028 |
| WP4 | done | factor conditions fail; top state flat; bottom/imbalance pack-only |
| WP5 | done | O3, [−0.036, +0.052]; dominant T_path; probe order unchanged |
| WP6 | skipped | no test protocol in data; 6.2 GB > 3 GB |

---

<a id="zh"></a>

# 第 11 轮 — ε 漂移能否迁移到我们的电池组？最终报告

> [English](#en) · 中文

**保留 SUB，保留第 7 轮的探测顺序。登记结果为 O3"无定论"：d ∈ [−0.036, +0.052] Ah/Ah，即 CK7 处 −0.29 到 +0.42 pp。** 主导项是 **T_path**（参考充电与运行充电之差），而不是电池固有的库伦效率。在唯一能干净分项的数据集里，漂移来自一个我们电池组没有表现出的机理。本轮没有改动提交，也没有使用任何 Challenge 2 代理标签。

## 问题是什么

- 代理与真值之间的差距对每个估计器都是同一个向量 g_k，所以唯一未解决的标量是随衰减成比例的斜率 d = dε/d(衰减)。
- 之前各轮合并的是黑箱斜率（中位数 −0.033，符号不稳健）。
- 本轮在有真值的公开数据上把 ε 拆成两项，测量本电池组自己的驱动量，并按登记的部分识别规则给 d 定界：
  - T_CE：RPT 内同倍率的参考放电 − 参考充电；
  - T_path：参考充电 − 第一次运行充电。

## 结果

1. **LIC 280 Ah（WP2，干净的案例）。**
   - T_CE 是平的：−0.0008 Ah/Ah，逐一剔除范围 −0.0011 到 +0.0009。
   - T_path 承载了 97% 的漂移：−0.0287（OLS −0.035）。
   - **台阶还是漂移：** 登记事件处（一次未记录充电加上 RPT 温度从 29.7 °C 升到 35.1 °C）的台阶模型，对 T_path 只比线性模型低 1.2 BIC，对 ε_total 只低 0.05，都没有超过登记的 2，所以保留漂移模型。在每个温度区间内部 T_path 仍在下降。
   - **机理：** T_path 跟随 1C 充电的**顶部状态**。随着老化，CV 段变长（ρ = −0.96）、结束电流变低、弛豫后的顶部电压变高，老化后的运行充电比参考充电充得更满。起点电压不是驱动量。
2. **Yagci 与国轩（WP3）。**
   - Yagci 精确复现了第 7 轮。
   - 但它分辨不出各项：第 0 次检查是化成测试，每只电芯只有 4 个点，各电芯斜率在 ±0.15 范围内。
   - 国轩只有总量，−0.028。
3. **本电池组（WP4，不用标签）。**
   - CV Ah 与 LIC 一样在上升（1.17 → 1.44 Ah）。
   - 但锚点充电始终在 **5.10 A** 结束，并弛豫到**相同的顶部电压**（13.439 → 13.435 V）。顶部状态没有移动。
   - 两个登记的系数条件都不成立，所以 f ∈ [0, 1]。
   - 本电池组特有的信号：起点电压上升 0.12 V，底部电芯离散度从 22 mV 增到 35 mV。
4. **迁移（WP5）。**
   - 全数据集中位数给出 [−0.0065, −0.0008]，单看会落在 O1。
   - 登记的逐一剔除数据集合并受 Yagci 噪声驱动，把区间扩大到 [−0.036, +0.052]，所以结果是 O3。所有敏感性分析都是同样的格局。
5. **Figgener（WP6）** 跳过：数据中没有测试协议，下载量 6.2 GB，超过 3 GB 上限。

## 含义

- **对提交：** 不变。之前筛选得到的 −0.25 到 −0.3 pp"共同偏差"**在我们的协议下并不成立**。
- **证据最充分的解读**（未登记）是漂移接近 0：LIC 的漂移来自顶部状态，而我们的顶部状态被准确的 0.05C 截止电流固定住了。没有直接检验，登记规则无法确认这一点。
- **探测顺序：** 保持 P_stress_early → P_start → P_drift。
- **第 12 轮**（[wp5/R12_HANDOFF.json](wp5/R12_HANDOFF.json)）：
  - 主要任务：**顶部充电模型**，把每次锚点的 CV 衰减（τ 从 179 s 到 217 s）外推到 5.1 A 以下，看是否存在 Δε_top(k)。
  - 还需要：本轮所有公开数据都评估不了的**底部 / 电芯不一致项**（起点电压上升、底部离散度增大）。
  - 约束：不做绝对 DMA（第 5B 轮）。
  - 门槛：先过可识别性检验，即范围小于 0.3 Ah。

## 各 WP 状态

| WP | 状态 | 一句话 |
|---|---|---|
| WP0 | 完成 | 复现第 7 轮通过（0.0006 pp）；当前 SUB 的 CK7 为 90.765 |
| WP1 | 完成 | 登记于 `d183743`；LIC 事件 = 未记录充电 + 温度台阶 |
| WP2 | 完成 | LIC 中 T_path 占主导（顶部状态）；台阶与漂移分不开 |
| WP3 | 完成 | Yagci 复现；各项分辨不出；国轩总量 −0.028 |
| WP4 | 完成 | 系数条件都不成立；顶部状态平坦；底部 / 不一致为本电池组特有 |
| WP5 | 完成 | O3，[−0.036, +0.052]；主导项 T_path；探测顺序不变 |
| WP6 | 跳过 | 数据中无测试协议；6.2 GB > 3 GB |
