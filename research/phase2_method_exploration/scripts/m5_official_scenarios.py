"""Strict-prefix, assumption-driven official 4S scenario envelopes (no truth labels)."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M5_official_scenarios_v1';OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(TASK/'src'))
from m5_pack import CK0Pack,PackState,uniform_mean_state,minimum_cell_usable_Ah
cfg=json.loads((TASK/'configs/m5_official_scenarios.json').read_text())
prefix=pd.read_csv(TASK/'runs/M4_deep_charge_audit_v1/strict_prefix_deep_charge_proxy.csv')
pack=CK0Pack(pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz'))
rng=np.random.default_rng(cfg['seed'])
rows=[]
for ck in prefix.itertuples(index=False):
    if ck.checkup=='CK0':continue
    assert pd.Timestamp(ck.latest_deep_event)<pd.Timestamp(ck.date)
    center=float(ck.CK0_calibrated_charge_proxy_Ah)
    for j in range(cfg['draws_per_checkup']):
        common=np.clip(rng.normal(center,cfg['common_Q_proxy_uncertainty_Ah']),70,120)
        q=np.clip(common+rng.normal(0,cfg['per_cell_Q_spread_standard_deviation_Ah'],4),70,120)
        z=rng.uniform(*cfg['initial_SOC_range'],4)
        R=rng.uniform(*cfg['delta_R_ohm_range'],4)
        shape=rng.uniform(*cfg['unmodelled_shape_mV_range'],4)
        state=PackState(q,z,R)
        full=pack.cutoff(state,truth_shape_mV=shape,truth_dynamic_R=True)
        rows.append({'checkup':ck.checkup,'date':ck.date,'draw':j,
                     'deep_event_used':ck.latest_deep_event,'deep_lag_days':ck.lag_days,
                     'deep_proxy_Ah':center,'assumed_common_Q_Ah':common,
                     'explicit_group_Ah':full['group_capacity_Ah'],
                     'uniform_group_Ah':pack.cutoff(uniform_mean_state(state))['group_capacity_Ah'],
                     'minimum_cell_Ah':minimum_cell_usable_Ah(state),
                     'lowest_voltage_cell':full['lowest_voltage_cell'],
                     'lowest_cell_voltage_V':float(full['cutoff_cell_V'].min()),
                     'cell_below_2p5V':full['below_2p5V_at_group_cutoff']})
out=pd.DataFrame(rows);out.to_csv(OUT/'assumption_draws.csv',index=False)
summary=[]
for checkup,g in out.groupby('checkup',sort=True):
    summary.append({'checkup':checkup,'latest_deep_event':g.deep_event_used.iloc[0],
                    'deep_proxy_Ah':float(g.deep_proxy_Ah.iloc[0]),
                    'explicit_q05_Ah':float(g.explicit_group_Ah.quantile(.05)),
                    'explicit_q50_Ah':float(g.explicit_group_Ah.quantile(.5)),
                    'explicit_q95_Ah':float(g.explicit_group_Ah.quantile(.95)),
                    'uniform_q50_Ah':float(g.uniform_group_Ah.quantile(.5)),
                    'minimum_q50_Ah':float(g.minimum_cell_Ah.quantile(.5)),
                    'fraction_cell_below_2p5V':float(g.cell_below_2p5V.mean()),
                    'limiting_cell_counts_json':json.dumps(g.lowest_voltage_cell.value_counts().sort_index().to_dict())})
s=pd.DataFrame(summary);s.to_csv(OUT/'official_assumption_envelopes.csv',index=False)
(OUT/'summary.json').write_text(json.dumps({'checkpoints':len(s),'draws_per_checkup':cfg['draws_per_checkup'],
 'selection_notice':cfg['selection_notice'],'capacity_truth':'CK1-CK7 hidden; these are assumption-driven stress envelopes, not validated error bars'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checkpoints':len(s),'draws_per_checkup':cfg['draws_per_checkup']},ensure_ascii=False),flush=True)
