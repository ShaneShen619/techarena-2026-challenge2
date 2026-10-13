"""Study paths, bilingual notes, immutable protocols, and stage bookkeeping."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode = True

STUDY = Path(__file__).resolve().parents[1]
REPO = STUDY.parents[1]
PACKAGE = REPO / 'TechArena_Challenge2_Team_Package'
BASE = REPO / 'research/phase2_anchor_step_20261013'
V2DIR = REPO / 'research/phase2_v2_phase_matched_20261013'
sys.path[:0] = [str(BASE / 'src'), str(V2DIR / 'src'), str(PACKAGE)]

def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + '\n')

def bilingual(path, title, en, zh):
    Path(path).write_text(f'<a id="en"></a>\n\n# {title}\n\n> English · [中文](#zh)\n\n{en}\n\n---\n\n<a id="zh"></a>\n\n# {title}\n\n> [English](#en) · 中文\n\n{zh}\n')

def status(stage, done, next_step):
    last = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    bilingual(STUDY / 'notes/STATUS.md', 'Execution status',
              f'Stage: {stage}.\n\nDone: {done}\n\nNext: {next_step}\n\nLast commit: `{last}`.',
              f'阶段：{stage}。\n\n已完成：{done}\n\n下一步：{next_step}\n\n最近提交：`{last}`。')

def decision(en, zh):
    path = STUDY / 'notes/decisions.json'
    entries = json.loads(path.read_text()) if path.exists() else []
    entries.append({'en': en, 'zh': zh})
    dump(path, entries)
    bilingual(STUDY / 'notes/DECISIONS.md', 'Decisions', '\n\n'.join(f'{i+1}. {v["en"]}' for i,v in enumerate(entries)), '\n\n'.join(f'{i+1}. {v["zh"]}' for i,v in enumerate(entries)))

GATES = {'G-causal': 'bit-identical future corruption and fit-prefix checks',
         'G-proxy': 'MAE lower for every delta; MAX <= V2 MAX + 0.10 pp',
         'G-epsfree': 'CK2-7 MAE <= V2 - 0.02 pp',
         'G-robust': 'wins in >=5/6 step variants',
         'G-regress': 'per-checkup absolute error growth <=0.30 pp',
         'G-impl': 'numpy/pandas only, <=0.001 pp agreement, Python3.11 sample smoke'}

def protocol(stage, config):
    path = STUDY / f'stage_{stage}/protocol.json'
    if path.exists():
        raise RuntimeError(f'Protocol already exists: {path}')
    dump(path, dict(exposure='exposed-exploratory; proxies are not hidden truth', gates=GATES, **config))
    path.with_suffix('.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest() + '  protocol.json\n')

