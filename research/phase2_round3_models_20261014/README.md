<a id="en"></a>

# phase2_round3_models_20261014

> **Language:** English · [中文](#zh)

Round 3 tested six alternatives to the V2 capacity model (stages B → D → A → C → E → F), unattended. The conclusions are in [FINAL_REPORT.md](FINAL_REPORT.md) and the brief is in [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md). Progress and decisions are in `notes/STATUS.md` and `notes/DECISIONS.md`.

| Path | Contents |
|---|---|
| `src/harness.py` | shared harness: causal cuts, proxies, pseudo-gap/pseudo-cut scenarios, metrics, gates, candidate checks |
| `src/gapx.py` | stage D gap-extrapolation rules D0–D3 |
| `src/registration.py` | stage A piecewise-linear registration of anchor charges, β_reg |
| `src/statespace.py` | stage C linear-Gaussian MAP state-space model |
| `stage0_reproduce.py`, `stage0/` | harness reproduces M4 and V2 |
| `stage_X/` | per stage: `protocol.json` + `protocol.sha256`, run scripts, `outputs/`, bilingual `REPORT.md` |
| `cache/` | cached cuts and event tables (git-ignored) |

**Dependencies.** The study reuses `../phase2_anchor_step_20261013/src/events.py` and `../phase2_v2_phase_matched_20261013/src/v2.py` unchanged. Data and framework come from `TechArena_Challenge2_Team_Package/`.

**Environment.** Python 3.13 with numpy, pandas, scipy and matplotlib. The reproduction commands are in the final report.

---

<a id="zh"></a>

# phase2_round3_models_20261014

> **语言：** [English](#en) · 中文

第三轮在无人值守的情况下，测试了 V2 容量模型的六个备选方案（阶段 B → D → A → C → E → F）。结论见 [FINAL_REPORT.md](FINAL_REPORT.md)，任务书见 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md)，进度与决策记录在 `notes/STATUS.md` 和 `notes/DECISIONS.md`。

| 路径 | 内容 |
|---|---|
| `src/harness.py` | 共享评估框架：因果截断、代理、伪缺口 / 伪截断情景、指标、接纳门、候选类检查 |
| `src/gapx.py` | 阶段 D 的缺段外推规则 D0–D3 |
| `src/registration.py` | 阶段 A：锚点充电的分段线性配准，以及 β_reg |
| `src/statespace.py` | 阶段 C：线性高斯 MAP 状态空间模型 |
| `stage0_reproduce.py`、`stage0/` | 评估框架复现 M4 与 V2 |
| `stage_X/` | 每个阶段：`protocol.json` + `protocol.sha256`、运行脚本、`outputs/`、中英双语 `REPORT.md` |
| `cache/` | 缓存的截断数据与事件表（git 忽略） |

**依赖。** 原样复用 `../phase2_anchor_step_20261013/src/events.py` 和 `../phase2_v2_phase_matched_20261013/src/v2.py`，数据与框架来自 `TechArena_Challenge2_Team_Package/`。

**环境。** Python 3.13，含 numpy、pandas、scipy、matplotlib。复现命令见最终报告。
