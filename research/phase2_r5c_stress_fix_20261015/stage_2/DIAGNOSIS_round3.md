<a id="en"></a>

# Round 3 diagnosis (pseudo / cold-start results and physics only)

> **Language:** English · [中文](#zh)

Source: [outputs/S2_R2_pseudo_cold_predictions.csv](outputs/S2_R2_pseudo_cold_predictions.csv).

1. **Round 2 is near its floor on the pseudo and cold-start scenarios.**
   - R2_B's mean signed error is −0.08 to 0.00 pp per scenario; its MAE is 0.119 (pseudo) and 0.144 (cold start).
   - The remaining errors are month-specific and shared by every model, V2 included (k = 4 positive; k = 6 negative in all scenarios). They point to proxy or month structure, not to the law.
   - Pseudo and cold-start scenarios contain no k = 1 or k = 2 case, so they cannot diagnose anything further.
2. **Physics (round 4, stage 5).** The post-checkup recovery transient decays with τ ≈ 2.5 days **once cycling resumes**. The step exclusion so far counts 5 days from the checkup date. Measured from the first row of the first segment after each checkup instead:
   - month 0's first 45 °C step (01-20 00:36) comes 0.23 days after operation restarts (01-19 19:10), well inside the transient;
   - in months 2–6, the first 45 °C step comes 10–22 days after the restart.

   The correction therefore changes only month 0, which is used only at CK1.
3. **Consequence.** A round-3 design built on point 2 affects only CK1. Under rule 7 it is **exposed-CK1**: it may be reported and gated, its CK1 change is not evidence, and it cannot be the round's main (it cannot win on cold-start scenarios, where it is identical to round 2). No other design is supported by pseudo/cold-start evidence, so round 3 registers only this physics correction and its ensemble.

---

<a id="zh"></a>

# 第三轮诊断（仅依据伪场景 / 冷启动结果和物理）

> **语言：** [English](#en) · 中文

来源：[outputs/S2_R2_pseudo_cold_predictions.csv](outputs/S2_R2_pseudo_cold_predictions.csv)。

1. **第二轮在伪场景和冷启动场景上已接近极限。**
   - R2_B 各场景的平均带符号误差为 −0.08 至 0.00 pp；MAE 为 0.119（伪场景）和 0.144（冷启动）。
   - 剩下的误差是各月特有的，而且包括 V2 在内的所有模型都有（k = 4 为正；k = 6 在所有场景中为负）。它们指向代理或月份本身的结构，而不是定律。
   - 伪场景和冷启动场景里没有 k = 1 或 k = 2 的情形，所以无法再诊断出更多问题。
2. **物理（第四轮第 5 阶段）。** 检查后的恢复暂态在**恢复运行之后**以 τ ≈ 2.5 天衰减。迄今的台阶排除规则是从检查日期起算 5 天。如果改为从每次检查后第一段的第一行起算：
   - 第 0 月的第一个 45 °C 台阶（01-20 00:36）距恢复运行（01-19 19:10）只有 0.23 天，正处在暂态之中；
   - 第 2–6 月的第一个 45 °C 台阶都在恢复运行 10–22 天之后。

   所以这一修正只改变第 0 月，而第 0 月只在 CK1 时使用。
3. **结论。** 依据第 2 点设计的第三轮方案只影响 CK1。按规则 7，它属于**已曝光 CK1**：可以报告、可以过门槛，但它在 CK1 上的变化不是证据，也不能成为本轮主模型（它在冷启动场景上与第二轮完全相同，不可能胜出）。没有其他设计得到伪场景 / 冷启动证据的支持，因此第三轮只登记这个物理修正及其集成。
