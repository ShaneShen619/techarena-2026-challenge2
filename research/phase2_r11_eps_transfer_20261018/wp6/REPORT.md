<a id="en"></a>

# WP6 — Figgener home-storage data (zenodo 12091223): skipped

> English · [中文](#zh)

**Result: skipped. The capacity-test protocol is not included, and the LFP systems with tests need 6.2 GB, above the 3 GB cap.**

| Screening condition | Result | Evidence |
|---|---|---|
| At least one LFP system | ✓ | `Metadata_Systems.xlsx`: IDs 14–21 are LFP, manufacturer E, 14S–16S packs, 158–300 Ah |
| Field capacity tests included, with protocol | ✗ | `Capacity_Tests.xlsx` lists only test **start times** (LFP: IDs 14, 15, 17, 19, 20, 21; 19 tests). No capacity values and no protocol (C-rate, cutoffs, temperature) are in the data. Per the record description, the protocol is in the paper's supplementary information. |
| Operating charge data around the tests | probably (not verified) | 1-s system-level current and voltage in the monthly files; no cell voltages |
| Total download ≤ 3 GB | ✗ | the six LFP systems with tests need 6.2 GB (ID 14 1.84, 15 0.81, 17 0.58, 19 0.63, 20 1.10, 21 1.25 GB) |

- Only the record's API metadata and the 31 kB `Metadata_and_Code.zip` (md5 checked) were downloaded, into `cache/downloads/figgener_meta/`. No `.m` file was run.
- **Possible follow-up, outside this round:** read the test protocol from the SI, then use a ≤ 3 GB subset (IDs 15, 17, 19: 2.0 GB, 10 tests). These are real LFP packs with pack-voltage limits, so they could also inform the imbalance term that round 11 could not assess.

---

<a id="zh"></a>

# WP6 — Figgener 家储数据（zenodo 12091223）：跳过

> [English](#en) · 中文

**结果：跳过。数据中不含容量测试协议，而且有测试的 LFP 系统需要下载 6.2 GB，超过 3 GB 上限。**

- **至少一个 LFP 系统：✓。** ID 14–21 为 LFP（厂商 E，14–16 串，158–300 Ah）。
- **包含现场容量测试及其协议：✗。** `Capacity_Tests.xlsx` 只列出测试**开始时间**（LFP 为 ID 14、15、17、19、20、21，共 19 次）。数据中没有容量值，也没有协议（倍率、截止条件、温度）。按记录说明，协议在论文的补充材料里。
- **测试前后的运行充电数据：** 很可能有（未核实）。月度文件中有 1 s 的系统级电流和电压，但没有电芯电压。
- **总下载量 ≤ 3 GB：✗。** 有测试的六个 LFP 系统共需 6.2 GB。
- 只下载了记录的 API 元数据和 31 kB 的 `Metadata_and_Code.zip`（已校验 md5），放在 `cache/downloads/figgener_meta/`，没有运行任何 `.m` 文件。
- **可能的后续工作（不在本轮）：** 先从补充材料中读到测试协议，再用 ≤ 3 GB 的子集（ID 15、17、19：2.0 GB，10 次测试）。这些是带电池组电压限制的真实 LFP 电池组，也有助于评估本轮没能评估的电芯不一致项。
