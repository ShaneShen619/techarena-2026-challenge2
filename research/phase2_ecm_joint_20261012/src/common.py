"""Isolated research run. Source data and prior runs are read-only."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
import scipy

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
OUT = TASK / 'runs' / os.environ.get('ECM_RUN_ID', 'v1')
CFG = json.loads((TASK/'configs/protocol.json').read_text())
CELLS = [f'cell{i}_V' for i in range(1,5)]

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def json_dump(p, data):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    def conv(x):
        if isinstance(x,(np.integer,np.floating)): return x.item()
        if isinstance(x,np.ndarray): return x.tolist()
        if isinstance(x,(Path,pd.Timestamp)): return str(x)
        raise TypeError(type(x).__name__)
    Path(p).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=conv)+'\n')

def environment():
    return dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,platform=platform.platform(),
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())

def seconds(t, origin=None):
    t=pd.DatetimeIndex(t)
    return (t-(t[0] if origin is None else pd.Timestamp(origin))).total_seconds().to_numpy(float)

def qualified_history(events, target, n=4, same_panel=False):
    cutoff=pd.Timestamp(target['start'])
    return [e for e in events if e.get('qualified',True) and e['chain_ok'] and e['T']==target['T']
        and (not same_panel or e['panel']==target['panel'])
        and pd.Timestamp(e['available_after']) < cutoff
        and cutoff-pd.Timestamp(e['available_after'])<=pd.Timedelta(days=CFG['history_max_days'])][-n:]

def protected_paths():
    return sorted([*ROOT.glob('framework/*.py'),ROOT/'run_model.py',ROOT/'validate_submission.py',*ROOT.glob('my_model/*'),
        ROOT/'research/phase2_initial_soc_four_methods_20261011/decision.json',
        ROOT/'research/phase2_initial_soc_four_methods_20261011/runs/v1/EVALUATION_COMPLETE'])
