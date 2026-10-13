<a id="en"></a>

# Independent execution review

> English · [中文](#zh)

Exposed-exploratory; proxies are not hidden truth.

The initial baseline/B commits appeared concurrently during preparation. The original harness was restored and its interface retained. Supplementary evaluation lives in harness_extended.py; stage_0 contains an independent audit and Python 3.11 candidate verifier.

Stage D selection.json was committed as 816a21d before run_eval.py computed real-data metrics. However run_select.py includes PC5/PC10 CK2 scenarios: their operation data are identical to real CK2 (confirmed in scenario_exposure_audit.json). Hence the instruction to commit selection before computing CK2 results was violated even though selection uses only PG1/PG2 and no CK2 tuning was observed. D remains diagnostic and does not supply a passing replacement: D0 was retained.

The D2 registered implementation also deviates from the specified beta-converted step observations: it uses M4 beta=1 step changes. Missing-gap throughput uses a visible-data rate because the post-gap counter jump is unavailable at CK2. The latter is causally conservative and documented; neither difference should be concealed as exact execution of the original D2 formula.

Independent checks must use exact floating-point equality for both future-noise and fit-prefix comparisons. Rounded comparisons alone do not establish bit identity. Scope and protocol hashes are audited separately.

---

<a id="zh"></a>

# Independent execution review

> [English](#en) · 中文

已曝光探索性研究；代理不是隐藏真值。

准备时阶段 0/B 被另一会话并发提交。已恢复原 harness 接口；补充评估位于 harness_extended.py，stage_0 提供独立审计和 Python 3.11 验证器。

阶段 D 在 816a21d 提交选择后才运行实际指标评估。但 run_select.py 的 PC5/PC10 CK2 情景与实际 CK2 数据完全相同（已在 scenario_exposure_audit.json 核验），所以“选择提交前不得计算 CK2 结果”的顺序要求受到违反。选择仍只使用 PG1/PG2，未观察到对 CK2 调参。D0 被保留，阶段 D 不提供通过验收的替代模型。

D2 登记实现另有公式偏差：台阶观测使用 M4 的 β=1，而非要求的 β 换算。缺段吞吐量使用可见数据速率，是因为 CK2 时看不到缺段后的计数器跳变；这个选择保持因果性并已记录，但两项差异均不能表述为原公式的精确执行。

未来噪声和 fit 前缀验证都必须比较浮点值的精确相等，单凭三位小数输出相等不满足逐位一致要求。另独立检查修改范围和协议哈希。
