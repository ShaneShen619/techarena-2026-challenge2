# 双方案夜间实验环境与启动条件

修订日期：2026-09-28，Europe/Berlin。**当前已具备离线启动条件：两条路线可用第一阶段真实数据做容量代理验证，Che 和 TU 按适用范围补充。** CK1–CK7 隐藏是官方盲测设计，不是运行阻塞，也不是应当下载的数据。

当前只完成准备、数据验收及 prompt 修订，尚未启动新 Goal 或 A/B 正式实验。旧版准备文件保存在 `*.before_local_data.md`，启动只读取新版 `START_PROMPT.md`。

## 本次实际核验

- 本地 Goal 工具可调用，目前没有活动 Goal。`/goal` 是持续目标功能，无需另装同名 skill。[官方指南](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)
- 独立 `.venv` 使用 Python 3.12.14，符合官方 3.11／3.12；系统 Python 3.13 不用于正式实验。
- numpy、pandas、scipy、matplotlib、pytest、h5py 及文档读取／生成依赖齐全。24 个 wheel 与完整 `requirements.lock.txt` 已保存；本次另建 `preflight/clean_venv`，离线安装成功、pip check 通过、官方 sample validator 通过。
- 优化、插值、Cholesky、MAT／HDF5 I/O、PNG 绘图已跑通；所有缓存放工作区可写路径。
- 官方第二阶段 13 段约 157 万行数据可读，原基线通过样例验证和完整八点预测。副本中 ExampleModel 警告是预期的基线状态，不是 A/B 验证结果。
- 第一阶段 65 个 CSV 全量读取；6 芯、8,601,857 行、19,292 个通过旧官方规则的容量标签。已构造 18 条跨六芯的充电输入／后续放电标签预检，按绝对时间配对并阻止同循环未来充电泄漏。
- Che 11 芯、23,853 循环，全部 47,706 个部分 Q／dQ 数组成功读取；没有原始 t/I/V 或显式电压网格。
- TU 28 文件共 18.54 GiB、132,777,059 行，已分块全扫描并记录 SHA256；完整时间、电流、组压、SOC 解析通过，其他字段做表头与样本检查。没有实测容量标签列。
- 三源首次验收约 110 秒，扫描进程峰值 RSS 约 1,015 MiB。此耗时不代表算法全量训练／推理时间。夜间复用路径／大小／mtime 一致的审计缓存，必要时 `--full` 重新读取并核验哈希。
- 使用打包 documents renderer 重新渲染已有中文综述，成功输出 7 页，检查中文页面显示正常。未来新报告仍须逐页视觉验收；本次没有生成或预先验收尚未写出的双路线报告。
- `caffeinate -i -s -t 3` 短测试退出码 0，`pmset -g assertions` 看到该测试 PID 的防休眠断言；测试已自行结束，未留下整晚防休眠进程。
- 原始第二阶段数据、模型和官方框架哈希保持不变；三份新增原始资料只读。

## 数据用途与不能跨越的边界

详细验收和风险见 `DATA_ACCEPTANCE.md`，来源／许可见 `SOURCES_AND_PROTOCOLS.md`。

第一阶段是本轮六折实测比较的必做主数据，但标签是 0.5C／1C 放电至 2.5 V，不是四串 C/20。必须屏蔽后续诊断放电，避免从其积分直接读出标签。已有同循环充电晚于放电、跨循环时间交叠、负相对时间和缺温度等情况，prompt 已要求逐项处理和回归测试。

Che 用于可解释的部分充电曲线／容量补充；坐标元信息未核实时只做受限形状分析，不能捏造电压网格。TU 用于现场异常、均衡影响和可观测性诊断；BMS SOC 不能当 SOH 真值。它们的这些限制不阻塞第一阶段的主验证。

## 夜间运行的资源与失败处理

机器为 macOS ARM64、8 个逻辑 CPU，下载后检查空闲磁盘约 136 GiB。物理内存总量查询受沙箱限制，未声称已获知；预检峰值是进程实际测量值。第一阶段逐芯处理，TU 分块、选列和限定连续窗口处理，不一次拼接全量现场数据。先测一芯／一点耗时，再扩展六折；默认至多两个轻计算任务并发，大数据读取一次一个。

核心数据和依赖均已本地化，主要实验无须联网；不要求安装 MATLAB、BattGP、PyTorch、CUDA 或使用 GPU。Che 细节的可选文献核查如果网络失败，保留其不确定性，继续已可执行主实验。不要再以外部数据未下载为由跳过第一阶段实测比较。

每次实验设置超时与日志、分阶段保存结果和配置。中断后读取 `notes/PROGRESS.md` 继续。token 充足不等于计算时间无限：按约一晚规划，先保证两方案实现、主验证、消融和报告；不能预先保证尚未实现算法的所有实验必在八小时内结束。

## 电源与应用

电源查询仍显示 AC Power 与电池 discharging 同时出现，因此睡前请确认充电器实际供电，保持开盖、Codex 应用运行。防休眠测试成功，但不等于能克服合盖、断电、系统更新或应用退出。

正式任务允许代理创建最长八小时的 `caffeinate -i -s -t 28800` 并记录 PID；完成后只结束自己创建的进程，不改系统电源配置。也可手动在终端运行同一命令，避免重复启动多个进程。

## 启动与复检

在当前项目会话发送：

```text
/goal 读取并完整执行 research/phase2_validation/START_PROMPT.md 的 v2 修订版。使用已落盘并验收的第一阶段原始数据、Che Dataset 3 和 TU Darmstadt 数据，完成两条路线的设计、实现、实测代理验证、压力测试、比较与 Word 交付。严格按文件的数据用途、因果边界和完成条件执行；普通疑问记录假设后继续，不等待逐章确认，不设置 token 预算。
```

若当前界面没有识别 `/goal`，去掉命令前缀并明确要求调用 `create_goal`；是否存在工具由启动时的会话核实，不伪称已开启。

完整复检：

```bash
bash research/phase2_validation/run_preflight.sh
```

实验统一入口：

```bash
bash research/phase2_validation/run_python.sh <脚本及参数>
```

`run_python.sh` 总会把 cwd 切回项目根目录。运行候选模型时必须传它的脚本路径；依赖 cwd 的程序需要显式在子进程中设候选 cwd，不能先 cd 再以为 wrapper 保持那个目录。

文档渲染使用已验证的打包工具（不要混用系统 LibreOffice）：

```bash
FONTCONFIG_FILE='/Users/shane/Desktop/Arena 阶段 2 官方材料/research/phase2_validation/fonts.conf' \
SAL_FONTPATH=/System/Library/Fonts/Supplemental \
/Users/shane/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
/Users/shane/.codex/plugins/cache/openai-primary-runtime/documents/26.905.11957/skills/documents/render_docx.py \
'<新报告.docx的路径>' --output_dir '<研究目录内的渲染目录>' --emit_pdf
```

本机 wheels 不是 Linux 发行包，本机通过不代表官方硬件已经通过。当前结论是“可以启动，有实测数据、有离线依赖、有断点与失败处理”，不承诺操作系统／会话绝不中断或两个方案必然达到某个精度。
