<a id="en"></a>

# Round 15 — Leaderboard probe plan

> **Language:** English · [中文](#zh)

**Result:** at most one probe, **P_A3fix** (round 12's anchor-3 correction, one constant). Its zip is built and validated but not uploaded. Use it only once SUB's board value is known and the deadline leaves room for one evaluation plus a re-upload of SUB. Until then, keep SUB. Details: [FINAL_REPORT.md](FINAL_REPORT.md); user steps: [wp3/HANDOVER.md](wp3/HANDOVER.md).

## Layout

| Path | Content |
|---|---|
| `EXECUTION_PROMPT.md` | the round's prompt (copy of the original) |
| `notes/` | `STATUS.md` (where the round stands), `DECISIONS.md` (every open decision, D1–) |
| `sources/` | read-only copies from rounds 3, 4, 6, 11–14 and the packaging script, with SHA256 (`SOURCES.md`) |
| `inputs/` | filled by the user: `leaderboard_log.csv`, `deadline.txt`, `pptx_path.txt` |
| `wp0/` | rules audit, existing-zip inventory, candidates |
| `wp1/` | registered protocol and its hashes, machinery tests |
| `wp2/` | probe vectors, Δs tables, ranking, probe plan, organiser question (draft) |
| `wp3/` | package hashes, build log, hand-over |
| `wp4/` | leaderboard readings (one dated section per run) |
| `src/` | code: `grid15.py`, `variants.py` (registered), `test_wp1.py`, drivers `wp0_*`, `wp2_run.py`, `wp3_*`, `package_submission.py` |
| `cache/` | git-ignored: package copies, CLI outputs, the probe zip (`cache/packages/P_A3fix/`) |

## Re-running

From this folder, with `python3 -B`:

1. `src/wp0_sources.py` (after `git fetch origin`), then `src/wp0_inventory.py`;
2. `src/test_wp1.py`;
3. `src/wp2_run.py` (checks the registered hashes first);
4. `src/wp3_stage.py`, then `src/package_submission.py "Current State" --members "Mona Zhu, Zhikuan Shen" --pptx <deck> --out cache/packages/P_A3fix`, then `src/wp3_packages.py`.

Nothing in this round modifies `TechArena_Challenge2_Team_Package/`, and nothing is uploaded.

---

<a id="zh"></a>

# 第 15 轮——排行榜探针计划

> [English](#en) · 中文

**结果：** 最多一个探针 **P_A3fix**（第 12 轮的锚点 3 修正，一个常数）。它的 zip 已构建并通过验证，但没有上传。只有在 SUB 的榜单值已知、且截止时间足够完成一次评估再重新上传 SUB 时才用它；在此之前保留 SUB。详情见 [FINAL_REPORT.md](FINAL_REPORT.md)；用户操作步骤见 [wp3/HANDOVER.md](wp3/HANDOVER.md)。

## 目录结构

| 路径 | 内容 |
|---|---|
| `EXECUTION_PROMPT.md` | 本轮 prompt（原文件的副本） |
| `notes/` | `STATUS.md`（本轮进度）、`DECISIONS.md`（所有未决问题的决定，D1 起） |
| `sources/` | 来自第 3、4、6、11–14 轮和打包脚本的只读副本，附 SHA256（`SOURCES.md`） |
| `inputs/` | 由用户填写：`leaderboard_log.csv`、`deadline.txt`、`pptx_path.txt` |
| `wp0/` | 规则审查、现有 zip 清点、候选 |
| `wp1/` | 登记的协议及哈希、方法测试 |
| `wp2/` | 探针向量、Δs 表、排名、探针计划、给主办方的问题（草稿） |
| `wp3/` | 包哈希、构建日志、交接说明 |
| `wp4/` | 排行榜读数（每次运行一个带日期的小节） |
| `src/` | 代码：`grid15.py`、`variants.py`（已登记）、`test_wp1.py`、驱动脚本 `wp0_*`、`wp2_run.py`、`wp3_*`、`package_submission.py` |
| `cache/` | git 忽略：包副本、CLI 输出、探针 zip（`cache/packages/P_A3fix/`） |

## 重新运行

在本目录下用 `python3 -B` 依次运行的步骤见英文部分。本轮不修改 `TechArena_Challenge2_Team_Package/`，也不上传任何东西。
