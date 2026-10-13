<a id="en"></a>

# Bounded nuisance profile audit

> English · [中文](#zh)

Exposed-exploratory; proxies are not hidden truth. The original A model used an unconstrained, analytically eliminated voltage offset and reported only scale profiles. This did not fully implement the prescribed bounded nuisance/profile requirement.

This unscored supplement bounds the charge-specific offset to ±20 mV and exports nuisance-optimized profiles for all three parameters, without changing or rescoring the main beta model. Definitions and grids were committed in bounded_profile_protocol.json before this computation. Identified fractions: {'bottom_scale': 0.4, 'top_scale': 0.8, 'voltage_offset_V': 0.2}. The original main result remains rejected; these post-main diagnostics cannot create a pre-registered winning candidate.

---

<a id="zh"></a>

# Bounded nuisance profile audit

> [English](#en) · 中文

已曝光探索性研究；代理不是隐藏真值。原 A 模型把电压偏置解析消除，未限定范围，且只报告两个缩放参数的剖面，因此没有完整实现所要求的有界干扰和逐参数剖面。

本不评分补充将充电特有偏置限制到 ±20 mV，输出三个参数在其他参数优化后的残差剖面，不改变或重评主 β 模型。定义和网格已在计算前提交 bounded_profile_protocol.json。各参数可辨识比例：{'bottom_scale': 0.4, 'top_scale': 0.8, 'voltage_offset_V': 0.2}。原主结果仍被拒绝，主评估后的诊断不能产生预登记赢家。
