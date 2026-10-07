from pathlib import Path
import hashlib,csv
TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'outputs/artifact_manifest.csv'
rows=[]
for p in sorted(TASK.rglob('*')):
    if not p.is_file() or p==OUT or '__pycache__' in p.parts or p.suffix=='.pyc':continue
    rel=p.relative_to(TASK)
    if rel.parts[0]=='tmp':continue
    role=rel.parts[0]
    rows.append({'relative_path':str(rel),'size_bytes':p.stat().st_size,
                 'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                 'role':role,'version_or_run_id':rel.parts[1] if role=='runs' and len(rel.parts)>1 else '',
                 'status':'superseded_or_invalidated' if ('_v1' in str(rel) and str(rel).startswith('runs/V1_event')) or 'V2_R02_sensitivity_20260929_v2' in str(rel) else 'current_or_record'})
with OUT.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
print(len(rows),OUT)
