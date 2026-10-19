<a id="en"></a>

# Round 14 WP0 — Setup and fact sheet: report

> **Language:** English · [中文](#zh)

## Conclusions

- **Setup is done.** The worktree is `/Users/shane/Desktop/Arena_1019_r14_path_drift`, on branch `exp/phase2-r14-path-drift-20261019` from base `6525edf` (still the tip). Sources are copied with SHA256 in `sources/SOURCES.md`. The optional round 12 / round 13 files are not on origin yet and are re-checked when they would be used.
- **SUB reproduces** through the package CLI: CK1..CK7 = 95.984, 94.507, 93.600, 92.821, 92.015, 91.426, **90.765 %**, the same as rounds 11 and 12 (`SUB_SOH.csv`).
- **The exposed facts hold, with two qualifications** (`FACTS.md`):
  - The 7–8 mV top rest-voltage gap is **per cell** (pack: 28–33 mV), and it has the opposite sign at 45 °C (anchor 0).
  - The first-program offset is +0.40 … +0.70 Ah **raw** (D1 − D2). It is ≈ +0.3 … +0.4 Ah after removing the normal program-to-program step change, which matches the earlier trend-adjusted +0.39–0.46 Ah.
  - The two Ah-balance facts (+0.1 Ah top-up excess; non-closing block balance) are deferred to WP2, because WP0 computes no Ah balance.
- **Two structural facts constrain the registration:**
  1. **Recording gaps** lie between the anchor and T1 for **anchors 3 and 7**. The registered Ah-chain rule excludes such pairs, which leaves P1 with anchors 1, 2, 4, 5, 6: exactly the 5-point minimum.
  2. **A second top-up** in the same segment exists only for **anchors 5 and 6**. So P1b has 2 points at 25 °C, below the 5-point minimum. There are only two 25 °C TT pairs (segments 10 and 12).

## Files

| File | Content |
|---|---|
| `SUB_SOH.csv` | SUB per checkup (SOH %, Q Ah) from `run_model.py` train + test |
| `anchor_blocks.csv` | one row per anchor k = 0..7: anchor, T1, T2 CV ends (row index and time), recording gaps between them, CV Ah / CV s / end current, pack and cell V30 |
| `facts.json` | all numbers behind `FACTS.md` |
| `FACTS.md` | the §2 facts with verdicts and numbers |

---

<a id="zh"></a>

# 第 14 轮 WP0 — 准备与事实清单：报告

> [English](#en) · 中文

## 结论

- **准备工作已完成。** 工作树为 `/Users/shane/Desktop/Arena_1019_r14_path_drift`，分支 `exp/phase2-r14-path-drift-20261019`，基点 `6525edf`（仍是分支末端）。来源文件已复制，SHA256 记在 `sources/SOURCES.md`。可选的第 12/13 轮文件在 origin 上还没有，用到时再检查。
- **SUB 可复现**（通过包 CLI）：CK1..CK7 = 95.984、94.507、93.600、92.821、92.015、91.426、**90.765 %**，与第 11、12 轮相同（`SUB_SOH.csv`）。
- **已曝光的事实成立，但有两点限定**（`FACTS.md`）：
  - 顶部静置电压 7–8 mV 的差是**按单体**而言（电池组：28–33 mV），在 45 °C（锚点 0）符号相反。
  - 首个程序偏移**原始值**（D1 − D2）为 +0.40 … +0.70 Ah。扣除正常的程序间台阶变化后约为 +0.3 … +0.4 Ah，与之前扣除趋势后的 +0.39–0.46 Ah 一致。
  - 两条电量对账类事实（补电多充 +0.1 Ah；逐块对账不闭合）推迟到 WP2，因为 WP0 不计算任何电量对账。
- **两个结构性事实约束登记：**
  1. **锚点 3 和 7** 的锚点与 T1 之间有**记录间隙**。登记的电量链规则排除这类配对，P1 只剩锚点 1、2、4、5、6：正好是 5 个点的下限。
  2. 同一段内的**第二次补电**只在**锚点 5 和 6** 存在。所以 P1b 在 25 °C 只有 2 个点，低于 5 个点的下限。25 °C 的 TT 配对只有两个（第 10、12 段）。

## 文件

| 文件 | 内容 |
|---|---|
| `SUB_SOH.csv` | 用 `run_model.py` 训练 + 测试得到的各检查点 SUB（SOH %、Q Ah） |
| `anchor_blocks.csv` | 每个锚点 k = 0..7 一行：锚点、T1、T2 的 CV 结束（行号和时间）、其间的记录间隙、CV 电量 / CV 时长 / 末电流、电池组和单体的 V30 |
| `facts.json` | `FACTS.md` 背后的全部数字 |
| `FACTS.md` | 第 2 节各条事实的判定和数字 |
