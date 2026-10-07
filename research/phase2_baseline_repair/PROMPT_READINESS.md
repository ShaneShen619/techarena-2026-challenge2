# 2026-09-30 启动前核查（不是实验结论）

已检查 `research/phase2_validation/.venv/bin/python`、官方 `my_model/model_example.py`、`framework/data.py`、`run_model.py`、`validate_submission.py`、官方运行数据与 `research/phase2_evidence_validation/` 已完成结果均在本地。原样示例在隔离输出目录曾运行成功，8 点预测 CSV 位于 `research/phase2_evidence_validation/runs/Advice_example_baseline_20260929/output.csv`；该运行只是下轮准备线索，应在新 TASK 带代码/输入哈希复现。

已观测异常：44.022503 Ah（segment 1 首事件）、58.412753 Ah（2025-02-12 segment 2）；常规约 21.4 Ah。原示例从全部最早 segment 取 `q_ref≈21.397264 Ah`，严格 CK1 前可用同段事件的中位数约 21.394615 Ah。区别需在启动后用独立前缀重建与未来行变异硬检查确认。V1 约 20 A 脉冲计数器错列与示例积分的区别要保持明确。

未发现新的同协议四串 D2 真容量标签包；P1、TU、Che 和官方包已在本地。用户说可直接用“这个数据”，但尚未给出新包路径/名称；启动后按 START_PROMPT B0 重搜，路径未明不妨碍官方基线 B1–B6。官方说明私有/专有外部数据不能用于提交，研究使用和比赛使用须分支记录。根目录活动 `my_model/` 仍是示例模型，本 prompt 不切换它。

文档工作可使用既有 Python/Word→PDF→Poppler 渲染路径；正式执行时需重测。已有 Goal 在本 prompt 编写时为 `null`，但真正启动时必须重新检查。此文件与 START_PROMPT 的存在不等于授权自动执行或提交。
