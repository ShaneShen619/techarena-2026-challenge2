"""Create a traceable, complete research-history document from retained evidence."""
from pathlib import Path
import os, re, csv, json, hashlib, math, textwrap
from collections import Counter
from datetime import datetime
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OUT=Path('/Users/shane/Desktop/LFP电池SOH第二阶段完整研究总报告_20261006.docx')

STAGES=[
 ('最初文献调查','phase2_literature',[
  ROOT/'research/phase2_literature_reassessment/archive/phase2_literature_before_20260929T230323/outputs/LFP_SOH_第二阶段文献综述与技术路线.md'],
  '本章为九月二十八日最初路线选择。原综述后来被深度重评替换，此处从留存归档恢复。首选和备选是当时研究假设，后续试验及纠错见其后各章。'),
 ('双方案设计实现和验证','phase2_validation',[
  ROOT/'research/phase2_validation/outputs/LFP_SOH_双方案设计验证与比较报告.md'],
  '本章完成 A 与 B 的实际原型、十八点单芯代理、合成和工程测试。该面板不同于后来的一百八十点。保留首次失败和修复，不将工程通过等同容量准确。'),
 ('温度修复和深充容量映射','phase2_temperature_improvement',[
  ROOT/'research/phase2_temperature_improvement/outputs/方案A_温度修复与提升报告.md',
  ROOT/'research/phase2_temperature_improvement/reassessment_20260928/REEVALUATION.md'],
  '先呈现温度修复和多窗口开发，随后直接附当日复评。约一点零四 pp 是完整深充代理成绩，官方浅充使用的是未确认的备用分支。温度面跨官方设备约十摄氏度的迁移偏差在后轮明确。'),
 ('严格浅充多路线研究','phase2_method_exploration',[
  ROOT/'research/phase2_method_exploration/outputs/LFP_SOH_多路线设计验证与比较报告.md'],
  '本章正式结论以严格 v1.5 为准。补充模块与运行台账同时保留 v1.4 和失败版本，若其资格看过完整事件，则只作为退役开发记录，不进入当前浅充排名。'),
 ('下一轮逐路线反证和尾部验证','phase2_next_round',[
  ROOT/'research/phase2_next_round/outputs/LFP_SOH_下一轮逐路线验证与决策报告.md'],
  '本章拆分波形、温度、元数据、截取终点和末期权重。严格去温度的平均领先是外层探索观察，尾部更差且未通过内层实体选模，不应当作已锁定官方候选。'),
 ('文献深度重评和路线重排','phase2_literature_reassessment',[
  ROOT/'research/phase2_literature_reassessment/outputs/LFP_SOH_第二阶段文献综述与技术路线_深度重评.md'],
  '本章为九月二十九日证据重评，包含十二类方法、八个问题、九张路线卡。原始论文和数据检查是历史记录，并未在本次重新联网核验。三十三篇详细精读卡集中在后面的论文证据附录。'),
 ('文献驱动双路线实证验证','phase2_evidence_validation',[
  ROOT/'research/phase2_evidence_validation/outputs/LFP_SOH_文献驱动验证与双路线决策报告.md'],
  '本章实际检验 R02 与 R05。R02 官方容量更新门关闭；R05 采样温度历史未胜出等维非温度对照。初版事件计数器与 R02 扫描问题均保留修正记录。'),
 ('官方局部充电基线修复','phase2_baseline_repair',[
  ROOT/'research/phase2_baseline_repair/outputs/LFP_SOH_官方基线修复与下一步决策报告.md'],
  '本章修复明确的 CK1 未来参考引用。原文三十五组覆盖所有存在未来行 CK 的说法后来被更正，CK7 后仍有未来行，以下一章的全八 CK 补测为准。大窗口不是已证实积分错误。'),
 ('真实容量接入和异协议单芯验证','phase2_capacity_validation',[
  ROOT/'research/phase2_capacity_validation/outputs/LFP_SOH_真实容量验证与测量计划.md'],
  '本章补全因果覆盖，建立容量接入与一次性评分。八封存单芯零点一三八一 Ah 结果限定为异协议探索，研究者曾看见文件名容量，不称真正盲法。官方七个隐藏检查点和同协议四串性能继续不可测。'),
 ('十月六日官方原始数据追加审计','official_temperature_review_20261006',[
  ROOT/'官方温度数据分析总结_20261006.md',
  TASK/'sources/official_data_record_extracted.md'],
  '本章追加温度与端点分析。温度部分重复信息不重复印刷，随后完整保留新增充放电章。旧示例的阈值局部窗口和本轮完整充电事件边界不同，四十四至五十九 Ah 与九十二至一百 Ah 并不矛盾。全量离线趋势含 CK7 后记录，不能直接回填早期 CK。'),
]

