<a id="en"></a>

# DECISIONS (round 7)

> **Language:** English · [中文](#zh)

- **D0.1 (WP0).** The sqrt_gap branch depends only on the anchors and dates, so PG1, PG2 and PC10 give identical SUB predictions at the same k (and PC10 equals PC10_all for k ≥ 3). The distinct non-real cases are k = 3..7 of the cut family (PG1/PG2/PC10) and k = 3..7 of CSE (anchors before k−1 removed). The CK2 cases of PC5_all/PC10_all are the real CK2 again and are exposed. WP2 registers its gap-case metric on these distinct cases.
- **D1.1 (WP1, exposure).** The two inputs of P1 (3a residual r_j and 3c offsets) were visible in round 6's committed outputs and were printed during prompt preparation, before the WP1 protocol was registered. The correlation between them was never computed before registration. P1 is therefore labelled "inputs seen, statistic not seen".
- **D1.2 (WP1, amendment 1).** Column (f) is not measurable (program-opening CCCV charges are about 21 Ah from 13.4 V and do not cross the step; recharges are dynamic). Li accounting shows the anchor Q_fc is not changed by an overhang release, while the rest voltage, r_j and the bottom section are; P1/P3/classification/H_ov were re-registered accordingly before computing (protocol.json amendment_1).

---

<a id="zh"></a>

# 决策记录（第七轮）

> **语言：** [English](#en) · 中文

- **D0.1（WP0）。** sqrt_gap 分支只依赖锚点和日期，所以 PG1、PG2、PC10 在同一 k 上给出相同的 SUB 预测（k ≥ 3 时 PC10 也等于 PC10_all）。不同的非真实案例只有截断族（PG1/PG2/PC10）的 k = 3..7 和 CSE（去掉 k−1 之前的锚点）的 k = 3..7。PC5_all/PC10_all 的 CK2 案例就是真实 CK2，属于已曝光。WP2 在这些不同案例上登记缺口案例指标。
- **D1.1（WP1，曝光）。** P1 的两个输入（3a 剩余电量 r_j 和 3c 偏移）在第六轮已提交的输出中可见，并在编写 prompt 时打印过，早于 WP1 协议登记；但两者的相关性在登记前从未计算。因此 P1 标为“输入已见、统计量未见”。
- **D1.2（WP1，修订 1）。** 列 (f) 无法测量（程序开头的 CCCV 充电只有约 21 Ah、从 13.4 V 开始，不越过台阶；回充是动态的）。锂库存推导表明 overhang 释放不改变锚点 Q_fc，但会改变静置电压、r_j 和底段；据此在计算前重新登记了 P1/P3/分类/H_ov（protocol.json 的 amendment_1）。
