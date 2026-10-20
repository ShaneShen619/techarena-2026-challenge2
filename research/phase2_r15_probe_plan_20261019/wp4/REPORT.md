<a id="en"></a>

# WP4 — Leaderboard readings

> **Language:** English · [中文](#zh)

One dated section per run, newest last. Code: `src/wp4_run.py` (applies the registered `src/grid15.py` rules); each run writes `wp4/run_<date>.json`.

## 2026-10-20 — waiting for leaderboard

- **Result: waiting for leaderboard.** `inputs/leaderboard_log.csv` has a header and **no data rows**, so there is nothing new since the last run (this is the first run).
- **The log the session goal refers to was not found.** The goal said that new results had been recorded in `inputs/leaderboard_log.csv`. That file did not exist anywhere under the Desktop when the round started (D6); WP0 created it as an empty template, and it was still header-only at this run. No other leaderboard log was found under Desktop, Downloads or Documents.
- **Action:** keep SUB (`Current State_Challenge2.zip`, SHA256 `a4ed59a3…200f`) as the active and last submission. Do not upload the probe yet ([../wp3/HANDOVER.md](../wp3/HANDOVER.md), step 1 needs SUB's own board value and a known deadline).
- **Next:** add one row per board evaluation to `research/phase2_r15_probe_plan_20261019/inputs/leaderboard_log.csv` in this worktree (format in the hand-over, section 3), then run WP4 again.
- **Confirmed by the user (D27):** asked where the results were, the user answered "No results yet". Nothing has been evaluated, so this end state is correct.
- The observation path of `src/wp4_run.py` was dry-tested in memory, not written to the study: hash mapping, surviving set and the reading rule on a synthetic SUB/P_A3fix pair.

---

<a id="zh"></a>

# WP4 — 排行榜读数

> [English](#en) · 中文

每次运行一个带日期的小节，最新的在最后。代码：`src/wp4_run.py`（应用登记的 `src/grid15.py` 规则）；每次运行写出 `wp4/run_<日期>.json`。

## 2026-10-20 — 等待排行榜

- **结果：等待排行榜。** `inputs/leaderboard_log.csv` 只有表头，**没有数据行**，所以自上次运行以来没有新内容（这是第一次运行）。
- **没有找到本会话目标所说的记录。** 目标说已在 `inputs/leaderboard_log.csv` 记录了新的排行榜结果。但本轮开始时，桌面下任何位置都没有这个文件（D6）；它由 WP0 作为空模板创建，到这次运行时仍然只有表头。在桌面、下载和文稿目录下也没有找到其他排行榜记录。
- **行动：** 保持 SUB（`Current State_Challenge2.zip`，SHA256 `a4ed59a3…200f`）为当前有效的提交，也作为最后一次提交。暂不上传探针（[../wp3/HANDOVER.md](../wp3/HANDOVER.md) 第 1 步需要 SUB 自己的榜单值和已知的截止时间）。
- **下一步：** 每次榜单评估后，在本工作树的 `research/phase2_r15_probe_plan_20261019/inputs/leaderboard_log.csv` 里加一行（格式见交接说明第 3 节），然后再运行 WP4。
- **用户已确认（D27）：** 被问及结果在哪里时，用户回答"还没有结果"。目前没有任何评估，所以这个结束状态是正确的。
- `src/wp4_run.py` 的观测处理路径已在内存中做过试运行，没有写入研究目录：在一对合成的 SUB/P_A3fix 观测上检验了哈希映射、存活集和解读规则。
