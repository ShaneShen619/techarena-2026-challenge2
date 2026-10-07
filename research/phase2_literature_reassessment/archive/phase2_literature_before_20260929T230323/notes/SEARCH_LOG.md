# 检索日志

日期：2026-09-28。检索仅使用通用论文题名与研究术语，不上传官方运行数据。

筛选优先级：LFP、大容量方形、现场/储能BMS、串联组、动态运行和少容量标签；跨体系和完整实验室循环作有条件参照。只有实际获得全文并检查方法、数据与结果位置才记“全文精读”。

待记录每次检索：查询词、入口、候选、入选/排除原因、全文入口和访问结果。第一阶段旧调研仅作题名线索。

## 2026-09-28 检索与筛选执行

入口：网页学术搜索、arXiv 完整 HTML、PMC 完整 HTML、机构公开 PDF、出版社出版页。检索式包括 `LFP state of health partial charging field data`、`series-connected module incremental capacity`、`dynamic charging virtual incremental capacity`、`LFP SOC SOH joint estimation bias`、`capacity estimation OCV invariance`、`battery voltage relaxation capacity`、`Schaeffer GP LFP field data`。只提交通用关键词/题名。

全文精读：Schaeffer2024（正式版出版页/作者稿全文，版本差异注明）、Krupp2021（DLR 13 页 PDF）、Deng2022（PMC HTML）、Yi2024（arXiv HTML）、ZhouAitioHowey2025（arXiv HTML）、Wang2025（arXiv HTML）、Zhou2026（arXiv HTML 及作者 PDF）、Cheng2024（arXiv HTML）。选择理由：覆盖现场 LFP、串联组、部分窗口、OCV/ECM、GP、变电流与多标签深网，并可定位方法/结果。

出版页/摘要核对而未算全文精读：Berecibar2016（Elsevier 出版页；付费全文）、Zhu2022（Nature 出版页；作者 PDF 打开失败）、Qi2024（出版社摘要；伪标签管线）、Tang2021（PMC reCAPTCHA）、2025 MethodsX 动态 ICA（PMC reCAPTCHA）。这些文献没有承担无法从可见原文验证的具体方法/误差结论。

排除/降权：生命周期/RUL 预测与当前容量估计目标不同；NMC/NCA 容量监督模型只用于说明迁移条件；只有搜索结果片段、未核对元数据的论文不纳入参考文献。没有为凑 15–25 篇而补不相关文献。

访问限制：`curl` 外部域名 DNS 解析失败；MDPI 网页 429，PMC 某些页需 reCAPTCHA，MIT/Nature 作者 PDF 打开超时。已改用合法可访问的机构 PDF、arXiv/PMC HTML；`papers/` 保持空目录。后续网络开放时按 DOI 下载并记录日期/许可，不影响当前文献判断。
