import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'candidates/route_b'))
from my_model.model_route_b import RouteB
from my_model.event_core import Event


def prepared_model():
    z=np.linspace(1,0,1001)
    voltage=(3.15+0.2*z+0.105/(1+np.exp(-(z-.9)/.032))
             -0.56/(1+np.exp((z-.055)/.018)))
    ref=pd.DataFrame({'discharged_Ah':100*(1-z),
        **{f'cell{i}_V':voltage for i in range(1,5)}})
    model=RouteB()
    model.fit(SimpleNamespace(bol_capacity_Ah=100,reference_discharge=ref))
    return model


def charge_event(model,z0):
    q=np.linspace(0,14,100)
    voltage=model._ocv(z0+q/95)+0.07
    times=np.arange(100)*25
    return Event(pd.Timestamp('2025-01-01'),pd.Timestamp('2025-01-01')+pd.Timedelta(seconds=int(times[-1])),
        1,20,25,float(times[-1]),14.0,times,q,np.column_stack([voltage]*4),None,('cell1_V',))


def test_high_slope_capacity_identifiable_in_mathematical_self_check():
    model=prepared_model()
    result,reason=model._event_fit(charge_event(model,0.84),100)
    assert reason=='accepted'
    assert abs(result['q_fit']-95)<0.1
    assert result['sigma_min']>0.05


def test_flat_plateau_capacity_rejected_despite_perfect_voltage_fit():
    model=prepared_model()
    result,reason=model._event_fit(charge_event(model,0.4),100)
    assert reason=='unidentifiable'
    assert result['voltage_rmse_V']<0.001
    assert result['sigma_min']<0.05
