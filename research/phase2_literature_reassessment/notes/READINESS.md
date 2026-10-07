# L0 环境与数据预检（2026-09-29）

状态：研究和中文 Word 实际生成可执行；标准 `render_docx.py` 由于本机无 LibreOffice `soffice`，已用安装的 Microsoft Word 作实际 DOCX→PDF→逐页 PNG 替代通道。后续长文仍需逐页人工核查；此处的一页烟雾测试不等于终稿验收。未修改全局配置或既有训练环境。

| 项目 | 实测 | 证据/备注 |
|---|---|---|
| 写入、存储 | 本轮目录可写；检查时剩余约 109 GiB | 本轮 `tmp/preflight/smoke.csv/.json/.bib/.docx` 已写 |
| 公开检索 | `web.run` 对出版平台、作者/机构、arXiv 三类入口返回页面 | 实际 query 与结果后续入 `search_queries.csv`；摘要不作方法证据 |
| 合法全文 | `papers/A_partial_temperature/Krupp2021.pdf` 可 `pdfinfo`，本轮另从 Chalmers 机构公开下载 `papers/D_trajectory/Zhang2024_knee_curvature.pdf` | 有一条错误 DLR URL 返回 HTTP 401，换公开来源，无绕过 |
| PDF 提取/公式页 | `pdftotext -layout` 对上述论文完成；`pdftoppm` 渲染 Krupp 第 2 页和 Zhang 第 4/5 页；人工查看公式与文字 | Zhang 文件有 PDF 字典语法警告，但提取/渲染成功；以原页为准 |
| CSV/JSON/BibTeX | 使用 Python 实际写入并读取 | `tmp/preflight/smoke.*`；中文 UTF-8 成功 |
| 中文 Word | `python-docx` 实际创建含中文标题、公式文字、表格的 `.docx`；Microsoft Word 导出 1 页 PDF，`pdftoppm` 出图并人工查看，中文无缺字 | `tmp/preflight/smoke_word.png`；本机 Python3.13 系统默认无 docx，采用本轮 `tmp/docenv` 隔离环境；旧 `phase2_validation/.venv` 只用于只读研究脚本 |
| 标准渲染器 | `render_docx.py` 首次缺 `pdf2image`，本轮隔离环境安装后缺 `soffice`，因此不能按原脚本走 LibreOffice | 采用本机 Word 实际排版替代，最终报告透明记录这一限制；不声称标准脚本成功 |
| 数据/测量 | CK0 70,876 行，19.687 h，参考曲线末值 100.412 Ah；首段 171,541 行，有重复时间戳/小缺口 | `runs/L0_measurement_20260929/result.json` 与脚本、输入哈希；只读原始数据 |

## 环境命令与恢复

研究脚本：`research/phase2_validation/.venv/bin/python research/phase2_literature_reassessment/scripts/l0_measurement_audit.py`。Word 生成与包：`research/phase2_literature_reassessment/tmp/docenv/bin/python`；只在本轮 `tmp/` 隔离目录安装 `python-docx pdf2image pillow pypdf pdfplumber reportlab`。要重建，使用 `python3 -m venv research/phase2_literature_reassessment/tmp/docenv` 后在此 venv 安装上述固定工作集；产物的脚本哈希和依赖版本在 `REPRODUCE.md` 冻结。

Word 导出采用 AppleScript 调用本机 Microsoft Word：打开本地 DOCX，`save as ... file format format PDF`，关闭文档；再 `pdfinfo`、`pdftoppm`。每份终稿应对所有页绘制缩略图审查，并针对拥挤/公式/表格页看原分辨率。任何导出失败不标记渲染通过。

网络下载设置 `curl --fail --retry 2 --connect-timeout 15 --max-time 90`；下载失败记录 URL/状态，试合法机构版或 HTML。任务与下载都保留中间文件，不因机器休眠或会话中断保证后台持续；恢复从 `notes/RESUME.md` 与 `TASK_LEDGER.csv` 继续，先核对已有哈希避免重复获取。
