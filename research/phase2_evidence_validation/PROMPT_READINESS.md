# 提示词准备时的实测记录

日期：2026-09-29。本记录用于下一轮启动准备；本轮验证任务和 Goal 尚未启动。执行 START_PROMPT 时必须重新做 V0 端到端检查。

已读取新文献路线卡/实验路线图、旧验收、D1 原始构建入口及官方框架。此前某些文字“真实浅充代理”容易误导；D1 v1.5 实为六枚 P1 深充记录的严格前缀裁剪代理，已在新 prompt 明确纠正。

实际本机检查：

- 剩余磁盘约 106.3 GiB。
- `research/phase2_validation/.venv/bin/python`：Python 3.12.14，NumPy 2.3.5、SciPy 1.18.1、Pandas 2.2.3、Matplotlib 3.11.2、h5py 3.16.0；sklearn、torch 未安装。SciPy 有界优化和根求解实际返回已知答案 2.0。
- 系统 `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`：Python 3.13.0、torch 2.12.1、NumPy 2.4.2、SciPy 1.18.0；torch CPU 自动微分实际通过。当前 MPS available=True，但未运行 MPS 候选运算或验证确定性。系统也缺 sklearn。不能把旧记录的 MPS 状态直接当当前事实。
- 文档环境 `research/phase2_literature_reassessment/tmp/docenv/bin/python` 有 python-docx 1.2.0，实际读取主报告成功（98 段）；本机 Microsoft Word.app 存在。上轮已完成 Word→PDF→PNG 全页核查，本次准备没有再生成新报告。
- 实际打开 CK0 gzip CSV，字段包括 timestamp、current_A、voltage_V、cell1_V–cell4_V、discharged_Ah；首行负电流 −5.096 A，与官方充电为正一致。CK0 不带温度字段，参考测试温度不能凭此自动推断。
- D1 v1.5 缓存 `research/phase2_method_exploration/runs/M9_D1_v15_inputs_v1/native_sequences.npz` 和 `runs/M9_D1_v15_target_map_v1/target_inputs.npz` 存在；准备时只确认文件存在，未把这当实际新一轮事件/单折测试通过。
- 官方 `framework/data.py` 使用 `<= until`；训练完整数据可见的约束已写入新 prompt。

环境判断：具备开始低维 R02/R05 实现与优化验证的计算基础，有既有 D1/D3 输入和文档交付通道。不能说所有环境/数据条件已齐全：sklearn 不在所测环境、MPS 候选未测、新独立四串同协议容量标签仍需执行时重新资格检查。prompt 要求在新任务目录隔离补依赖并先实测，禁止改历史环境；不必为线性/低维原型强制安装 sklearn。

关键源目录：`research/phase2_literature_reassessment/`；`research/phase2_next_round/`；`research/phase2_method_exploration/`；`research/phase2_temperature_improvement/`；`research/phase2_validation/`。旧 run_python.sh 会在历史目录写缓存，新任务要重建本地 wrapper 或指定 TASK 缓存后再复用解释器。
