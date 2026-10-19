<a id="en"></a>

# WP0 — Fact sheet: the §2 "facts to re-verify", checked against the data

> English · [中文](#zh)

Numbers come from [cv_catalogue.csv](cv_catalogue.csv) and [facts.json](facts.json), written by `src/wp0_catalogue.py` from the challenge data in this worktree. Round 11's fit values come from the copied `sources/r11_wp4_pack_drivers.csv`. **No tail model was fitted in WP0** (see D3 in `notes/DECISIONS.md`).

**Summary.** Four of the six facts hold as stated. Two need a correction: the anchors' CV phase is somewhat longer than "about 7 min / 40 samples" and lengthens with ageing, and the top-ups' CV phase is 1.9–4.4 min, not 2–9 min. The back-of-envelope arithmetic reproduces, but it mixes two models (see fact 6), so it stays a hypothesis for WP2.

| # | Fact in the prompt | Verdict | Number from the data |
|---|---|---|---|
| 1 | Round 11 fitted I = I∞ + A·e^(−t/τ); anchor 1 gave τ = 179 s, I∞ = 4.23 A | **holds** | `r11_wp4_pack.py` fits `a + b·exp(−x/c)` over the samples with pack ≥ 13.995 V; its table gives τ = 178.6 s, I∞ = 4.230 A for anchor 1 (anchor 7: τ = 216.6 s, I∞ = 4.272 A). For anchor 1 its window starts on the same sample as ours. |
| 1b | "The observed CV window does not by itself show a decay to zero" | **holds** | Anchors 1–7 end at I = 5.094–5.100 A, with the current still falling: 60 s before the end it is 5.66–5.88 A. Nothing in the window shows where the current would level off. |
| 2a | Anchors' CV phase ≈ 7 min, ≈ 40 samples at 10 s | **partly** | Anchors 1–7: **438–530 s (7.3–8.8 min), 45–54 samples**. It lengthens with ageing: 438, 456, 455, 505, 522, 514, 530 s for anchors 1–7. |
| 2b | Top-ups' CV phase lasts 2–9 min | **corrected** | 25 °C top-ups: 239–262 s (4.0–4.4 min, 25–28 samples). 45 °C top-ups: 112–176 s (1.9–2.9 min, 13–19 samples). No top-up exceeds 4.4 min. |
| 2c | Anchor 0 (45 °C) has a 36 s CV phase where round 11's fit fails | **holds** | Anchor 0: 37 s, 5 samples (I 13.26 → 5.09 A). Round 11's fit returned τ = −152 886 s and I∞ = 31 853 A, i.e. it failed. |
| 3 | 41 full charges: 8 from empty, 33 top-ups | **holds** | 41 charges reach the CV phase. 8 anchors (91.97–100.13 Ah charged) and 33 top-ups (20.63–21.75 Ah); of the top-ups, 9 are at 25 °C and 24 at 45 °C. All 41 match round 8's `E00`–`E40` by CV-end time. |
| 4a | CK0's C/20 discharge starts at 13.590 V under 5.1 A, with cell3 at 3.511 V | **holds** | First CK0 sample: 13.590 V at −5.096 A; cells 3.374 / 3.351 / **3.511** / 3.359 V. |
| 4b | Cell3 also sets anchor 0's top (3.53 V 30 min after the CV end) | **holds, and more** | Anchor 0 at +30 min: cells 3.385 / 3.358 / **3.530** / 3.371 V. **Cell3 is the highest cell at the CV end and at +30 min in all 41 full charges.** |
| 4c | The pack enters each checkup at 13.1–13.3 V | **roughly** | Last operating sample before CK1, CK3–CK7: 13.190, 13.220, 13.200, 13.440, 13.270, 13.257 V, all under load (−8.6 to +7.5 A). Five of six are in 13.1–13.3 V; before CK5 it is 13.44 V while charging at 7.5 A. The last rest voltages are 13.07–13.37 V. Before CK2 there is no data (segment 3 is missing). Either way, the pack enters each checkup well below full. |
| 5 | Round 11, pack: end current fixed at 5.094–5.100 A; relaxed top voltage flat (13.439 → 13.435 V) | **holds** | I_end 5.094–5.100 A; V_pack at +30 min 13.439, 13.438, 13.435, 13.434, 13.432, 13.434, 13.435 V for anchors 1–7. Cell3 at +30 min falls 3.373 → 3.366 V; cell1 and cell4 stay within 1–2 mV. |
| 6 | Back-of-envelope: I_end·τ ≈ 0.25 Ah (anchor 1) → 0.31 Ah (anchor 7); tail drift ≈ 0.05 Ah | **arithmetic reproduces; hypothesis only** | With round 11's τ: 5.094 × 178.6 s = 0.253 Ah; 5.098 × 216.6 s = 0.307 Ah; difference 0.054 Ah. But round 11's τ comes from the model with I∞ ≈ 4.2 A. I_end·τ is the tail of an exponential that decays to **zero** (M1), which is a different model. Whether M1 fits, and with what τ, is a WP2 question. |

Other catalogue facts that bear on WP1:

- **CV start.** By the registered definition (pack ≥ 13.95 V and I < 19.9 A), the CV start is the first sample after the CC→CV switch. Its current is 17.7–19.4 A for anchors 1–7, depending on where the switch falls between two 10 s samples.
- **CV Ah, our definition.** This is the trapezoid of I over the CV samples. Anchors 1–7: 1.146, 1.169, 1.167, 1.293, 1.362, 1.315, 1.369 Ah. Round 11 reported 1.17 → 1.44 Ah with a different window and a rectangle rule.
- **Rest before the pulse.** Every full charge is followed by a rest of 1800–1801 s with |I| < 0.5 A, then a 20.4 A discharge pulse. So "+30 min" is the last rest sample before the pulse, for all 41 charges. No charge has a recording gap above 600 s.
- **Temperature at the CV end.** Anchors 1–7: 26.9–27.2 °C. 25 °C top-ups: 26.5–26.8 °C. 45 °C charges: 46.3–46.9 °C.
- **SUB** (`6525edf`, package CLI) in SOH %: CK0 98.441, CK1 95.984, CK2 94.507, CK3 93.600, CK4 92.821, CK5 92.015, CK6 91.426, CK7 90.765 ([SUB_SOH.csv](SUB_SOH.csv)). These are identical to round 11's WP0.

---

<a id="zh"></a>

# WP0 — 事实清单：逐条用数据核实第 2 节"需重新核实的事实"

> [English](#en) · 中文

数字来自 [cv_catalogue.csv](cv_catalogue.csv) 和 [facts.json](facts.json)，由 `src/wp0_catalogue.py` 从本工作树的赛题数据算出。第 11 轮的拟合值取自复制来的 `sources/r11_wp4_pack_drivers.csv`。**WP0 中没有拟合任何尾巴模型**（见 `notes/DECISIONS.md` 中的 D3）。

**总结。** 六条事实中四条如原文成立。两条需要修正：锚点的 CV 段比"约 7 min / 40 个样本"略长，并且随老化变长；补电的 CV 段为 1.9–4.4 min，不是 2–9 min。粗算的算术能复现，但它混用了两个模型（见第 6 条），因此仍只是留给 WP2 检验的假设。

| # | Prompt 中的事实 | 结论 | 数据中的数字 |
|---|---|---|---|
| 1 | 第 11 轮拟合 I = I∞ + A·e^(−t/τ)；锚点 1 得 τ = 179 s、I∞ = 4.23 A | **成立** | `r11_wp4_pack.py` 在电池组 ≥ 13.995 V 的样本上拟合 `a + b·exp(−x/c)`；其表中锚点 1 为 τ = 178.6 s、I∞ = 4.230 A（锚点 7：τ = 216.6 s、I∞ = 4.272 A）。对锚点 1，它的窗口与我们的窗口从同一个样本开始。 |
| 1b | "单看观测到的 CV 窗口，并不能看出电流衰减到零" | **成立** | 锚点 1–7 结束时 I = 5.094–5.100 A，此时电流仍在下降：结束前 60 s 为 5.66–5.88 A。窗口内看不出电流会在哪里趋平。 |
| 2a | 锚点 CV 段约 7 min、10 s 采样下约 40 个样本 | **部分成立** | 锚点 1–7：**438–530 s（7.3–8.8 min），45–54 个样本**。随老化变长：锚点 1–7 依次为 438、456、455、505、522、514、530 s。 |
| 2b | 补电 CV 段 2–9 min | **需修正** | 25 °C 补电：239–262 s（4.0–4.4 min，25–28 个样本）。45 °C 补电：112–176 s（1.9–2.9 min，13–19 个样本）。没有补电超过 4.4 min。 |
| 2c | 锚点 0（45 °C）CV 段 36 s，第 11 轮拟合失败 | **成立** | 锚点 0：37 s，5 个样本（I 从 13.26 降到 5.09 A）。第 11 轮拟合给出 τ = −152 886 s、I∞ = 31 853 A，即拟合失败。 |
| 3 | 41 次满充：8 次从空开始，33 次补电 | **成立** | 41 次充电进入 CV 段。8 个锚点（充入 91.97–100.13 Ah），33 次补电（20.63–21.75 Ah）；补电中 9 次在 25 °C、24 次在 45 °C。41 次全部按 CV 结束时间与第 8 轮的 `E00`–`E40` 对上。 |
| 4a | CK0 的 C/20 放电在 5.1 A 下从 13.590 V 开始，cell3 为 3.511 V | **成立** | CK0 第一个样本：−5.096 A 下 13.590 V；各电芯 3.374 / 3.351 / **3.511** / 3.359 V。 |
| 4b | 锚点 0 的顶部也由 cell3 决定（CV 结束 30 min 后 3.53 V） | **成立，且更普遍** | 锚点 0 在 +30 min：各电芯 3.385 / 3.358 / **3.530** / 3.371 V。**在全部 41 次满充中，cell3 在 CV 结束时和 +30 min 时都是最高的电芯。** |
| 4c | 电池组进入每次检查时为 13.1–13.3 V | **大致成立** | CK1、CK3–CK7 之前最后一个运行样本：13.190、13.220、13.200、13.440、13.270、13.257 V，都处于负载下（−8.6 到 +7.5 A）。六次中五次在 13.1–13.3 V；CK5 之前是 13.44 V，当时正以 7.5 A 充电。最后的静置电压为 13.07–13.37 V。CK2 之前没有数据（第 3 段缺失）。无论如何，电池组进入每次检查时都远未充满。 |
| 5 | 第 11 轮，电池组：末电流固定在 5.094–5.100 A；静置顶部电压持平（13.439 → 13.435 V） | **成立** | I_end 为 5.094–5.100 A；锚点 1–7 在 +30 min 的电池组电压依次为 13.439、13.438、13.435、13.434、13.432、13.434、13.435 V。cell3 在 +30 min 从 3.373 降到 3.366 V；cell1 和 cell4 的变化在 1–2 mV 以内。 |
| 6 | 粗算：I_end·τ ≈ 0.25 Ah（锚点 1）→ 0.31 Ah（锚点 7）；尾巴漂移约 0.05 Ah | **算术可复现；仍只是假设** | 用第 11 轮的 τ：5.094 × 178.6 s = 0.253 Ah；5.098 × 216.6 s = 0.307 Ah；差 0.054 Ah。但第 11 轮的 τ 来自 I∞ ≈ 4.2 A 的模型，而 I_end·τ 是衰减到**零**的指数（M1）的尾巴，是另一个模型。M1 是否拟合得上、τ 是多少，是 WP2 的问题。 |

目录中与 WP1 相关的其他事实：

- **CV 开始。** 按登记的定义（电池组 ≥ 13.95 V 且 I < 19.9 A），CV 开始是 CC→CV 切换后的第一个样本。锚点 1–7 在该样本的电流为 17.7–19.4 A，取决于切换落在两个 10 s 样本之间的哪个位置。
- **CV 电量（本轮定义）。** 即 CV 样本上 I 的梯形积分。锚点 1–7：1.146、1.169、1.167、1.293、1.362、1.315、1.369 Ah。第 11 轮报告的 1.17 → 1.44 Ah 用的是不同的窗口和矩形法。
- **脉冲前的静置。** 每次满充之后都有 1800–1801 s 的静置（|I| < 0.5 A），然后是 20.4 A 的放电脉冲。因此对全部 41 次充电，"+30 min"就是脉冲前最后一个静置样本。没有任何一次充电存在超过 600 s 的记录缺口。
- **CV 结束时的温度。** 锚点 1–7：26.9–27.2 °C。25 °C 补电：26.5–26.8 °C。45 °C 充电：46.3–46.9 °C。
- **SUB**（`6525edf`，包 CLI），单位 SOH %：CK0 98.441、CK1 95.984、CK2 94.507、CK3 93.600、CK4 92.821、CK5 92.015、CK6 91.426、CK7 90.765（[SUB_SOH.csv](SUB_SOH.csv)），与第 11 轮 WP0 完全一致。
