# Decisions

> English first; 中文在后。

All decisions below were made in the cloud session that wrote this study, on synthetic cells and on the pack's own data only. **No Challenge 1 file was read and no Challenge 1 output existed.** They are part of the registered version 1.

- **D0.1 label0 rule.** The first draft used the median of the first five labels after B_0. On the synthetic cells this put the fast break-in into eps0 (about 0.1 Ah). The oracle beta then read 14 % low against the planted value. label0 is now the label of the anchor-0 cycle itself, which mirrors CK0 sitting right next to the post-CK0 anchor.
- **D0.2 Gap comparator.** In the gap scenario, the fallback comparator must also switch the sqrt(t) rule off. Otherwise the submitted gap rule fires first and the comparator equals E2. Added `predict(..., gap_rule=False)` (GAP_DAYS = inf) and named the comparator `E1_fallback_no_sqrt`.
- **D0.3 Tables on common targets.** The oracle beta exists only on phase targets. The summary tables are therefore split: all targets without the oracle, and phase targets with it. The gates always pair estimators on common targets.
- **D0.4 Interpolated single variants.** `i0..i5` were added so that C5 can be decided at the `method` level as well.
- **D0.5 Robust slope for C2.** A Theil–Sen slope with intercept diverged when the x values cluster (one synthetic cell gave −253). C2 reports the least-squares slope through the origin, the median ratio r/x, R² and the residual SD.

---

# 决策记录

以下决策都是在编写本研究的云端会话中做出的，只用了合成电芯和本题电池组自己的数据。**当时没有读取任何 Challenge 1 文件，也不存在任何 Challenge 1 输出。** 它们属于登记的第 1 版。

- **D0.1 label0 规则。** 初稿用 B_0 之后前五个标签的中位数。在合成电芯上，这会把快速磨合带进 eps0（约 0.1 Ah），使 oracle β 比植入值低 14%。现在 label0 改为锚点 0 所在循环自己的标签，对应 CK0 紧挨着检查后第一次锚点充电。
- **D0.2 缺口场景的对照。** 缺口场景中的回退对照必须同时关掉 √t 规则，否则提交代码的缺口规则会先触发，对照就等于 E2。为此增加了 `predict(..., gap_rule=False)`（GAP_DAYS = inf），对照命名为 `E1_fallback_no_sqrt`。
- **D0.3 在共同目标上制表。** oracle β 只在相位目标上存在，所以汇总表拆成两张：全部目标（不含 oracle）和相位目标（含 oracle）。门槛判定始终在共同目标上配对比较估计器。
- **D0.4 插值版单一变体。** 增加了 `i0..i5`，使 C5 也能在 `method` 层判定。
- **D0.5 C2 的稳健斜率。** x 值聚集时，带截距的 Theil–Sen 斜率会发散（一个合成电芯给出 −253）。C2 改为报告过原点的最小二乘斜率、比值 r/x 的中位数、R² 和残差标准差。
