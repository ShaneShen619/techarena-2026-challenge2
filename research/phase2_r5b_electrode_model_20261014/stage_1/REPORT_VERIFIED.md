<a id="en"></a>

# Stage1 — verified interpretation and deviations

> English · [中文](#zh)

**Surrogate synthetic numerical gates pass; real-electrode interpretation remains unsupported.** Exposed-exploratory; no hidden labels. This clarification qualifies the preserved original [REPORT.md](REPORT.md): the electrode equations match, but the complete implementation does not exactly meet the current-replay and hard-domain rules.

| Quantity | Median absolute recovery error | Unit |
| --- | --- | --- |
| Q_C20 | 0.033667 | Ah |
| beta_E | 0.070505 | dimensionless |
| Q_fc | 0.040155 | Ah |
| LLI | 0.173480 | Ah |
| LAM_NE fraction | 0.255309 | percentage points of reference electrode capacity |
| LAM_PE fraction | 0.071010 | percentage points of reference electrode capacity |

All 30 states are finite. LAM recovery uses the saved per-cell-normalized fraction errors in percentage points; the original run did not retain per-state individual electrode fits, so exact mean-cell Ah recovery errors cannot be reconstructed and are not invented. The synthetic input is model-generated10-s CCCV, not the specified measured anchor1 current. The start shift is uniform±30mV, not an empirical observed-start-range sample. Therefore the numeric gate is a surrogate pass, not confirmation of the exact prescribed experiment or these cells' mechanism.

The144-start two-phase solver, ideal-current CCCV, development fit before registration, soft state penalties, endpoint clipping and negative-total-R floor are disclosed in the final report. The independent invalid-theta test produced a finite legacy charge despite theta_n0=1.2; legacy simulation is unsuitable for arbitrary accepted targets. Stage3 preregistered strict domain rejection and rejects the negative-R anchor0 chain. Completed originals are preserved, not overwritten or retroactively called compliant.

OCP source version/functions and full BSD-3 licence are in [../ocp/](../ocp/). Anchor1 main/alternative/dVdQ fits hit Qp200Ah and have strongly autocorrelated residuals. These observations suggest mismatch/confounding, not unique evidence of an ageing mechanism. See [final report](../FINAL_REPORT.md) for the CK0/free-start versus full-chain distinction and registered no-model exit.

---

<a id="zh"></a>

# Stage1 — verified interpretation and deviations

> [English](#en) · 中文

**替代合成实验的数值门通过，真实电极机理仍无支持。** 已曝光探索性（exposed-exploratory），无隐藏标签。本澄清限定保留的原[REPORT.md](REPORT.md)：电极方程相同，不代表完整实现精确满足电流回放和硬有效域要求。

| Quantity | Median absolute recovery error | Unit |
| --- | --- | --- |
| Q_C20 | 0.033667 | Ah |
| beta_E | 0.070505 | dimensionless |
| Q_fc | 0.040155 | Ah |
| LLI | 0.173480 | Ah |
| LAM_NE fraction | 0.255309 | percentage points of reference electrode capacity |
| LAM_PE fraction | 0.071010 | percentage points of reference electrode capacity |

30状态均有限。LAM恢复误差用原保存的逐芯归一比例，以百分点报告；原运行未保留各状态逐芯电极拟合，不能重建精确平均Ah恢复误差，也不编造。合成输入为自身10s CCCV，非要求的锚点1实测电流；起点±30mV均匀扰动，非实测起点范围抽样。因此只称替代数值门通过，不确认原实验或真实电芯机制。

144起点分段搜索、理想电流CCCV、登记前开发拟合、软域罚项、端点截值及负总R下限均在最终报告披露。独立测试theta_n0=1.2仍得到有限旧充电结果，故旧模拟器不能用于任意接受目标。阶段3预登记硬域拒绝并拒绝负R锚点0链；保留原完成文件，不覆盖，也不事后称其合规。

OCP函数版本及完整BSD-3许可证见[../ocp/](../ocp/)。锚点1主/备选/dVdQ拟合撞Qp200Ah边界、残差强自相关，提示失配/混淆，不能唯一证明退化机制。完整CK0起点与链条区别及登记退出见[最终报告](../FINAL_REPORT.md)。
