"""Contracts that catch causal or physical changes, not implementation mirrors."""
import json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/"src"))
from exposure import intervals,histogram,histograms_at,rate_weights
from age_prior import MyModel,prior_value,shallow_observations
from fusion import correction_sequence


def frame(amps=100.,n=61,step=60.,temperature=25.):
    ts=pd.Timestamp('2025-01-14')+pd.to_timedelta(np.arange(n)*step,unit='s')
    return pd.DataFrame({'timestamp':ts,'segment':1,'current_A':amps,'temp_mean_C':temperature,'chamber_temperature_C':temperature,
        'cell1_V':np.linspace(3.3,3.51,n),'cell2_V':np.linspace(3.3,3.51,n),'cell3_V':np.linspace(3.3,3.51,n),'cell4_V':np.linspace(3.3,3.51,n)})


def dataset(op):
    ck=pd.DataFrame({'date':[pd.Timestamp('2025-01-14')],'capacity_Ah':[100.41]})
    return SimpleNamespace(operation=op,checkups_released=ck)


def test_constant_current_Ah_units_and_4S_no_multiplication():
    a,_=intervals(frame());assert histogram(a).sum()*102==pytest.approx(100.)


def test_small_positive_current_is_not_silently_zero_usage():
    a,_=intervals(frame(amps=.1));assert histogram(a).sum()*102==pytest.approx(.1)


def test_negative_current_and_zero_current_not_charged():
    for amps in [-100.,0.]:
        a,_=intervals(frame(amps=amps));assert histogram(a).sum()==0


def test_duplicates_and_long_gaps_not_integrated_twice():
    f=frame();f=pd.concat([f,f.iloc[[20]]]).sort_values('timestamp',kind='stable')
    a,diag=intervals(f);assert histogram(a).sum()*102==pytest.approx(100.);assert diag['duplicate_time_steps']==1
    g=frame(n=2,step=3600);a,_=intervals(g);assert histogram(a).sum()==0


def test_prefix_rate_and_histogram_do_not_read_future_run_median():
    f=frame(n=101,step=10);f.loc[f.index>=50,'current_A']=1e4
    cutoff=f.timestamp.iloc[40]+pd.Timedelta(nanoseconds=1)
    entire,_=intervals(f);prefix,_=intervals(f.loc[f.timestamp<cutoff])
    assert np.array_equal(histograms_at(entire,[cutoff])[0],histogram(prefix))


def test_training_source_state_does_not_depend_on_full_operation():
    m1=MyModel(TASK/'artifacts/source_prior.json');m2=MyModel(TASK/'artifacts/source_prior.json')
    m1.fit(dataset(frame()));m2.fit(dataset(frame().iloc[:0]))
    assert m1.q0==m2.q0 and m1.anchor_date==m2.anchor_date and m1.artifact==m2.artifact


def test_source_anchor_and_constant_condition_equivalence():
    artifact=json.loads((TASK/'artifacts/source_prior.json').read_text());m=artifact['model'];anchor=100.41*100/102.
    h=np.zeros(648);assert prior_value(m,h,anchor,artifact['xi0'])==pytest.approx(anchor)
    h[25*8+5]=50.
    weights=rate_weights(m['parameters'],m['rate_mode'])
    assert h@weights==pytest.approx(50*weights[25*8+5])


def test_missing_temperature_uses_visible_chamber_not_source_thermal_floor():
    f=frame(temperature=25.).drop(columns='temp_mean_C');a,_=intervals(f)
    assert a.temperature_C.eq(25.).all()


def test_shallow_endpoint_is_available_before_complete_charge_and_future_invariant():
    f=frame(n=121,step=30);f['current_A']=100.
    for c in ['cell1_V','cell2_V','cell3_V','cell4_V']:f[c]=np.linspace(3.2,3.8,len(f))
    first=f.index[f.cell1_V.ge(3.5)][0];prefix=f.iloc[:first+1].copy()
    a=shallow_observations(prefix);b=shallow_observations(f)
    assert len(a)==4
    assert np.allclose(a[[f'w{i:02d}_Ah' for i in range(9)]],b[[f'w{i:02d}_Ah' for i in range(9)]],equal_nan=True)
    assert (pd.to_datetime(a.fragment_end)<=prefix.timestamp.max()).all()


def test_monitor_does_not_change_point_prediction_if_voltage_changes():
    m=MyModel(TASK/'artifacts/source_prior.json');f=frame();m.fit(dataset(f));cut=f.timestamp.iloc[-1]
    a=m.estimate_soh(dataset(f),cut);f2=f.copy();f2.cell1_V+=.05;b=m.estimate_soh(dataset(f2),cut)
    assert a==pytest.approx(b);assert m.last_diagnostics['A_numeric_correction_enabled'] is False


def test_duplicate_observations_do_not_repeat_correction_and_K0_is_B():
    b=np.array([98.,97.,96.]);event=['a','a','b']
    out,log=correction_sequence(b,[2.,2.,2.],[True]*3,event,.2,1.)
    assert log[1]['increment_pp']==0 and log[0]['increment_pp']==pytest.approx(.2)
    no,log=correction_sequence(b,[2.,2.,2.],[True]*3,event,0.,1.)
    assert np.array_equal(no,b)


def test_same_total_exposure_different_order_collapses_to_same_prior():
    artifact=json.loads((TASK/'artifacts/source_prior.json').read_text());m=artifact['model']
    first=frame(amps=50.,temperature=25.);second=frame(amps=50.,temperature=45.)
    second.timestamp+=pd.Timedelta(hours=2);second.segment=2
    op=pd.concat([first,second],ignore_index=True)
    swapped=op.copy();swapped.temp_mean_C=np.where(swapped.segment.eq(1),45.,25.)
    ledger,_=intervals(op);other,_=intervals(swapped)
    h=histogram(ledger);reversed_h=histogram(other)
    assert np.array_equal(h,reversed_h)
    assert prior_value(m,h,98.44,.001)==pytest.approx(prior_value(m,reversed_h,98.44,.001))
    # This is an explicit model limitation, not evidence that real order is irrelevant.


def test_large_unobserved_exposure_holds_and_repeated_query_is_identical():
    f=frame(amps=20.,n=10,step=30)
    f.timestamp+=pd.Timedelta(days=365)
    m=MyModel(TASK/'artifacts/source_prior.json');m.fit(dataset(f));cut=f.timestamp.iloc[-1]
    a=m.estimate_soh(dataset(f),cut);b=m.estimate_soh(dataset(f),cut)
    assert a==b and m.last_diagnostics['status']=='hold_due_to_exposure_uncertainty'
    assert m.last_diagnostics['scenario_span_pp']>5


def test_all_outer_fits_and_residual_generation_exclude_held_entities():
    for row in json.loads((TASK/'outputs/inner_selection.json').read_text()):assert row['heldout'] not in row['training_cells']
    for row in json.loads((TASK/'outputs/residual_generation_audit.json').read_text()):assert row['residual_held'] not in row['source_fit_and_selection_cells']
    for row in pd.read_csv(TASK/'outputs/inner_B_predictions.csv').itertuples(index=False):
        ids=row.training_cells.split('|');assert row.outer_held not in ids and row.inner_held not in ids
