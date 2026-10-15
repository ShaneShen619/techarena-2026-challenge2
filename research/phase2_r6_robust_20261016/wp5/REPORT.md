<a id="en"></a>

# WP5 — Report and presentation material (index)

> **Language:** English · [中文](#zh)

Bilingual drafts for the team to merge into `REPORT.md` and the final presentation. **Nothing in the submission package was edited.** WP5 has no protocol; it produces no model metric. WP4 (open-data prior) was still running when these drafts were written, so they mark it "in progress".

| # | Draft | For |
|---|---|---|
| 1 | [01_method_draft.md](../report_material/01_method_draft.md) | REPORT §1: the submitted model (SUB) in brief, plus the model families tried and why none replaced it |
| 2 | [02_interpretability_draft.md](../report_material/02_interpretability_draft.md), figure [fig_stress_law_decomposition.png](../report_material/fig_stress_law_decomposition.png), [table](../report_material/fig_stress_law_decomposition_table.csv), [parameters](../report_material/fig_stress_law_params.json) | interpretability (10 % criterion): break-in 2.03 Ah, calendar 5.79 Ah, cycle 0.42 Ah to the end of the campaign, with the identifiability caveat |
| 3 | [03_open_data_table.md](../report_material/03_open_data_table.md) | REPORT §2: six open sources, licences, use, whether each enters the model |
| 4 | [04_validation_philosophy_draft.md](../report_material/04_validation_philosophy_draft.md) | REPORT §3: causality, exposed proxies, causal hold-outs, the hypothesis grid |
| 5 | [05_negative_results_draft.md](../report_material/05_negative_results_draft.md) | REPORT §4 / presentation: 5B, 5A cold start, WP2 fusion transfer, WP3 path correction |
| 6 | [06_slide_outline.md](../report_material/06_slide_outline.md) | an 11-slide outline for the Challenge 2 part |
| 7 | [07_code_quality_audit.md](../report_material/07_code_quality_audit.md) | code quality (10 %): pycodestyle, docstrings, magic numbers in the submitted model, with fixes |

**Figure.** Made with [figure_wp5.py](figure_wp5.py). The palette is the dataviz reference (categorical slots 1–3), validated for colour-vision deficiency (worst adjacent ΔE 9.2). The third colour is below 3:1 contrast, so every area is directly labelled and a data table accompanies the figure.

**Code-quality findings in brief:** 23 lines exceed 79 characters (clean at 100); 11 of 18 definitions lack docstrings; 9 magic numbers sit inside functions.

---

<a id="zh"></a>

# WP5——报告与演示材料（索引）

> **语言：** [English](#en) · 中文

供团队合并进 `REPORT.md` 和最终演示的双语草稿。**没有编辑提交包里的任何内容。** WP5 没有协议，也不产生任何模型指标。撰写这些草稿时 WP4（开放数据先验）仍在运行，所以草稿中把它标为"进行中"。

| # | 草稿 | 用途 |
|---|---|---|
| 1 | [01_method_draft.md](../report_material/01_method_draft.md) | REPORT 第 1 节：简述提交的模型（SUB），以及试过的模型族和它们为何没有替代 SUB |
| 2 | [02_interpretability_draft.md](../report_material/02_interpretability_draft.md)、图 [fig_stress_law_decomposition.png](../report_material/fig_stress_law_decomposition.png)、[表](../report_material/fig_stress_law_decomposition_table.csv)、[参数](../report_material/fig_stress_law_params.json) | 可解释性（10 % 评分项）：到试验结束时磨合 2.03 Ah、日历 5.79 Ah、循环 0.42 Ah，附可辨识性说明 |
| 3 | [03_open_data_table.md](../report_material/03_open_data_table.md) | REPORT 第 2 节：六个开放来源、许可证、用途，以及是否进入模型 |
| 4 | [04_validation_philosophy_draft.md](../report_material/04_validation_philosophy_draft.md) | REPORT 第 3 节：因果性、已曝光的代理、因果留出、假设网格 |
| 5 | [05_negative_results_draft.md](../report_material/05_negative_results_draft.md) | REPORT 第 4 节 / 演示：5B、5A 冷启动、WP2 融合的迁移、WP3 路径修正 |
| 6 | [06_slide_outline.md](../report_material/06_slide_outline.md) | Challenge 2 部分的 11 页演示大纲 |
| 7 | [07_code_quality_audit.md](../report_material/07_code_quality_audit.md) | 代码质量（10 %）：对提交模型做的 pycodestyle、docstring、魔法数字检查，附修复建议 |

**关于图。** 由 [figure_wp5.py](figure_wp5.py) 生成。配色取自 dataviz 参考调色板（分类色第 1–3 位），已做色觉障碍验证（相邻色最差 ΔE 9.2）。第三个颜色的对比度低于 3:1，所以每个面积区都有直接标注，并附有数据表。

**代码质量发现要点：** 23 行超过 79 字符（按 100 字符则无问题）；18 个定义中有 11 个缺少 docstring；函数内有 9 处魔法数字。
