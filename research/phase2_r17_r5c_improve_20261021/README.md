<a id="en"></a>

# Round 17 — r5c stress-model physics improvements

> **Language:** English · [中文](#zh)

**Result: no design improves r5c; the submission is unchanged.** Details are in [FINAL_REPORT.md](FINAL_REPORT.md).

- **Inert designs.** The switch fix (B0), the SOC-weighted calendar clock (S), the calendar Ea on k (C) and dropping the cycle term (D) move predictions by less than the noise floor (T_move = 0.110 pp). The operating SOC is the same every month, so A_cal absorbs any SOC weight.
- **Movers that fail.** τ_b model averaging (O1) and the literature overhang state (O2) do move predictions, but fail the paired causal check (mean +0.008 / +0.007 pp). τ_b is not identified (0 of 28 cases with a top weight ≥ 0.8).
- **Exposed-CK2 trap.** On the real proxies O1/O2 ensembles would look best (0.108 / 0.103 vs REF 0.131, SUB 0.120). The gain is entirely CK2, so it is labelled exposed-CK2 and not recommended.
- **FINAL = REF.** It is not causally better than SUB (−0.018 pp < δ 0.028), so no candidate code was written (WP5 skipped).
- **Out of scope.** The leaderboard level error (0.7–1 pp) is out of scope. r5c-family models sit 0.06–0.19 pp below SUB.

**Layout:**

| Path | Contents |
|---|---|
| `EXECUTION_PROMPT.md` | The registered plan |
| `src/` | Copies of r5c code, plus `stress17.py`, `smodel17.py`, `designs17.py`, `eval17.py` |
| `wp0/` … `wp4/` | Protocols, scripts, outputs and reports |
| `notes/` | STATUS and DECISIONS |
| `sources/` | Copied inputs with SHA256 |

**Reproduce:**
1. `python3 -B wp0/run_wp0_repro.py`
2. `python3 -B wp0/run_wp0_facts.py`
3. `python3 -I -B wp1/run_wp1.py <TUM dir>`
4. `python3 -B wp2/run_screen.py`
5. `python3 -B wp2/run_paired.py`
6. `python3 -B wp3/run_wp3.py`
7. `python3 -B wp4/run_real.py`

---

<a id="zh"></a>

# 第 17 轮——r5c 压力模型的物理改进

> **语言：** [English](#en) · 中文

**结果：没有设计能改进 r5c，提交版本不变。** 详见 [FINAL_REPORT.md](FINAL_REPORT.md)。

- **惰性的设计。** 换温箱修正（B0）、按 SOC 加权的日历时钟（S）、日历 Ea 加在 k 上（C）、去掉循环项（D）让预测变化低于噪声底（T_move = 0.110 pp）。运行 SOC 每月相同，任何 SOC 权重都会被 A_cal 吸收。
- **能动但不通过的设计。** τ_b 模型平均（O1）和文献 overhang 状态（O2）能让预测动起来，但配对因果检查不通过（均值 +0.008 / +0.007 pp）。τ_b 识别不出来（28 个案例中最大权重 ≥ 0.8 的为 0 个）。
- **exposed-CK2 陷阱。** 在真实代理上 O1/O2 的集成看起来最好（0.108 / 0.103，REF 0.131，SUB 0.120），但收益全部来自 CK2，所以标为 exposed-CK2，不推荐。
- **FINAL = REF。** 它在因果上并不优于 SUB（−0.018 pp，小于 δ 0.028），所以没有写候选代码（WP5 跳过）。
- **不在范围内。** 排行榜显示的水平误差（0.7–1 pp）不在本轮范围内。r5c 系列模型比 SUB 低 0.06–0.19 pp。

**目录：**

| 路径 | 内容 |
|---|---|
| `EXECUTION_PROMPT.md` | 登记的计划 |
| `src/` | r5c 代码副本，以及 `stress17.py`、`smodel17.py`、`designs17.py`、`eval17.py` |
| `wp0/` … `wp4/` | 协议、脚本、输出和报告 |
| `notes/` | STATUS 和 DECISIONS |
| `sources/` | 复制来的输入及其 SHA256 |

**复现：** 按上面英文部分列出的 7 条命令依次运行。
