"""Independent M5 score and causal-time recomputation from saved predictions."""
from pathlib import Path
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1]
r=TASK/'runs/M5_pack_v1'
p=pd.read_csv(r/'synthetic_pack_predictions.csv')
s=pd.read_csv(r/'method_scores.csv')
for row in s.itertuples(index=False):
    mask=p.family.eq(row.family)&p.information.eq(row.information)&p.method.eq(row.method)
    g=p.loc[mask]
    if row.subset=='no_cell_below_2p5V':g=g.loc[~g.truth_below_2p5V]
    assert len(g)==row.n
    assert abs(g.error_Ah.abs().mean()-row.MAE_Ah)<1e-10
    assert abs(g.error_Ah.abs().quantile(.95)-row.P95_abs_Ah)<1e-10

d=pd.read_csv(TASK/'runs/M5_delayed_proxy_v1/causal_predictions.csv')
for row in d.itertuples(index=False):
    target=int(row.checkup[2:]);prior=int(row.latest_observation_checkpoint[2:])
    assert prior==target-1
assert not d.truth_Ah.isna().any()

o=pd.read_csv(TASK/'runs/M5_official_scenarios_v1/assumption_draws.csv')
e=pd.read_csv(TASK/'runs/M5_official_scenarios_v1/official_assumption_envelopes.csv')
for row in e.itertuples(index=False):
    g=o.loc[o.checkup.eq(row.checkup)]
    assert len(g)==2000
    assert (pd.to_datetime(g.deep_event_used)<pd.to_datetime(g.date)).all()
    for q,name in ((.05,'explicit_q05_Ah'),(.5,'explicit_q50_Ah'),(.95,'explicit_q95_Ah')):
        assert abs(g.explicit_group_Ah.quantile(q)-getattr(row,name))<1e-9
assert set(e.checkup)=={f'CK{i}' for i in range(1,8)}
print('M5 independent score, prefix and assumption-envelope checks passed')
