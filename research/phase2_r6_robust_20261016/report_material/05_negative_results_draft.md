<a id="en"></a>

# Draft — Negative results worth showing

> **Language:** English · [中文](#zh)

1. **Electrode-level model (5B): not identifiable on this pack.**
   - With literature half-cell OCPs (PyBaMM), a synthetic test recovered the C/20 capacity to 0.03 Ah. On the real anchor charges, every fit hit the LFP capacity bound, with an unphysical half-used cathode.
   - Admissible parameter sets differed by 8–10.5 Ah in the predicted C/20 capacity, against a 0.6 Ah requirement.
   - Lesson: degradation-mode analysis needs half-cell curves measured on these cells.
2. **Stress law cold start (5A).** Calibrated on the pack's anchors, it tracks CK3–CK7 to within 0.4 pp. At CK1, with no anchor pair yet, the literature prior over-predicted the first month's loss by 1.2 Ah (−1.13 pp).
3. **Fusion weights learned on hold-out scenarios do not transfer to CK1 and CK2 (round 6 WP2).** The cold-start scenario (later months without earlier anchors) and the pseudo-gaps (a few days) do not resemble the real first month (break-in) or the real CK2 gap (a whole missing 45 °C segment). These two checkups cannot be validated causally with this data.
4. **Path-effect correction (round 6 WP3).** The first program after each anchor reads 0.41–0.56 Ah deeper (6 of 6 detection methods). Correcting for it in the fallback branch nevertheless moves CK1 by +0.75 pp, against every label hypothesis. It is kept as a diagnostic, not a correction.

---

<a id="zh"></a>

# 草稿——值得展示的负面结果

> **语言：** [English](#en) · 中文

1. **电极级模型（5B）：在本电池组上不可辨识。**
   - 用文献半电池 OCP（PyBaMM），合成测试能把 C/20 容量还原到 0.03 Ah 以内。但在真实锚点充电上，每个拟合都撞到 LFP 容量上界，得到只用了一半的正极，这在物理上不成立。
   - 可接受的参数组合给出的 C/20 容量相差 8–10.5 Ah，而要求是 0.6 Ah 以内。
   - 教训：退化模式分析需要在这些电芯上实测的半电池曲线。
2. **应力定律的冷启动（5A）。** 用电池组的锚点标定后，它在 CK3–CK7 上的误差都在 0.4 pp 以内。但在还没有锚点对的 CK1，文献先验把首月损失多算了 1.2 Ah（−1.13 pp）。
3. **在留出场景上学到的融合权重迁移不到 CK1 和 CK2（第六轮 WP2）。** 冷启动场景（后面的月份删掉早期锚点）和伪缺口（几天）既不像真实的第一个月（磨合期），也不像真实的 CK2 缺口（整整一个缺失的 45 °C 段）。用这批数据无法对这两个检查点做因果验证。
4. **路径效应修正（第六轮 WP3）。** 每次锚点后的第一次程序读数偏深 0.41–0.56 Ah（六种检测方法全部一致）。但在 fallback 分支里修正它，会让 CK1 上调 0.75 pp，与每一种标签假设都相矛盾。它作为诊断保留，而不作为修正。
