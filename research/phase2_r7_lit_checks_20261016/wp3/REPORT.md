<a id="en"></a>

# WP3 — ε drift on the Yagci 180 Ah cycling cells

> **Language:** English · [中文](#zh)

- **Protocol:** [protocol.json](protocol.json), SHA256 in `protocol.sha256`, committed in `a6cc2e0` before any ε value was computed. The qualification audit (file structure only) came before it.
- **Scripts:** [eps_yagci.py](eps_yagci.py) (`python3 -I -B`, reads round 6's download in place); [run_wp3.py](run_wp3.py).
- **Outputs:** [wp3_yagci_eps.csv](outputs/wp3_yagci_eps.csv), [d by cell](outputs/wp3_yagci_d_by_cell.json), [pooling](outputs/wp3_pooling.json), [SOH table](outputs/wp3_SUB_drift_SOH.csv), [grid](outputs/wp3_grid_decision.csv), [figure](outputs/wp3_eps_vs_fade.png), and the post-hoc check [without checkup 0](outputs/wp3_posthoc_excl_ck0.json).

## Conclusions first

1. **Registered outcome: "drift sign not robust".** The Yagci 35 °C group gives d = +0.18 Ah/Ah (registered threshold > +0.01). By the rule, P_drift should be probed **after** the other probes, and d stays at round 6's −0.031.

| Dataset | d (Ah per Ah of fade) | Note |
|---|---|---|
| LIC 280 Ah | −0.035 | external screening (round 5/6) |
| Gotion 53 Ah cell | −0.031 | same |
| Yagci 50 °C (cells 22, 28) | −0.056, −0.058 → **−0.057** | same sign as LIC/Gotion, a little larger |
| Yagci 35 °C (cells 19, 42) | +0.203, +0.153 → **+0.178** | opposite sign |
| Pooled median (4 datasets) | **−0.033** | leave-one-dataset-out medians −0.031 to −0.035 |

2. **The 35 °C sign comes from the first checkup.**
   - At the initial RPT, the RPT discharge capacity is 1.9 and 3.5 Ah (102 Ah scale) **below** the first operating charge. This is a start-of-life effect (formation or overhang equilibration after delivery, plus the 20 °C vs 35 °C test temperature).
   - **Post-hoc** (descriptive, not part of the rule): without checkup 0 the group slopes are −0.012 (35 °C) and +0.017 (50 °C), with cells disagreeing in sign. On this subset the Yagci cycling cells show **no consistent drift at all**.
   - The start-state guard never fired: no first operating cycle was a partial charge.

3. **What this means for P_drift.**
   - The negative drift now rests on LIC and Gotion, plus the Yagci 50 °C cells in the registered estimate. The pooled median (−0.033) still matches round 6's −0.031.
   - But one of two Yagci temperature groups contradicts it, and without the first checkup neither group supports it.
   - So **P_drift remains the best hedge on the grid but is not a safe default**. That is consistent with round 6 ("probe, do not adopt blind"). The registered recommendation is to move it behind the other probes.

4. **Grid (round-6 grid + WP1's H_ov_after family):** SUB has the lowest max regret (0.037). SUB + drift (−0.031) has the best worst case (0.194 vs 0.225) and the best expectations (diagnosis prior 0.087 vs 0.095). The drift values −0.031 and −0.033 are practically indistinguishable.

## SOH table (leaderboard-only, Δ = 0.4 configuration)

| Model | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB | 95.992 | 94.451 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| SUB + drift −0.020 | 95.943 | 94.371 | 93.443 | 92.698 | 91.954 | 91.189 | 90.668 |
| SUB + drift −0.031 | 95.916 | 94.327 | 93.389 | 92.637 | 91.884 | 91.111 | 90.585 |
| SUB + drift −0.033 | 95.911 | 94.319 | 93.379 | 92.625 | 91.871 | 91.097 | 90.569 |

## Limits

- **Estimand mismatch.** Yagci RPTs are 50 A CC-CV at 20 °C and operating charges are at 35/50 °C. Our pack compares a C/20 discharge with an about 0.2C charge at about 26 °C. The slope is the closest available analogue, not the same quantity.
- **Sample size.** Two cells per temperature and 4 points per cell. The leave-one-checkup-out ranges are wide (cell 42: −0.15 to +0.38).
- **Checkup 1500** is a byte-identical copy of checkup 1000 in the summary file and is excluded, as in round 6.
- **Not usable for ε:** TUM kxh42bfgtj (2018 calendar) and Mendeley 6hgyr25h8d (2020 cycle) publish no charge capacity.

---

<a id="zh"></a>

# WP3 — 在 Yagci 180 Ah 循环芯上检验 ε 漂移

> **语言：** [English](#en) · 中文

- **协议：** [protocol.json](protocol.json)，在计算任何 ε 值之前于 `a6cc2e0` 提交；在此之前只做了资格审查（文件结构）。
- **脚本：** [eps_yagci.py](eps_yagci.py)（`python3 -I -B`，原地读取第六轮下载的数据）；[run_wp3.py](run_wp3.py)。

## 结论先读

1. **登记的结果：“漂移符号不稳健”。** Yagci 35 °C 组给出 d = +0.18 Ah/Ah（登记阈值为 > +0.01）。按规则，P_drift 应排在其他探测**之后**，d 保持第六轮的 −0.031。
   - LIC −0.035，Gotion −0.031；
   - Yagci 50 °C 两只芯 −0.056、−0.058（组均值 −0.057），与 LIC/Gotion 同号且略大；
   - Yagci 35 °C 两只芯 +0.203、+0.153（组均值 +0.178），符号相反；
   - 4 个数据集合并的中位数为 −0.033，逐一剔除数据集后的中位数在 −0.031 到 −0.035 之间。
2. **35 °C 的正号来自第一次检查。**
   - 在初始 RPT 时，RPT 放电容量比第一次运行充电**低** 1.9 和 3.5 Ah（按 102 Ah 折算）。这是寿命初期效应（化成或出厂后 overhang 的平衡，加上 20 °C 与 35 °C 测试温度的差异）。
   - **事后**（描述性，不属于登记规则）：去掉检查 0 后，两组斜率分别为 −0.012（35 °C）和 +0.017（50 °C），而且同组电芯符号不一致。在这个子集上，Yagci 循环芯**完全没有一致的漂移**。
   - 起点状态保护从未触发：没有任何第一次运行循环是部分充电。
3. **对 P_drift 的含义。**
   - 负漂移现在依靠 LIC 和 Gotion，加上登记估计中的 Yagci 50 °C 芯；合并中位数（−0.033）仍与第六轮的 −0.031 一致。
   - 但 Yagci 两个温度组中有一个与之矛盾，去掉第一次检查后两个组都不支持它。
   - 所以 **P_drift 仍是网格上最好的对冲，但不能作为稳妥的默认选择**，这与第六轮“先探测、不要盲目采用”的结论一致。登记建议是把它排到其他探测之后。
4. **网格**（第六轮网格 + WP1 的 H_ov_after 假设族）：SUB 的最大后悔值最低（0.037）；SUB + 漂移（−0.031）的最坏情况最好（0.194，SUB 为 0.225），期望也最好（诊断先验 0.087，SUB 为 0.095）。−0.031 与 −0.033 实际上没有区别。

## 局限

- **估计量不完全对应。** Yagci 的 RPT 是 20 °C 下 50 A CC-CV，运行充电在 35/50 °C；本题比较的是 C/20 放电与约 26 °C 下约 0.2C 的充电。斜率只是能找到的最接近的类比量，不是同一个量。
- **样本量。** 每个温度 2 只芯、每只芯 4 个点；逐一剔除检查点后的范围很宽（42 号芯为 −0.15 到 +0.38）。
- **检查 1500** 在汇总文件中与检查 1000 逐字节相同，与第六轮一样排除。
- **无法用于检验 ε 的数据：** TUM kxh42bfgtj（2018 日历老化）和 Mendeley 6hgyr25h8d（2020 循环老化）没有公开充电容量。
