"""Create local candidate ZIPs and validate clean extractions in a fresh venv."""
from pathlib import Path
import subprocess
import zipfile

task=Path(__file__).resolve().parents[1]
out=task/'runs/package_check'
out.mkdir(parents=True,exist_ok=True)
python=task/'preflight/final_clean_venv/bin/python'
assert python.exists(), 'First create the fresh venv described in REPRODUCE.md'

for route in ('route_a','route_b'):
    source=task/'candidates'/route
    archive=out/f'{route}_Challenge2.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(source.rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc' or p.name=='validation_report.txt':
                continue
            z.write(p,p.relative_to(source))
    extract=out/f'extracted_{route}'
    extract.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(extract)
        assert not any(name.startswith('data/') for name in z.namelist())
    result=subprocess.run([str(python),str(extract/'validate_submission.py')],
                          cwd=extract,capture_output=True,text=True,timeout=180)
    (out/f'{route}_validator.log').write_text(result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError(f'{route} extracted validator failed; see log')
    assert 'PASSED - output schema satisfied' in result.stdout
    print(route,'ZIP',archive.stat().st_size,'bytes, extracted clean validator PASS')
