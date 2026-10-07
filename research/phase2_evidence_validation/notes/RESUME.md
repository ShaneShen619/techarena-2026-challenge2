# 中断恢复

先读 `notes/STATUS.md`、`outputs/acceptance_results.json`、`notes/EXPERIMENT_INDEX.csv`，检查 run_id 完成标记与 `outputs/artifact_manifest.csv` SHA256；不重跑已完成实验，不覆盖冻结配置或逐点文件。本轮 V0–V8 研究流程已完成，容量高目标未达，官方 CK1–CK7 真值和同协议新四串组标签仍缺。下一轮触发条件是新 D2 原始包或官方参考满充/温度规格到位；先执行 `outputs/D2_MEASUREMENT_PROTOCOL.md` 的资格/计量试点，再冻结新组划分和容量盲测。若仅复核本轮，运行 `python scripts/finalize_acceptance.py` 和单元测试前确认工作目录及解释器，已完成 run 脚本默认拒绝覆盖。
