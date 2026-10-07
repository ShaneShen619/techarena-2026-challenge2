import sys
from pathlib import Path
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from event_core import extract_charge_events, partial_ah


def frame(seconds, voltage, current=10):
    return pd.DataFrame({'timestamp':pd.Timestamp('2025-01-01')+pd.to_timedelta(seconds,unit='s'),
        'current_A':current,'cell1_V':voltage,'segment':1,'temp_mean_C':25.0})


def test_integral_and_crossing_interpolation():
    d=frame(np.arange(0,110,10),np.linspace(3.30,3.50,11))
    d=pd.concat([d,frame([110],[3.5],current=0)],ignore_index=True)
    e=extract_charge_events(d,voltage_cols=('cell1_V',),min_duration_s=60)
    assert len(e)==1
    assert np.isclose(e[0].ah,10*100/3600)
    assert np.isclose(partial_ah(e[0],0,3.34,3.44),10*50/3600)


def test_duplicate_and_gap_never_integrated():
    d=frame([0,10,20,30,40,50,60,70,80,90,90,200,210,220,230,240,250,260,270,280,290],
            np.linspace(3.3,3.5,21))
    d=pd.concat([d,frame([300],[3.5],current=0)],ignore_index=True)
    e=extract_charge_events(d,voltage_cols=('cell1_V',),min_duration_s=60)
    assert len(e)==2
    assert all(x.ah < 0.3 for x in e)


def test_future_cutoff_and_missing_cell():
    d=frame(np.arange(0,210,10),np.linspace(3.3,3.5,21))
    d=pd.concat([d,frame([210],[3.5],current=0)],ignore_index=True)
    e=extract_charge_events(d,voltage_cols=('cell1_V',),until=pd.Timestamp('2025-01-01 00:03:30'))
    assert len(e)==1 and e[0].end<=pd.Timestamp('2025-01-01 00:03:30')
    assert partial_ah(e[0],1,3.33,3.4) is None


def test_no_unfinished_window_at_cutoff():
    d=frame(np.arange(0,210,10),np.linspace(3.3,3.5,21))
    e=extract_charge_events(d,voltage_cols=('cell1_V',),until=pd.Timestamp('2025-01-01 00:01:00'))
    assert len(e)==0


def test_empty_prefix_and_nan_voltage_do_not_create_evidence():
    assert extract_charge_events(pd.DataFrame()) == []
    d=frame(np.arange(0,210,10),np.linspace(3.3,3.5,21))
    d.loc[10,'cell1_V']=np.nan
    d=pd.concat([d,frame([210],[3.5],current=0)],ignore_index=True)
    # The invalid midpoint splits the charge into runs too short to establish
    # a reliable full-window Ah measurement.
    assert all(partial_ah(e,0,3.33,3.47) is None for e in
               extract_charge_events(d,voltage_cols=('cell1_V',)))


def test_counter_reset_cannot_replace_current_integration():
    d=frame(np.arange(0,210,10),np.linspace(3.3,3.5,21))
    d['charge_Ah_cum']=np.arange(len(d))*10/3600
    d.loc[11:,'charge_Ah_cum']-=1.0
    d=pd.concat([d,frame([210],[3.5],current=0)],ignore_index=True)
    e=extract_charge_events(d,voltage_cols=('cell1_V',),counter_col='charge_Ah_cum')
    assert len(e)==1
    assert partial_ah(e[0],0,3.34,3.44) is not None
    assert partial_ah(e[0],0,3.34,3.44,use_counter=True) is None
