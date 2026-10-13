"""Causal event cache, pseudo scenarios, proxy scoring and common gates."""
import pickle
import hashlib
import numpy as np
import pandas as pd
from common import STUDY, PACKAGE, dump
from framework.data import load_dataset, load_eval_points
from events import full_charges, step_programs, charge_step_split, STEP_VARIANTS
from v2 import anchors_by_checkup, month_steps, m4, v2

DATA = PACKAGE / 'data'
CK = pd.DatetimeIndex(load_eval_points(DATA).date)
DELTAS = (0., .4, .8)
SMOOTHS = (1., 2., 3.)

def extract(op):
    fc = full_charges(op)
    return {'fc': fc, 'steps': {v: step_programs(op, **cfg) for v,cfg in STEP_VARIANTS.items()},
            'a4': {s: charge_step_split(op, fc, s) for s in SMOOTHS}}

def cut_operation(op, k, scenario='normal', steps=None, fc=None):
    """Keep completed deep discharges, not just their pre-discharge CV ends."""
    op = op[op.timestamp <= CK[k]].copy()
    if scenario.startswith('PC'):
        return op[op.timestamp <= CK[k] - pd.Timedelta(days=int(scenario[2:]))].reset_index(drop=True)
    if scenario.startswith('PG'):
        fc = full_charges(op) if fc is None else fc
        steps = step_programs(op) if steps is None else steps
        anc = anchors_by_checkup(fc, CK)
        s = month_steps(steps, anc, k-1)
        s = s[s.setpoint_C == 45].sort_values('t_cv_end')
        if len(s):
            r = s.iloc[min(int(scenario[2:]), len(s))-1]
            op = op[~((op.segment == r.segment) & (op.timestamp > r.t_measured))]
    if scenario == 'LOAO':
        fc = full_charges(op) if fc is None else fc
        anc = anchors_by_checkup(fc, CK)
        if k-1 in anc:
            r = anc[k-1]
            op = op[~((op.segment == r.segment) & (op.timestamp >= r.t_start) & (op.timestamp <= r.t_end))]
    return op.reset_index(drop=True)

def bundle(k, scenario='normal'):
    path = STUDY / f'cache/{scenario}_CK{k}_v1.pkl'
    if path.exists():
        return pickle.loads(path.read_bytes())
    ds = load_dataset(DATA, until=CK[k])
    op = cut_operation(ds.operation, k, scenario)
    out = extract(op)
    out.update(k=k, scenario=scenario, op=op)
    path.write_bytes(pickle.dumps(out, protocol=5))
    return out

def eps0(fc):
    f = fc[fc.setpoint_C == 45]
    return 100.41 - float(f.Q_Ah.iloc[0]) if len(f) else 0.

def proxies():
    path = STUDY / 'cache/proxies.pkl'
    if path.exists():
        return pickle.loads(path.read_bytes())
    fc = full_charges(load_dataset(DATA).operation)
    anc = anchors_by_checkup(fc, CK)
    out = {k: float(anc[k].Q_Ah) + eps0(fc) for k in range(1,8)}
    path.write_bytes(pickle.dumps(out))
    return out

def scenarios():
    return [('normal', range(1,8)), ('PG1', range(4,8)), ('PG2', range(4,8)),
            ('PC5', range(2,8)), ('PC10', range(2,8))]

def evaluate(models, scenario_list=None, robust=True):
    labels = proxies()
    rows = []
    for scenario, ks in scenarios() if scenario_list is None else scenario_list:
        for k in ks:
            b = bundle(k, scenario)
            settings = [(v,2.) for v in STEP_VARIANTS] + [('main',1.), ('main',3.)] if robust else [('main',2.)]
            for variant, smooth in settings:
                for delta in DELTAS:
                    for name, fn in models.items():
                        val = fn(b, variant, smooth, eps0(b['fc']) + delta)
                        q, meta = val if isinstance(val, tuple) else (val,{})
                        rows.append(dict(model=name, scenario=scenario, k=k, step=variant, smooth=smooth,
                                         delta=delta, Q=q, proxy_Q=labels[k]+delta,
                                         err_pp=(q-labels[k]-delta)/102*100, **meta))
    return pd.DataFrame(rows)

def metrics(pred):
    keys = ['model','scenario','step','smooth','delta']
    rows=[]
    for key,g in pred.groupby(keys):
        e=g.err_pp.to_numpy()
        rows.append(dict(zip(keys,key), MAE=float(np.abs(e).mean()), MAX=float(np.abs(e).max()),
                         RMSE=float(np.sqrt(np.mean(e*e))), CK2_7_MAE=float(g[g.k>=2].err_pp.abs().mean())))
    return pd.DataFrame(rows)

BASELINES = {'M4': lambda b,v,s,e: m4(b['fc'],b['steps'][v],e),
             'V2': lambda b,v,s,e: v2(b['fc'],b['steps'][v],b['a4'][s],CK,b['k'],e)[0]}

def save_eval(stage, pred):
    out=STUDY / f'stage_{stage}/outputs'
    pred.to_csv(out/'predictions.csv', index=False)
    metrics(pred).to_csv(out/'metrics.csv', index=False)
    return metrics(pred)

def gates(pred, name):
    met=metrics(pred)
    m=met.set_index(['model','scenario','step','smooth','delta'])
    wins=0
    for variant in STEP_VARIANTS:
        wins += bool(m.loc[(name,'normal',variant,2.,.4),'MAE'] < m.loc[('V2','normal',variant,2.,.4),'MAE'])
    p=pred[(pred.scenario=='normal') & (pred.step=='main') & (pred.smooth==2.) & (pred.delta==.4)]
    a=p[p.model==name].set_index('k').err_pp
    b=p[p.model=='V2'].set_index('k').err_pp
    return {'G-proxy': all(m.loc[(name,'normal','main',2.,d),'MAE'] < m.loc[('V2','normal','main',2.,d),'MAE'] and m.loc[(name,'normal','main',2.,d),'MAX'] <= m.loc[('V2','normal','main',2.,d),'MAX']+.1 for d in DELTAS),
            'G-epsfree': bool(m.loc[(name,'normal','main',2.,.4),'CK2_7_MAE'] <= m.loc[('V2','normal','main',2.,.4),'CK2_7_MAE']-.02),
            'G-robust': wins>=5, 'step_wins':wins,
            'G-regress': bool((a.abs()-b.abs()).max()<=.3), 'max_regression_pp':float((a.abs()-b.abs()).max())}

