<a id="en"></a>

# WP3 — Probe package and hand-over (no upload)

> **Language:** English · [中文](#zh)

## Conclusions

- **One validated probe zip exists:** `cache/packages/P_A3fix/Current State_Challenge2.zip`, SHA256 `3d792662…72e6`, 18 files, 3.75 MB ([packages.csv](packages.csv)).
  - `validate_submission.py` **passed** in a fresh Python 3.11.14 venv (numpy 2.4.6, pandas 3.0.6).
  - The full-data output **equals** P_A3fix's own vector: CK4 92.461, CK5 91.987, CK6 91.410, CK7 90.750; CK1–CK3 as SUB.
- **The diff against SUB is the registered hook plus one docstring line**, and the README gains one disclosure section. Nothing else differs from the base package ([staging.json](staging.json)).
- **Presentation warning:** the zip carries the template presentation, because `inputs/pptx_path.txt` = "template". The current SUB zip does too.
- **Nothing was uploaded.** The zip lives in the git-ignored `cache/`, and the Desktop and the existing zips were not touched. The user's next steps are in [HANDOVER.md](HANDOVER.md).

## Steps

1. Staging (`src/wp3_stage.py`): a full copy of the base package in `cache/pkg_P_A3fix/`. `model_template.py` = the registered research copy (round 12's hook via `src/variants.py`) plus the docstring line "Leaderboard probe variant P_A3fix: anchor 3 (segment 6) charge minus a_3^rel = 0.3047 Ah (round 12)." The README section "Leaderboard probe variant (P_A3fix)" is inserted before "Method". The staged copy reproduces the WP2 vector through the CLI.
2. Packaging: `src/package_submission.py` is the base script with exactly three changes (`PKG` → `cache/pkg_P_A3fix`, `EXPECTED_SOH` → P_A3fix's CLI output, `--out` default → `cache/packages/`). It was run with `"Current State" --members "Mona Zhu, Zhikuan Shen" --pptx <template> --out cache/packages/P_A3fix` ([build_log_P_A3fix.txt](build_log_P_A3fix.txt)).
3. Hashes: [packages.csv](packages.csv) (`src/wp3_packages.py`).
4. Hand-over: [HANDOVER.md](HANDOVER.md).
5. `FINAL_REPORT.md` and `README.md` in the study folder.

| Diff line (base → probe `model_template.py`) |
|---|
| `+Leaderboard probe variant P_A3fix: anchor 3 (segment 6) charge minus a_3^rel = 0.3047 Ah (round 12).` |
| `+    top = _charge_step_to_top(seg, i, ah, start, end, q)` |
| `+    if int(seg["segment"].iloc[0]) == 6:   # research copy (round 12 WP4): anchor-3 bottom correction a_3^rel` |
| `+        q = q - 0.3047` |
| `-        "top": _charge_step_to_top(seg, i, ah, start, end, q),` |
| `+        "top": top,` |

---

<a id="zh"></a>

# WP3 — 探针包与交接（不上传）

> [English](#en) · 中文

## 结论

- **已有一个通过验证的探针 zip：** `cache/packages/P_A3fix/Current State_Challenge2.zip`，SHA256 `3d792662…72e6`，18 个文件，3.75 MB（[packages.csv](packages.csv)）。
  - `validate_submission.py` 在全新的 Python 3.11.14 venv（numpy 2.4.6、pandas 3.0.6）中**通过**。
  - 全量数据输出与 P_A3fix 自己的向量**一致**：CK4 92.461、CK5 91.987、CK6 91.410、CK7 90.750；CK1–CK3 与 SUB 相同。
- **与 SUB 的差异只有登记的钩子加一行文档字符串**，README 增加了一节披露。其余与基点包完全相同（[staging.json](staging.json)）。
- **演示文稿警告：** 由于 `inputs/pptx_path.txt` = "template"，zip 里是模板演示文稿。当前 SUB 的 zip 也是如此。
- **没有上传任何东西。** zip 放在 git 忽略的 `cache/` 中，没有动桌面和现有的 zip。用户的下一步见 [HANDOVER.md](HANDOVER.md)。

## 步骤

1. 暂存（`src/wp3_stage.py`）：在 `cache/pkg_P_A3fix/` 中放一份基点包的完整副本。`model_template.py` = 登记的研究副本（通过 `src/variants.py` 应用第 12 轮的钩子）加一行文档字符串。README 在 "Method" 之前插入 "Leaderboard probe variant (P_A3fix)" 一节。暂存副本通过 CLI 复现了 WP2 的向量。
2. 打包：`src/package_submission.py` 是基点脚本，只改了三处（`PKG` → `cache/pkg_P_A3fix`，`EXPECTED_SOH` → P_A3fix 的 CLI 输出，`--out` 默认 → `cache/packages/`）。运行参数为 `"Current State" --members "Mona Zhu, Zhikuan Shen" --pptx <模板> --out cache/packages/P_A3fix`（[build_log_P_A3fix.txt](build_log_P_A3fix.txt)）。
3. 哈希：[packages.csv](packages.csv)（`src/wp3_packages.py`）。
4. 交接：[HANDOVER.md](HANDOVER.md)。
5. 研究目录中的 `FINAL_REPORT.md` 和 `README.md`。

差异行见英文部分的表。
