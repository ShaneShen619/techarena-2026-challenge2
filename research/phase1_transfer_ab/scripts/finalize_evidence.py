"""Finalize separate scientific/engineering acceptance and artifact integrity."""
import hashlib,importlib.metadata,json,platform,subprocess,sys,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((TASK/'outputs'/name).read_text())
preserved=[]
for entry in json.loads((ROOT/'research/phase1_transfer_ab_plan_20261010/SOURCE_SNAPSHOT.json').read_text())['files']:
    p=Path(entry['path']);actual=sha(p);same=actual==entry['sha256'];assert same,p
    preserved.append({'path':str(p),'sha256':actual,'unchanged':same})
frozen=[]
for entry in json.loads((TASK/'configs/frozen_manifest.json').read_text())['files']:
    actual=sha(ROOT/entry['path']);assert actual==entry['sha256'],entry['path']
    frozen.append({'path':entry['path'],'sha256':actual,'unchanged':True})
tracked=subprocess.check_output(['git','diff','--name-only','HEAD','--','framework','my_model','run_model.py','validate_submission.py','requirements.txt','data'],cwd=ROOT,text=True).strip()
assert not tracked,tracked
(TASK/'outputs/preservation_checks.json').write_text(json.dumps({'source_snapshot':preserved,'frozen_execution_files':frozen,'protected_tracked_changes':tracked,'all_pass':True},indent=2)+'\n')
env={'python':sys.version,'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','pytest']},
     'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
     'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
(TASK/'outputs/execution_environment.json').write_text(json.dumps(env,indent=2)+'\n')
root=ET.parse(TASK/'outputs/tests.xml').getroot();suites=list(root.iter('testsuite'))
tests=sum(int(x.get('tests',0)) for x in suites);failed=sum(int(x.get('failures',0))+int(x.get('errors',0)) for x in suites)
assert tests==14 and failed==0
clean=read('clean_validation.json');causal=read('official_check_summary.json');manifest=read('package_manifest.json')
assert clean['all_pass'] and clean['python_version'].startswith('Python 3.12') and causal['all_pass']
archive=ROOT/manifest['archive'];assert sha(archive)==manifest['sha256']
with zipfile.ZipFile(archive) as z:
    for entry in manifest['files']:assert hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256']
    runtime=(TASK/'src/age_prior.py').read_text().replace('from exposure import','from .exposure import').replace('from observation_a import','from .observation_a import')
    assert z.read('my_model/model.py').decode()==runtime
    for name in ['exposure.py','observation_a.py']:assert z.read('my_model/'+name)==(TASK/'src'/name).read_bytes()
    assert z.read('my_model/source_prior.json')==(TASK/'artifacts/source_prior.json').read_bytes()
e3=read('E3_gate.json');e5=read('E5_gate.json');e3['hard_checks']='pass_E6_engineering'
(TASK/'outputs/E3_gate.json').write_text(json.dumps(e3,indent=2)+'\n')
result={'branch':env['branch'],'E0':'pass_provenance_and_input_freeze','E1':'pass_exact_legacy_reproduction',
    'E2':'completed_minimal_exposure_audit; calendar_and_real_path_order_not_testable',
    'E3_source_development_B_performance_pass':e3['B_E3_performance_pass'],
    'E4_A_independent_increment_pass':e5['A_increment_gate_pass'],'E5_numeric_fusion_pass':e5['fusion_performance_gate_pass'],
    'E6_engineering_pass':True,'E7':'not_testable_missing_independent_same_protocol_4S_labels',
    'tests':{'total':tests,'failures':failed},'causal_checks':causal['causal_checks'],'stress_scenarios':causal['stress_scenarios'],
    'mechanism_cases':read('mechanism_provenance.json')['n_cases'],'isolated_package_validated':True,'root_model_switched':False,
    'final_candidate':'B_new_dynamic_fixed_xi0.001 plus A monitoring; numeric correction disabled',
    'source_B_macro_MAE_pp':e5['B_macro_MAE_pp'],'source_F_signal_macro_MAE_pp':e5['F_signal_macro_MAE_pp'],
    'official_capacity_performance':'not_testable','D1_restricted_model_performance':'not_applicable_full_history_not_allowed',
    'independent_blind_test':False,'hard_check_pass_is_accuracy_proof':False,
    'remaining_scientific_limits':['low-rate extrapolation','source timestamp overlaps and temperature missingness','source-target capacity protocol',
       'unobserved exposure and calendar ageing','small previously developed entity sample','path ordering','4S capacity/SOC imbalance',
       'temperature bias increases late errors','numeric fusion event-level deployment equivalence not implemented; candidate rejected'],
    'ZIP_sha256':manifest['sha256'],'clean_runtime_python':clean['python_version']}
(TASK/'outputs/acceptance.json').write_text(json.dumps(result,indent=2)+'\n')
files=[]
for directory in ['configs','src','scripts','tests','outputs','artifacts','candidates/phase1_ab']:
    for p in sorted((TASK/directory).rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or p.name.endswith('.partial.csv') or p.name.endswith('.partial.json') or p.name=='reproducibility_manifest.json':continue
        files.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
for p in [TASK/'README.md',TASK/'REPRODUCE.md',TASK/'E7_DATA_REQUIREMENTS.md',archive]:
    files.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
(TASK/'outputs/reproducibility_manifest.json').write_text(json.dumps({'files':files,'generation':'after verification; manifest does not hash itself','protected_files_unchanged':True},indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
