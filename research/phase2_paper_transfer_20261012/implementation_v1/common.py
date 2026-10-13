from pathlib import Path
import json, hashlib, pickle, sys
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
OLD=ROOT/'research/phase2_initial_soc_four_methods_20261011'
OLD_RUN=OLD/'runs/v1'
sys.path.insert(0,str(OLD/'src'))
import engine as legacy
import synthetic as generator
CFG=json.loads((TASK/'config.json').read_text())

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()

def events():return pickle.loads((TASK/'events.pkl').read_bytes())
def key(e):return f"{e['panel']}_{e['T']}"
def savejson(name,value):
    (TASK/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def protected():
    paths=list((OLD/'src').glob('*.py'))+list((OLD/'configs').glob('*'))
    paths += [OLD_RUN/'freeze_manifest.json',OLD_RUN/'EVALUATION_COMPLETE',OLD_RUN/'events.pkl']
    paths += list((ROOT/'my_model').glob('*.py'))
    return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()}

class StrictTemplate(legacy.Template):
    def values(self,x,cell):
        x=np.asarray(x,float)
        if np.any(x<self.x[0]-1e-9) or np.any(x>self.x[-1]+1e-9):
            raise ValueError('strict_template_domain')
        return np.interp(x,self.x,self.y[:,cell])

def prepare(e,tau,max_points=None):
    p=legacy.prepare(e,tau)
    if max_points and len(p['q'])>max_points:
        ix=np.unique(np.linspace(0,len(p['q'])-1,max_points).round().astype(int))
        p={k:v[ix] for k,v in p.items()}
    return p

def profile_path(e,loss,mode):
    return TASK/'profiles'/f"{e['id'].replace(':','-')}_{loss}_{mode}.npz"

def history(all_events,e,n=4):
    return [h for h in all_events if key(h)==key(e) and h['available_after']<e['start']][-n:]
