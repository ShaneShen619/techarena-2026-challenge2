"""Independent M5 conservation, step and physical-cell permutation checks."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
sys.path.insert(0,str(TASK/'src'))
from m5_pack import CK0Pack,PackState,Q0,I_DISCHARGE_A
ref=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
model=CK0Pack(ref)
state=PackState(np.array([90.,102.,97.,104.]),np.array([.97,1.,.99,.98]),
                np.array([.001,0,.0005,.0015]))
orig=model.cutoff(state)
assert abs(orig['cutoff_voltage_sum_V']-11.2)<1e-7
assert abs(model.stepped_cutoff(state,1)-model.stepped_cutoff(state,60))<.01
assert abs(model.stepped_cutoff(state,1)-orig['group_capacity_Ah'])<.01

# A physical cell carries both its state and its reference curve when renamed.
perm=np.array([2,0,3,1]);other=CK0Pack(ref)
for attr in ('curves','start','end','tail_slope','head_slope'):
    setattr(other,attr,getattr(other,attr)[perm])
renamed=PackState(state.capacity_Ah[perm],state.initial_SOC[perm],state.delta_R_ohm[perm])
assert abs(other.cutoff(renamed)['group_capacity_Ah']-orig['group_capacity_Ah'])<1e-8

# Integrated Ah and elapsed seconds agree at common current.
seconds=orig['group_capacity_Ah']*3600/I_DISCHARGE_A
assert abs(seconds*I_DISCHARGE_A/3600-orig['group_capacity_Ah'])<1e-10
ck0=PackState(np.full(4,Q0),np.ones(4),np.zeros(4))
assert abs(model.cutoff(ck0)['group_capacity_Ah']-100.412)<.03
print('M5 cutoff, unit, convergence and physical permutation checks passed')
