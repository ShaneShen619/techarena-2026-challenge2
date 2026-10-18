<a id="en"></a>

# Round 11 — ε transfer study

> English · [中文](#zh)

**Outcome: O3 "inconclusive". d ∈ [−0.036, +0.052] Ah/Ah; the dominant term is T_path; the submission is unchanged.** See [FINAL_REPORT.md](FINAL_REPORT.md).

| Path | Content |
|---|---|
| `EXECUTION_PROMPT.md` | the executed prompt (SHA256 6147cec9…) |
| `notes/` | STATUS, DECISIONS |
| `sources/` | copied inputs with SHA256 (`SOURCES.md`) |
| `src/` | all scripts. External data are read with `python3 -I -B` and path arguments. |
| `wp0/` … `wp6/` | protocol (committed before outputs), REPORT, outputs |
| `wp5/R12_HANDOFF.json` | input for round 12 |
| `cache/` | git-ignored: LIC npz cache, Yagci extracts, package runs, Figgener metadata |

**Reproduce:**

```
python3 -I -B src/lic_cache.py <LIC_aging_data.csv> cache/lic.npz
python3 -I -B src/lic_seg.py cache/lic.npz cache/lic_segments_all.csv
python3 -I -B src/lic_audit.py cache/lic_segments_all.csv cache/lic.npz wp1/lic_sequence.csv wp1/lic_rpt_summary.csv
python3 -I -B src/wp2_lic.py .
python3 -I -B src/eps_yagci_r7copy.py <yagci Data dir> cache/r7_repro
python3 -I -B src/wp3_ext.py . <Gotion Capacity_Calibration_Cell_data.xlsx>
python3 -B src/wp4_pack.py . <package data dir>
python3 -B src/wp5_decide.py .
```

WP0 needs the two package runs in `cache/out_*` (see `wp0/REPORT.md`).

---

<a id="zh"></a>

# 第 11 轮 — ε 迁移研究

> [English](#en) · 中文

**结果：O3"无定论"。d ∈ [−0.036, +0.052] Ah/Ah，主导项为 T_path，提交不变。** 详见 [FINAL_REPORT.md](FINAL_REPORT.md)。

目录：
- `EXECUTION_PROMPT.md`：执行的 prompt；
- `notes/`：STATUS 与 DECISIONS；
- `sources/`：复制来的输入及其 SHA256；
- `src/`：全部脚本；
- `wp0/` … `wp6/`：各 WP 的协议（先于输出提交）、报告和输出；
- `wp5/R12_HANDOFF.json`：第 12 轮的输入；
- `cache/`：被 git 忽略的缓存。

复现命令见英文部分。
