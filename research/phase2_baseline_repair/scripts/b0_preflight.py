"""Fresh B0 environment/source qualification; no model fitting or label selection."""
from __future__ import annotations
import csv,hashlib,json,os,platform,shutil,sys,time
from pathlib import Path
import numpy,pandas,scipy

TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
RUN=TASK/'runs/B0_preflight_20260930_v1';RUN.mkdir(parents=True,exist_ok=True)
assert not (RUN/'COMPLETED').exists(), 'do not overwrite completed run'

old=ROOT/'research/phase2_evidence_validation/data_manifests/input_manifest.csv'
rows=[]
with old.open(newline='') as f:
    for row in csv.DictReader(f):
        p=ROOT/row['path']
        if not p.is_file():
            row['verification']='missing_on_20260930';rows.append(row);continue
        row['bytes']=p.stat().st_size
        # Rehash official files and representative external inputs, not all 19 GB of TU.
        if row['source']=='official_D3' or row['source'].startswith(('P1','Che','TU')):
            h=hashlib.sha256()
            with p.open('rb') as src:
                for chunk in iter(lambda:src.read(8*1024*1024),b''):h.update(chunk)
            row['verification']='fresh_sha256_matches_prior' if h.hexdigest()==row['sha256'] else 'SHA256_CHANGED'
            row['sha256']=h.hexdigest()
        else:row['verification']='stat_checked_prior_SHA256_not_recomputed'
        rows.append(row)
assert rows and not any(r['verification']=='SHA256_CHANGED' for r in rows)
manifest=TASK/'data_manifests/input_manifest.csv'
with manifest.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)

cf={}
for p in sorted((TASK/'configs').glob('*.json')):
    cf[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(TASK/'configs/frozen_manifest.json').write_text(json.dumps({'frozen_before_B1':cf},indent=2)+'\n')

op_files=sorted((ROOT/'data/operation').glob('segment_*.csv*'))
prior_eligibility=ROOT/'research/phase2_evidence_validation/outputs/data_eligibility.csv'
eligible=pandas.read_csv(prior_eligibility)
disk=shutil.disk_usage(TASK)
info={'run_id':RUN.name,'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
      'python':sys.version.split()[0],'platform':platform.platform(),'numpy':numpy.__version__,
      'pandas':pandas.__version__,'scipy':scipy.__version__,'logical_cpus':os.cpu_count(),
      'free_disk_GiB':round(disk.free/2**30,2),'official_operation_files':len(op_files),
      'manifest_rows':len(rows),'fresh_hashed_rows':sum(r['verification'].startswith('fresh_') for r in rows),
      'prior_new_4S_D2_status':eligible.loc[eligible.dataset_id.eq('New_4S_independent_group'),'eligibility'].iloc[0],
      'new_D2_status':'not_found_in_current_qualified_local_inventory; rescan if user supplies path',
      'word_app':bool(Path('/Applications/Microsoft Word.app').exists()),
      'pdftoppm':shutil.which('pdftoppm'),'soffice':shutil.which('soffice'),
      'config_sha256':cf,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(RUN/'result.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
(RUN/'COMPLETED').write_text('immutable run completed\n')
print(json.dumps(info,ensure_ascii=False))
