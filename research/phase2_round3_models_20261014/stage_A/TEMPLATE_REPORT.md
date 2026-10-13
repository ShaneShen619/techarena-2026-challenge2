<a id="en"></a>

# Dual-reference derivative templates

> English · [中文](#zh)

Exposed-exploratory; proxies are not hidden truth. This supplement supplies CK0 (45 C) and first25C (anchor1) templates on a 0.25-Ah grid for every cell and 1/2/3-Ah smoothing. Definitions were frozen in template_protocol.json before this supplement ran; they were not available in the original A pre-registration and never alter its main model.

Robust feature counts out of eight anchor-cell pairs: {'high_SOC_feature_Ah': 8, 'low_tail_onset_Ah': 8, 'main_step_Ah': 8}. A feature is robust only when all three windows locate it within a 1-Ah span. Missing high-SOC peaks and unstable low tails are reported as unavailable/unreliable. See A_dual_reference_features.csv, A_dual_reference_robustness.csv and the derivative curves. This is measurement diagnosis, not ICA-peak-to-capacity regression.

---

<a id="zh"></a>

# Dual-reference derivative templates

> [English](#en) · 中文

已曝光探索性研究；代理不是隐藏真值。本补充提供 CK0（45℃）及首个25℃锚点1的逐芯模板：0.25 Ah 网格，1/2/3 Ah 平滑。定义已在本补充运行前写入 template_protocol.json；原 A 协议未包含这些定义，补充不会改变主模型。

八个锚点-电芯组合中的稳健特征数量：{'high_SOC_feature_Ah': 8, 'low_tail_onset_Ah': 8, 'main_step_Ah': 8}。只有三个窗口都能定位且跨度不超过 1 Ah，才算稳健；不存在的高 SOC 峰和不稳定低端尾段如实标记。详见特征表、稳健性表和导数曲线。本项是测量诊断，不是 ICA 峰位到容量的回归。
