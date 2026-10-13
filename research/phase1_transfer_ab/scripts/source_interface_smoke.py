"""Rebuild and validate an isolated copy of the specified stage1 submission."""
import shutil,subprocess,sys
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
source=Path('/Users/shane/Desktop/项目/Current State_Challenge1')
dest=TASK/'runs/source_smoke'
if dest.exists():shutil.rmtree(dest)
shutil.copytree(source,dest,ignore=shutil.ignore_patterns('.git','.venv','venv','__pycache__','*.pyc','out','validation_report.txt'))
result=subprocess.run([sys.executable,'validate_submission.py'],cwd=dest,capture_output=True,text=True,timeout=300)
(TASK/'runs/source_smoke.log').write_text(result.stdout+'\n'+result.stderr)
assert result.returncode==0,result.stdout+result.stderr
print(result.stdout)
