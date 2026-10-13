# 方案3研究验证

先读 FINAL_REPORT.md；复现见 REPRODUCE.md。根目录为最终结果；development_before_pairing_and_F0_completion 保存实现完整性审计前的初步结果，不用于最终接纳。

结论：联合容量模型不接纳；真实四串组容量 UNVERIFIED；官方 CK1–CK7 没有新的SOH估计。论文公式和源码审计完成，作者真实容量基准因ZIP成员下载超时未完成，缺项明确登记。

代码及结果独立于正式提交模型。RESULTS_FROZEN.json 与 artifact_manifest.json 封存本次成果；后续重跑使用 reproduce.py 创建新的同级研究目录。
