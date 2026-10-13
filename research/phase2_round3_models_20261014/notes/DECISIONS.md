<a id="en"></a>

# Decisions

> English · [中文](#zh)

1. The branch already exists at 24728fa, directly after 886bfc1, with the prompt as its first commit. Resume it without rewriting history.

2. Read both archived literature documents. Retain identifiability profiles, temperature layering, loaded-template identity and first pack-voltage root; 37.3 kJ/mol is a fixed sensitivity prior, not independently validated for this pack.

3. Concurrent external commits c958688 and ce6ce01 completed stages 0/B while this executor was preparing the harness. Restored the original harness interface; the additional evaluator is harness_extended.py. Preserve completed stages; subsequent work uses the existing interface and avoids rewriting protocols.

---

<a id="zh"></a>

# Decisions

> [English](#en) · 中文

1. 分支已存在，24728fa 紧接 886bfc1，首提交为 prompt；继续使用，不改写历史。

2. 已读两份归档文献，保留可辨识性、温度分层、带载模板恒等和组端首根约束；37.3 kJ/mol 仅作固定先验。

3. 准备期间另一会话提交 c958688 与 ce6ce01，完成 0/B。已恢复原 harness 接口，补充评估器为 harness_extended.py；保留完成阶段和已有协议。
- DD.1 Stage D D2: throughput across a gap is estimated from the visible 45 C daily discharge rate, because the counter jump is not visible before the checkup (deviation from prompt wording, causality takes precedence).
- DD.2 Stage D selection: chosen D0 (PG1+PG2 MAE D0 0.229, D1 0.361, D2 0.381; D3 0.217 but undefined for CK2, not selectable). Exposure note: PC5/PC10 at k=2 contain no rows after 17 Feb, so they equal the real CK2 cut; their D1/D2 CK2 values (-1.43/-1.05 pp) were printed by run_select.py before this commit. The selection rule used PG1+PG2 only.
