"""One-page Chinese Word render smoke for this task's document pipeline."""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

task = Path(__file__).resolve().parents[1]
out = task / "runs/V0_preflight_20260929/v0_chinese_smoke.docx"
doc = Document()
title = doc.add_paragraph("LFP 电池 SOH 验证文档烟雾测试", style="Title")
normal = doc.styles["Normal"]
normal.font.name = "PingFang SC"
normal.font.size = Pt(11)
normal._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "PingFang SC")
doc.add_paragraph("检查中文、公式文字、表格和页码排版。此页只用于 V0 环境测试，不包含容量模型结论。")
doc.add_paragraph("SOH = 100 × Q_ref / 102 Ah；CK0 为 100.41 Ah。")
table = doc.add_table(rows=2, cols=2, style="Table Grid")
table.cell(0, 0).text = "字段"
table.cell(0, 1).text = "本轮状态"
table.cell(1, 0).text = "容量真值"
table.cell(1, 1).text = "CK1–CK7 隐藏"
doc.save(out)
print(out, out.stat().st_size)
