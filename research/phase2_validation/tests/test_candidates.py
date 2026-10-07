"""Physical-sign, causality, persistence and order checks on isolated candidates."""
import os, subprocess, sys, textwrap
from pathlib import Path
import pytest

TASK=Path(__file__).resolve().parents[1]

SCRIPT=r'''
import pickle
from types import SimpleNamespace
import numpy as np
import pandas as pd
from my_model import ActiveModel

q=np.linspace(0,100,101)
reference=pd.DataFrame({'discharged_Ah':q,**{f'cell{i}_V':3.0+0.5*(1-q/100) for i in range(1,5)}})
def event(start,voltage_shift=0.0):
    t=pd.Timestamp(start)+pd.to_timedelta(np.arange(361)*10,unit='s')
    v=np.linspace(3.32+voltage_shift,3.47+voltage_shift,361)
    d=pd.DataFrame({'timestamp':t,'segment':1,'current_A':20.0,
        'temp_mean_C':45.0,'charge_Ah_cum':np.arange(361)*20/360,
        **{f'cell{i}_V':v for i in range(1,5)}})
    rest=d.tail(1).copy();rest['timestamp']=t[-1]+pd.Timedelta(seconds=10);rest['current_A']=0.0
    return pd.concat([d,rest],ignore_index=True)
past=pd.concat([event('2025-01-01'),event('2025-01-02',0.002)],ignore_index=True)
future=event('2025-01-03',0.09)
allop=pd.concat([past,future],ignore_index=True)
cutoff=pd.Timestamp('2025-01-02 23:00:00')
def dataset(op):
    return SimpleNamespace(operation=op,bol_capacity_Ah=100.0,reference_discharge=reference)
m1=ActiveModel();m1.fit(dataset(allop))
m2=ActiveModel();m2.fit(dataset(past))
p1=m1.estimate_soh(dataset(allop),cutoff)
d1=m1.last_diagnostics.copy()
p2=m2.estimate_soh(dataset(past),cutoff)
assert np.isfinite(p1) and abs(p1-p2)<1e-10,(p1,p2)
assert d1==m2.last_diagnostics,(d1,m2.last_diagnostics)
restored=pickle.loads(pickle.dumps(m1))
p3=restored.estimate_soh(dataset(past),cutoff)
assert abs(p3-p1)<1e-10
late=pd.Timestamp('2025-01-04')
_ = m1.estimate_soh(dataset(allop),late)
again=m1.estimate_soh(dataset(allop),cutoff)
assert abs(again-p1)<1e-10
assert abs(100.0/102.0*100.0-98.03921568627452)<1e-10
print('PASS',round(p1,6),d1)
'''

@pytest.mark.parametrize('route',['route_a','route_b'])
def test_fit_prefix_future_mutation_pickle_and_call_order(route):
    env=os.environ.copy()
    env['PYTHONPATH']=str(TASK/'candidates'/route)
    p=subprocess.run([sys.executable,'-c',SCRIPT],cwd=TASK/'candidates'/route,
                     env=env,capture_output=True,text=True,timeout=60)
    assert p.returncode==0,p.stdout+p.stderr

@pytest.mark.parametrize('route',['route_a','route_b'])
def test_sample_validator(route):
    candidate=TASK/'candidates'/route
    p=subprocess.run([sys.executable,str(candidate/'validate_submission.py')],capture_output=True,text=True,timeout=120)
    assert p.returncode==0,p.stdout+p.stderr
