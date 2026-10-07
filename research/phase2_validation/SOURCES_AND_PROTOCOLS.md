# 数据出处与标签口径

本文件保存离线研究所需来源索引。原文件只读；新解析结果与原始数据分离。

1. **Challenge 1 官方原始数据**：`dataset original/TechArena_2026_Topic_1_Challenge1.pdf` 与 6 个 `102Ah_*` 目录。协议：30 秒，CC-CV 至 3.649 V、CC 放电至 2.5 V，名义 0.5C／1C，温度 25–55°C；以实际电流列为准。旧标签定义参考 `/Users/shane/Desktop/项目/Current State_Challenge1/framework/data.py`。第二阶段复用授权见 `submission_instructions_2026.md` 第 184 行起及题目第 2.1 节。非开放许可原始资料，限当前比赛工作区使用，不重新分发。
2. **Che 等，Dataset 3**：https://data.mendeley.com/datasets/n3b54nsw8m/9 ，DOI 10.17632/n3b54nsw8m.9，CC BY 4.0。对应论文 DOI 10.1016/j.xcrp.2023.101743。作者元数据说明提供部分充电 Q 曲线和容量，其工作使用充电容量归一化 SOH。D3 文件中缺少电压网格与原始时间／电流，进一步的物理解释必须查原文元信息，不靠猜测。
3. **Schaeffer 等，TU Darmstadt 现场数据**：https://zenodo.org/records/13715694 ，DOI 10.5281/zenodo.13715694，CC BY-NC 4.0；README：https://zenodo.org/records/13715694/files/README.md?download=1 。论文 DOI 10.1016/j.xcrp.2024.102258；作者代码 https://github.com/JoachimSchaeffer/BattGP 。28 套 8 串约 160 Ah LFP 系统，主动均衡、退回厂家样本，存在选择偏差。数据许可与 BattGP 代码许可分别对待，不安装其完整研究栈也可解析原始 CSV。
4. **Challenge 2 目标包**：`data/` 与 `CHALLENGE2_DESCRIPTION.pdf`。只公开 CK0=100.41 Ah，目标为 5.1 A 放电至组压 11.2 V 的四串容量／102 Ah；CK1–CK7 保留为官方评分，不是缺失的可下载标签。

已在 2026-09-28 重新读取上述公开元数据与本地原始文件。下载日期由用户本次提供事实与文件到达记录说明；文件 mtime 可能保留源文件日期，不能当下载日期。远端版本与本地文件的一一字节匹配尚未核实；本地 SHA256 及大小见 `preflight/downloaded_data/audit_report.json`。
