<a id="en"></a>

# Stage 6 — Temperature-based ε refinement (leaderboard-only)

> **Language:** English · [中文](#zh)

Exposed-exploratory. **Leaderboard-only.** The proxies use the same ε assumption, so this variant cannot be judged on them and no proxy error is reported.

Protocol: `protocol.json`. Code: `run_6.py`. Output: `outputs/V2_epsT_table.csv`.

**Idea.** The 25 → 45 °C step bridge δ says that a 45 °C full charge ends about δ Ah fuller above the graphite step than a 25 °C full charge. If the bottom of the curve is unaffected, the 25 °C anchors need ε0 + δ rather than the assumed ε0 + 0.4. δ is the mean of the visible bridges at each cutoff (0.4 if none is visible).

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 SOH (%) | 95.992 | 95.137 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| V2_epsT SOH (%) | 95.992 | 95.137 | 93.366 | 92.595 | 91.863 | 91.117 | 90.607 |
| difference (pp) | 0 | 0 | −0.175 | −0.216 | −0.218 | −0.214 | −0.214 |
| δ_k (Ah), bridges used | — (0.4), 0 | — (0.4), 0 | 0.222, 1 | 0.179, 2 | 0.178, 3 | 0.182, 4 | 0.182, 5 |

- **No bridge in month 1.** Month 1 contributes no bridge: its only 45 °C step follows a CV end recorded at the 25 °C setpoint, and segment 3 is missing.
- **Direction of the shift.** V2_epsT lowers CK3–CK7 by about 0.21 pp. This is the same direction as the stage-5 risk (a partly recovered checkup state), but the two are separate hypotheses.
- **Use.** Treat it as an optional leaderboard probe, never as a proxy improvement. No stage 1–4 model passed, so there is no cumulative variant.

---

<a id="zh"></a>

# 阶段 6——基于温度细化 ε（只供排行榜检验）

> **语言：** [English](#en) · 中文

已曝光的探索性研究。**只供排行榜检验。** 代理用的是同一个 ε 假设，所以无法在代理上评判这个变体，也没有报告任何代理误差。

协议：`protocol.json`。代码：`run_6.py`。输出：`outputs/V2_epsT_table.csv`。

**思路。** 25 → 45 °C 的台阶跳变 δ 表明：45 °C 的满充比 25 °C 的满充在石墨台阶以上多充约 δ Ah。如果曲线底部不受影响，25 °C 锚点就应该用 ε0 + δ，而不是假定的 ε0 + 0.4。δ 取每个截断点上可见跳变的均值（尚无可见跳变时取 0.4）。

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 SOH（%） | 95.992 | 95.137 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| V2_epsT SOH（%） | 95.992 | 95.137 | 93.366 | 92.595 | 91.863 | 91.117 | 90.607 |
| 差值（pp） | 0 | 0 | −0.175 | −0.216 | −0.218 | −0.214 | −0.214 |
| δ_k（Ah）、所用跳变数 | —（0.4）、0 | —（0.4）、0 | 0.222、1 | 0.179、2 | 0.178、3 | 0.182、4 | 0.182、5 |

- **第 1 月没有跳变。** 第 1 月唯一的那次 45 °C 台阶，所跟随的 CV 末端在记录中仍是 25 °C 设定，而第 3 段又缺失，所以第 1 月贡献不了跳变。
- **调整的方向。** V2_epsT 把 CK3–CK7 下调约 0.21 pp。这与阶段 5 的风险（检查时只部分恢复）方向相同，但两者是不同的假设。
- **用法。** 只作为可选的排行榜探测，绝不能当作代理上的改进。阶段 1–4 没有模型通过，所以没有累积变体。
