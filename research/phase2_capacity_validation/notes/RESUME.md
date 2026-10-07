# 恢复检查点

本轮封存已一次性评分，不能复用八个 Ji 单芯封存组调参。`configs/freeze_manifest.json`、`sealed/HOLDOUT_SCORED_ONCE` 和 `sealed/provenance_postscore.json` 保留；可安全重跑 `capacity_pipeline.py inventory/qualify/extract/predict/report`，`score` 预期拒绝第二次。独立审查更正的结果用 `outputs/pipeline_result_v2.json`，旧 v1 原件保留。

获得新独立四串数据时，以新 TASK 版本启动：先核准许可/化学体系/4S 102 Ah/满充/温度/5.1 A/首次 11.2 V，按物理组冻结划分与末期阶段，接入真实 RPT，再开发比较 C0–C4 和合法简单基线。只得一个新组只做接入个案。不得将本轮单芯 Ah 成绩混入四串 pp。

本轮主文件：`outputs/LFP_SOH_真实容量验证与测量计划.docx/.pdf`、`outputs/EXECUTIVE_SUMMARY.md`、`outputs/DATA_HANDOFF.md`、`outputs/REPRODUCE.md`、`outputs/acceptance_results.json` 与 `outputs/artifact_manifest.csv`。
