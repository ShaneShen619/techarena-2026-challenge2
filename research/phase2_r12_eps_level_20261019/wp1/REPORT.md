<a id="en"></a>

# WP1 — Registration: report

> **Language:** English · [中文](#zh)

## Conclusions

1. **The protocol is registered before any WP2/WP3 output.**
   - `wp1/protocol.json` (version 1) holds:
     - the §2 definitions (verbatim plus a structured form);
     - every WP2 locator and WP3 Ah-chain step, with all numeric constants;
     - the §4 gates and decision rules verbatim;
     - an `operationalisation` block for the details the prompt leaves open (DECISIONS D10–D27).
   - `wp1/protocol.sha256` hashes the protocol and the four registered code files.
2. **Registered code.**
   - `src/locators.py` holds the charge-side CL1–CL5, the discharge-side DL1–DL5, DL1 on the deep programs, the combination rules, the Theil–Sen trend with σ_LOO, the CK0 split and the WP2 gates.
   - `src/ahchain.py` holds the package-convention integration, pairing (AT/TT/X with the gap and flat-counter rules), the loss rule, Term1/2/3, the intervals, T_top, the WP3 gates and the E3 arithmetic.
   - WP2 and WP3 import both unchanged.
3. **Synthetic tests pass (15/15, `src/test_registered.py`).**
   - Known step locations are recovered within 0.02 Ah by every variant, on clean curves at sub-grid positions. The actual error is ≤ 0.002 Ah.
   - Known Ah offsets (Term1, Term2 across a switch, Term3) are recovered within 0.005 Ah. The actual error is at float precision.
   - Gap exclusion, the flat-counter rule at switches, both λ fallbacks, G_E2 widening and the G_noise exit behave as registered.
   - The integration is identical to the package's `_integrated_ah`.
   - The module constants equal `protocol.json`.
4. **Resolution caveat (synthetic, reported, not gating).**
   - With 1 mV voltage quantisation, the prescribed dV/dQ-peak variants are much less precise than on clean curves. Single-curve errors reach 0.26–1.34 Ah (median 0.07–0.21 Ah), because a broad dV/dQ peak is nearly flat at its top.
   - The midpoint variants and the cell median are far better: median 0.02–0.10 Ah (`wp1/synthetic_resolution.json`).
   - This limits what B2/B3 can resolve. The registered gates absorb it only through the data's own scatter (σ_LOO) and the variant ranges.
5. **No value computed on challenge data appears in any WP1 file.** WP1 ran no locator, chain or gate on the challenge data.

## What each outcome would mean

| Outcome | Registered condition | Meaning | Consequence |
|---|---|---|---|
| **L1** "assumption supported" | 0.4 ∈ [lo, hi] of EPS_EXTRA_hat = T_top + a_0, width ≤ 0.50 Ah | The pack's own data put the 25 °C anchor offset within ±0.25 Ah of a range that contains 0.4. The assumption is backed by a measurement, not only by its registered range {0, 0.4, 0.8} | Keep SUB. The README may cite the interval. The CK2–CK7 level uncertainty from EPS_EXTRA is at most 0.49 pp (100/102 pp per Ah × 0.5 Ah; CK2 more, through the √t branch) |
| **L2** "assumption off" | 0.4 ∉ [lo, hi], width ≤ 0.50 Ah, G_noise passed, G_SB not failed | The level is measurably different from 0.4, the chain noise is acceptable, and the shared-bottom condition holds | Candidate SUB_L = SUB with EPS_EXTRA_AH = point rounded to 0.05 Ah. Leaderboard-only, not wired. CK2–CK7 move together (≈ 0.98 pp per Ah, CK2 more). The user decides; a P_level probe is discussed in WP4 |
| **L3** "inconclusive" | any other case (width > 0.50 Ah, G_noise failed, no finite a_0, or 0.4 outside but G_SB failed) | The data do not constrain the level well enough, or a prerequisite failed. "Not identifiable" is a valid result | Keep SUB. EPS_EXTRA stays an assumption. The measured interval and its components are reported for round 13 |
| **Anchor-3 rule passes** (G_a3) | \|a_3^rel\| > max(2·σ_LOO, 0.15 Ah) on the combined value, same sign on ≥ 4 of CL1–CL5 | Anchor 3's bottom section is anomalous beyond the relaxed anchors' scatter, consistently across locators, so its start state is not the common bottom. By the registered prediction note this biases every prediction that uses anchor 3 as its base | Candidate SUB_A3fix: Q_fc,3 − a_3^rel in a research copy, so it reaches every use of anchor 3. Leaderboard-only, not wired |
| **Anchor-3 rule fails** | otherwise | Anchor 3's start anomaly is not shown to move its bottom section beyond the scatter, or the locators disagree | No anchor-3 correction. Anchor 3 stays as in SUB |
| **H_SB not failed** (G_SB passes) | σ_LOO ≤ 0.25 Ah and no relaxed anchor with \|LOO residual\| > max(2·σ_LOO, 0.15 Ah) | The relaxed 25 °C anchors' bottom sections follow one smooth trend. This is the necessary condition for "anchor starts at its C/20 end state". It does **not** prove a_k = 0, because S_k (k ≥ 1) is not visible | EPS_EXTRA_hat = T_top + a_0 may be used, and L2 stays possible |
| **H_SB failed** (G_SB fails) | σ_LOO > 0.25 Ah, or some relaxed anchor exceeds the threshold | The bottoms scatter or an anchor deviates: H_SB is "rejected for anchor(s) …" and those anchors join the anomaly list | L2 is blocked, so only L1 or L3 remain. The anomalous anchors are flagged for round 13 |

Related gate outcomes:
- **G_noise fails:** E1 exits "not identifiable", T_top is unmeasured, and the budget is L3.
- **G_T fails:** T_top enters with its wider interval.
- **G_E2 inconsistent:** Term2's interval, and with it T_top's, is widened to include median J_dvdq.
- **G_B3 fails:** a_0 enters with its full interval. Without a finite interval the budget is L3.

## Files

`wp1/protocol.json`, `wp1/protocol.sha256`, `wp1/synthetic_resolution.json`, `src/locators.py`, `src/ahchain.py`, `src/test_registered.py`, `src/wp1_protocol.py` (writes the protocol and the hash).

---

<a id="zh"></a>

# WP1 — 登记：报告

> [English](#en) · 中文

## 结论

1. **协议在 WP2/WP3 产生任何输出之前已登记。**
   - `wp1/protocol.json`（第 1 版）包含：
     - 第 2 节的定义（原文 + 结构化形式）；
     - WP2 的每个定位器和 WP3 电量链的每一步，以及全部数值常数；
     - 原样照抄的第 4 节门槛与决策规则；
     - 一个 `operationalisation` 块，用于 prompt 未规定的细节（DECISIONS D10–D27）。
   - `wp1/protocol.sha256` 记录协议和四个登记代码文件的哈希。
2. **登记代码。**
   - `src/locators.py`：充电侧 CL1–CL5、放电侧 DL1–DL5、深放电程序上的 DL1、合并规则、带 σ_LOO 的 Theil–Sen 趋势、CK0 拆分以及 WP2 的门槛。
   - `src/ahchain.py`：按包内约定的积分、配对（AT/TT/X，含间隙规则和计数器不变规则）、损耗规则、Term1/2/3、区间、T_top、WP3 的门槛以及 E3 的算式。
   - WP2 和 WP3 原样导入这两个模块。
3. **合成测试全部通过（15/15，`src/test_registered.py`）。**
   - 在干净曲线上，台阶位于亚网格位置时，所有变体都在 0.02 Ah 以内找回已知台阶位置；实际误差 ≤ 0.002 Ah。
   - 已知电量偏移（Term1、跨切换的 Term2、Term3）在 0.005 Ah 以内找回，实际误差为浮点精度。
   - 间隙排除、切换处计数器不变规则、两种 λ 回退、G_E2 放宽和 G_noise 退出都按登记方式运行。
   - 积分与包内 `_integrated_ah` 完全一致。
   - 模块常数与 `protocol.json` 一致。
4. **分辨率的局限（合成数据，仅报告，不作门槛）。**
   - 电压按 1 mV 量化时，规定的 dV/dQ 峰值变体远不如在干净曲线上精确：单条曲线误差可达 0.26–1.34 Ah（中位数 0.07–0.21 Ah），因为较宽的 dV/dQ 峰在顶部几乎是平的。
   - 中点穿越变体和电芯中位数要好得多：中位误差 0.02–0.10 Ah（`wp1/synthetic_resolution.json`）。
   - 这限制了 B2/B3 能分辨的程度。登记的门槛只通过数据自身的离散度（σ_LOO）和各变体的范围来吸收它。
5. **WP1 的任何文件中都没有在赛题数据上算出的值。** WP1 没有在赛题数据上运行任何定位器、电量链或门槛。

## 各结果意味着什么

| 结果 | 登记条件 | 含义 | 后果 |
|---|---|---|---|
| **L1"假设得到支持"** | 0.4 ∈ EPS_EXTRA_hat = T_top + a_0 的区间 [lo, hi]，宽度 ≤ 0.50 Ah | 电池组自身的数据把 25 °C 锚点偏移定在一个含 0.4 的、±0.25 Ah 以内的范围；这个假设有了测量支持，而不只是登记范围 {0, 0.4, 0.8} | 保留 SUB；README 可以引用该区间。EPS_EXTRA 带来的 CK2–CK7 水平不确定度至多 0.49 pp（每 Ah 100/102 pp × 0.5 Ah；CK2 经 √t 分支更大） |
| **L2"假设偏离"** | 0.4 ∉ [lo, hi]，宽度 ≤ 0.50 Ah，G_noise 通过，G_SB 未失败 | 水平与 0.4 有可测的差别，电量链噪声可接受，"共用底部"条件成立 | 候选 SUB_L = 把 EPS_EXTRA_AH 设为点估计（取整到 0.05 Ah）的 SUB；只用于排行榜，不接入。CK2–CK7 一起移动（约每 Ah 0.98 pp，CK2 更多）。由用户决定；P_level 探针在 WP4 讨论 |
| **L3"无定论"** | 其他所有情况（宽度 > 0.50 Ah、G_noise 失败、a_0 没有有限区间，或 0.4 在区间外但 G_SB 失败） | 数据对水平的约束不够，或某个前提不成立；"无法识别"是有效结果 | 保留 SUB；EPS_EXTRA 仍是假设；测得的区间及其各分项交给第 13 轮 |
| **锚点 3 规则通过**（G_a3） | 合并值上 \|a_3^rel\| > max(2·σ_LOO, 0.15 Ah)，且 CL1–CL5 中 ≥ 4 个同号 | 锚点 3 的底部区段异常，超出已静置锚点的离散度，且各定位器一致；它的起点不是共同的底部。按登记的预测说明，这会使所有以锚点 3 为基础的预测产生偏差 | 候选 SUB_A3fix：在研究副本中用 Q_fc,3 − a_3^rel，使改动传到锚点 3 的每一处使用；只用于排行榜，不接入 |
| **锚点 3 规则未通过** | 其他情况 | 没有证据表明锚点 3 的起点异常使其底部区段偏离超过离散度，或者各定位器不一致 | 不修正锚点 3，保持 SUB 原样 |
| **H_SB 未被否定**（G_SB 通过） | σ_LOO ≤ 0.25 Ah，且没有已静置锚点的 \|留一残差\| > max(2·σ_LOO, 0.15 Ah) | 已静置的 25 °C 锚点的底部区段遵循同一条平滑趋势。这是"锚点从其 C/20 结束状态开始"的必要条件，但**不能**证明 a_k = 0，因为 S_k（k ≥ 1）不可见 | 可以使用 EPS_EXTRA_hat = T_top + a_0，L2 仍有可能 |
| **H_SB 不成立**（G_SB 失败） | σ_LOO > 0.25 Ah，或某个已静置锚点超过阈值 | 底部离散或有锚点偏离：H_SB 记为"对锚点……不成立"，这些锚点加入异常列表 | L2 被排除，只剩 L1 或 L3；异常锚点留给第 13 轮 |

相关门槛的结果：
- **G_noise 失败：** E1 以"无法识别"退出，T_top 未测得，预算为 L3。
- **G_T 失败：** T_top 以更宽的区间进入预算。
- **G_E2 不一致：** 放宽 Term2 的区间（T_top 的区间随之放宽），使其包含 J_dvdq 的中位数。
- **G_B3 失败：** a_0 以完整区间进入预算；若没有有限区间，预算为 L3。

## 文件

`wp1/protocol.json`、`wp1/protocol.sha256`、`wp1/synthetic_resolution.json`、`src/locators.py`、`src/ahchain.py`、`src/test_registered.py`、`src/wp1_protocol.py`（写出协议和哈希）。
