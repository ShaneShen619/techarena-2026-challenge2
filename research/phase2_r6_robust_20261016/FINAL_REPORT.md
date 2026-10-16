<a id="en"></a>

# Round 6: Hypothesis-Robust Selection, Fusion, Truth-Oriented Corrections and Open-Data Prior — Final Report

> **Language:** English · [中文](#zh)

- **Run:** 2026-10-15/16, following [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md), as seven work packages (WP0–WP6), each registered before its results.
- **Where:** branch `exp/phase2-r6-robust-20261016`, worktree `/Users/shane/Desktop/Arena_1016_r6_robust`.
- **Reference:** the submitted model **SUB = V2 + √t gap branch** (submission branch commit `21a7a55`).
- **Exposure:** all real-proxy numbers are exposed-exploratory. Selection used only causal hold-out scenarios or the registered hypothesis grid.
- **Untouched:** no submission package was modified.

## Conclusions first

1. **Keep SUB as the submission.** On an 18-hypothesis label grid (true anchor offset Δ, unseen post-checkup recovery f, ε drift d), scored the way the official board scores (normalised by ExampleModel), SUB has the lowest maximum regret (0.027; WP1). No alternative passed the registered gates against it (WP2, WP4).
2. **The open question is the labels, not the model.**
   - SUB's normalised score is about 0.03–0.05, since ExampleModel's proxy MAE is about 4.3 pp.
   - Within one hypothesis, our leading models (SUB, the 5C ensembles, the WP2 fusions) differ by less than 0.05 normalised units. Across hypotheses the same model moves by up to 0.2 (for example, if the hidden C/20 misses the recovery, every model's maximum error reaches 1.2–1.6 pp).
   - Only the leaderboard can tell which hypothesis holds.
3. **The stress law is better in causal tests but cannot be validated where it matters.**
   - The stress law and its fusions beat SUB on pseudo-gap/cut and cold-start tests: pseudo 0.106–0.119 vs 0.148; cold start 0.141–0.144 vs 0.174.
   - SUB and the stress models disagree mainly at CK1 (first month, break-in) and CK2 (whole missing segment). Neither checkup has a causal analogue in this data, and the class weights learned on the analogues transfer badly (WP2).
4. **Open data say the stress-law prior is too pessimistic (WP4).** Over their own histories, the prior over-predicts the measured fade of two open LFP cycling datasets by 24 % (Gotion 53 Ah) and 50 % (LIC 280 Ah). That is consistent with the over-predicted CK1 loss. The Yagci storage data that could fix the calendar term could not be obtained: two failed downloads, and a manual download did not arrive in time. The prior is therefore unchanged.
5. **ε drift is the best hedge, to be tested by a probe (WP3, WP6).** SUB with a −0.031 Ah per Ah drift correction has the best worst case and the best expectations on the grid, and wins in 14 of 18 hypotheses. Its max regret is higher, so it should be probed, not adopted blind.
   - The anchor start-state correction is large (up to 1.29 Ah) but low in confidence.
   - The path-effect correction is physically confirmed (6/6 detection methods) but contradicts the proxies at CK1.
6. **Probe plan (WP6):**
   1. P_drift (SUB + drift);
   2. P_stress_early (F1 fusion with the restart rule, exposed-CK1);
   3. optionally P_start.

   End on the best observed option; SUB is the default.
7. **Report material is ready (WP5):** method, interpretability figure, open-data table, validation, negative results, an 11-slide outline, and a code-quality audit of the submitted model.

## Work packages

| WP | Content | Outcome | Report |
|---|---|---|---|
| 0 | re-baselining against SUB | V2 / SUB / 5C reproduced; archived submitted class = SUB within 0.0004 pp; ExampleModel proxy MAE about 4.3 pp | [wp0](wp0/REPORT.md) |
| 1 | hypothesis-robust selection | real grid: SUB (max regret 0.027); stress ensembles complementary (best worst case); causal grid favours the stress ensembles (tie window wide) | [wp1](wp1/REPORT.md) |
| 2 | uncertainty-weighted fusion | no design passes; main F2_S_A fails (CK1 −0.56, CK2 −0.64); F1 best but behind SUB at Δ 0.4; causal scenarios do not represent CK1/CK2 | [wp2](wp2/REPORT.md) |
| 3 | truth-oriented corrections | ε drift = best hedge; start state material, low confidence; path effect verified but correction contradicted | [wp3](wp3/REPORT.md) |
| 4 | open-data prior | registered fallback (Yagci not obtained); prior2 over-predicts LIC +50 % and Gotion +24 %; prior3 = prior2; no candidate | [wp4](wp4/REPORT.md) |
| 5 | report material | 7 bilingual drafts and a figure in [report_material/](report_material/) | [wp5](wp5/REPORT.md) |
| 6 | synthesis and probes | keep SUB; probe order P_drift → P_stress_early → P_start | [wp6](wp6/REPORT.md) |

## Key numbers

| Model | Proxy MAE Δ0 / .4 / .8 (pp) | MAX Δ0 / .4 / .8 | Pseudo | Cold start | Grid max regret (WP1) | Grid worst s |
|---|---|---|---|---|---|---|
| **SUB** | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.148 | 0.174 | **0.027** | 0.225 |
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | 0.240 | 0.252 | 0.069 | 0.236 |
| 5C R3_TD_w0.75 (exposed-CK1) | 0.188 / 0.131 / 0.174 | 0.440 / 0.311 / 0.344 | 0.123 | 0.134 | 0.047 | 0.215 |
| WP2 F1_S_A | 0.141 / 0.128 / 0.173 | 0.282 / 0.232 / 0.624 | 0.119 | 0.141 | 0.042* | 0.214 |
| SUB + ε drift (WP3) | leaderboard-only | | | | 0.098** | **0.194** |

\* In the WP1 set with the WP2 designs added. \*\* In the WP3 enlarged set, where SUB's own max regret is 0.058.

## Risks and limits

- **Single pack and exposed proxies.** Causal scenarios reuse the same months and cannot represent CK1 and CK2.
- **The hypothesis grid is our construction.** Its axes (Δ, f, d) and priors are assumptions; the official metric set is not published, and s approximates it.
- **The stress-law prior is too pessimistic and its calendar/cycle split is not identifiable.** The fix (Yagci storage data) is pending.
- **Deviations** are recorded in [notes/DECISIONS.md](notes/DECISIONS.md):
  - a pandas-3 cast in the copied causality check;
  - the WP1 tie window;
  - the WP3 amendment;
  - the WP4 bound fallback applied explicitly;
  - the WP5-before-WP4 order;
  - the manual-download wait.

## Reproduction

```bash
cd /Users/shane/Desktop/Arena_1016_r6_robust/research/phase2_r6_robust_20261016
python3 -B wp0/run_wp0.py
python3 -B wp1/run_wp1.py
python3 -B wp2/run_wp2.py select && python3 -B wp2/run_wp2.py real
python3 -B wp3/audit_wp3.py && python3 -B wp3/run_wp3.py
python3 -I -B wp4/axes_cycling.py /Users/shane/Desktop/Arena_1013_model/external_data wp4/outputs/wp4_cycling_axes.csv
python3 -I -B wp4/fit_prior3.py "$PWD"          # add <yagci_table.csv> once the Yagci data are available
python3 -B wp4/run_wp4.py select && python3 -B wp4/run_wp4.py real
python3 -B wp5/figure_wp5.py
python3 -B wp6/run_wp6.py
```

- **Before running:** the archived submission package must be in `cache/submitted_package/`, extracted with `git -C /Users/shane/Desktop/Arena_1013_model archive 21a7a55 TechArena_Challenge2_Team_Package | tar -x -C cache/submitted_package`.
- **Environment:** Python 3.13.0, numpy 2.4.2, pandas 3.0.0, scipy 1.18.0.

---

<a id="zh"></a>

# 第六轮：多假设稳健选择、融合、真值导向修正与开放数据先验——最终报告

> **语言：** [English](#en) · 中文

- **运行：** 2026-10-15/16，按 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) 执行，分七个工作包（WP0–WP6），每个都在出结果之前登记。
- **位置：** 分支 `exp/phase2-r6-robust-20261016`，worktree `/Users/shane/Desktop/Arena_1016_r6_robust`。
- **参照：** 当前提交的模型 **SUB = V2 + √t 缺口分支**（提交分支上的提交 `21a7a55`）。
- **曝光：** 所有真实代理数字都是已曝光的探索性结果。选择只使用因果留出场景或登记的假设网格。
- **未改动：** 没有修改任何提交包。

## 结论先读

1. **保留 SUB 作为提交。** 在 18 种标签假设（真实锚点偏差 Δ、未被测到的检查后恢复 f、ε 漂移 d）构成的网格上，按官方榜单的方式打分（用 ExampleModel 归一），SUB 的最大后悔值最低（0.027；WP1）。没有任何替代方案通过对它的登记门槛（WP2、WP4）。
2. **悬而未决的是标签，而不是模型。**
   - SUB 的归一化得分约为 0.03–0.05，因为 ExampleModel 的代理 MAE 约为 4.3 pp。
   - 在同一个假设下，我们的领先模型（SUB、5C 集成、WP2 融合）之间相差不到 0.05 个归一化单位；而在不同假设之间，同一个模型的得分可以相差 0.2（例如，如果隐藏的 C/20 没有测到恢复，每个模型的最大误差都会达到 1.2–1.6 pp）。
   - 哪个假设成立，只有排行榜能告诉我们。
3. **应力定律在因果检验上更好，但在关键处无法验证。**
   - 应力定律及其融合在伪缺口 / 伪截断和冷启动检验上优于 SUB：伪场景 0.106–0.119 对 0.148；冷启动 0.141–0.144 对 0.174。
   - SUB 与应力模型的分歧主要在 CK1（第一个月，磨合期）和 CK2（整段数据缺失）。这两个检查点在这批数据里都没有因果上的对应场景，而在对应场景上学到的类别权重迁移得很差（WP2）。
4. **开放数据表明应力定律的先验过于悲观（WP4）。** 按两个开放 LFP 循环数据集各自的历史，先验把实测衰减高估了 24 %（Gotion 53 Ah）和 50 %（LIC 280 Ah）。这与 CK1 损失被高估一致。能修正日历项的 Yagci 存储数据没能拿到：两次下载失败，手动下载也没有及时到位。因此先验保持不变。
5. **ε 漂移是最好的对冲，应通过探测来检验（WP3、WP6）。** 加上每衰减 1 Ah 漂移 −0.031 Ah 修正的 SUB，在网格上最坏情况最好、期望也最好，在 18 种假设中有 14 种胜出。但它的最大后悔值更高，所以应先探测，不要直接采用。
   - 锚点起点修正量级大（最多 1.29 Ah），但置信度低。
   - 路径效应在物理上得到证实（6/6 种检测方法），但它对应的修正在 CK1 与代理相矛盾。
6. **探测计划（WP6）：**
   1. P_drift（SUB + 漂移修正）；
   2. P_stress_early（带恢复运行规则的 F1 融合，已曝光 CK1）；
   3. 可选 P_start。

   最后要落在观察到的最佳选项上；SUB 是默认选项。
7. **报告材料已备好（WP5）：** 方法、可解释性图、开放数据表、验证、负面结果、11 页演示大纲，以及对提交模型的代码质量审计。

## 各工作包

| WP | 内容 | 结果 | 报告 |
|---|---|---|---|
| 0 | 以 SUB 为新基准重新确定基线 | 复现 V2 / SUB / 5C；归档的提交类与 SUB 相差不超过 0.0004 pp；ExampleModel 代理 MAE 约 4.3 pp | [wp0](wp0/REPORT.md) |
| 1 | 多假设稳健选择 | 真实网格：SUB（最大后悔值 0.027）；应力集成与之互补（最坏情况最好）；因果网格偏向应力集成（并列阈值偏宽） | [wp1](wp1/REPORT.md) |
| 2 | 不确定度加权融合 | 无设计通过；主模型 F2_S_A 失败（CK1 −0.56，CK2 −0.64）；F1 最好，但 Δ 0.4 时落后于 SUB；因果场景代表不了 CK1/CK2 | [wp2](wp2/REPORT.md) |
| 3 | 真值导向修正 | ε 漂移是最好的对冲；起点状态量级可观、置信度低；路径效应得到证实，但修正与代理矛盾 | [wp3](wp3/REPORT.md) |
| 4 | 开放数据先验 | 按登记规则回退（未拿到 Yagci）；prior2 高估 LIC +50 %、Gotion +24 %；prior3 = prior2；无候选 | [wp4](wp4/REPORT.md) |
| 5 | 报告材料 | [report_material/](report_material/) 中的 7 份双语草稿和一张图 | [wp5](wp5/REPORT.md) |
| 6 | 综合与探测 | 保留 SUB；探测顺序 P_drift → P_stress_early → P_start | [wp6](wp6/REPORT.md) |

## 关键数字

| 模型 | 代理 MAE Δ0 / .4 / .8（pp） | MAX Δ0 / .4 / .8 | 伪场景 | 冷启动 | 网格最大后悔值（WP1） | 网格最坏 s |
|---|---|---|---|---|---|---|
| **SUB** | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.148 | 0.174 | **0.027** | 0.225 |
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | 0.240 | 0.252 | 0.069 | 0.236 |
| 5C R3_TD_w0.75（已曝光 CK1） | 0.188 / 0.131 / 0.174 | 0.440 / 0.311 / 0.344 | 0.123 | 0.134 | 0.047 | 0.215 |
| WP2 F1_S_A | 0.141 / 0.128 / 0.173 | 0.282 / 0.232 / 0.624 | 0.119 | 0.141 | 0.042* | 0.214 |
| SUB + ε 漂移（WP3） | 只用于排行榜 | | | | 0.098** | **0.194** |

\* 在加入 WP2 设计后的 WP1 集合中。\*\* 在 WP3 扩大后的集合中；在该集合里 SUB 自身的最大后悔值为 0.058。

## 风险与限制

- **单个电池组与已曝光的代理。** 因果场景复用同样的月份，无法代表 CK1 和 CK2。
- **假设网格是我们自己构造的。** 它的各轴（Δ、f、d）和先验都是假设；官方指标集没有公布，s 只是近似。
- **应力定律的先验过于悲观，日历 / 循环划分也不可辨识。** 修正办法（Yagci 存储数据）尚待取得。
- **偏离**都记录在 [notes/DECISIONS.md](notes/DECISIONS.md) 中：
  - 复制的因果检查中为适配 pandas 3 加的类型转换；
  - WP1 的并列阈值；
  - WP3 的协议修订；
  - WP4 中显式补上的边界回退；
  - WP5 先于 WP4 的执行顺序；
  - 等待手动下载。

## 复现

```bash
cd /Users/shane/Desktop/Arena_1016_r6_robust/research/phase2_r6_robust_20261016
python3 -B wp0/run_wp0.py
python3 -B wp1/run_wp1.py
python3 -B wp2/run_wp2.py select && python3 -B wp2/run_wp2.py real
python3 -B wp3/audit_wp3.py && python3 -B wp3/run_wp3.py
python3 -I -B wp4/axes_cycling.py /Users/shane/Desktop/Arena_1013_model/external_data wp4/outputs/wp4_cycling_axes.csv
python3 -I -B wp4/fit_prior3.py "$PWD"          # 拿到 Yagci 数据后，再加上 <yagci_table.csv>
python3 -B wp4/run_wp4.py select && python3 -B wp4/run_wp4.py real
python3 -B wp5/figure_wp5.py
python3 -B wp6/run_wp6.py
```

- **运行之前：** 归档的提交包必须放在 `cache/submitted_package/`，用 `git -C /Users/shane/Desktop/Arena_1013_model archive 21a7a55 TechArena_Challenge2_Team_Package | tar -x -C cache/submitted_package` 解压。
- **环境：** Python 3.13.0、numpy 2.4.2、pandas 3.0.0、scipy 1.18.0。
