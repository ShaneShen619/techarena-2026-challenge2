<a id="en"></a>

# Causal pack-root mapping supplement

> English · [中文](#zh)

Exposed-exploratory. This supplement is not scored on proxies and does not validate hidden capacity.

The prescribed per-cell maps were applied to the CK0 loaded discharge. Stage-A maps were composed with a CK0-to-anchor1 A4 bridge; per-cell A4 maps and relative discharge-step offsets provide fallback variants. Every state comes from the last anchor visible before CK_k (anchor k−1), so no post-checkup anchor is used to correct that checkup.

The raw four-cell sum ends at 11.203 V. Its 11.2 V root requires a short, explicitly reported linear tail extension (at most 0.1 Ah); the baseline root is 100.416854 Ah. No absolute IR or polarization term was added. Charge-fit voltage offsets were treated as charge-specific nuisance terms and were not transferred to discharge.

Maximum |model ε−ε0| among finite roots: 0.022651 pp. 15 of 105 roots are unavailable within the allowed tail extension; the overall drift is therefore inconclusive, not established negligible. The finite range and each per-cell-map root are in E_required_causal_ranges.csv and E_required_causal_maps.csv. This is a physical sensitivity range, not a calibrated interval. Charge-to-discharge transfer, the 45/25-C bridge, map identifiability and start-state confounding remain unvalidated. It cannot support promoting an ε correction without independent evidence.

---

<a id="zh"></a>

# Causal pack-root mapping supplement

> [English](#en) · 中文

已曝光探索性研究。本补充不按代理评分，也不验证隐藏容量。

按执行文件要求，把逐芯映射应用于 CK0 带载放电曲线。阶段 A 映射与 CK0→锚点1 的 A4 桥接组合，并提供逐芯 A4 及相对放电台阶偏移作为回退变体。所有状态均来自 CK_k 前最后可见锚点（k−1），没有用检查后的锚点修正该检查点。

原始四芯和末端为 11.203 V，因此首次 11.2 V 根需要明确报告的短尾段线性外延（最多 0.1 Ah）；基准首根为 100.416854 Ah。没有重复添加绝对 IR 或极化项。充电拟合的电压偏置视为充电特有干扰，没有移植到放电。

可找到的首根中 |模型 ε−ε0| 最大为 0.022651 pp；105 个首根中有 15 个在允许的尾段外延内无法找到，因此整体漂移无定论，不能判定可忽略。逐根和有限范围见 E_required_causal_maps.csv 与 E_required_causal_ranges.csv。这是物理敏感性范围，不是校准区间。充放电映射迁移、45/25℃ 桥接、映射可辨识性和起点混淆仍未验证，不能据此直接提升 ε 修正模型。
