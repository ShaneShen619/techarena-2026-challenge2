"""Rerun into a NEW sibling research folder; never overwrite archived results."""
from pathlib import Path
import sys,shutil,subprocess,argparse
p=argparse.ArgumentParser();p.add_argument('--out',required=True,help='new nonexistent sibling directory name');p.add_argument('--public-download',action='store_true');args=p.parse_args()
here=Path(__file__).resolve().parent;dest=here.parent/args.out
if dest.exists():raise SystemExit('Refusing to overwrite existing results: '+str(dest))
if '/' in args.out:raise SystemExit('Use a sibling folder name, not a path')
dest.mkdir()
for source in list(here.glob('*.py'))+list(here.glob('protocol*.json'))+list(here.glob('*amendment*.json'))+[here/'paper_to_project.md']:
 shutil.copy2(source,dest/source.name)
for directory in ['public_data','paper_sources']:
 source=here/directory
 if source.exists():shutil.copytree(source,dest/directory,ignore=shutil.ignore_patterns('*.bin','*.zip','*.h5'))
commands=[['-c','from extract_sources import p1;p1()'],['extract_official.py'],['source_benchmarks.py'],['complete_raw_baseline.py'],['controls.py'],['registered_A.py'],['legacy_NT.py'],['raw_robustness.py'],['transfer.py'],['official_diagnostics.py'],['causal_prefix_replay.py'],['audit.py'],['finish_outputs.py'],['report.py']]
if args.public_download:commands=[['download_subset.py'],['-c','from extract_sources import zhu;zhu()']]+commands
commands.insert(-1,['public_benchmarks.py'])
for command in commands:
 print('Running',command,flush=True);subprocess.run([sys.executable,*command],cwd=dest,check=True)
print('New results:',dest)
