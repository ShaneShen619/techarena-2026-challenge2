"""Fresh extraction, official validator, cross-process state and fixed CK replay."""
import hashlib,json,os,resource,shutil,subprocess,sys,time,zipfile
from pathlib import Path
import pandas as pd
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
run=TASK/'runs/clean_validation';dest=run/'extracted'
if dest.exists():shutil.rmtree(dest)
dest.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(TASK/'candidates/Phase1AB_Research_Challenge2.zip') as z:z.extractall(dest)
python=run/'.venv/bin/python';env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
records=[]
def call(name,args):
    t=time.monotonic()
    r=subprocess.run([str(python),*map(str,args)],cwd=dest,env=env,capture_output=True,text=True,timeout=300)
    (run/f'{name}.log').write_text(r.stdout+'\n'+r.stderr)
    records.append({'name':name,'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-t})
    print(name,'exit',r.returncode,flush=True)
    assert r.returncode==0,r.stdout+r.stderr
call('official_sample_validator',['validate_submission.py'])
state=run/'full_state';out=run/'full_test'
call('official_full_train',['run_model.py','--model','train','--input',ROOT/'data','--output-dir',state])
call('official_full_test',['run_model.py','--model','test','--input',ROOT/'data','--state-dir',state,'--output-dir',out,'--eval-point','all'])
actual=pd.read_csv(out/'output.csv');expected=pd.read_csv(TASK/'outputs/official_predictions_unlabeled.csv')
comparison=actual.merge(expected[['checkup','SOH_est']],on='checkup',suffixes=('_CLI','_research'))
comparison['rounded_difference_pp']=comparison.SOH_est_CLI-comparison.SOH_est_research.round(3)
assert comparison.rounded_difference_pp.abs().max()<1e-10
comparison.to_csv(TASK/'outputs/package_prediction_comparison.csv',index=False)
for ck in ['CK7','CK1','CK4']:
    point=run/f'query_{ck}'
    call(f'separate_process_{ck}',['run_model.py','--model','test','--input',ROOT/'data','--state-dir',state,'--output-dir',point,'--eval-point',ck])
    v=pd.read_csv(point/'output.csv').SOH_est.iloc[0]
    assert abs(v-actual.loc[actual.checkup.eq(ck),'SOH_est'].iloc[0])<1e-10
framework=[]
for name in ['run_model.py','validate_submission.py',*[str(x.relative_to(ROOT)) for x in (ROOT/'framework').glob('*.py')]]:
    same=(dest/name).read_bytes()==(ROOT/name).read_bytes();assert same
    framework.append({'path':name,'identical':same,'sha256':hashlib.sha256((dest/name).read_bytes()).hexdigest()})
peak=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
peak_mb=peak/(1024**2 if sys.platform=='darwin' else 1024)
(TASK/'outputs/clean_validation.json').write_text(json.dumps({'checks':records,'all_pass':True,'framework':framework,
   'CLI_precision_decimals':3,'maximum_rounded_prediction_difference_pp':float(comparison.rounded_difference_pp.abs().max()),
   'max_child_process_peak_RSS_MB':peak_mb,'memory_measurement':'maximum child-process ru_maxrss; includes dataset IO; OS-specific peak metric',
   'fresh_venv':str(python),'python_version':subprocess.check_output([str(python),'--version'],text=True).strip(),
   'installed_packages':subprocess.check_output([str(python),'-m','pip','freeze'],text=True).splitlines()},indent=2)+'\n')
