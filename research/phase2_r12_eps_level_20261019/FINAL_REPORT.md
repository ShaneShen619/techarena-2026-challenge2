<a id="en"></a>

# Round 12 — The ε level on our own pack: final report

> **Language:** English · [中文](#zh)

**Keep SUB. Registered decision L3, "inconclusive": EPS_EXTRA_hat = T_top + a_0 = +4.48 Ah [2.35, 6.34], with neither component identified.** The 45/25 °C anchor-top offset is bounded at T_top = +1.11 Ah [0.60, 1.62], but its λ-driven half-width of 0.51 Ah fails G_T. The bottom term a_0 = +3.37 Ah [1.74, 4.72] fails G_B3 and is an artefact of carrying the 25 °C step reference over to the 45 °C anchor 0. The budget point would put CK2 above CK0. `EPS_EXTRA_AH = 0.4` therefore remains an assumption that the pack's own data neither confirm nor overturn. The anchor-3 rule holds, giving the leaderboard-only candidate SUB_A3fix (CK4 −0.36 pp). The probe order is unchanged, and nothing was submitted.

## What was asked

- SUB maps every 25 °C anchor to the checkup protocol with q_anchor = Q_fc,k + ε0 + EPS_EXTRA_AH. Here ε0 = 0.288 Ah comes from the 45 °C anchor 0, and EPS_EXTRA_AH = 0.4 Ah is assumed.
- Proxy scoring cannot see this level, because P_k shares it. This round measured it from the pack's own data:

```
EPS_EXTRA_true = [F^A_0 − F^A_k]  (T_top, WP3)  +  [F^CK_k − F^CK_0]  (drift d, out of scope)  +  [a_0 − a_k]  (WP2)
```

- Under the shared-bottom hypothesis H_SB (a_k = 0) and at equal ageing, EPS_EXTRA_true = T_top + a_0.
- The decision protocol and core methods were registered in WP1 (`b3f3e7a`) before WP2/WP3 evaluation. Later exploratory diagnostics are labelled separately and enter no decision gate.

## Results

1. **Setup and facts (WP0).**
   - SUB reproduces through the package CLI: CK7 = 90.765 %.
   - EPS_EXTRA moves CK3–CK7 by 0.980 pp/Ah. CK2 moves by **1.446 pp/Ah**, because the √t gap branch uses ε twice. CK1 does not move.
   - The data hold 41 CCCV charges that reach CV, 8 of them anchors.
   - Of the 35 facts of §2: 23 confirmed, 6 corrected, 2 cited, 3 deferred (WP0 forbids balances and step locations), 1 recorded.
   - New facts:
     - the AT pairs of anchors 3 and 7 contain recording gaps, across which the counters stay flat (the profile paused);
     - anchor 0 cools by 0.9 K/h during its 0.5 h rest.
2. **Registration (WP1).**
   - The protocol, `src/locators.py` and `src/ahchain.py` were committed before any WP2/WP3 evaluation output. 15/15 synthetic tests pass (step ≤ 0.002 Ah, Ah offsets at float precision).
   - Synthetic caveat: with 1 mV quantisation, dV/dQ-peak errors reach 0.91 Ah; with an additional 0.5 mV noise they reach 1.34 Ah. Midpoint locators and the cell-median combination have **median** absolute errors of 0.02–0.10 Ah across these cases, not a worst-case bound; their recorded maxima reach 0.402 Ah. See [synthetic resolution results](wp1/synthetic_resolution.json).
3. **Bottom (WP2).**
   - **G_SB failed:** σ_LOO = 0.13 Ah, but anchors 5 (−0.52) and 7 (+0.40) exceed 0.26 Ah. H_SB is "rejected for anchors 5, 7".
   - **G_a3 passed:** a_3^rel = +0.305 Ah, with 4 of 5 locators sharing the sign. Anchor 3 started ≈ 0.3 Ah deeper, which fits its unrelaxed start (+53 mV/h).
   - **G_B3 failed:** a_0 = +3.37 [1.74, 4.72] Ah.
     - h (discharge-side step depth minus charge-side step-to-top distance at a common top) is −5.46 Ah from the 25 °C anchors.
     - At anchor 0's own 45 °C top, h is −1.6 … −1.8 Ah (exploratory, not registered). With that h, a_0 ≈ −0.3 … −0.5 Ah, before removing the first-program offset.
   - **Start audit:**
     - anchors 1, 2 and 4–7 are relaxed;
     - anchor 0 is consistent with an unrecorded current event shortly before recording, but does not prove one: +84 mV/h, 2 K above the set point and cooling, cells within 7 mV;
     - anchor 3 is not explained by its short window.
   - Round 8's charge-side step values are uncertain by about ±1 Ah per cell. The broad, quantised dV/dQ plateau makes argmax unstable.
4. **Top (WP3).**
   - **G_noise passed:** σ_TT,25 = 0.125 and σ_TT,45 = 0.026 Ah.
   - **T_top = +1.11 Ah [0.60, 1.62]**, from Term1 +0.07, Term2 (45 vs 25 °C top) +0.62 and Term3 +0.42. **G_T failed** (half-width 0.51).
   - **G_E2 consistent:** median J_DL1 0.705 vs Term2 0.616 Ah.
   - The width comes from a **non-stationary loss ratio**: λ drifts from −0.97 to −2.82·10⁻³ over the months, and the pooled 25 °C λ is taken from months 5–6. An exploratory time-matched λ gives T_top ≈ 0.68 Ah.
   - E3 (voltage to Ah) is not informative.
   - Cell 3 sets the top in all 41 events.
5. **Budget and decision (WP4).**
   - EPS_EXTRA_hat = 4.48 [2.35, 6.34] Ah, so the decision is **L3**: 0.4 lies outside, the width is 3.99 > 0.50, and G_SB failed.
   - The anchor-3 rule holds, giving **SUB_A3fix**.
   - **No P_level probe**: its +4.08 Ah shift is an artefact. The order P_stress_early → P_start → P_drift is unchanged.

## SOH per checkup (%, leaderboard-only candidates, never scored against proxies)

| Model | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| **SUB** (6525edf, EPS_EXTRA 0.4) — kept | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| SUB_A3fix (anchor 3 Q_fc − 0.305 Ah) — candidate | 95.984 | 94.507 | 93.600 | 92.461 | 91.987 | 91.410 | 90.750 |
| SUB, EPS_EXTRA = 2.347 (budget lower end) | 95.984 | 97.324 | 95.509 | 94.730 | 93.924 | 93.335 | 92.674 |
| SUB, EPS_EXTRA = 4.483 (budget point) | 95.984 | 100.413 | 97.603 | 96.824 | 96.018 | 95.429 | 94.768 |
| SUB, EPS_EXTRA = 6.338 (budget upper end) | 95.984 | 103.096 | 99.422 | 98.642 | 97.837 | 97.248 | 96.587 |

The three EPS_EXTRA rows show what the non-identified budget would imply. They are not candidates: the point and the upper end put CK2 above CK0 (98.44 %).

## What this means

- **For the submission:** nothing changes, and the EPS_EXTRA level stays an assumption.
- **Draft README wording (not applied).** Two sentences in `wp4/REPORT.md` §5 say exactly that: the anchor-top offset is bounded, the bottom term is not identified, and CK2–CK7 share a level uncertainty of about 0.98 pp per Ah (CK2 1.45).
- **What the data do say** (not registered):
  - the 45 °C top holds ≈ 0.4–0.7 Ah more than the 25 °C top;
  - the exploratory pieces put EPS_EXTRA roughly between 0.2 and 1.2 Ah, a range that contains 0.4 but does not measure it.
- **SUB_A3fix** is a registered candidate for P_start's question at one anchor. It moves CK4 by −0.36 pp and the rest by ≤ 0.03 pp. Its evidence is marginal: +0.305 Ah only just exceeds the 0.264 Ah gate, and G_SB fails at anchors 5 and 7. It has no demonstrated leaderboard gain in this round; whether to probe it remains the user's decision.
- **Round 13** ([wp4/R13_HANDOFF.json](wp4/R13_HANDOFF.json)) inherits:
  - the drift d (round 11's top-of-charge model);
  - a **time-dependent, registered loss rule** for the Ah chain;
  - a **45 °C h** with an explicit first-program correction, so that a_0 can be identified;
  - the checkup protocol and temperature;
  - self-discharge in the checkup rests;
  - midpoint-type or model-based locators instead of dV/dQ argmax.

## WP status

| WP | Status | One line |
|---|---|---|
| WP0 | done | SUB reproduced (CK7 90.765); CK2 1.446 pp/Ah via √t; 41 CV events; facts re-verified; anchors 3/7 AT pairs have gaps |
| WP1 | done | protocol v1 `b3f3e7a`; registered modules; 15/15 synthetic tests; quantisation caveat |
| WP2 | done | G_SB failed (anchors 5, 7); G_a3 identified (+0.305 Ah); a_0 +3.37 [1.74, 4.72] not identified (h transfer) |
| WP3 | done | T_top +1.11 [0.60, 1.62] not identified; G_noise pass; G_E2 consistent; λ non-stationary |
| WP4 | done | L3, keep SUB; SUB_A3fix leaderboard-only; no P_level probe; R13 hand-off |

## Evidence and final verification — 2026-10-19

This report closes **Round 12**, using the existing WP0–WP4 results at `af263cb`; it does not execute Round 15 or interpret new leaderboard observations. The probe order above is Round 12's inherited recommendation, not a newly validated submission schedule.

- [Bottom gates](wp2/gates.json) and [CK0 split](wp2/ck0_split.json) establish G_SB, G_a3, a_0 and the h-transfer limitation.
- [Top budget](wp3/T_top.json), [final decision](wp4/budget_decision.json), [SOH variants](wp4/SOH_variants.csv) and [handoff](wp4/R13_HANDOFF.json) are the numerical sources. The reported intervals follow the registered sensitivity/interval rules; they are not calibrated confidence intervals for the hidden true capacities.
- All five entries in [protocol.sha256](wp1/protocol.sha256) match. The registered core modules are unchanged from `b3f3e7a`. The existing synthetic suite was rerun with `python3 -B research/phase2_r12_eps_level_20261019/src/test_registered.py`: **15/15 passed**.
- Budget addition, interval endpoints and SUB/SUB_A3fix SOH agree with the machine-readable decision and handoff. The report's five SOH rows were checked against the CSV. This closeout does not rerun the completed challenge-data analyses.
- The submission package is unchanged relative to base `6525edf`. No proxy-label error was computed during closeout, and no file was uploaded. The final report, study README and notes are committed locally; the prompt's push requirement is superseded for this closeout by the user's explicit no-upload instruction. **Local closeout is complete; remote synchronization is intentionally not performed.**

---

<a id="zh"></a>

# 第 12 轮 — 在本电池组上测 ε 的水平：最终报告

> [English](#en) · 中文

**保留 SUB。登记决策为 L3"无定论"：EPS_EXTRA_hat = T_top + a_0 = +4.48 Ah [2.35, 6.34]，两个分项都未识别。** 45/25 °C 锚点顶部偏移被限定在 T_top = +1.11 Ah [0.60, 1.62]，但由 λ 造成的半宽 0.51 Ah 使 G_T 未通过。底部项 a_0 = +3.37 Ah [1.74, 4.72] 未通过 G_B3，它是把 25 °C 的台阶参照搬到 45 °C 锚点 0 上造成的假象。预算的点估计会使 CK2 高于 CK0。因此 `EPS_EXTRA_AH = 0.4` 仍是一个假设，电池组自身的数据既没有证实它，也没有推翻它。锚点 3 规则成立，给出只用于排行榜的候选 SUB_A3fix（CK4 −0.36 pp）。探针顺序不变，本轮没有提交任何东西。

## 问的是什么

- SUB 用 q_anchor = Q_fc,k + ε0 + EPS_EXTRA_AH 把每个 25 °C 锚点映射到检查协议。其中 ε0 = 0.288 Ah 来自 45 °C 的锚点 0，EPS_EXTRA_AH = 0.4 Ah 是假设。
- 代理评分看不到这个水平，因为 P_k 含有同一个水平。本轮改用电池组自身的数据来测它：EPS_EXTRA_true = T_top（WP3）+ 漂移 d（不在本轮范围）+ [a_0 − a_k]（WP2）。
- 在"共用底部"假设 H_SB（a_k = 0）下、老化程度相同时，EPS_EXTRA_true = T_top + a_0。
- 决策协议和核心方法在 WP1（`b3f3e7a`）中先于 WP2/WP3 评估登记；后续探索性诊断另行标注，不进入任何决策门槛。

## 结果

1. **准备与事实（WP0）。**
   - 用包 CLI 复现了 SUB：CK7 = 90.765 %。
   - EPS_EXTRA 使 CK3–CK7 每 Ah 移动 0.980 pp；CK2 每 Ah 移动 **1.446 pp**，因为 √t 间隙分支两次用到 ε；CK1 不动。
   - 数据中共有 41 次到达 CV 的充电，其中 8 次是锚点。
   - 第 2 节的 35 条事实：23 条确认，6 条更正，2 条引用，3 条推迟（WP0 禁止计算电量对账和台阶位置），1 条记录。
   - 新事实：
     - 锚点 3 和 7 的 AT 配对内有记录间隙，前后计数器不变（工况程序暂停）；
     - 锚点 0 在 0.5 h 静置中以 0.9 K/h 降温。
2. **登记（WP1）。**
   - 协议、`src/locators.py` 和 `src/ahchain.py` 都先于 WP2/WP3 的评估输出提交；合成测试 15/15 通过（台阶 ≤ 0.002 Ah，电量偏移为浮点精度）。
   - 合成实验的局限：仅有 1 mV 量化时，dV/dQ 峰值定位误差最高为 0.91 Ah；再叠加 0.5 mV 噪声时最高为 1.34 Ah。中点定位器和电芯中位数组合在这些情形下的**绝对误差中位数**为 0.02–0.10 Ah，这不是最大误差上限；记录中的最大值可达 0.402 Ah。见[合成分辨率结果](wp1/synthetic_resolution.json)。
3. **底部（WP2）。**
   - **G_SB 失败：** σ_LOO = 0.13 Ah，但锚点 5（−0.52）和 7（+0.40）超过 0.26 Ah，H_SB 记为"对锚点 5、7 不成立"。
   - **G_a3 通过：** a_3^rel = +0.305 Ah，5 个定位器中 4 个同号。锚点 3 起点深约 0.3 Ah，与其未静置好的起点（+53 mV/h）一致。
   - **G_B3 失败：** a_0 = +3.37 [1.74, 4.72] Ah。
     - h（同一顶部下，放电侧台阶深度减充电侧台阶至顶部的距离）由 25 °C 锚点得到，为 −5.46 Ah。
     - 在锚点 0 自己 45 °C 的顶部，h 为 −1.6 … −1.8 Ah（探索性，未登记）；用它得到 a_0 ≈ −0.3 … −0.5 Ah（尚未去掉首个程序偏移）。
   - **起点审查：**
     - 锚点 1、2、4–7 已静置好；
     - 锚点 0 的表现与记录开始前不久发生过未记录电流事件相符，但不能证明该事件：+84 mV/h，比设定温度高 2 K 且在降温，电芯相差仅 7 mV；
     - 锚点 3 的异常无法用窗口短来解释。
   - 第 8 轮充电侧台阶值逐电芯约有 ±1 Ah 的不确定性：dV/dQ 平台宽且被量化，argmax 不稳定。
4. **顶部（WP3）。**
   - **G_noise 通过：** σ_TT,25 = 0.125、σ_TT,45 = 0.026 Ah。
   - **T_top = +1.11 Ah [0.60, 1.62]**，由 Term1 +0.07、Term2（45 °C 与 25 °C 顶部之差）+0.62、Term3 +0.42 组成；**G_T 未通过**（半宽 0.51）。
   - **G_E2 一致：** J_DL1 中位数 0.705，Term2 中位数 0.616 Ah。
   - 宽度来自**不平稳的损耗比**：λ 在几个月间从 −0.97 漂移到 −2.82·10⁻³，而 25 °C 合并 λ 取自第 5–6 月。探索性的时间匹配 λ 给出 T_top ≈ 0.68 Ah。
   - E3（电压换算为 Ah）没有信息量。
   - 41 次事件中都是 cell3 决定顶部。
5. **预算与决策（WP4）。**
   - EPS_EXTRA_hat = 4.48 [2.35, 6.34] Ah，决策为 **L3**：0.4 在区间外，宽度 3.99 > 0.50，且 G_SB 失败。
   - 锚点 3 规则成立，给出 **SUB_A3fix**。
   - **不做 P_level 探针**：它的 +4.08 Ah 平移是假象。顺序 P_stress_early → P_start → P_drift 不变。

## 各检查点的 SOH

表格与英文部分相同。SUB 保留；SUB_A3fix 为候选（只用于排行榜，从不与代理标签对比打分）；三行 EPS_EXTRA 变体只用来说明未识别的预算意味着什么，不是候选——其中点估计和上端都会使 CK2 高于 CK0（98.44 %）。

## 意味着什么

- **对提交：** 不改动，EPS_EXTRA 的水平仍是假设。
- **README 措辞草稿（未应用）：** `wp4/REPORT.md` 第 5 节的两句话正是这样表述的：顶部偏移有界，底部项未识别，CK2–CK7 共有约每 Ah 0.98 pp 的水平不确定度（CK2 为 1.45）。
- **数据实际说明了什么**（未登记）：
  - 45 °C 的顶部比 25 °C 的顶部多存约 0.4–0.7 Ah；
  - 各探索性分项把 EPS_EXTRA 大致放在 0.2–1.2 Ah 之间——这个范围包含 0.4，但不是对它的测量。
- **SUB_A3fix** 是针对单个锚点的登记候选：CK4 −0.36 pp，其余 ≤ 0.03 pp。证据只是勉强通过门槛：+0.305 Ah 仅略高于 0.264 Ah，且锚点 5、7 的 G_SB 失败。本轮没有证明其排行榜收益；是否探测由用户决定。
- **第 13 轮**（[wp4/R13_HANDOFF.json](wp4/R13_HANDOFF.json)）继承以下事项：
  - 漂移 d（第 11 轮的充电顶部模型）；
  - 电量链的**随时间变化、事先登记的损耗规则**；
  - 带明确首个程序修正的 **45 °C h**，以便识别 a_0；
  - 检查协议与温度；
  - 检查静置期间的自放电；
  - 用中点型或基于模型的定位器取代 dV/dQ argmax。

## 各工作包状态

| WP | 状态 | 一句话 |
|---|---|---|
| WP0 | 完成 | 复现 SUB（CK7 90.765）；CK2 经 √t 为每 Ah 1.446 pp；41 次 CV 事件；事实已核对；锚点 3/7 的 AT 配对有间隙 |
| WP1 | 完成 | 协议 v1 `b3f3e7a`；登记模块；合成测试 15/15；量化局限 |
| WP2 | 完成 | G_SB 失败（锚点 5、7）；G_a3 已识别（+0.305 Ah）；a_0 +3.37 [1.74, 4.72] 未识别（h 迁移问题） |
| WP3 | 完成 | T_top +1.11 [0.60, 1.62] 未识别；G_noise 通过；G_E2 一致；λ 不平稳 |
| WP4 | 完成 | L3，保留 SUB；SUB_A3fix 只用于排行榜；不做 P_level 探针；交给第 13 轮 |

## 证据与最终核验 — 2026-10-19

本报告收尾的是**第 12 轮**，依据 `af263cb` 中已有的 WP0–WP4 结果；本次没有执行第 15 轮，也没有解读新的排行榜记录。上面的探针顺序是第 12 轮沿用的建议，不是本次重新验证的提交时间表。

- [底部门槛](wp2/gates.json)和 [CK0 拆分](wp2/ck0_split.json)支持 G_SB、G_a3、a_0 及 h 迁移局限的结论。
- [顶部预算](wp3/T_top.json)、[最终决策](wp4/budget_decision.json)、[SOH 变体](wp4/SOH_variants.csv)及[交接文件](wp4/R13_HANDOFF.json)是数值依据。报告区间按登记的敏感性与区间规则构造，不是对隐藏真实容量校准过的置信区间。
- [protocol.sha256](wp1/protocol.sha256) 中 5 项哈希全部一致，核心登记模块自 `b3f3e7a` 后未变。以 `python3 -B research/phase2_r12_eps_level_20261019/src/test_registered.py` 复跑已有合成测试，**15/15 通过**。
- 已核对预算加法、区间端点以及 SUB/SUB_A3fix 与机器可读交接文件的一致性；报告五行 SOH 与 CSV 一致。本次没有重跑已完成的赛题数据分析。
- 提交包相对基点 `6525edf` 保持不变。本次收尾未计算任何代理标签误差，未上传任何文件。最终报告、研究目录 README 和记录在本地提交；用户明确要求“不得上传”，因此本次不执行 prompt 中的 push。**本地收尾完成，远端同步有意不执行。**
