<a id="en"></a>

# Hand-over: the P_A3fix probe zip

> **Language:** English · [中文](#zh)

**Short version.** Do not upload anything yet. One probe zip is ready and validated. Upload it only after (1) the board shows SUB's own score, and (2) you know the deadline and the next evaluation is at least 3 days before it. Re-upload SUB right after the probe's evaluation unless the probe wins. Round 15 itself uploaded nothing and sent nothing.

## 1. The files

| Zip | Path | SHA256 | Role |
|---|---|---|---|
| **P_A3fix** (probe) | `/Users/shane/Desktop/Arena_1019_r15_probe/research/phase2_r15_probe_plan_20261019/cache/packages/P_A3fix/Current State_Challenge2.zip` | `3d7926628da238925700599079d621925d865a65fb8728880c4a0e6fa43972e6` | the one probe |
| **SUB** (current model, `6525edf`) | `/Users/shane/Desktop/Arena项目书面文件/提交包/Current State_Challenge2.zip` | `a4ed59a36c154a106482c4c8f4ae620ba7904f31627b767917eccb972b24200f` | the default last submission |

**Both files have the same name** (the rules require `<TeamName>_Challenge2.zip`). Check the hash before every upload: `shasum -a 256 "<path>"`.

## 2. Which zip, and when

1. **Now:** make sure SUB is the active submission. When the board shows its value, log it (section 3). Try to learn the deadline, the cadence and the board's precision ([../wp2/ORGANIZER_QUESTION.md](../wp2/ORGANIZER_QUESTION.md) is a draft you may send or not). Write the deadline into `inputs/deadline.txt` (date, time, time zone).
2. **Upload P_A3fix** right after SUB's value is logged, **only if** the next evaluation (two weeks per the guide; the PDF says weekly) is expected at least 3 days before the deadline.
3. **After the board shows P_A3fix's value:** log it and run WP4. Unless WP4 says "probe wins", **re-upload SUB the same day.**
4. If the deadline stays unknown, **do not upload the probe.** SUB stays the last submission.

## 3. What to log in `inputs/leaderboard_log.csv`

Add one row per board evaluation, in the study folder of this worktree (`research/phase2_r15_probe_plan_20261019/inputs/leaderboard_log.csv`):

| Column | What to write |
|---|---|
| `board_date` | date the board was updated, `YYYY-MM-DD` |
| `package_file` | file name of the zip that was active at that evaluation |
| `package_sha256` | its SHA256 (section 1) |
| `model_commit` | `6525edf` for SUB; `6525edf+P_A3fix` for the probe |
| `metrics_verbatim` | every value the board shows, copied exactly with all decimals and labels, e.g. `score=0.0873; MAE=0.091` |
| `rank` | the rank shown, or empty |
| `notes` | anything else (e.g. a reduced-budget score, or that the board changed format) |

Put a field in double quotes if it contains a comma. Example:

```
board_date,package_file,package_sha256,model_commit,metrics_verbatim,rank,notes
2026-10-27,Current State_Challenge2.zip,a4ed59a36c154a106482c4c8f4ae620ba7904f31627b767917eccb972b24200f,6525edf,"score=0.0873",5,
```

## 4. When to run WP4

After every board evaluation you have logged. WP4 checks the hash, filters the hypotheses, applies the registered reading rule and states the next action. With no new row, it records "waiting for leaderboard" and stops.

## 5. Reminders

- **The last submission counts.** Re-upload SUB's zip at the end unless the probe wins. A probe must never be the last submission unless it won.
- **Presentation warning.** `inputs/pptx_path.txt` says `template`, so the probe zip carries the **template** presentation. So do all three existing zips, SUB's included (same SHA256 `8bcd38a1…`). The presentation in the last submission is the one used at the final event. If the team has a real deck, write its path into `inputs/pptx_path.txt` and rebuild before uploading:
  `python3 -B src/package_submission.py "Current State" --members "Mona Zhu, Zhikuan Shen" --pptx "<deck path>" --out cache/packages/P_A3fix`
  (run from the study folder). SUB's zip would need the same rebuild with the base packaging script.
- **Disclosure.** The probe's README has a section that describes the variant. If it is ever kept, the report must disclose it too (WP4 drafts the text).
- **Git.** Commits after `f0480d8` are local only, because of the "upload no file" instruction (D4). To publish the branch: `git -C /Users/shane/Desktop/Arena_1019_r15_probe push origin exp/phase2-r15-probe-plan-20261019`.

---

<a id="zh"></a>

# 交接说明：P_A3fix 探针 zip

> [English](#en) · 中文

**简短版。** 现在不要上传任何东西。一个探针 zip 已构建并通过验证。只有在 (1) 榜单已显示 SUB 自己的分数，并且 (2) 你知道截止时间、下一次评估在截止前至少 3 天时，才上传它。探针评估之后，除非探针胜出，立即重新上传 SUB。第 15 轮本身没有上传、也没有发送任何东西。

## 1. 文件

| Zip | 路径 | SHA256 | 作用 |
|---|---|---|---|
| **P_A3fix**（探针） | `/Users/shane/Desktop/Arena_1019_r15_probe/research/phase2_r15_probe_plan_20261019/cache/packages/P_A3fix/Current State_Challenge2.zip` | `3d7926628da238925700599079d621925d865a65fb8728880c4a0e6fa43972e6` | 唯一的探针 |
| **SUB**（当前模型，`6525edf`） | `/Users/shane/Desktop/Arena项目书面文件/提交包/Current State_Challenge2.zip` | `a4ed59a36c154a106482c4c8f4ae620ba7904f31627b767917eccb972b24200f` | 默认的最后一次提交 |

**两个文件同名**（规则要求命名为 `<TeamName>_Challenge2.zip`）。每次上传前核对哈希：`shasum -a 256 "<路径>"`。

## 2. 上传哪个、什么时候

1. **现在：** 确认 SUB 是当前有效的提交。榜单显示它的值后，记录下来（第 3 节）。设法弄清截止时间、评估频率和榜单精度（[../wp2/ORGANIZER_QUESTION.md](../wp2/ORGANIZER_QUESTION.md) 是草稿，发不发由你决定）。把截止时间（日期、时间、时区）写进 `inputs/deadline.txt`。
2. **上传 P_A3fix：** 在 SUB 的值记录之后立即上传，**前提是**下一次评估（按指南为两周；PDF 说每周）预计在截止前至少 3 天。
3. **榜单显示 P_A3fix 的值之后：** 记录并运行 WP4。除非 WP4 给出"探针胜出"，**当天重新上传 SUB。**
4. 如果截止时间一直未知，**不要上传探针。** SUB 保持为最后一次提交。

## 3. 在 `inputs/leaderboard_log.csv` 里记录什么

每次榜单评估加一行，文件在本工作树的研究目录里（`research/phase2_r15_probe_plan_20261019/inputs/leaderboard_log.csv`）：

| 列 | 写什么 |
|---|---|
| `board_date` | 榜单更新的日期，`YYYY-MM-DD` |
| `package_file` | 那次评估时有效的 zip 文件名 |
| `package_sha256` | 它的 SHA256（第 1 节） |
| `model_commit` | SUB 写 `6525edf`；探针写 `6525edf+P_A3fix` |
| `metrics_verbatim` | 榜单显示的每个值，原样照抄，保留所有小数和标签，例如 `score=0.0873; MAE=0.091` |
| `rank` | 显示的排名，没有就留空 |
| `notes` | 其他信息（例如缩减数据量的分数，或榜单格式变了） |

字段里有逗号时用双引号括起来。示例见英文部分。

## 4. 什么时候运行 WP4

每记录一次榜单评估就运行一次。WP4 会核对哈希、筛选假设、应用登记的解读规则，并给出下一步行动。没有新行时，它记为"等待排行榜"并停止。

## 5. 提醒

- **最后一次提交才算数。** 除非探针胜出，最后要重新上传 SUB 的 zip。除非探针胜出，绝不能让探针成为最后一次提交。
- **演示文稿警告。** `inputs/pptx_path.txt` 写的是 `template`，所以探针 zip 里是**模板**演示文稿。现有的三个 zip 也都是（包括 SUB 的，SHA256 同为 `8bcd38a1…`）。最后一次提交里的演示文稿就是决赛用的版本。如果团队有正式的演示文稿，把路径写进 `inputs/pptx_path.txt`，上传前重新构建（命令见英文部分，在研究目录中运行）。SUB 的 zip 也需要用基点的打包脚本同样重建。
- **披露。** 探针的 README 有一节说明这个变体。如果最终保留它，报告里也必须披露（WP4 会起草文字）。
- **Git。** 由于"不得上传任何文件"的要求，`f0480d8` 之后的提交只保存在本地（D4）。如需发布分支：`git -C /Users/shane/Desktop/Arena_1019_r15_probe push origin exp/phase2-r15-probe-plan-20261019`。