EXTRA_NAMES={'DECISIONS.md','FAILURES.md','FINAL_AUDIT.md','INDEPENDENT_AUDIT.md',
 'PREREGISTRATION.md','INFORMATION_BUDGET.md','SOURCE_CORRECTIONS.md',
 'AUDIT_CORRECTIONS.md','PROJECT_EVIDENCE_AUDIT.md','INDEPENDENT_EVIDENCE_AUDIT.md',
 'INDEPENDENT_EVIDENCE_AUDIT_ADDENDUM.md','INDEPENDENT_EVIDENCE_AUDIT_FINAL_ADDENDUM.md',
 'V0_DATA_QUALIFICATION.md','V5_CONDITIONAL_ROUTES.md','R02_MATH_PREFLIGHT.md','R05_FEATURE_PREFLIGHT.md',
 'ASSUMPTIONS.md','ASSUMPTIONS_AND_OPEN_ITEMS.md','M2_PRELIMINARY.md','DATA_GAPS.md','DATA_SEARCH_LOG.md',
 'CITATION_FOLLOWUP.md'}
OUTPUT_EXTRA={'MEASUREMENT_PLAN.md','measurement_plan.md','D2_MEASUREMENT_PROTOCOL.md',
 'DATA_HANDOFF.md','MECHANISM_FINDINGS.md','PRIOR_EVIDENCE_CORRECTIONS.md','SEARCH_COVERAGE.md',
 'EXPERIMENT_ROADMAP.md','OLD_TO_NEW_CHANGELOG.md'}

used=[]; missing_images=[]; figure_count=0; table_count=0; bookmark_id=1; toc=[]
doc=Document();sec=doc.sections[0]
sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(1.85);sec.bottom_margin=Cm(1.85)
sec.left_margin=Cm(1.95);sec.right_margin=Cm(1.95)
sec.header_distance=Cm(.7);sec.footer_distance=Cm(.8)
for name,size,bold in [('Normal',10.5,False),('Title',25,True),('Subtitle',12,False),
 ('Heading 1',17,True),('Heading 2',13.5,True),('Heading 3',11.5,True),('Heading 4',10.5,True),
 ('List Bullet',10.5,False),('List Number',10.5,False),('Caption',9,False)]:
 st=doc.styles[name];st.font.name='Arial Unicode MS';st.font.size=Pt(size);st.font.bold=bold;st.font.color.rgb=RGBColor(0,0,0)
 rf=st.element.get_or_add_rPr().get_or_add_rFonts();rf.set(qn('w:eastAsia'),'Arial Unicode MS')
 st.paragraph_format.line_spacing=1.12;st.paragraph_format.space_after=Pt(5)
 st.paragraph_format.widow_control=True
 for b in st.element.get_or_add_pPr().findall(qn('w:pBdr')):st.element.get_or_add_pPr().remove(b)
 if name.startswith('Heading'):
  st.paragraph_format.space_before=Pt(11);st.paragraph_format.space_after=Pt(6);st.paragraph_format.keep_with_next=True
doc.styles['Caption'].paragraph_format.line_spacing=1.06

def clean_heading(t):
 t=re.sub(r'\[([^]]+)\]\([^)]*\)',r'\1',t)
 return re.sub(r'[^\w\u4e00-\u9fff\s]+',' ',t.replace('_',' ')).strip()

def breakable(s):
 # Give Word legal wrapping points in long hashes, identifiers and paths.
 s=re.sub(r'([/\\_])',lambda m:m.group(1)+'\u200b',str(s))
 s=re.sub(r'(?<!\w)([0-9a-f]{40,})(?!\w)',lambda m:'\u200b'.join(textwrap.wrap(m.group(1),16)),s)
 return s

