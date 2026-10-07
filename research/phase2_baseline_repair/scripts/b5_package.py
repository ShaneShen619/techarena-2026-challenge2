"""Create a research candidate zip without any operating/checkup data."""
import hashlib
import json
import zipfile
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
source=TASK/'candidates/causal_baseline'
dest=TASK/'candidates/causal_baseline_research_only_v2.zip'
allow=[source/'run_model.py',source/'validate_submission.py',source/'requirements.txt',*sorted((source/'framework').glob('*.py')),*sorted((source/'my_model').glob('*.py'))]
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in allow:z.write(p,p.relative_to(source))
assert not any('data/' in n for n in zipfile.ZipFile(dest).namelist())
manifest={'zip':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':[str(p.relative_to(source)) for p in allow],'status':'research_candidate_not_submitted'}
(TASK/'runs/B5_official_candidate_20260930_v2').mkdir(exist_ok=True)
(TASK/'runs/B5_official_candidate_20260930_v2/package_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
