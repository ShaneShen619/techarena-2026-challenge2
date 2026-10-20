<a id="en"></a>

# WP0 — Setup, rules audit and inventory

> **Language:** English · [中文](#zh)

## Conclusions

- **SUB reproduces exactly** through the package CLI: CK1..CK7 = 95.984, 94.507, 93.600, 92.821, 92.015, 91.426, 90.765 (= `EXPECTED_SOH`). See [SUB_SOH.csv](SUB_SOH.csv).
- **No leaderboard observations.** `inputs/leaderboard_log.csv` did not exist anywhere under the Desktop, so the template was created and is empty. The deadline is "unknown" and the presentation is "template" (D6).
- **The rules allow resubmission without limit; the last submission counts.** Five facts are unpublished: deadline, platform, cadence (weekly vs two-weekly), metric set, and board layout ([RULES.md](RULES.md)).
- **Existing zips:** three, all in `Arena项目书面文件/提交包/`. `Current State_Challenge2.zip` is the current SUB (`6525edf`); the two backups are T_main (`5cd305c`) and V2 + √t (`21a7a55`). The log does not say which one was submitted. All three carry the **template** presentation ([existing_packages.csv](existing_packages.csv)).
- **Rounds 12–14 are present and complete:** R12 = L3 with G_a3 passed; R13 = O3; R14 = O3 ([candidates.md](candidates.md)).
- **Push policy:** following the session's "upload no file" instruction and round 12's precedent, commits after the first one stay local (D4).

## Steps

1. Worktree `/Users/shane/Desktop/Arena_1019_r15_probe` on `exp/phase2-r15-probe-plan-20261019` from base `6525edf` (D1). The prompt copy is byte-identical to the original (SHA256 `1e028f36…1069`) and was the first commit (`f0480d8`).
2. Sources: 25 files from origin refs and the worktree, with SHA256 in [../sources/SOURCES.md](../sources/SOURCES.md) (script `src/wp0_sources.py`). The prompt's required list is complete; support files are explained in D5.
3. Rules: [RULES.md](RULES.md), 13 verbatim rule sentences and 9 open points.
4. Inputs: templates created ([../inputs/](../inputs/)); state in [inputs_state.json](inputs_state.json).
5. Inventory: [existing_packages.csv](existing_packages.csv) (script `src/wp0_inventory.py`).

| Zip | Size (B) | SHA256 (zip) | model_template.py SHA256 | Commit | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | Logged |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `Current State_Challenge2.zip` | 3 745 277 | `a4ed59a3…200f` | `3bd26ed8…fbd5` | `6525edf` (SUB, A3) | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 | no (log empty) |
| `…_backup_Tmain_20261017.zip` | 3 742 919 | `81e1615f…40ea` | `e3f094e6…0496` | `5cd305c` (T_main) | 95.992 | 94.507 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 | no |
| `…_backup_V2sqrt_20261015.zip` | 3 741 114 | `aead82c8…7ebb` | `2b0266c2…be8f` | `21a7a55` (V2 + √t) | 95.992 | 94.451 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 | no |

6. Candidates: [candidates.md](candidates.md).

## Next

WP1 registers the protocol: grid, metric family, eligible probes, reading rules.

---

<a id="zh"></a>

# WP0 — 准备、规则审查与清点

> [English](#en) · 中文

## 结论

- **SUB 通过包的 CLI 完全复现：** CK1..CK7 = 95.984、94.507、93.600、92.821、92.015、91.426、90.765（= `EXPECTED_SOH`）。见 [SUB_SOH.csv](SUB_SOH.csv)。
- **没有排行榜观测。** 桌面下任何位置都没有 `inputs/leaderboard_log.csv`，所以创建了空模板。截止时间为"unknown"，演示文稿为"template"（D6）。
- **规则允许无限次重新提交，最后一次提交才算数。** 五件事没有公布：截止时间、平台、评估频率（每周还是每两周）、指标集、榜单形式（[RULES.md](RULES.md)）。
- **现有 zip：** 三个，都在 `Arena项目书面文件/提交包/`。`Current State_Challenge2.zip` 是当前 SUB（`6525edf`）；两个备份分别是 T_main（`5cd305c`）和 V2 + √t（`21a7a55`）。记录里没有说提交过哪一个。三个 zip 里都是**模板**演示文稿（[existing_packages.csv](existing_packages.csv)）。
- **第 12–14 轮都已存在且已完成：** R12 = L3，G_a3 通过；R13 = O3；R14 = O3（[candidates.md](candidates.md)）。
- **推送策略：** 按本会话"不得上传任何文件"的要求和第 12 轮的先例，第一次提交之后的提交只保存在本地（D4）。

## 步骤

1. 工作树 `/Users/shane/Desktop/Arena_1019_r15_probe`，分支 `exp/phase2-r15-probe-plan-20261019`，基点 `6525edf`（D1）。prompt 副本与原文件逐字节相同（SHA256 `1e028f36…1069`），作为第一次提交（`f0480d8`）。
2. 来源：25 个文件，来自 origin 引用和工作树，SHA256 见 [../sources/SOURCES.md](../sources/SOURCES.md)（脚本 `src/wp0_sources.py`）。prompt 要求的清单齐全；支持文件的说明见 D5。
3. 规则：[RULES.md](RULES.md)，13 条原文规则和 9 个未决事项。
4. 输入：已创建模板（[../inputs/](../inputs/)）；状态见 [inputs_state.json](inputs_state.json)。
5. 清点：[existing_packages.csv](existing_packages.csv)（脚本 `src/wp0_inventory.py`），表见英文部分。
6. 候选：[candidates.md](candidates.md)。

## 下一步

WP1 登记协议：网格、指标族、合格探针、解读规则。