def hyperlink(p,label,url,internal=False):
 h=OxmlElement('w:hyperlink')
 if internal:h.set(qn('w:anchor'),url)
 else:h.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
 r=OxmlElement('w:r');rp=OxmlElement('w:rPr');c=OxmlElement('w:color');c.set(qn('w:val'),'234E68');rp.append(c)
 rf=OxmlElement('w:rFonts');rf.set(qn('w:eastAsia'),'Arial Unicode MS');rp.append(rf)
 r.append(rp);t=OxmlElement('w:t');t.text=breakable(label);r.append(t);h.append(r);p._p.append(h)

def inline(p,line,base=ROOT):
 for c in re.split(r'(\*\*.*?\*\*|`[^`]+`|\[[^]]+\]\([^)]+\))',line):
  if not c:continue
  if c.startswith('**') and c.endswith('**'):p.add_run(breakable(c[2:-2])).bold=True
  elif c.startswith('`') and c.endswith('`'):
   r=p.add_run(breakable(c[1:-1]));r.font.size=Pt(9.5)
  elif c.startswith('[') and '](' in c:
   label,url=c[1:].split('](',1);url=url[:-1].strip('<>')
   if not re.match(r'https?://',url):url=(base/url).resolve().as_uri()
   hyperlink(p,label,url)
  else:p.add_run(breakable(c))
 return p

def para(t='',style=None,base=ROOT):return inline(doc.add_paragraph(style=style),t,base)

def heading(t,level=1,page=False,nav=True):
 global bookmark_id
 t=clean_heading(t);p=doc.add_heading(t,level)
 if page:p.paragraph_format.page_break_before=True;p.paragraph_format.space_before=Pt(0)
 name='h'+str(bookmark_id);start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(bookmark_id));start.set(qn('w:name'),name)
 end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(bookmark_id));p._p.insert(0,start);p._p.append(end);bookmark_id+=1
 if nav and level<=2:toc.append((t,level,name))
 return p

