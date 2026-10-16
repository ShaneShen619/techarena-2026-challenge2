<a id="en"></a>

# WP4 — Open-data prior for the stress model

> **Language:** English · [中文](#zh)

- **Protocol:** [protocol.json](protocol.json), committed `b3108bd` before any download or fit. Pseudo/cold-start results were committed in `a85f8af` before the real run.
- **Code:** [axes_cycling.py](axes_cycling.py), [fit_prior3.py](fit_prior3.py), [run_wp4.py](run_wp4.py).

## Conclusions first

1. **Yagci 2025 data could not be obtained, so WP4 ran under its registered fallback and is marked capped** (D4.1, [cap record](CAP_RECORD.md)).
   - The automatic download failed twice: an SSL error, then a truncated retry.
   - The manual download the user offered had not arrived after 7.5 hours, well past the 3-hour cap.
   - The calendar and break-in terms therefore stay at the 5C prior2 values.
2. **The cycling datasets show that prior2 is too pessimistic.** This is the main new evidence of WP4, and it is not exposed: it uses no pack data. Over each dataset's own time, temperature and throughput, prior2 predicts:

   | Dataset | Days | Mean cell T | Observed loss (Ah on 102 Ah) | prior2 calendar + break-in | prior2 total |
   |---|---|---|---|---|---|
   | LIC 280 Ah | 113 | 38.1 °C | 7.21 | 8.55 | **10.78 (+50 %)** |
   | Gotion 53 Ah cell | 181 | 26.6 °C | 7.99 | 8.22 | **9.88 (+24 %)** |

   Calendar + break-in alone already exceeds the observed loss, so the cycle-term estimate hits its floor (1e-12). By the registered bound rule it falls back to prior2. Hence **prior3 = prior2**, and S_A3 equals S_A on every case. This agrees with the pack: 5A/5C's prior-only first month over-predicted the CK1 loss (5A S_main −1.13 pp).
3. **Evaluation (as registered).** S_A3, F2_S_A3 and F1_S_A3 reproduce the WP2 numbers exactly and fail the gates against SUB: G-proxy, G-epsfree, G-robust, G-hyp; F2/S_A3 also fail G-regress ([gates](outputs/wp4_gates.json), [summary](outputs/wp4_summary_table.csv)). No candidate.
4. **Next step if the data arrive.** Put `Data.zip` (Zenodo 22939281, 2,456,145,428 bytes) into `cache/downloads/yagci/` and rerun `fit_prior3.py` with the extracted storage table. The storage cells are the only open data that can separate the calendar term. Given point 2, they would likely lower A_cal and A_b, which is the direction that would fix the CK1 cold start without the exposed restart rule.

## Data qualification

| Dataset | Licence | Independent capacity points | Duty | Identifies |
|---|---|---|---|---|
| LIC 280 Ah (TEMPEST), doi 10.5281/zenodo.20813753 | CC BY 4.0 | 15 (0.1C RPT every 50 cycles) | 1C cycling, 1-day rest per block, 25 → 38 °C self-heating | total loss under continuous cycling; calendar and cycle collinear |
| Gotion 53 Ah cell, doi 10.17632/4nww8p6vxf.1 | CC BY 4.0 | 21 (every 50 cycles) | continuous cycling at ~26.7 °C | as above |
| Gotion 53 Ah 10S module | CC BY 4.0 | 21 | as above; capacity first rises 1.1 % | robustness only |
| Yagci 2025, doi 10.5281/zenodo.22939281 | CC BY 4.0 (verified on the record API) | about 5 RPTs per cell | storage at 35/50 °C, 75/100 % SOC, plus cycling | calendar and break-in, separately (not obtained) |

The cycling axes ([CSV](outputs/wp4_cycling_axes.csv)) match each LIC capacity point to its reference test by throughput, because one reference test was repeated without cycling in between.

## Attribution (for the report)

- Yagci, M. C., Richter, O., Behmann, R., Bessler, W. G., J. Energy Storage 124, 116774 (2025); data doi 10.5281/zenodo.22939281 (the readme asks to also cite 10.5281/zenodo.22010995). Used: published numbers as the prior centre; raw data not obtained.
- TEMPEST LIC 280 Ah, doi 10.5281/zenodo.20813753, CC BY 4.0. Used: prior check and ε drift.
- Gotion 53 Ah, doi 10.17632/4nww8p6vxf.1, CC BY 4.0. Used: prior check and ε drift.

---

<a id="zh"></a>

# WP4——为应力模型构建开放数据先验

> **语言：** [English](#en) · 中文

- **协议：** [protocol.json](protocol.json)，在任何下载或拟合之前于 `b3108bd` 提交。伪场景 / 冷启动结果在真实运行之前于 `a85f8af` 提交。
- **代码：** [axes_cycling.py](axes_cycling.py)、[fit_prior3.py](fit_prior3.py)、[run_wp4.py](run_wp4.py)。

## 结论先读

1. **没能拿到 Yagci 2025 的数据，所以 WP4 按登记的回退方案执行，并标为到达上限**（D4.1，[上限记录](CAP_RECORD.md)）。
   - 自动下载失败了两次：一次 SSL 错误，一次重试时文件被截断。
   - 用户提出手动下载，但 7.5 小时后文件仍未到位，远远超过了 3 小时的上限。
   - 因此日历项和磨合项保留 5C 的 prior2 值。
2. **循环数据集表明 prior2 过于悲观。** 这是 WP4 的主要新证据，而且它没有曝光：没有用到任何电池组数据。按每个数据集自己的时间、温度和吞吐，prior2 的预测如下：

   | 数据集 | 天数 | 平均芯温 | 实测损失（按 102 Ah 折算，Ah） | prior2 日历 + 磨合 | prior2 合计 |
   |---|---|---|---|---|---|
   | LIC 280 Ah | 113 | 38.1 °C | 7.21 | 8.55 | **10.78（+50 %）** |
   | Gotion 53 Ah 单芯 | 181 | 26.6 °C | 7.99 | 8.22 | **9.88（+24 %）** |

   单是日历项加磨合项就已经超过了实测损失，所以循环项的估计撞到下限（1e-12）。按登记的边界规则，它回退到 prior2。因此 **prior3 = prior2**，S_A3 在每个情形上都与 S_A 相同。这与电池组上的现象一致：5A/5C 只靠先验算的第一个月，高估了 CK1 的损失（5A S_main −1.13 pp）。
3. **评估（按登记执行）。** S_A3、F2_S_A3、F1_S_A3 完全复现了 WP2 的数字，对 SUB 都没过门槛：G-proxy、G-epsfree、G-robust、G-hyp；F2/S_A3 还没过 G-regress（[门槛](outputs/wp4_gates.json)、[汇总](outputs/wp4_summary_table.csv)）。没有候选。
4. **如果数据到位，下一步怎么做。** 把 `Data.zip`（Zenodo 22939281，2,456,145,428 字节）放进 `cache/downloads/yagci/`，用解压出的存储表重新运行 `fit_prior3.py`。存储电芯是唯一能把日历项单独分离出来的开放数据。根据第 2 点，它们很可能会把 A_cal 和 A_b 调低，而这正是能在不依赖已曝光的恢复运行规则的情况下修好 CK1 冷启动的方向。

## 数据资格

| 数据集 | 许可证 | 独立容量点 | 工况 | 能辨识什么 |
|---|---|---|---|---|
| LIC 280 Ah（TEMPEST），doi 10.5281/zenodo.20813753 | CC BY 4.0 | 15（每 50 循环一次 0.1C RPT） | 1C 循环，每块后静置 1 天，自热从 25 °C 升到 38 °C | 连续循环下的总损失；日历与循环共线 |
| Gotion 53 Ah 单芯，doi 10.17632/4nww8p6vxf.1 | CC BY 4.0 | 21（每 50 循环） | 约 26.7 °C 下连续循环 | 同上 |
| Gotion 53 Ah 10 串模组 | CC BY 4.0 | 21 | 同上；容量先上升 1.1 % | 只用于稳健性 |
| Yagci 2025，doi 10.5281/zenodo.22939281 | CC BY 4.0（已在记录 API 上核实） | 每芯约 5 次 RPT | 35/50 °C、75/100 % SOC 存储，加上循环 | 可分别辨识日历项和磨合项（未取得） |

循环数据的时间轴（[CSV](outputs/wp4_cycling_axes.csv)）按吞吐把每个 LIC 容量点与其参考测试对应起来，因为其中有一次参考测试是在没有循环的情况下重复做的。

## 来源说明（供报告使用）

- Yagci, M. C., Richter, O., Behmann, R., Bessler, W. G., J. Energy Storage 124, 116774 (2025)；数据 doi 10.5281/zenodo.22939281（readme 要求同时引用 10.5281/zenodo.22010995）。用途：以公布的数字作为先验中心；原始数据未取得。
- TEMPEST LIC 280 Ah，doi 10.5281/zenodo.20813753，CC BY 4.0。用途：先验检查和 ε 漂移。
- Gotion 53 Ah，doi 10.17632/4nww8p6vxf.1，CC BY 4.0。用途：先验检查和 ε 漂移。
