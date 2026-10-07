# B0 环境和数据资格实测

2026-09-30（Europe/Berlin）使用 `research/phase2_validation/.venv/bin/python`：Python 3.12.14、NumPy 2.3.5、Pandas 2.2.3、SciPy 1.18.1、8 逻辑核，约 103.28 GiB 可用磁盘。13 个官方 operation 分段与 CK0/评估 CSV、P1 D1 代表文件共 21 行重新 SHA256，全部与上一轮 manifest 一致；清单见 `data_manifests/input_manifest.csv` 和 `runs/B0_preflight_20260930_v1/result.json`。TU 代表 8S 文件与 Che 包另重新 SHA256，见 `external_inventory.csv`，均不符合官方四串容量标签协议。此前 D2 扫描为 absent；截至本次 B0 未收到用户所称新包的明确路径，不能预判其资格。

在 TASK 隔离输出目录原样运行根目录 `run_model.py` 的 ExampleModel 和旧 CK0 常数研究候选；各自 train 约 1.4 s、all-CK test 约 9.4 s，均输出八点；模型 pickle 的字段已检查。ExampleModel `q_ref=21.3972638889 Ah`、`soh0=98.44%`，CK1–CK7 输出 `[98.416,98.878,97.612,97.634,97.207,95.718,95.148]%`；CK0 常数候选每点为 98.441%。这些是输出而非 CK1–CK7 容量误差。run 及代码/输出/输入哈希在 `runs/B0_example_20260930_v1/`、`runs/B0_ck0_constant_20260930_v1/`。

本机有 Microsoft Word 和 Poppler `pdftoppm`，无 `soffice`；上一轮的 Word→PDF→PNG 链路已验证，本轮 B8 仍须真实生成并逐页复查。环境链满足本轮 CPU/pandas 简单候选；未假设 GPU。根目录活动 `my_model/__init__.py` 仍指向 ExampleModel，未修改。配置在新 B1 结果前冻结于 `configs/frozen_manifest.json`。
