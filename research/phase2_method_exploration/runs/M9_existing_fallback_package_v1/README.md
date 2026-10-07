# 温度与多窗口候选包

`my_model` 为基于 P1 六个单芯开发数据拟合的多窗口模型与官方四串接口适配器。`framework`、`run_model.py`、`validate_submission.py` 和 `requirements.txt` 保留官方入口。训练与测试必须在不同 Python 进程执行；模型通过 pickle 序列化恢复。

本包不含原始训练数据、官方完整运行数据或隐藏容量标签。六芯 180 点的 1.039 pp 宏 MAE 是第一阶段高倍率单芯放电容量代理上的开发验证，不能解释为第二阶段四串 C/20 组容量误差。官方 CK1–CK7 无公开真值；当前这些检查点均走未经真实组容量校准的降级分支，其输出仅供无标签诊断。

在含官方 `data` 目录的隔离目录解压后，按官方 `run_model.py` 与 `validate_submission.py` 使用；不要将无标签诊断当作已验证比赛成绩。
