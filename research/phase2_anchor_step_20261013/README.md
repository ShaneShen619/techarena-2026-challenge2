# phase2_anchor_step_20261013

检查后完整充电锚点 + 石墨台阶位移的容量估计验证。结论见 [FINAL_REPORT.md](FINAL_REPORT.md)，任务书见 [执行Prompt.md](执行Prompt.md)。

## 分支布局

本分支 = `main`（`TechArena_Challenge2_Team_Package/` 提交模板、框架与官方数据）+ 本研究目录。脚本从 `TechArena_Challenge2_Team_Package/` 读取 `framework/`、`my_model/model_example.py` 和 `data/`。

报告与执行 Prompt 中引用的其他研究目录（三份失败报告、10 月 6 日端点审计、第一性原理诊断、文献卡等）在分支 `research-archive-20261010` 上。B 基线 CSV 已复制到 `inputs/history_B_prior_baseline.csv`。`input_manifest.json` 记录的是原始运行时的路径与哈希。

## 复现

在仓库根目录下执行（需要 numpy、pandas、scipy、matplotlib；本地环境为 Python 3.13）：

```bash
cd research/phase2_anchor_step_20261013
python3 run_stage_a.py        # A：事件提取与审计      -> outputs/A_*
python3 run_causal_eval.py    # B–D：因果预测与代理评估 -> outputs/C_*, D_*
python3 run_stage_e.py        # E：稳健性与合成反证      -> outputs/B_*, E_*
python3 run_candidate.py      # F：候选模型、因果检查、冒烟 -> outputs/F_*
python3 make_figures.py       # figures/overview.png
```

`run_candidate.py` 读取 `run_causal_eval.py` 的输出做一致性对比，所以要按上面的顺序运行。

## 文件

- `protocol.json` / `protocol.sha256`：评估前冻结的协议。
- `environment.json`、`input_manifest.json`：环境与输入 SHA256。
- `src/events.py`：事件提取（积分电量、完整充电、台阶定位、CK0 参考）。
- `src/predictors.py`：M2–M5。
- `candidate_model/anchor_step_model.py`：可接入框架的候选类（未接入正式模型）。
- `outputs/`：全部 CSV/JSON。
