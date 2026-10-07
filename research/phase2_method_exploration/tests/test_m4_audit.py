"""Independent recomputation of M4 visibility and voltage score invariants."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
R=TASK/'runs/M4_state_identifiability_v4'
p=pd.read_csv(R/'official_forward_predictions.csv')
diag=pd.read_csv(R/'official_gate_diagnostics.csv')
assert len(diag)==148
assert p.q_Ah.min()>=2 and p.q_Ah.max()<=10
assert not diag.gate_accept.any()
assert np.allclose(diag.Q_gated_Ah,100.41)
for cell,group in diag.sort_values('start').groupby('cell'):
    assert np.allclose(group.uncertainty_halfwidth_Ah.to_numpy(),10+.5*np.arange(1,len(group)+1))
assert set(p.method)=={'CK0_fixed_shape','CK0_fixed_RC_from_prior','last_same_temp_shift',
                       'early_ungated_Q_SOC','early_gated_Q_fixed_SOC'}
recalc=(p.assign(a=p.error_mV.abs()).groupby(['start','cell','method']).a.mean()
        .reset_index().groupby('method').a.mean())
summary=json.loads((R/'summary.json').read_text())
for k,v in summary['official_voltage_MAE_mV_by_method'].items():
    assert abs(recalc[k]-v)<1e-9,(k,recalc[k],v)
old=json.loads((TASK/'runs/M1_voltage_forecast_v1/summary.json').read_text())
assert abs(recalc['last_same_temp_shift']-old['mae_mV_by_method']['matched_last_shift'])<1e-9
assert diag.Q_ungated_Ah.eq(70).all()  # all unconstrained fits hit lower bound

deep=pd.read_csv(TASK/'runs/M4_deep_charge_audit_v1/strict_prefix_deep_charge_proxy.csv')
for row in deep.itertuples(index=False):
    if pd.notna(row.latest_deep_event):
        assert pd.Timestamp(row.latest_deep_event)<pd.Timestamp(row.date)
assert abs(deep.iloc[0].CK0_calibrated_charge_proxy_Ah-100.41)<1e-12
assert deep.iloc[-1].checkup=='CK7'
last_event=pd.read_csv(TASK/'runs/M4_deep_charge_audit_v1/deep_charge_events.csv')
assert pd.Timestamp(last_event.event_end.iloc[-1])>pd.Timestamp(deep.date.iloc[-1])
assert deep.latest_deep_event.iloc[-1]!=last_event.event_end.iloc[-1]

s=pd.read_csv(R/'synthetic_identifiability.csv')
assert s.loc[s.window_Ah.eq(10),'gate_accept'].sum()==0
assert s.loc[s.window_Ah.eq(90),'capacity_unique_signal_mV_for_10Ah'].median()>s.loc[s.window_Ah.eq(10),'capacity_unique_signal_mV_for_10Ah'].median()
print('M4 independent score and causal-prefix audit passed')
