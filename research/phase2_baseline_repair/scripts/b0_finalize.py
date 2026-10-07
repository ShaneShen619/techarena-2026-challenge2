from pathlib import Path
import hashlib,json,pickle,pickletools,csv,sys
import pandas as pd
T=Path(__file__).resolve().parents[1];R=T.parents[1]
sys.path.insert(0,str(R))
entries=[('B0_example_20260930_v1',R/'my_model/model_example.py'),
         ('B0_ck0_constant_20260930_v1',R/'research/phase2_evidence_validation/candidates/official_gated/my_model/research_candidate.py')]
for run,code in entries:
    p=T/'runs'/run
    assert p.exists() and not (p/'COMPLETED').exists()
    d=pd.read_csv(p/'output.csv')
    assert len(d)==8 and d.checkup.tolist()==[f'CK{i}' for i in range(8)]
    raw=(p/'model_state.pkl').read_bytes()
    try:
        model=pickle.loads(raw)
        state={k:v for k,v in vars(model).items() if isinstance(v,(int,float,str,bool,type(None)))}
        cls=type(model).__name__
    except ModuleNotFoundError:
        state={'pickle_literal_values':[(op.name,str(arg)) for op,arg,pos in pickletools.genops(raw) if op.name in ('BINUNICODE','SHORT_BINUNICODE','BINFLOAT','NEWTRUE','NEWFALSE')]}
        cls='ResearchCandidate_in_isolated_package'
    out={'run_id':run,'output_rows':8,'state':state,'model_class':cls,
         'model_pickle_bytes':(p/'model_state.pkl').stat().st_size,
         'source_code_path':str(code.relative_to(R)),
         'source_code_sha256':hashlib.sha256(code.read_bytes()).hexdigest(),
         'output_sha256':hashlib.sha256((p/'output.csv').read_bytes()).hexdigest(),
         'input_manifest_sha256':hashlib.sha256((T/'data_manifests/input_manifest.csv').read_bytes()).hexdigest(),
         'capacity_truth_CK1_CK7':'hidden_not_scored'}
    (p/'result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    (p/'COMPLETED').write_text('immutable run completed\n')
    print(json.dumps(out,ensure_ascii=False))
