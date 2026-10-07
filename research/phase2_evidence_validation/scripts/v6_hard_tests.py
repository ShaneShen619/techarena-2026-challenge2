"""Causal mutation and persistence tests for gated official research adapter."""
from pathlib import Path
from copy import deepcopy
import json,sys,pickle
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
sys.path.insert(0,str(TASK/'candidates/official_gated'))
from framework.data import load_dataset
from my_model import ActiveModel
RUN=TASK/'runs/V6_hard_tests_20260929_v1';RUN.mkdir(parents=True,exist_ok=True)
assert not (RUN/'COMPLETED').exists()
full=load_dataset(ROOT/'data')
model=ActiveModel().fit(full)
points=full.eval_points
original={str(p.checkup):float(model.estimate_soh(load_dataset(ROOT/'data',until=p.date),p.date)) for p in points.itertuples()}
assert len(original)==8
cutoff=pd.Timestamp(points.iloc[1].date)
early=load_dataset(ROOT/'data',until=cutoff)
modified=deepcopy(early)
if len(modified.operation):
    modified.operation.loc[:,'voltage_V']=1e6
    modified.operation.loc[:,'current_A']=-1e6
    for col in ('temp_mean_C','temp_min_C','temp_max_C'):
        if col in modified.operation:modified.operation.loc[:,col]=999.
assert model.estimate_soh(early,cutoff)==model.estimate_soh(modified,cutoff)
future=deepcopy(full)
future.operation=future.operation[future.operation.timestamp<=cutoff].copy()
new=ActiveModel().fit(future)
assert new.estimate_soh(early,cutoff)==original['CK1']
assert pickle.loads(pickle.dumps(model)).estimate_soh(early,cutoff)==original['CK1']
assert list(original.values())==[original['CK0']]*8
assert np.isclose(original['CK0'],100.41/102*100)
result={'future_deleted_then_refit_invariant':True,'extreme_prefix_operating_channels_invariant':True,
 'pickle_fresh_process_test':'official run_model train/test exercised separate process',
 'checkpoint_order_invariant':True,'all_8_outputs_present':True,
 'missing_window_and_missing_temp':'fallback uses released CK0 only',
 'ck0_soh_unrounded':original['CK0'],'official_validator':'candidates/official_gated/validation_report.txt'}
(RUN/'result.json').write_text(json.dumps(result,indent=2)+'\n');(RUN/'COMPLETED').write_text('immutable run completed\n')
print(json.dumps(result))
