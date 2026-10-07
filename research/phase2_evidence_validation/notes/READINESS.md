# V0 数据、环境与最小链路实测

执行日期：2026-09-29。状态：**V0 通过，附明确数据限制**。实际运行记录是 `runs/V0_preflight_20260929/result.json`、脚本 `scripts/v0_preflight.py` 和 `data_manifests/input_manifest.csv`；V0 原始 P1 事件的 CSV 哈希在首轮脚本完成后补入顶层清单，原始 run 结果保持不可改。V0 数据资格的独立复核见 `notes/V0_DATA_QUALIFICATION.md` 和 `outputs/data_eligibility.csv`。

本机 Python 3.12.14 验证环境有 NumPy/SciPy/Pandas，已实际完成已知答案有界优化和根求解。系统 Python 3.13.0 的 PyTorch 2.12.1 CPU 自动微分实测通过；MPS 报 available，但本轮未采用 MPS 模型，也未把可用标志当数值验证。验证 venv 缺 sklearn/torch，系统 Python 缺 sklearn；低维 NumPy/SciPy 路线可先实施，不需为缺包修改旧环境。机器 8 逻辑核，V0 完成时空闲磁盘约 105.5 GiB；没有发现本任务或相关旧任务的活跃训练进程。

原始数据端到端检查：20 个官方/D1 主要输入完整 SHA256 已在脚本中重算，加 1 个实际读到的 P1 原始事件文件顶层清单共 21 行。冻结 D1 面板 SHA256 与历史一致：180 目标、6 枚物理单芯、每芯 30 目标；一条原始 P1 充电事件从 CSV 重建到 2021-04-26 17:00:22 首次 3.50 V 越线，与 v1.5 manifest 对齐。这只是严格裁剪代理的来源核验，并非真实浅循环或容量性能结果。单折简单模型在新进程复载后预测差为 0；只做执行烟雾测试。

CK0 70,876 行末值 100.412 Ah；原始电流/时间梯形积分 100.41118 Ah，对已释放容量 100.41 Ah；1 个重复时间步，无负向时间步。组压减四芯和中位 −3 mV、绝对差 95 分位约 5 mV。参考 CSV 没有温度字段，不能凭其确定 `T_ref`。官方框架 `load_dataset(..., until=CK1)` 实跑得到 165,918 行，末时戳 2025-02-07 23:59:52，且只含 CK0 一条已释放容量；检查点截止使用 `<=` 代码行为。

Word 烟雾测试通过：中文、公式文字和表格生成一页 `.docx`。文档技能 `render_docx.py --emit_pdf --verbose` 实际失败，报本机未找到 LibreOffice `soffice`；随后本机 Microsoft Word 将同一 DOCX 导出 PDF，Poppler 渲染成 `rendered/v0_smoke/page-1.png`，已人工看清无缺字/裁切。最终报告仍需逐页单独核查；烟雾测试页使用 Word 默认蓝色 Title 线，最终报告生成器要移除标题边线并按技能要求检查。

本地相关目录新数据复查没有发现 D2-compatible 的独立四串组容量真值。官方 CK1–CK7 隐藏，Che 是单芯异协议充入量标签，TU 没有参考容量，He 16S 包的 SOH 来源和许可待核。R02/R05 原型、D1 代理和 D3 前缀检查可执行；官方容量 MAE、同协议独立确认和新组最差/末期容量误差目前不可评价。

后续资源纪律：所有新配置、模型、日志和缓存放本任务目录；旧脚本按只读输入审查后复制并改输出路径。长训练先用短跑实测耗时/RAM，运行使用唯一 run_id 和完成标记。若需要 sklearn/torch 同一解释器，另建 TASK/.venv 并锁依赖；低维路线先用当前验证环境。
