"""Dump candidate decisions without hidden labels; invoked after model runs."""
import csv, importlib.util, pickle, sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
sys.path.insert(0,str(ROOT))
from framework.data import load_dataset, load_eval_points


def run(route):
    package=TASK/'candidates'/route
    sys.path.insert(0,str(package))
    for name in list(sys.modules):
        if name=='my_model' or name.startswith('my_model.'):
            del sys.modules[name]
    with (TASK/'runs'/('A_official_v4' if route=='route_a' else 'B_official_v3')/'model_state.pkl').open('rb') as f:
        model=pickle.load(f)
    rows=[]
    for p in load_eval_points(ROOT/'data').itertuples():
        ds=load_dataset(ROOT/'data',until=p.date)
        y=model.estimate_soh(ds,p.date)
        rows.append({'route':route,'checkup':p.checkup,'date':str(p.date.date()),'soh':y,**model.last_diagnostics})
    return rows

if __name__=='__main__':
    all_rows=[]
    for route in ('route_a','route_b'):
        all_rows += run(route)
    out=TASK/'runs'/'official_diagnostics.csv'
    with out.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for row in all_rows for k in row)))
        writer.writeheader();writer.writerows(all_rows)
    print(out)
    print(pd.DataFrame(all_rows).to_string(index=False))
