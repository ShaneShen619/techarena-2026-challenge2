# phase2_anchor_step_20261013

检查后完整充电锚点 + 石墨台阶位移的容量估计验证。结论见 [FINAL_REPORT.md](FINAL_REPORT.md)，任务书见 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md)。

## 分支布局

本分支 = `main`（`TechArena_Challenge2_Team_Package/` 提交模板、框架与官方数据）+ 本研究目录。脚本从 `TechArena_Challenge2_Team_Package/` 读取 `framework/`、`my_model/model_example.py` 和 `data/`。

报告与执行 Prompt 中引用的其他研究目录（三份失败报告、10 月 6 日端点审计、第一性原理诊断、文献卡等）在分支 `research-archive-20261010` 上。B 基线 CSV 已复制到 `inputs/history_B_prior_baseline.csv`。`input_manifest.json` 记录的是原始运行时的路径与哈希。

## 环境

| 用途 | Python | 依赖 |
|---|---|---|
| 研究流程（阶段 A–G） | 3.13（已验证） | [requirements.txt](requirements.txt)：numpy、pandas、scipy、matplotlib |
| 候选模型 `candidate_model/` | 3.11 与 3.13（已验证；官方环境为 3.11/3.12） | 只需 numpy、pandas，与 `TechArena_Challenge2_Team_Package/requirements.txt` 一致 |

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r research/phase2_anchor_step_20261013/requirements.txt
```

运行记录见 [environment.json](environment.json)。

## 复现

在仓库根目录下执行：

```bash
cd research/phase2_anchor_step_20261013
python3 stage_a_events.py          # A：事件提取与审计            -> outputs/A*
python3 stage_bcd_causal_eval.py   # B–D：因果预测与代理评估       -> outputs/C_*, D_*
python3 stage_e_robustness.py      # E：稳健性、ε 漂移检查、合成反证 -> outputs/B_*, E*
python3 stage_f_candidate.py       # F：候选模型、因果检查、冒烟     -> outputs/F_*
python3 stage_g_figures.py         # G：图                        -> figures/overview.png
```

按顺序运行：`stage_f_candidate.py` 会读取 `stage_bcd_causal_eval.py` 的输出做一致性对比。阶段 B 的 ε 漂移检查依赖完整事件表，所以放在 `stage_e_robustness.py` 里一起运行，输出仍用 `B_` 前缀。输出文件前缀与报告中的阶段编号一一对应。

## 文件

| 路径 | 内容 |
|---|---|
| `EXECUTION_PROMPT.md` | 执行任务书（原文保留，开头有布局更新说明） |
| `FINAL_REPORT.md` | 验证报告 |
| `protocol.json` / `protocol.sha256` | 评估前冻结的协议及其哈希 |
| `environment.json`、`input_manifest.json` | 运行环境记录与输入 SHA256 |
| `requirements.txt` | 研究流程依赖 |
| `inputs/` | 从归档分支复制的对照输入（B 基线） |
| `src/events.py` | 事件提取：积分电量、完整充电、台阶定位、CK0 参考 |
| `src/predictors.py` | 预登记预测器 M2–M5 |
| `candidate_model/anchor_step_model.py` | 可接入框架的候选类 `AnchorStepModel`（未接入正式模型） |
| `stage_*.py` | 各阶段运行脚本 |
| `outputs/`、`figures/` | 全部结果与图 |
