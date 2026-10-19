<a id="en"></a>

# Round 14 — Path drift on our own pack: final report

> English · [中文](#zh)

**Keep SUB. Registered outcome: O3 "not identifiable".** The registered path drift is d_path = −0.118 Ah/Ah, i.e. E = −0.97 Ah at CK7. Its leave-one-anchor-out (LOO) range is −1.37 … −0.78 Ah, which is 0.59 Ah wide, against a 0.30 Ah limit.

The registered number is not a property of the pack's tops. It comes from the Ah chain's loss rate λ, which steps between checkup cycles. With a same-cycle λ (exploratory, not registered), Term3 shows no trend (−0.11 … +0.04 Ah at CK7). The λ-free voltage check gives −0.28 Ah, all of it from one cell.

This round changed nothing in the submission and used no Challenge 2 proxy label.

## What was asked

- With charge contents in Ah, ε_k = C20_k − Q_fc,k = (F^CK_k − F^A_k) + (B_k − S_k).
- The checkup reaches its top from a part-charged state, like our top-ups; the anchor reaches its top from empty.
- The pack-native measure is Term3_k = F^T_k − F^A_k: the top of the first top-up after anchor k minus the anchor's own top. Both charges end at the same 14.0 V / 5.1 A CV termination, and the Ah chain joins them: Term3 = N(A → T1) − λ·thr.
- **The path drift d_path is the trend of Term3 against fade.** In round 11 this term carried 97 % of LIC's ε drift.

## Results

1. **Setup and facts (WP0).**
   - SUB reproduces through the package CLI: CK7 = 90.765 %.
   - The exposed facts hold:
     - the top rest-voltage gap is 7–8 mV **per cell** (28–33 mV pack);
     - the first-program offset is +0.40 … +0.70 Ah raw, which is +0.3 … +0.4 Ah after removing the normal program-to-program step change;
     - the counters book every 20 A pulse as +10.1–10.2 Ah of charge.
   - Two structural facts shaped everything after:
     - recording gaps lie between the anchor and T1 for anchors 3 and 7;
     - a second top-up exists only for anchors 5 and 6.
2. **Registration (WP1, `46f3c26`).**
   - Round 12's `ahchain.py` was not on origin, so the same rule was implemented here. The synthetic test passes 19/19, with planted offsets recovered to within 4·10⁻¹³ Ah.
   - From the WP0 structure alone, P1 has exactly 5 points and P1b only 2, so P1b is not estimable. Both O1 and O2 need P1b, so they were unreachable before any value was computed. This was registered and stated in advance.
3. **Measurements (WP2).**
   - **P1:** Term3 = +0.60, +0.58, +0.42, +0.09, +0.14 Ah (anchors 1, 2, 4, 5, 6). d_path = −0.118 Ah/Ah, ΔBIC = +7.2.
   - The noise gate passes: σ_TT,25 = 0.125 Ah (conservative reading); σ_TT,45 = 0.032 Ah.
   - **P2** (top rest-voltage gap, λ-free) falls from 33 to 28 mV (E = −0.28 Ah). Only **cell 3** moves (14 → 9 mV); cells 1, 2 and 4 are flat.
   - **P3** (descriptive): the anchor's CV phase grows relative to T1 (+0.50 → +0.80 Ah, +182 → +284 s). The two end currents stay equal to within ±0.005 A.
   - Round 12's registered `ahchain.py`, run on our events, gives identical N on all 27 shared pairs.
   - **Exploratory finding:**
     - λ (top-up → top-up N/thr) is flat within a segment, but it steps between checkup cycles, from −0.94 to −2.82 ×10⁻³.
     - The only 25 °C TT pairs come from July and August, so the registered pooled 25 °C λ over-corrects anchors 2–4 by +0.29 … +0.39 Ah.
     - With the same cycle's 45 °C λ, Term3 = +0.07 … +0.32 Ah, with no trend.
4. **Decision (WP3).**
   - The noise gate passes; identifiability fails (LOO width 0.59 > 0.30 Ah). **Outcome: O3 "not identifiable".**
   - Combined with round 13 (whose tail drift is also O3, d_tail = 0.013 Ah/Ah, range 0 … 0.050): d_top = −0.105 Ah/Ah (range −0.167 … −0.045), i.e. E_top = −0.86 Ah (−1.37 … −0.37). This is reported only and inherits the λ artefact.

## Per-checkup SOH (%)

Leaderboard-only, never scored against proxies, **not recommended**.

| Variant | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| **SUB** | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | **90.765** |
| SUB + d_path (median, −0.118) | 95.694 | 94.043 | 93.029 | 92.158 | 91.257 | 90.599 | 89.860 |
| SUB + d_path (LOO −0.167 … −0.095), CK7 | | | | | | | 89.483 … 90.034 |
| SUB + d_top (median, −0.105) | 95.727 | 94.095 | 93.093 | 92.232 | 91.342 | 90.691 | 89.961 |
| SUB + d_top (−0.167 … −0.045), CK7 | | | | | | | 89.483 … 90.419 |

CK0 is 98.441 % in every variant. The full table is in `wp3/SOH_variants.csv`.

## What this means

- **For the submission:** nothing changes. A −0.9 pp "path drift" correction would rest on an Ah-chain artefact, so it must not be made.
- **For the ε-drift question:** the best-supported reading (not registered) is that the from-empty and top-up tops move together to within a few tenths of an Ah over the campaign. The evidence:
  - same-cycle Term3 is flat;
  - three of the four cells show no change in the top rest-voltage gap;
  - both charges keep ending at the same 5.1 A.
  - The open part of ε remains the **checkup's own** charge protocol (CV termination and rate), which no pack signal can see. This is round 13's conclusion too.
- **For other rounds:**
  - **Round 12's Term3 uses the same pooled 25 °C λ** for anchors 1–4 and 7, so its ε-level terms carry the same month-mismatch, up to ≈ 0.4 Ah. Round 12 is running in parallel and was not modified.
  - **Round 15:** any Ah-chain term must use a same-cycle λ. Register that rule first: take λ from the 45 °C segment of the same cycle; the 25/45 °C transfer error is −0.03 / +0.18 Ah per block; anchors 1 and 7 have no such segment. Only then re-estimate d_path. The probe or organiser answer on the checkup's CV termination stays the lever that would close ε.

## WP status

| WP | Status | One line |
|---|---|---|
| WP0 | done | SUB reproduces (90.765); facts hold (7–8 mV per cell; offset raw +0.40…+0.70); gaps for anchors 3, 7; T2 only for anchors 5, 6 |
| WP1 | done | registered `46f3c26`; synthetic 19/19; P1 = 5 points; P1b not estimable → O1/O2 unreachable |
| WP2 | done | d_path −0.118 (E −0.97 Ah), LOO width 0.59; P2 −0.28 Ah (cell 3); the trend is a month-specific λ (exploratory) |
| WP3 | done | **O3 "not identifiable"**; SUB unchanged; d_top −0.105 (−0.167 … −0.045) reported |

---

<a id="zh"></a>

# 第 14 轮 — 本电池组上的路径漂移：最终报告

> [English](#en) · 中文

**保留 SUB。登记结果：O3"无法识别"。** 登记的路径漂移为 d_path = −0.118 Ah/Ah，即 CK7 处 E = −0.97 Ah。它的留一锚点（LOO）范围为 −1.37 … −0.78 Ah，宽 0.59 Ah，上限为 0.30 Ah。

登记得到的这个数字并不是电池组顶部的性质。它来自电量链的损耗率 λ，而 λ 在检查周期之间会跳变。改用同周期 λ 后（探索性，未登记），Term3 没有趋势（CK7 处 −0.11 … +0.04 Ah）。不依赖 λ 的电压检验给出 −0.28 Ah，而且全部来自一个电芯。

本轮没有改动提交，也没有使用任何 Challenge 2 代理标签。

## 问题是什么

- 以 Ah 计的电荷量：ε_k = C20_k − Q_fc,k = (F^CK_k − F^A_k) + (B_k − S_k)。
- 检查从部分荷电状态充到顶部，与我们的补电相同；锚点则从空充到顶部。
- 本电池组上的对应量是 Term3_k = F^T_k − F^A_k：锚点 k 之后第一次补电的顶部减去锚点自己的顶部。两次充电都结束于同样的 14.0 V / 5.1 A CV 终止条件，用电量链连接：Term3 = N(A → T1) − λ·thr。
- **路径漂移 d_path 就是 Term3 随衰减的趋势。** 在第 11 轮中，这一项占 LIC 的 ε 漂移的 97 %。

## 结果

1. **准备与事实（WP0）。**
   - SUB 可通过包 CLI 复现：CK7 = 90.765 %。
   - 已曝光的事实成立：
     - 顶部静置电压差为**每个电芯** 7–8 mV（电池组 28–33 mV）；
     - 首个程序偏移原始值为 +0.40 … +0.70 Ah，扣除正常的程序间台阶变化后为 +0.3 … +0.4 Ah；
     - 计数器把每个 20 A 脉冲记作 +10.1–10.2 Ah 的充电。
   - 两个结构性事实决定了之后的一切：
     - 锚点 3 和 7 的锚点与 T1 之间有记录间隙；
     - 只有锚点 5 和 6 有第二次补电。
2. **登记（WP1，`46f3c26`）。**
   - 第 12 轮的 `ahchain.py` 当时不在 origin 上，所以在本轮按同一规则实现。合成测试 19/19 通过，植入的偏移找回误差在 4·10⁻¹³ Ah 以内。
   - 仅凭 WP0 的结构就可以知道：P1 正好 5 个点，P1b 只有 2 个点，所以 P1b 无法估计。O1 和 O2 都需要 P1b，因此在算出任何数值之前它们就已不可达。这一点已登记并事先说明。
3. **测量（WP2）。**
   - **P1：** Term3 = +0.60、+0.58、+0.42、+0.09、+0.14 Ah（锚点 1、2、4、5、6）。d_path = −0.118 Ah/Ah，ΔBIC = +7.2。
   - 噪声门通过：σ_TT,25 = 0.125 Ah（保守读法）；σ_TT,45 = 0.032 Ah。
   - **P2**（顶部静置电压差，不依赖 λ）从 33 mV 降到 28 mV（E = −0.28 Ah）。只有**电芯 3** 在变（14 → 9 mV）；电芯 1、2、4 都是平的。
   - **P3**（描述性）：锚点的 CV 阶段相对 T1 越来越长（+0.50 → +0.80 Ah，+182 → +284 s）。两者的末电流始终相差在 ±0.005 A 以内。
   - 在我们的事件上运行第 12 轮已登记的 `ahchain.py`，全部 27 个共有配对的 N 完全相同。
   - **探索性发现：**
     - λ（补电 → 补电的 N/thr）在段内平稳，但在检查周期之间跳变，从 −0.94 到 −2.82 ×10⁻³。
     - 25 °C 的 TT 配对只来自 7 月和 8 月，所以登记的 25 °C 合并 λ 把锚点 2–4 多修正了 +0.29 … +0.39 Ah。
     - 改用同周期 45 °C 的 λ 后，Term3 = +0.07 … +0.32 Ah，没有趋势。
4. **决策（WP3）。**
   - 噪声门通过；可识别性不通过（LOO 宽 0.59 > 0.30 Ah）。**结果：O3"无法识别"。**
   - 与第 13 轮合并（其尾巴漂移同样是 O3，d_tail = 0.013 Ah/Ah，范围 0 … 0.050）：d_top = −0.105 Ah/Ah（范围 −0.167 … −0.045），即 E_top = −0.86 Ah（−1.37 … −0.37）。这只作报告，并且继承了 λ 假象。

## 各检查点 SOH（%）

只用于排行榜，绝不与代理对比打分，**不推荐使用**。

| 变体 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| **SUB** | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | **90.765** |
| SUB + d_path（中位数，−0.118） | 95.694 | 94.043 | 93.029 | 92.158 | 91.257 | 90.599 | 89.860 |
| SUB + d_path（LOO −0.167 … −0.095），CK7 | | | | | | | 89.483 … 90.034 |
| SUB + d_top（中位数，−0.105） | 95.727 | 94.095 | 93.093 | 92.232 | 91.342 | 90.691 | 89.961 |
| SUB + d_top（−0.167 … −0.045），CK7 | | | | | | | 89.483 … 90.419 |

所有变体的 CK0 都是 98.441 %。完整表格见 `wp3/SOH_variants.csv`。

## 这意味着什么

- **对提交：** 不做任何改动。−0.9 pp 的"路径漂移"修正会建立在电量链的假象之上，所以不能做。
- **对 ε 漂移问题：** 证据最充分的解读（未登记）是：在整个试验期间，从空充满和补电的顶部同步移动，误差在零点几 Ah 以内。依据是：
  - 同周期 Term3 是平的；
  - 四个电芯中有三个的顶部静置电压差没有变化；
  - 两种充电始终停在同一个 5.1 A。
  - ε 中仍未确定的部分是**检查自身**的充电协议（CV 终止条件和倍率），任何电池组信号都看不到它。这也是第 13 轮的结论。
- **对其他轮次：**
  - **第 12 轮的 Term3 对锚点 1–4 和 7 使用同一个 25 °C 合并 λ**，所以它的 ε 水平项也带有同样的月份错配，最多约 0.4 Ah。第 12 轮正在并行运行，本轮没有改动它。
  - **第 15 轮：** 任何电量链项都必须使用同周期的 λ。先登记这条规则：λ 取同一周期的 45 °C 段；25/45 °C 迁移误差为每块 −0.03 / +0.18 Ah；锚点 1 和 7 没有这样的段。之后再重新估计 d_path。能够让 ε 收敛的抓手仍是对检查 CV 终止条件的探测或主办方的答复。

## 各工作包状态

| WP | 状态 | 一句话 |
|---|---|---|
| WP0 | 完成 | SUB 可复现（90.765）；事实成立（每个电芯 7–8 mV；偏移原始值 +0.40…+0.70）；锚点 3、7 有间隙；只有锚点 5、6 有 T2 |
| WP1 | 完成 | 登记于 `46f3c26`；合成测试 19/19；P1 = 5 个点；P1b 无法估计 → O1/O2 不可达 |
| WP2 | 完成 | d_path −0.118（E −0.97 Ah），LOO 宽 0.59；P2 −0.28 Ah（电芯 3）；趋势来自按月变化的 λ（探索性） |
| WP3 | 完成 | **O3"无法识别"**；SUB 不变；报告 d_top −0.105（−0.167 … −0.045） |
