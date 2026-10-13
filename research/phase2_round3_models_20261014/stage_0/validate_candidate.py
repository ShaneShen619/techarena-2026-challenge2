"""Independent exact causality and Python 3.11 candidate interface verification.

Run with candidate file, research predictions CSV and registered model name.
Only numpy/pandas and the standard library are required.
"""
import argparse
import importlib.util
import json
import pickle
import sys
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import pandas as pd

STUDY=Path(__file__).resolve().parents[1]
PACKAGE=STUDY.parents[1]/'TechArena_Challenge2_Team_Package'
sys.path.insert(0,str(PACKAGE))
from framework.data import Dataset, load_dataset

def validate(candidate, prediction_file, name):
    spec=importlib.util.spec_from_file_location('independent_candidate',candidate)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    cls=module.MyModel
    full=load_dataset(PACKAGE/'data')
    ck=pd.DatetimeIndex(full.eval_points.sort_values('date').date)
    model=cls(); model.fit(full)
    model=pickle.loads(pickle.dumps(model))
    prefix=cls(); prefix.fit(load_dataset(PACKAGE/'data',until=ck[1]))
    rows=[]; rng=np.random.default_rng(714)
    for k,date in enumerate(ck):
        ds=load_dataset(PACKAGE/'data',until=date)
        actual=float(model.estimate_soh(ds,date))
        fit_cut=float(prefix.estimate_soh(ds,date))
        op=full.operation.copy()
        future=op.timestamp>date
        for c in op.columns:
            if c not in ('timestamp','segment','elapsed_s') and pd.api.types.is_numeric_dtype(op[c]):
                op[c]=op[c].astype(float)
                op.loc[future,c]=rng.normal(size=int(future.sum()))
        corrupted=Dataset(op[~future].reset_index(drop=True),ds.checkups_released,full.eval_points,full.reference_discharge,date)
        noisy=float(model.estimate_soh(corrupted,date))
        rows.append({'k':k,'SOH':actual,'fit_prefix_exact':actual==fit_cut,'future_noise_exact':actual==noisy})
    ref=pd.read_csv(prediction_file)
    real='normal' if 'normal' in set(ref.scenario) else 'real'
    ref=ref[(ref.model==name)&(ref.scenario==real)&(ref.step=='main')&(ref.delta==.4)]
    smooth='smooth' if 'smooth' in ref.columns else 'a4s'
    ref=ref[ref[smooth]==2.].sort_values('k')
    predicted=np.array([r['SOH'] for r in rows[1:]])
    expected=ref.Q.to_numpy()/102*100
    assert len(expected)==7
    sample=load_dataset(PACKAGE/'sample_data')
    sm=cls(); sm.fit(sample)
    sample_rows=[]
    for p in sample.eval_points.itertuples():
        val=float(sm.estimate_soh(load_dataset(PACKAGE/'sample_data',until=p.date),p.date))
        assert np.isfinite(val)
        sample_rows.append({'checkup':p.checkup,'SOH':val})
    diff=float(np.max(np.abs(predicted-expected)))
    result={'candidate':str(candidate),'python':sys.version,'predictions':rows,'sample_smoke':sample_rows,
            'max_research_difference_pp':diff,'G-causal':all(r['fit_prefix_exact'] and r['future_noise_exact'] for r in rows),
            'G-impl':diff<=.001}
    result['passed']=result['G-causal'] and result['G-impl']
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('candidate',type=Path)
    parser.add_argument('predictions',type=Path)
    parser.add_argument('model')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=validate(args.candidate,args.predictions,args.model)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('predictions','sample_smoke')},indent=2))
    assert result['passed']
