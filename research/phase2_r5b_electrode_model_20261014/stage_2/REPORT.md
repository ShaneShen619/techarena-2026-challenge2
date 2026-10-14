<a id="en"></a>

# Stage 2 — CK0 held-out tail check

> English · [中文](#zh)

Exposed-exploratory; proxies are not hidden capacity truth. CK0 is the only released capacity label. Protocol was committed as 1173340 before the evaluation artifacts.

Main reference is anchor0 at 45 C, with 25-C literature OCPs. The fixed-health discharge fit uses only 5–85.412 Ah, with the final 15 Ah withheld. Main root: 100.698604 Ah; error from 100.41 Ah: +0.288604 Ah, and from 100.416854 Ah: +0.281750 Ah. Per-cell step differences: [0.21800000000000352, 0.044000000000004036, 0.23499999999999943, 0.1319999999999979] Ah. The registered scalar credibility gate passes.

Held-out tail RMS: [23.39923016240788, 23.929638844247766, 25.77308126561922, 24.130544512544294] mV. Lowest-voltage cell at the group root: cell 3. The anchor1 reference variant predicts 107.476813 Ah and fails credibility.

The separately fitted CK0 start state is not the anchor's simulated full-charge end state. The latter chain gives 102.398747 Ah and raw epsilon 2.276360 Ah, versus observed epsilon0 0.287614 Ah. This mismatch is not repaired by the scalar gate. The legacy CCCV simulator floors a negative fitted total resistance to 1e-6; this convention is not the prescribed physical CV equation and is independently audited. Stage3 uses explicit validity checks and does not promote an undefined physical chain.

Code/data: run_2.py, outputs/S2_ck0_check.json and the two prediction-curve CSVs. Existing fit parameters and the registered main configuration are retained unchanged.

---

<a id="zh"></a>

# Stage 2 — CK0 held-out tail check

> [English](#en) · 中文

已曝光探索性研究；代理不是隐藏容量真值。CK0 是唯一公开容量标签。协议在 1173340 提交，早于评估产物。

主参考为45℃锚点0，OCP 来自25℃文献。固定健康参数后只用 5–85.412 Ah 拟合放电，最后15 Ah 留出。主首根 100.698604 Ah，相对100.41偏差 +0.288604 Ah，相对100.416854偏差 +0.281750 Ah。四芯台阶偏差 [0.21800000000000352, 0.044000000000004036, 0.23499999999999943, 0.1319999999999979] Ah，登记的标量可信度门通过。

留出尾段 RMS [23.39923016240788, 23.929638844247766, 25.77308126561922, 24.130544512544294] mV，组端首根时最低电压为电芯 3。锚点1参考变体预测 107.476813 Ah，不通过可信度门。

独立拟合的 CK0 起点并非锚点模拟满充末端；后者预测 102.398747 Ah，原始 ε=2.276360 Ah，公开 ε0=0.287614 Ah。标量门不能消除这个链条差异。旧 CCCV 模拟器将拟合负总电阻截成1e-6，该约定不符合规定的物理恒压方程，已独立审计；阶段3明确检查有效性，不提升无定义物理链条。

代码/数据为 run_2.py、outputs/S2_ck0_check.json 及两张预测曲线 CSV；原拟合参数及主配置保持不变。
