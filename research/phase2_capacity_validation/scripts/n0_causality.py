"""Eight-checkpoint, all-future-data causality and serialization audit."""
import copy
import hashlib
import importlib.util
import json
import os
import pickle
import platform
import shutil
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework.data import load_dataset
sys.path.insert(0,str(ROOT/'research/phase2_baseline_repair/candidates/causal_baseline'))
from my_model.model_baseline import ActiveModel,events

def dataset_with(base,op):
    d=copy.copy(base);d.operation=op;return d

def state_and_result(base,training,prefix,gate,date):
    model=ActiveModel(gate);model.fit(dataset_with(base,training))
    blob=pickle.dumps(model,protocol=4)
    restored=pickle.loads(blob)
    value=restored.estimate_soh(dataset_with(base,prefix),date)
    return blob,float(value),restored.last_q_ref

def main():
    began=time.time();run=TASK/'runs/N0_causality_20260930_v1';run.mkdir(exist_ok=True)
    full=load_dataset(ROOT/'data');op=full.operation
    src=ROOT/'research/phase2_baseline_repair/candidates/causal_baseline/my_model/model_baseline.py'
    cfg=TASK/'configs/protocol_v1.json'
    source_hash=hashlib.sha256(src.read_bytes()).hexdigest()
    config_hash=hashlib.sha256(cfg.read_bytes()).hexdigest()
    gates=['none','start','gap','combined','range']
    coverage=[];mutations=[]
    for point in full.eval_points.itertuples():
        date=pd.Timestamp(point.date)
        mask=op.timestamp<=date
        prefix=op.loc[mask].reset_index(drop=True)
        after=op.loc[~mask]
        count=len(events(prefix))
        coverage.append(dict(checkup=point.checkup,date=str(date),prefix_rows=len(prefix),future_rows=len(after),prefix_events=count,
            source_hash=source_hash,config_hash=config_hash,evidence_level='official_operating_data_unlabeled'))
        changed=op.copy()
        changed.loc[~mask,'current_A']=1e6
        changed.loc[~mask,'pack_voltage_V']=14.1
        shuffled=pd.concat([prefix,after.sample(frac=1,random_state=20260930)],ignore_index=True)
        variants={'delete':prefix,'shuffle':shuffled,'extreme':changed}
        for gate in gates:
            state0,value0,q0=state_and_result(full,op,prefix,gate,date)
            # A previous CK evaluation must not poison a subsequent independent CK call.
            seq=ActiveModel(gate);seq.fit(full)
            seq.estimate_soh(dataset_with(full,op),'2025-08-28')
            ordered=float(seq.estimate_soh(dataset_with(full,prefix),date))
            for intervention,training in variants.items():
                # A fresh fit on the mutated full data, then inference receives exactly its prefix.
                p=training.loc[training.timestamp<=date].reset_index(drop=True)
                state,value,q=state_and_result(full,training,p,gate,date)
                mutations.append(dict(checkup=point.checkup,candidate=gate,intervention=intervention,
                    future_rows=len(after),reference_prediction_pct=value0,changed_prediction_pct=value,
                    delta_pp=value-value0,reference_q_ref_Ah=q0,changed_q_ref_Ah=q,
                    training_state_equal=state0==state,ordered_call_equal=ordered==value0,
                    passed=(value==value0 and q==q0 and state==state0 and ordered==value0),
                    evidence_level='official_prefix_invariance_not_capacity_accuracy'))
    a=pd.DataFrame(coverage);b=pd.DataFrame(mutations)
    a.to_csv(TASK/'outputs/causal_coverage.csv',index=False)
    b.to_csv(TASK/'outputs/causal_mutations.csv',index=False)
    result=dict(run_id=run.name,started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(began)),
        duration_s=round(time.time()-began,3),python=platform.python_version(),free_disk_GiB=round(shutil.disk_usage(ROOT).free/2**30,2),
        cpu_count=os.cpu_count(),source_sha256=source_hash,config_sha256=config_hash,
        total_operation_rows=len(op),n_checkpoints=len(a),all_checkpoints_have_future=bool((a.future_rows>0).all()),
        ck7_future_rows=int(a.loc[a.checkup=='CK7','future_rows'].iloc[0]),n_mutation_cases=len(b),
        all_passed=bool(b.passed.all()),n_failures=int((~b.passed).sum()))
    (run/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    if not result['all_passed']:raise AssertionError(result)
    (run/'COMPLETED').write_text('complete\n')
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
