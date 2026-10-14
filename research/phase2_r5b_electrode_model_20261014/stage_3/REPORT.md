<a id="en"></a>

# Stage 3 — real-anchor identifiability audit

> English · [中文](#zh)

Exposed-exploratory; no proxy metrics were evaluated. The registered exit rule **fails**, so stage4 is diagnostic-only and no E1/E3 model will be evaluated.

All 32 anchor-cell main fits and 1,266 fixed-QLi profile refits were computed. Residual-effective likelihood statistics use n_eff, a model-mismatch scale max(2 mV,RMS), nominal cell95 profiles, and Bonferroni per-cell envelopes for a joint nominal95 pack box. These are conditional diagnostics, not externally calibrated confidence intervals.

For anchors1–7, admissible profile tuples already yield finite C/20 differences of at least **8.101–10.516 Ah** (the gate requires <=0.6 Ah). Every denominator envelope contains zero, so beta_E has no finite certified interval <=0.3. Thus zero of seven anchors meet either identification gate. Fitted LLI points are monotone and interval-compatible, but their correlation with start pack voltage is 0.455; this is not validation of an LLI mechanism.

Each full discrete Cartesian box contains about 0.73–0.92 million tuples. The registered computational design evaluated approximately 1,180 witnessed tuples per anchor, including every one-cell excursion, parameter extrema and deterministic random tuples. Reported finite spans are **lower bounds** on the full nominal95 box range, not tight95 confidence limits. The lower bounds alone exceed the acceptance gate by over an order of magnitude; no exhaustive narrowness claim is needed or made. Some admitted tuples have unavailable roots. In that case no finite full95 target range is reported. The QLi grid also reaches the reference bound, so the mode itself is not identified.

The main anchor0 fitted total R is negative. A valid passive CCCV taper is not available; stage3 reports that root unavailable instead of reproducing the earlier simulator's undocumented resistance floor. Other charge and discharge states are checked over their whole stoichiometric domains, and all four program steps are required. Continuous endpoint bisection replaces the legacy0.02-Ah endpoint discretization; this numerical/validity convention was frozen in stage3 before the audit. For beta's health-only direction, R/h and start OCV are held at anchor1 reference values.

Files: S3_main_fits.csv (RMS, autocorrelation, effective n, modes and event nuisance); S3_LLI_profile_fits.csv (all refits and acceptance statistics); S3_LLI_cell_intervals.csv; S3_pack_intervals.csv (root availability, lower-bound spans, denominator support); S3_LLI_trajectory.csv; S3_exit.json. The completion decision is rejection from demonstrated nonidentifiability, not a claim that sampled bounds cover every accepted tuple.

---

<a id="zh"></a>

# Stage 3 — real-anchor identifiability audit

> [English](#en) · 中文

已曝光探索性研究；没有评估代理指标。登记的退出门**不通过**，阶段4仅诊断，不评估 E1/E3 模型。

完成32个锚点-电芯主拟合和1266个固定 QLi 剖面重新拟合。似然统计使用 n_eff 以及 max(2 mV,RMS) 失配尺度，逐芯名义95剖面通过 Bonferroni 组合成电池组名义95参数盒。这些是模型条件诊断，不是外部校准置信区间。

锚点1–7中，已找到的允许参数组合之间，有限 C/20 容量差至少 **8.101–10.516 Ah**，而门要求 <=0.6 Ah。全部台阶变化分母包络都含零，β_E 没有可认证宽度 <=0.3 的有限区间。因此七个锚点中两项可辨识门均为零个通过。LLI 拟合点单调，区间也可容纳单调序列，但与起始组压相关为 0.455，不能验证 LLI 机制。

完整离散笛卡尔参数盒每个约73–92万组；按登记计算设计，各锚点评估约1180个见证组合，含所有单芯扰动、参数极值及固定随机组。有限跨度只是完整名义95参数盒范围的**下界**，不是紧致95置信限。仅这些下界已超过验收门一个数量级以上，不需要也没有宣称已穷尽所有组合证明窄区间。部分允许组合不可求根，此时不报告完整有限95目标区间。参考 QLi 剖面还触及边界，因此退化模式本身不可辨识。

锚点0主拟合总 R 为负，不支持被动 CCCV 电流递减；阶段3把该首根记为不可得，不沿用旧模拟器未登记的电阻下限。其余充放电均检查完整化学计量域，程序台阶要求四芯全部可得。连续端点二分替代旧0.02 Ah离散端点，这些数值和有效性约定在阶段3审计前已冻结；β 的健康方向固定锚点1参考 R/h 和起始 OCV。

文件包括主拟合、全部剖面、逐芯区间、组端目标可用性及跨度下界、LLI轨迹和退出 JSON。完成决定来自已经展示的不可辨识性，不声称抽样范围覆盖全部允许组合。
