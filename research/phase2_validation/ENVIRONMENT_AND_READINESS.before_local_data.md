# 双方案夜间实验：环境与启动条件

检查日期：2026-09-28，Europe/Berlin。当前结论：**具备本地双方案设计、实现、工程验证、官方无标签诊断和合成压力测试条件；尚不具备官方隐藏精度验证条件，独立外部实测容量数据也尚未准备成功。** 后两项不能通过增加 token 消除。

本次只做启动准备和预检，尚未开始 A/B 正式实验、未创建新 Goal、未开启长时间防休眠进程。

## 已实际验证的条件

- 当前会话有 `create_goal/get_goal/update_goal` 工具。`/goal` 是持续目标命令，不是本地安装的同名 skill；在本地技能目录未找到 goal/SKILL.md，也不需要为本任务安装它。官方说明支持将可核验完成条件交给 Goal 持续执行。[官方 Goals 指南](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)
- 工作区 `research/phase2_validation/` 可写，写入、读取、创建隔离环境和子进程均实测成功。额外桌面目录可能需要审批，夜间交付全部放当前项目内。
- 本机 macOS 15.7.4、ARM64，8 个逻辑 CPU；预检时空闲磁盘约 158 GiB。沙箱拒绝读取物理内存总量，未把未知内存容量写成已确认。两条低阶路线无需 GPU，正式运行先测样本耗时／内存并控制并发。
- 原系统 Python 是 3.13.0，不符合官方 3.11／3.12 要求。已创建独立 `research/phase2_validation/.venv`，使用 Python 3.12.14，不继承系统 site-packages。
- 已装：numpy 2.3.5、pandas 2.2.3、scipy 1.18.1、matplotlib 3.11.2、pytest 9.1.1、h5py 3.16.0、python-docx 1.2.0、pypdf 6.19.0、Pillow 12.3.0。完整含间接依赖版本见 `requirements.lock.txt`。`pip check` 通过。
- 24 个 wheel 已保存到 `wheelhouse/`，可以不联网离线安装。此处含本机 macOS ARM64 二进制包，不能用于 Linux 评测机；正式模型应尽量只声明必要运行依赖。
- 实际完成最小二乘优化、Cholesky、单调插值、MAT／HDF5 写入读回和 matplotlib PNG 绘制。字体缓存路径已改为工作区可写目录，避免写用户目录失败；`run_python.sh` 配置绘图、缓存和线程环境。
- 文档创建依赖可用；documents 技能及其打包 LibreOffice renderer 已在前一轮中文 Word 中使用成功。本轮不声称已经检查尚未生成的 A/B 报告，夜间仍必须逐页渲染验收。

## 数据与官方流程预检

`preflight/data_manifest.csv` 保存每段大小、哈希、行数、时间边界、重复／缺口、计数器与组压一致性统计；`preflight/preflight_report.json` 保存环境、命令、退出码和计时。

- 13 个 operation gzip 文件均成功完整解析，共 1,572,894 行。检查的必需字段无缺失值；这不等于所有数值都准确。
- 共 181 个重复时间戳、3 个片段内部超过 60 秒的缺口，segment 03 未提供。正式事件质量规则仍待实现与验证。
- CK0 参考放电 70,876 行，`discharged_Ah` 最大 100.412，与标签 100.41 的精度／舍入差异应保留说明。
- 只公开 CK0 容量 100.41 Ah、SOH 98.44%；有 CK0–CK7 日期，但 CK1–CK7 容量真值没有给出。
- 在 `preflight/baseline_template/` 的未经修改的官方副本运行样例验证成功，共 5 个样例评估点。日志中的 ExampleModel 警告是预期的：本次刻意验证原始官方基线，不代表新模型已通过。
- 完整数据的官方训练约 1.35 秒，全部 8 点测试约 9.60 秒（本机一次预检；不代表 A/B 或评分机速度）。结果在 `preflight/baseline_full/output.csv`，CK0=98.440、CK7=95.148，其余点见文件。这些数是预测，不是标签。
- `run_model.py`、`framework/`、`validate_submission.py`、原始 my_model、requirements、data、sample_data 的前后 SHA256 一致。基线训练状态与输出均在研究目录，根目录 ActiveModel 未切换。

## 外部验证数据与网络

当前没有成功落盘、解析并审核过的独立 LFP 多老化阶段容量验证数据。桌面相关 Challenge 1 项目中找到示例 CSV、预训练参数和模型文件；未把 sample_data 当作真实外部精度标签，也未盲目反序列化旧模型。

普通沙箱 shell 访问 PyPI 出现 DNS 解析失败。为当前环境准备依赖时，使用受控 `require_escalated` 下载公开 PyPI wheels，审批与下载成功；其后在沙箱内离线安装成功。未关闭沙箱、未修改全局配置。后续外部源仍可能需要受控网络权限，不能因为 PyPI 成功就保证所有站点可访问。

已核实候选 HUST 原始数据元信息：77 个 1.1 Ah LFP／石墨单体、30°C、相同充电／不同多阶段放电，CC BY 4.0，DOI 10.17632/nsc7hnsg4s.2。[原始数据页](https://data.mendeley.com/datasets/nsc7hnsg4s/2) 这只是候选源，容量标签的定义、时序字段和适配仍未实际验证。网页工具能读取元数据，shell 抓取返回标题为 FAQ 的页面，尝试文件列表 URL 返回 404；没有把 HTML 当成数据或记录成下载成功。

[CALCE 数据说明](https://calce.umd.edu/data) 提供 LFP A123 的 OCV／动态研究入口；是否适合容量老化验证需要另行确认。其 CS2／CX2 系列是 LCO，不能冒充 LFP。[Battery Archive](https://www.batteryarchive.org/) 当前要求联系申请完整 CSV，未经用户另行授权不发邮件。公开外部数据可用性探索已写入夜间任务，失败时仍继续 E0/E1/E2，并准确限定比较结论。

## 电源与持久运行

`caffeinate` 存在。`pmset` 报告 AC Power 配置 `sleep 1`；电池状态同时显示 discharging，供电状态不能仅凭 AC Power 字样保证。启动前应接好电源、保持开盖和 Codex 应用／网络可用。

可在终端执行：
```bash
caffeinate -i -s -t 28800
```
它只在有限时长内建立防空闲休眠断言；不会启动 Goal、不能保证合盖／断电／应用退出时继续。夜间 prompt 也允许代理为任务创建并记录该进程。不要同时重复启动多个不必要的防休眠进程。

启动后依靠 `notes/PROGRESS.md`、配置、哈希和分实验结果断点恢复。没有 prompt 能承诺网络、系统和会话绝不故障；本准备已把必要本地依赖离线化，并规定普通失败的修复／降级路径。

## 启动与复检

在当前项目会话发送：
```text
/goal 读取并完整执行 research/phase2_validation/START_PROMPT.md。这是正式夜间任务：两条方案都要完成设计、实现、验证和比较，按文件验收并交付，不只写计划。普通疑问记录假设后继续，不等待逐章确认，不设置 token 预算。
```

若界面未识别 `/goal`，发送同一句去掉 `/goal` 并补充“请调用 create_goal 创建持续目标”；工具是否可用由当时会话核实。本次会话已确认 Goal 工具存在，尚未为夜间任务创建活动目标。

随时复检：
```bash
bash research/phase2_validation/run_preflight.sh
```
核心本地实验没有网络依赖。正式 A/B 文件的路径、实验协议、数学要求、消融／压力矩阵和完成条件见 `START_PROMPT.md`；本说明不是模型验证结论。
