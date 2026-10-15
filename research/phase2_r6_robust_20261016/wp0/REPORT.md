<a id="en"></a>

# WP0 — Setup and re-baselining

> **Language:** English · [中文](#zh)

**Result: all reproductions pass.** The reference for every later WP is **SUB = V2 + √t gap branch**, the model submitted at `21a7a55`. All numbers are exposed-exploratory proxy numbers. Code: [run_wp0.py](run_wp0.py); outputs: [outputs/reproduce.json](outputs/reproduce.json).

| Model | MAE Δ0 / 0.4 / 0.8 (pp) | MAX Δ0 / 0.4 / 0.8 | Pseudo | Cold start | Check |
|---|---|---|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 | 0.240 | 0.252 | exact (0.215726) |
| **SUB (V2+√t)** | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.148 | 0.174 | pass |
| 5C R3_TD_w0.75 | 0.188 / 0.131 / 0.174 | 0.440 / 0.311 / 0.344 | 0.123 | 0.134 | pass |
| 5C R2_B | 0.202 / 0.258 / 0.314 | 0.638 / 0.638 / 0.953 | 0.119 | 0.144 | pass |

- **Submitted class.** `my_model/model_template.py` from the archived `21a7a55` package, run causally (fit on full data, estimate on each cut), matches SUB within 0.00037 pp at Δ = 0.4.
- **Official baseline ExampleModel** (archived `model_example.py`, run causally): SOH 98.42, 98.88, 97.61, 97.63, 97.21, 95.72, 95.15 % for CK1–CK7 ([CSV](outputs/wp0_example_and_submitted_class.csv)).
  - Against the proxies its MAE is 4.69 / 4.30 / 3.90 pp and its MAX 5.67 / 5.28 / 4.88 pp at Δ = 0 / 0.4 / 0.8 ([JSON](outputs/example_proxy_errors.json)). It is strongly optimistic.
  - On the official normalised scale (baseline = 1.0), SUB therefore scores about 0.03–0.05. Differences of 0.01 pp between our models are tiny on that scale; the worst-case component matters more.

Sources copied read-only are listed in [../sources/SOURCES.md](../sources/SOURCES.md).

---

<a id="zh"></a>

# WP0——准备与重新确定基线

> **语言：** [English](#en) · 中文

**结果：所有复现都通过。** 之后每个工作包的参照都是 **SUB = V2 + √t 缺口分支**，也就是在 `21a7a55` 提交的模型。所有数字都是已曝光的代理数字。代码：[run_wp0.py](run_wp0.py)；输出：[outputs/reproduce.json](outputs/reproduce.json)。

| 模型 | MAE Δ0 / 0.4 / 0.8（pp） | MAX Δ0 / 0.4 / 0.8 | 伪场景 | 冷启动 | 检查 |
|---|---|---|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 | 0.240 | 0.252 | 精确（0.215726） |
| **SUB（V2+√t）** | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.148 | 0.174 | 通过 |
| 5C R3_TD_w0.75 | 0.188 / 0.131 / 0.174 | 0.440 / 0.311 / 0.344 | 0.123 | 0.134 | 通过 |
| 5C R2_B | 0.202 / 0.258 / 0.314 | 0.638 / 0.638 / 0.953 | 0.119 | 0.144 | 通过 |

- **提交的类。** 归档的 `21a7a55` 提交包中的 `my_model/model_template.py`，按因果方式运行（用全部数据拟合、在每个截断上估计），在 Δ = 0.4 时与 SUB 相差不超过 0.00037 pp。
- **官方基线 ExampleModel**（归档的 `model_example.py`，按因果方式运行）：CK1–CK7 的 SOH 为 98.42、98.88、97.61、97.63、97.21、95.72、95.15 %（[CSV](outputs/wp0_example_and_submitted_class.csv)）。
  - 对照代理，它在 Δ = 0 / 0.4 / 0.8 时的 MAE 为 4.69 / 4.30 / 3.90 pp，MAX 为 5.67 / 5.28 / 4.88 pp（[JSON](outputs/example_proxy_errors.json)），明显偏乐观。
  - 因此按官方归一化尺度（基线 = 1.0），SUB 的分数约为 0.03–0.05。在这个尺度上，我们各模型之间 0.01 pp 的差别微乎其微；更重要的是最差误差那一项。

只读复制的来源见 [../sources/SOURCES.md](../sources/SOURCES.md)。
