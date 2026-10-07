"""Same-input candidate comparison and strict future-only mutation tests."""
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework.data import load_dataset
from my_model.model_example import ExampleModel
spec=importlib.util.spec_from_file_location('candidate',TASK/'candidates/causal_baseline/my_model/model_baseline.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def one(op,ds,cutoff,gate):
    ds.operation=op
    m=mod.ActiveModel(gate);m.fit(ds)
    ds.operation=op[op.timestamp<=cutoff].reset_index(drop=True)
    value=m.estimate_soh(ds,cutoff)
    return value,m.last_q_ref

def main():
    run=TASK/'runs/B2_candidate_comparison_20260930_v4';run.mkdir(exist_ok=True)
    ds=load_dataset(ROOT/'data');op=ds.operation
    rows=[];checks=[]
    for ck in ds.eval_points.itertuples():
        cutoff=pd.Timestamp(ck.date)
        prefix=op[op.timestamp<=cutoff].reset_index(drop=True)
        original=ExampleModel();ds.operation=op;original.fit(ds);ds.operation=prefix
        original_y=original.estimate_soh(ds,cutoff)
        for gate in ['none','range','gap','combined','start']:
            y,q=one(op,ds,cutoff,gate)
            ev=mod.events(prefix)
            if gate in ('range','combined') and q is not None:
                ev=ev[(ev.Q_partial_Ah>=.5*q)&(ev.Q_partial_Ah<=1.5*q)]
            if gate in ('gap','combined'):ev=ev[ev.max_gap_s<=60]
            if gate=='start':ev=ev[ev.start_current_A<=5]
            rows.append(dict(checkup=ck.checkup,date=str(cutoff.date()),candidate=gate,
                prediction_pct=y,original_pct=original_y,delta_from_original_pp=y-original_y,
                q_ref_Ah=q,n_eligible_events=len(ev),n_total_events=len(mod.events(prefix)),
                fallback=bool(q is None or ev.empty),capacity_truth_pct=None,capacity_error_pp=None,
                evidence_level='official_unlabeled',protocol='official_four_series_operating_prefix'))
            # Future-only modifications must not alter training state or earlier output.
            if ck.checkup!='CK7':
                ix=op.index[op.timestamp>cutoff]
                extreme=op.copy()
                extreme.loc[ix,'current_A']=1e6
                extreme.loc[ix,'pack_voltage_V']=14.1
                y2,q2=one(extreme,ds,cutoff,gate)
                # Delete future data and shuffle its current/voltage pairs.
                yd,qd=one(prefix,ds,cutoff,gate)
                shuffled=op.copy()
                if len(ix):
                    seed=np.random.default_rng(20260930)
                    perm=seed.permutation(len(ix))
                    shuffled.loc[ix,['current_A','pack_voltage_V']]=op.loc[ix,['current_A','pack_voltage_V']].to_numpy()[perm]
                ys,qs=one(shuffled,ds,cutoff,gate)
                passed=(y==y2==yd==ys and q==q2==qd==qs)
                checks.append(dict(checkup=ck.checkup,candidate=gate,original_prediction=y,
                    extreme_prediction=y2,delete_prediction=yd,shuffle_prediction=ys,
                    original_q_ref=q,extreme_q_ref=q2,delete_q_ref=qd,shuffle_q_ref=qs,passed=passed))
    pred=pd.DataFrame(rows);pred.to_csv(TASK/'outputs/per_ck_predictions.csv',index=False)
    chk=pd.DataFrame(checks);chk.to_csv(run/'future_invariance.csv',index=False)
    summary=pred.groupby('candidate').agg(n_checkpoints=('checkup','count'),n_fallback=('fallback','sum'),
        n_eligible_events_final=('n_eligible_events','last'),max_abs_delta_pp=('delta_from_original_pp',lambda x:float(x.abs().max()))).reset_index()
    summary['causal_mutations_passed']=summary.candidate.map(chk.groupby('candidate').passed.all())
    summary['capacity_MAE_pp']=np.nan
    summary['capacity_status']='not_testable_CK1_CK7_hidden'
    summary.to_csv(TASK/'outputs/candidate_comparison.csv',index=False)
    result=dict(all_future_invariance_passed=bool(chk.passed.all()),n_tests=len(chk),candidates=summary.astype(object).where(pd.notna(summary),None).to_dict('records'))
    (run/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
    assert chk.passed.all()
    (run/'COMPLETED').write_text('completed\n')
    print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))

if __name__=='__main__':main()
