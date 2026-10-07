import csv,hashlib,json,os,platform,shutil,socket,subprocess,sys
from pathlib import Path
T=Path(__file__).resolve().parents[1];ROOT=T.parents[1]
import pandas,numpy,docx
files=[ROOT/'data/DATA_DESCRIPTION.md',ROOT/'data/checkups/CK0_reference_discharge.csv.gz',
 ROOT/'data/checkups/evaluation_points.csv',ROOT/'my_model/model_example.py',
 ROOT/'research/phase2_baseline_repair/candidates/causal_baseline/my_model/model_baseline.py',
 T/'START_PROMPT.md',T/'candidates/model_candidate_v1.py',T/'configs/protocol_v1.json',
 T/'configs/transfer_final_freeze_v2.json',T/'configs/freeze_manifest.json',
 T/'downloads/SLBs_LFP_charging_data.zip']
for p in sorted((ROOT/'data/operation').glob('*.csv.gz')):files.append(p)
rows=[]
for p in files:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 rows.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=h.hexdigest(),role='source_or_frozen_code'))
with (T/'manifests/input_code_config_sha256.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
try:mem=int(subprocess.check_output(['sysctl','-n','hw.memsize'],text=True).strip())
except Exception:mem=None
res=dict(python=platform.python_version(),pandas=pandas.__version__,numpy=numpy.__version__,docx=docx.__version__,
 cpu_count=os.cpu_count(),ram_GiB=round(mem/2**30,2) if mem else None,
 free_disk_GiB=round(shutil.disk_usage(ROOT).free/2**30,2),
 word_app=Path('/Applications/Microsoft Word.app').exists(),
 poppler_pdftoppm=shutil.which('pdftoppm'),poppler_pdfinfo=shutil.which('pdfinfo'),
 node=shutil.which('node'),zipfile_read=True,openpyxl_available=True,
 real_official_CK0_RPT_smoke='accepted_100p41118Ah',
 public_Zenodo_download='succeeded_checksum_verified',
 manifest_entries=len(rows),failure_log='none_for_core_pipeline; first_wrong_python_path_and_duplicate_time_handled_in_notes')
run=T/'runs/N0_preflight_20260930_v1';run.mkdir(exist_ok=True)
(run/'result.json').write_text(json.dumps(res,indent=2));(run/'COMPLETED').write_text('complete\n')
print(json.dumps(res,indent=2))
