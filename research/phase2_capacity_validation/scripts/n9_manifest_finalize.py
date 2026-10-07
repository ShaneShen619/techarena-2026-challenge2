"""Versioned final artifact inventory; omits its own hash to avoid a cycle."""
import csv,hashlib,shutil
from pathlib import Path
T=Path(__file__).resolve().parents[1];O=T/'outputs'
old=O/'artifact_manifest.csv'
if old.exists() and not (O/'artifact_manifest_v1.csv').exists():shutil.copy2(old,O/'artifact_manifest_v1.csv')
rows=[]
for p in sorted(T.rglob('*')):
 if not p.is_file():continue
 rel=str(p.relative_to(T))
 if any(x in p.parts for x in ['__pycache__','.DS_Store']):continue
 if rel.startswith(('downloads/','staging/','sealed/','rendered/','tmp/')):continue
 if rel=='outputs/artifact_manifest.csv':continue
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 rows.append(dict(path=rel,bytes=p.stat().st_size,sha256=h.hexdigest(),
  role='deliverable' if rel.startswith('outputs/') else 'code_config_run_or_note',manifest_version='2026-09-30-final-v2'))
with old.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
print(len(rows))
