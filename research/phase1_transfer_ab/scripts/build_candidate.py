"""Package a frozen research model without modifying the root submission."""
import hashlib,json,shutil,zipfile
from pathlib import Path
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
dest=TASK/'candidates/phase1_ab';dest.mkdir(parents=True,exist_ok=True)
for name in ['run_model.py','validate_submission.py']:
    shutil.copy2(ROOT/name,dest/name)
for name in ['framework','sample_data']:
    shutil.copytree(ROOT/name,dest/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
model=dest/'my_model';model.mkdir(exist_ok=True)
(model/'__init__.py').write_text('from .model import MyModel as ActiveModel\n')
text=(TASK/'src/age_prior.py').read_text().replace('from exposure import','from .exposure import').replace('from observation_a import','from .observation_a import')
(model/'model.py').write_text(text)
for name in ['exposure.py','observation_a.py']:
    shutil.copy2(TASK/'src'/name,model/name)
shutil.copy2(TASK/'artifacts/source_prior.json',model/'source_prior.json')
(dest/'requirements.txt').write_text('numpy==2.3.5\npandas==2.2.3\n')
(dest/'README.md').write_text('# Research candidate: stage1 transferred B + A monitoring\n\nNumeric A correction is disabled after the prespecified fusion gate failed.\nNo independent 4S C/20 accuracy claim; not a final submission.\nThe frozen source artifact is included; train reads CK0 only.\nOfficial framework and entry points are unchanged.\n')
files=[]
archive=TASK/'candidates/Phase1AB_Research_Challenge2.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(dest.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
            rel=p.relative_to(dest);z.write(p,str(rel));files.append({'path':str(rel),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(TASK/'outputs/package_manifest.json').write_text(json.dumps({'archive':str(archive.relative_to(ROOT)),
    'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':files,'numeric_A_enabled':False,
    'root_model_switched':False},indent=2)+'\n')
print(archive)