def table(headers,rows):
 global table_count
 if not rows:return
 table_count+=1
 # Horizontal panels preserve all columns while keeping the first identity column.
 if len(headers)>6:
  for k in range(1,len(headers),5):
   ids=[0]+list(range(k,min(k+5,len(headers))))
   para('宽表分栏 '+str((k-1)//5+1)+'  各分栏首列为相同记录标识','Caption')
   table([headers[j] for j in ids],[[r[j] if j<len(r) else '' for j in ids] for r in rows])
  return
 n=len(headers);weights=[]
 for j,h in enumerate(headers):
  lens=[len(str(r[j])) if j<len(r) else 0 for r in rows]
  average=sum(lens)/max(len(lens),1)
  weights.append(max(1.05,min(3.2,math.sqrt(max(len(str(h)),average))/2)))
 if n>2:weights[0]=max(weights[0],1.65)
 widths=[17.1*w/sum(weights) for w in weights]
 t=doc.add_table(rows=1,cols=n);t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 for c,w in zip(t.columns,widths):c.width=Cm(w)
 borders=OxmlElement('w:tblBorders')
 for edge in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
 t._tbl.tblPr.append(borders)
 allrows=[headers]+rows
 for i,values in enumerate(allrows):
  row=t.rows[0] if i==0 else t.add_row();pr=row._tr.get_or_add_trPr()
  # Large narrative rows must be allowed to flow; short numeric rows stay together.
  if max(map(lambda x:len(str(x)),values),default=0)<500:pr.append(OxmlElement('w:cantSplit'))
  if i==0:pr.append(OxmlElement('w:tblHeader'))
  for j,c in enumerate(row.cells):
   c.width=Cm(widths[j]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   tcpr=c._tc.get_or_add_tcPr();mar=OxmlElement('w:tcMar')
   for side,v in [('top',70),('bottom',70),('left',95),('right',95)]:
    el=OxmlElement('w:'+side);el.set(qn('w:w'),str(v));el.set(qn('w:type'),'dxa');mar.append(el)
   tcpr.append(mar);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'243C4A' if i==0 else ('F0F3F5' if i%2==0 else 'FFFFFF'));tcpr.append(sh)
   p=c.paragraphs[0];p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.05
   val=str(values[j]) if j<len(values) else ''
   inline(p,val)
   short=len(val)<22 and not ('/' in val or '_' in val)
   p.alignment=WD_ALIGN_PARAGRAPH.CENTER if (j>0 and short) else WD_ALIGN_PARAGRAPH.LEFT
   for r in p.runs:r.font.size=Pt(9);r.font.bold=i==0;r.font.color.rgb=RGBColor(255,255,255) if i==0 else RGBColor(0,0,0)
 para('').paragraph_format.space_after=Pt(3)

def add_figure(path,caption):
 global figure_count
 if not path.exists():missing_images.append(str(path));return
 try:
  with Image.open(path) as im:w,h=im.size
  width=min(16.8,17.8*w/h);height=width*h/w
  p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
  pic=p.add_run().add_picture(str(path),width=Cm(width));pic._inline.docPr.set('descr',caption)
  figure_count+=1;para('图 '+str(figure_count)+'  '+caption,'Caption')
 except Exception as exc:missing_images.append(str(path)+' '+str(exc))

def parse_md(text,base=ROOT,level_offset=0,strip_title=False):
 lines=text.splitlines();i=0;in_code=False
 while i<len(lines):
  s=lines[i].strip();i+=1
  if not s:continue
  if s.startswith('```'):in_code=not in_code;continue
  if in_code:
   p=para(s);p.paragraph_format.left_indent=Cm(.35);p.paragraph_format.space_after=Pt(1)
   for r in p.runs:r.font.size=Pt(8.5)
   continue
  if re.fullmatch(r'[-*_]{3,}',s):continue
  match=re.match(r'^(#{1,6})\s+(.*)',s)
  if match:
   if strip_title and len(match.group(1))==1:continue
   l=min(4,len(match.group(1))+level_offset);heading(match.group(2),l,nav=False);continue
  im=re.match(r'^!\[([^]]*)\]\(([^)]+)\)',s)
  if im:
   candidates=[base/im.group(2),ROOT/im.group(2)]
   path=next((p for p in candidates if p.exists()),candidates[0]);add_figure(path.resolve(),im.group(1));continue
  if s.startswith('|'):
   group=[s]
   # Some extracted native Word tables contain blank lines between rows.
   while i<len(lines):
    if lines[i].strip().startswith('|'):group.append(lines[i].strip());i+=1
    elif not lines[i].strip() and i+1<len(lines) and lines[i+1].strip().startswith('|'):i+=1
    else:break
   cells=[[c.strip() for c in line.strip('|').split('|')] for line in group]
   cells=[r for r in cells if not all(re.fullmatch(r':?-{2,}:?',c or '-') for c in r)]
   if len(cells)>1:table(cells[0],cells[1:])
   else:para(s)
   continue
  if s.startswith('>'):para(s.lstrip('> ').strip());continue
  if re.match(r'^[-*]\s',s):para(s[2:],'List Bullet',base)
  elif re.match(r'^\d+[.)]\s',s):para(re.sub(r'^\d+[.)]\s','',s),'List Number',base)
  else:para(s,base=base)

def record_source(p,role,chapter):
 b=p.read_bytes();used.append({'path':str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),
  'role':role,'chapter':chapter,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})

def include(p,role,chapter,offset=1,content=None):
 record_source(p,role,chapter)
 para('来源 '+str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else '来源 '+str(p),'Caption')
 parse_md(p.read_text(errors='replace') if content is None else content,p.parent,offset,True)

def notes_for(stage):
 folder=ROOT/'research'/stage
 out=[]
 for p in sorted((folder/'notes').glob('*.md')):
  if p.name in EXTRA_NAMES or 'FINDINGS' in p.name:out.append(p)
 for p in sorted((folder/'outputs').glob('*.md')):
  if p.name in OUTPUT_EXTRA:out.append(p)
 if stage=='phase2_literature_reassessment':
  for p in sorted((folder/'notes/workstreams').rglob('*.md')):
   if any(x in p.name for x in ['SYNTHESIS','QUALIFICATION','DECISIONS','R3_cluster']):out.append(p)
 return out

def normpath(stage,v):
 v=str(v).strip()
 if not v:return None
 p=Path(v)
 if p.is_absolute():return p
 if v.startswith('research/'):return ROOT/p
 return ROOT/'research'/stage/p

def fmt(v):
 if v is None:return '未提供或不可测'
 if isinstance(v,bool):return 'true' if v else 'false'
 if isinstance(v,float):return f'{v:.8g}'
 return str(v)

def summary_string(obj,prefix=''):
 """Retain aggregate metrics and conditions, exclude raw arrays and model coefficients."""
 result=[]
 if isinstance(obj,dict):
  for k,v in obj.items():
   if any(x in k.lower() for x in ['sha256','hash','weights','coeff','predictions','residuals','raw_rows','timestamp','command','config_path','input_path','script']):continue
   key=prefix+'.'+k if prefix else k
   if isinstance(v,dict):result.extend(summary_string(v,key))
   elif isinstance(v,list):
    if len(v)>60:result.append(key+' 记录数='+str(len(v))+' 详见原文件');continue
    if all(not isinstance(x,(dict,list)) for x in v):result.append(key+'='+', '.join(fmt(x) for x in v))
    else:
     for idx,x in enumerate(v):result.extend(summary_string(x,key+'['+str(idx)+']'))
   else:result.append(key+'='+fmt(v))
 elif isinstance(obj,list):
  for i,v in enumerate(obj):result.extend(summary_string(v,prefix+'['+str(i)+']'))
 return result

def run_records(stage):
 folder=ROOT/'research'/stage;records={}
 p=folder/'notes/EXPERIMENT_INDEX.csv'
 if p.exists():
  record_source(p,'完整运行登记','实验台账')
  for r in csv.DictReader(p.open(encoding='utf-8-sig')):
   rid=r.get('run_id') or r.get('experiment_id') or r.get('run')
   if not rid:rid='登记行 '+str(len(records)+1)
   records[rid]={'index':r,'dir':folder/'runs'/rid}
 runs=folder/'runs'
 if runs.exists():
  for d in sorted(runs.iterdir()):
   if d.is_dir() and d.name not in records:records[d.name]={'index':{},'dir':d}
 return records

def ledger():
 heading('实验台账和补充数值结果',1,True)
 para('这里逐项保留原运行登记和未登记但有运行目录的尝试。success 或 complete 是运行状态，不自动表示科学结论有效；v1.4 等退役口径仍受前文纠错约束。汇总结果按原文件字段显示，数值单位由字段名、协议与所在轮次给出。没有汇总文件时保留原产物路径，不臆算成绩。')
 total=0
 for _,stage,_,_ in STAGES:
  if stage in {'phase2_literature','official_temperature_review_20261006'}:continue
  records=run_records(stage)
  if not records:continue
  heading(stage+' 完整运行记录',2)
  for rid,rec in records.items():
   total+=1;r=rec['index'];d=rec['dir']
   heading(str(total)+' '+rid,3,nav=False)
   info=[]
   for key in ['module','question','method','status','exit_code','label_protocol','evidence_level','split','seed','elapsed_s','conclusion','notes']:
    if r.get(key):info.append(key+'='+r[key])
   if info:para('登记信息 '+'；'.join(info))
   else:para('该目录未列入当前实验索引。只按保留产物记录尝试，完成和有效性不得由目录存在推定。')
   candidates=[]
   for key in ['metric_path','output_result','output_path']:
    p=normpath(stage,r.get(key,''))
    if p and p.exists() and p.suffix=='.json':candidates.append(p)
   if d.exists():
    candidates+=sorted(p for p in d.glob('*.json') if any(x in p.name.lower() for x in ['summary','result','metric','acceptance']) and 'selection' not in p.name.lower())
   seen=set();added=False
   for p in candidates:
    if p in seen:continue
    seen.add(p)
    try:obj=json.loads(p.read_text())
    except Exception:continue
    vals=summary_string(obj)
    if not vals:continue
    record_source(p,'运行汇总数值','实验台账');added=True
    para('结果来源 '+str(p.relative_to(ROOT)),'Caption')
    # Group scalar fields in prose to avoid a 30-column table or truncated values.
    group=[];length=0
    for s in vals:
     if len(s)>1300:
      if group:para('；'.join(group));group=[];length=0
      para(s);continue
     if length+len(s)>550 and group:para('；'.join(group));group=[];length=0
     group.append(s);length+=len(s)
    if group:para('；'.join(group))
   paths=[r.get(k,'') for k in ['metric_path','artifact_path','output_result','output_path'] if r.get(k)]
   if paths:para('原始产物 '+'；'.join(paths),'Caption')
   if not added and not paths and d.exists():
    names=[p.name for p in sorted(d.iterdir()) if p.is_file()]
    para('目录留存文件 '+', '.join(names),'Caption')
 return total

def csv_appendix(p,cols=None,label=''):
 if not p.exists():return
 rows=list(csv.DictReader(p.open(encoding='utf-8-sig')))
 if not rows:return
 heading(label or p.stem,3,nav=False);record_source(p,'完整汇总结果表','补充结果')
 para('来源 '+str(p.relative_to(ROOT))+' 记录数 '+str(len(rows)),'Caption')
 columns=cols or list(rows[0])
 # Data summaries wider than six columns use a record paragraph retaining every field.
 if len(columns)>6:
  for i,r in enumerate(rows,1):
   ident=r.get('method') or r.get('run_id') or r.get('metric') or r.get(columns[0]) or str(i)
   p=para(str(i)+' '+ident);p.runs[0].bold=True
   vals=[k+'='+str(r.get(k,'')) for k in columns if r.get(k,'')!='']
   group=[];length=0
   for s in vals:
    if length+len(s)>550 and group:para('；'.join(group));group=[];length=0
    group.append(s);length+=len(s)
   if group:para('；'.join(group))
 else:table(columns,[[r.get(c,'') for c in columns] for r in rows])

def main():
 # Cover and executive narrative.
 doc.add_paragraph('LFP 电池 SOH 第二阶段完整研究总报告',style='Title')
 doc.add_paragraph('调查 实验 验证 结果与纠错的完整档案',style='Subtitle')
 para('汇编日期 2026 年 10 月 6 日')
 para('适用对象 项目负责人 研究队友 新加入成员')
 para('本报告将第二阶段已保留的研究证据汇编为一份可编辑 Word 文档和相同内容的 PDF。正文按问题和时间顺序组织，论文及实验台账用于防止遗漏。历史有效范围和后续纠错均在章节开头注明。')
 para('当前结论 研究和因果实现已经多轮验证 严格浅充平均收益存在但尾部未达标 官方隐藏容量与独立同协议四串精度仍未确认')
 doc.add_page_break()
 heading('阅读目录',1,False,False)
 toc_anchor=doc.paragraphs[-1]
 para('点击目录条目可跳转。Word 可打开导航窗格检索三级及以下标题；PDF 可全文检索实验编号、论文编号和指标名。')
 toc_insert=doc.paragraphs[-1]
 doc.add_page_break()
 synth=TASK/'sources/synthesis.md';record_source(synth,'新写统一解释','总览')
 parse_md(synth.read_text(),ROOT,0,True)

 for num,(title,stage,primaries,note) in enumerate(STAGES,7):
  chapter=str(num)+' '+title
  heading(chapter,1,True);para(note)
  folder=ROOT/'research'/stage
  primaries_set=set(primaries)
  for i,p in enumerate(primaries,1):
   if stage=='official_temperature_review_20261006' and p.name=='official_data_record_extracted.md':
    text=p.read_text();text=text.split('## 第二章 充放电量与容量相关趋势',1)[-1]
    heading('充放电电量 端点和固定窗口趋势',2)
    include(p,'十月六日新增充放电章',chapter,1,text)
   else:
    heading(str(num)+' '+str(i)+' '+p.stem,2)
    include(p,'正式报告或复评完整内容',chapter,1)
  supplements=notes_for(stage)
  if supplements:
   heading(str(num)+' 补充模块 失败 决策和审查',2)
   para('以下补充记录保留正式报告没有逐项展开的实验细节、早期失败版本、反证和审查修正。相同结论出现多次时，以更晚的有效版本及前文状态解释为准。')
   for p in supplements:
    if p in primaries_set:continue
    heading(p.stem,3,nav=False);include(p,'补充尝试与证据',chapter,2)
  if stage=='phase2_literature_reassessment':
   heading('九条技术路线的实施和停止条件',2)
   for p in sorted((folder/'route_cards').glob('*.md')):
    heading(p.stem,3,nav=False);include(p,'完整路线卡',chapter,2)
  if stage=='official_temperature_review_20261006':
   # Explicitly retain all recent chart evidence even when native DOCX extraction had no image links.
   for f,caption in [('temperature_timeline.png','官方温度随时间变化和传感器温差 全量离线审计'),
    ('temperature_distributions.png','官方温度偏差和最高最低温差分布'),
    ('largest_spread_episode.png','最大传感器温差附近原始曲线 待复核并未判为坏值')]:
    if not any(x in f for x in []):pass
   csv_appendix(ROOT/'research/charge_capacity_review_20261006/fixed_CC_voltage_windows.csv',label='所有固定恒流窗口逐事件结果')
   csv_appendix(ROOT/'research/official_temperature_review_20261006/segment_statistics.csv',label='逐运行段温度完整统计')
   csv_appendix(ROOT/'research/official_temperature_review_20261006/threshold_statistics.csv',label='异常阈值敏感性完整统计')

 heading('论文精读与历史文献证据',1,True)
 para('这里完整保留深度重评附册的三十三篇精读与验证卡。作者报告数值维持其原数据、单位和分割，不能与本地不同任务组成容量排行榜。全文不足或来源冲突均保留。随后附初始研究的证据卡，便于看出旧认识怎样改变。')
 annex=ROOT/'research/phase2_literature_reassessment/outputs/LFP_SOH_核心论文精读与证据附册.md'
 include(annex,'三十三篇精读卡完整附册','论文附录',0)
 oldbase=ROOT/'research/phase2_literature_reassessment/archive/phase2_literature_before_20260929T230323'
 for name in ['EVIDENCE_CARDS.md','SEARCH_LOG.md','ASSUMPTIONS_AND_OPEN_ITEMS.md']:
  p=oldbase/'notes'/name
  if p.exists():heading('最初文献 '+p.stem,2);include(p,'最初文献历史证据','论文附录',1)
 # Screening and registries retain every investigation, not only selected deep-read papers.
 for p,label in [(ROOT/'research/phase2_literature_reassessment/screening.csv','全部文献筛选与纳排'),
   (ROOT/'research/phase2_literature_reassessment/outputs/dataset_registry.csv','全部数据集资格'),
   (ROOT/'research/phase2_literature_reassessment/outputs/contradictions.csv','文献与数据冲突'),
   (ROOT/'research/phase2_literature_reassessment/outputs/research_questions.csv','全部研究问题')]:
  csv_appendix(p,label=label)

 run_count=ledger()
 heading('分层完整模型比较和补充结果',1,True)
 para('本部分按来源完整列出汇总表，保留各方法、随机种子、输入预算、实体数及协议。退役版本不并入有效比较。没有以全领域单一排序替代分层评价。')
 tables=[
 ('phase2_validation','outputs/metrics.csv'),
 ('phase2_temperature_improvement','outputs/ablation_results.csv'),
 ('phase2_temperature_improvement','outputs/per_cell_metrics.csv'),
 ('phase2_method_exploration','outputs/method_comparison.csv'),
 ('phase2_next_round','outputs/method_comparison.csv'),
 ('phase2_evidence_validation','outputs/data_eligibility.csv'),
 ('phase2_baseline_repair','outputs/baseline_comparison_matrix.csv'),
 ('phase2_baseline_repair','outputs/candidate_comparison.csv'),
 ('phase2_baseline_repair','outputs/stress_results.csv'),
 ('phase2_capacity_validation','outputs/data_eligibility.csv'),
 ('phase2_capacity_validation','outputs/per_target_predictions.csv'),
 ('phase2_capacity_validation','outputs/measurement_plan.csv')]
 for stage,rel in tables:csv_appendix(ROOT/'research'/stage/rel,label=stage+' '+Path(rel).stem)

 heading('验收结果和当前活动模型',1,True)
 for _,stage,_,_ in STAGES:
  for name in ['acceptance_results.json','acceptance.json','review_acceptance.json']:
   p=ROOT/'research'/stage/'outputs'/name
   if p.exists():
    heading(stage+' '+p.stem,2)
    record_source(p,'逐项验收原结果','验收附录')
    for s in summary_string(json.loads(p.read_text())):para(s)
 model=ROOT/'my_model/__init__.py'
 record_source(model,'汇编时只读活动模型核对','验收附录')
 heading('汇编时活动模型开关',2);para(model.read_text())
 para('本次汇编没有切换活动模型，没有重新训练或重新评分封存集，没有上传赛事。正式提交状态不能由研究 ZIP 的存在推断。')

 heading('来源覆盖和复现索引',1,True)
 para('以下逐项记录进入本报告的来源、使用位置和 SHA256。源文件保留原位，归档仅用于恢复被替换的历史文献。未全文打印原始采样、权重或逐点预测；报告中的引用路径可在原项目中复算。')
 # Deduplicate provenance while retaining its different uses.
 unique={}
 for u in used:
  if u['path'] not in unique:unique[u['path']]=dict(u)
  else:
   for key in ['role','chapter']:
    if u[key] not in unique[u['path']][key]:unique[u['path']][key]+='；'+u[key]
 for i,u in enumerate(unique.values(),1):
  para(str(i)+' '+u['path'])
  para('用途 '+u['role']+'；位置 '+u['chapter']+'；SHA256 '+u['sha256'],'Caption')

 # A source-to-coverage inventory also accounts for navigation and planning artifacts.
 exclusions=[]
 excluded_dirs={'.venv','clean_venv','site-packages','__pycache__','node_modules','papers','tmp','rendered','preflight','archive','staging','sealed','downloads','wheelhouse','candidates','data_external','data_synthetic'}
 for _,stage,_,_ in STAGES:
  f=ROOT/'research'/stage
  for current,dirs,files in os.walk(f):
   dirs[:]=[d for d in dirs if d not in excluded_dirs and not d.startswith('docx_qa')]
   for name in files:
    if not name.endswith('.md'):continue
    p=Path(current)/name;rel=str(p.relative_to(ROOT))
    if rel in unique:continue
    if '/notes/workstreams/' in rel:reason='论文卡或材料已在精读附册及综合证据中展开 原文件保留复核'
    elif any(x in name for x in ['START_PROMPT','PROMPT','PROTOCOL','READINESS','PREPARATION','ENVIRONMENT']):reason='任务书 协议或环境 作为计划与运行边界 不单独算已完成实验'
    elif any(x in name for x in ['STATUS','RESUME','PROGRESS','READER','DOCX','REPRODUCE','EXECUTIVE','NEXT_STEPS','README','HISTORICAL','CURRENT_REVIEW']):reason='导航 状态或重复摘要 实质结果已进入对应轮次'
    else:reason='辅助说明 保留来源索引 待查对应主报告或模块'
    exclusions.append((rel,reason))
 heading('其他留存文本的归类和去重说明',2)
 para('这张清单说明哪些文本是任务准备、导航、摘要或已整合的重复证据。任务书中的愿望不计完成；辅助文本如有独立科学结果，应以对应实验台账和模块记录回查。')
 table(['文件','归类与处理'],exclusions)

 # Insert compact internal navigation; it has no unstable placeholder page numbers.
 parent=toc_insert._p.getparent();ref=toc_insert._p
 for t,level,bm in toc:
  p=OxmlElement('w:p');ref.addnext(p);ref=p
  from docx.text.paragraph import Paragraph
  pp=Paragraph(p,doc._body);pp.paragraph_format.space_after=Pt(3)
  if level==2:pp.paragraph_format.left_indent=Cm(.45)
  hyperlink(pp,t,bm,True)
  for r in pp.runs:r.font.size=Pt(9.5)
 # Header and page field.
 hp=sec.header.paragraphs[0];hp.add_run('LFP 电池 SOH 第二阶段完整研究总报告');hp.runs[0].font.size=Pt(8)
 fp=sec.footer.paragraphs[0];fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
 fp.add_run('2026 年 10 月 6 日  ·  ')
 for instr in ['PAGE','NUMPAGES']:
  if instr=='NUMPAGES':fp.add_run(' / ')
  fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),instr);fp._p.append(fld)
 for r in fp.runs:r.font.size=Pt(8)
 doc.core_properties.title='LFP 电池 SOH 第二阶段完整研究总报告'
 doc.core_properties.subject='初始调查至十月六日的数据审计 实验 结果 纠错和来源'
 doc.core_properties.author='项目研究记录汇编'
 doc.save(OUT)
 (TASK/'source_manifest.json').write_text(json.dumps(list(unique.values()),ensure_ascii=False,indent=2))
 (TASK/'other_text_coverage.json').write_text(json.dumps(exclusions,ensure_ascii=False,indent=2))
 report={'docx':str(OUT),'source_count':len(unique),'run_count':run_count,'figure_count':figure_count,
  'table_count':table_count,'missing_images':missing_images,'paragraphs':len(doc.paragraphs),
  'body_chars':sum(len(p.text) for p in doc.paragraphs),'tables':len(doc.tables)}
 (TASK/'build_result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
