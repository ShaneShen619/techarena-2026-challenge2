"""Assemble all canonical source cards verbatim, with provenance and version policy."""
import csv
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((TASK/'outputs/paper_registry.csv').open(encoding='utf-8')))
canonical=[r for r in rows if not r['version_duplicate_of']]
out=TASK/'outputs/LFP_SOH_核心论文精读与证据附册.md'
with out.open('w',encoding='utf-8') as f:
 f.write('# LFP SOH 第二阶段核心论文精读与证据附册\n\n')
 f.write('版本：2026-09-29。此附册汇集每篇原始证据卡全文，不把版本重复计为独立研究。卡片内容是研究笔记；作者报告、原文核对、本地重算和独立组容量验证不能互换。主报告只引用与决策相关的结论；原文 PDF/HTML 和每卡来源定位可供追溯。旧版/重复卡仍保存在 `notes/workstreams/`。\n\n')
 f.write(f'收录 {len(canonical)} 项独立研究的完整卡片；另外 {len(rows)-len(canonical)} 张不同工作流或版本重复卡不重复计数。\n\n')
 for i,r in enumerate(canonical,1):
  p=TASK/r['card_path'];s=p.read_text(encoding='utf-8',errors='replace').strip()
  f.write(f'\n## {i}．{r["paper_id"]}｜{r["title"]}\n\n')
  f.write(f'来源卡：`{r["card_path"]}`。书目身份：`{r["identity"] or "见卡片"}`。\n\n')
  lines=s.splitlines()
  if lines and lines[0].startswith('# '):
   lines=lines[1:]
  for line in lines:
   if line.startswith('#'):
    level=len(line)-len(line.lstrip('#'))
    f.write('#'*min(level+2,6)+line[level:]+'\n')
   else:f.write(line+'\n')
  f.write('\n')
print('annex canonical cards',len(canonical),'bytes',out.stat().st_size)
