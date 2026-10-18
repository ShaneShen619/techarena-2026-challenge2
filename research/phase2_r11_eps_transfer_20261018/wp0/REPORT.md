<a id="en"></a>

# WP0 — Setup and reproduction check

> English · [中文](#zh)

**Conclusions first.**

- **The reproduction check passes.** The round 7 drift function, Q' = Q + d·max(0, 100.41 − Q), applied to the 21a7a55 package output reproduces round 7's table. The largest difference is 0.0006 pp, below the registered 0.001 pp tolerance; it comes from the 0.001-pp rounding of the package output. Details: [reproduction_check.json](reproduction_check.json).
- **Current SUB (6525edf, T_main + A3)** and the same drift function applied to it ([SUB_drift_reference.csv](SUB_drift_reference.csv)), in SOH %:

| Model | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| SUB + drift −0.031 | 95.908 | 94.385 | 93.450 | 92.647 | 91.816 | 91.209 | 90.527 |

- The protocol fact sheet is in [PACK_PROTOCOL.md](PACK_PROTOCOL.md). Sources and their SHA256 are in [../sources/SOURCES.md](../sources/SOURCES.md).
- Both packages were run through their own CLI (`run_model.py` train, then test `--eval-point all`) under system Python 3.13 with pandas 3.0. See decision D1 in `notes/DECISIONS.md`.

---

<a id="zh"></a>

# WP0 — 准备与复现检查

> [English](#en) · 中文

**结论先读。**

- **复现检查通过。** 把第 7 轮的漂移函数 Q' = Q + d·max(0, 100.41 − Q) 套到 21a7a55 包的输出上，能复现第 7 轮的表。最大差 0.0006 pp，低于登记的 0.001 pp 容差；这个差来自包输出保留到 0.001 pp 的舍入。
- **当前 SUB（6525edf，T_main + A3）**及其套用同一漂移函数的结果见上表（单位：SOH %）。
- 协议变量表见 [PACK_PROTOCOL.md](PACK_PROTOCOL.md)，来源及其 SHA256 见 [../sources/SOURCES.md](../sources/SOURCES.md)。
- 两个包都用各自的 CLI 运行（`run_model.py` 先 train，再 test `--eval-point all`），环境为系统 Python 3.13 和 pandas 3.0，见 `notes/DECISIONS.md` 中的 D1。
