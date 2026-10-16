<a id="en"></a>

# Round 7 — literature-driven checks

> **Language:** English · [中文](#zh)

Tests three findings of the 2026-10-16 literature refresh against the submitted model SUB (V2 + √t gap branch). Base: round 6 (`e144086`). Nothing is wired into the submission.

**Results:** [FINAL_REPORT.md](FINAL_REPORT.md).
- WP2: temperature-weighted √t passes all gates → recommend switching (CK2 +0.057 pp).
- WP1: overhang explanation of the post-anchor offset not supported.
- WP3: ε-drift sign not robust → probe P_drift last.

| Path | Content |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | the execution prompt (English governs) |
| [notes/](notes/) | STATUS, DECISIONS |
| [sources/](sources/) | copied sources with SHA256 (round 6 code, v3, literature refresh, TUM check) |
| [src/](src/) | round-6 code copies (`common6.py` adjusted), `grid7.py`, `audits6.py`, `tsqrt.py` |
| [wp0/](wp0/REPORT.md) … [wp5/](wp5/REPORT.md) | protocol, scripts, outputs, report per work package |
| [wp2/candidate_model/](wp2/candidate_model/model_template.py) | T_main candidate class (research copy, not wired) |
| [report_material/risk_addendum.md](report_material/risk_addendum.md) | risk paragraphs for the submission REPORT |
| `cache/` | git-ignored: archived package, Python 3.11 venv, package copy |

Reproduction: see [FINAL_REPORT.md](FINAL_REPORT.md#reproduction).

---

<a id="zh"></a>

# 第七轮——文献驱动的检验

> **语言：** [English](#en) · 中文

在提交模型 SUB（V2 + √t 缺口分支）上检验 2026-10-16 文献更新的三项发现。基于第六轮（`e144086`），没有接入提交。

**结果：** 见 [FINAL_REPORT.md](FINAL_REPORT.md)。
- WP2：温度加权 √t 通过全部门槛 → 建议切换（CK2 +0.057 pp）。
- WP1：锚点后偏移的 overhang 解释不被支持。
- WP3：ε 漂移符号不稳健 → P_drift 放到最后探测。

目录说明见英文部分的表格。
