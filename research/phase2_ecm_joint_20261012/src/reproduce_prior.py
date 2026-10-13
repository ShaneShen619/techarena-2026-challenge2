"""Read-only three-event reproduction of the old loaded-curve failure profile."""
from __future__ import annotations
import importlib.util,pickle,sys
import numpy as np
import pandas as pd
from common import ROOT,OUT,json_dump

def run():
    folder=ROOT/'research/phase2_initial_soc_four_methods_20261011'
    sys.path.insert(0,str(folder/'src'))
    spec=importlib.util.spec_from_file_location('prior_engine_readonly',folder/'src/engine.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    with (folder/'runs/v1/events.pkl').open('rb') as f:events=pickle.load(f)
    ref=old.Template();rows=[]
    for panel,T in [('short',25),('short',45),('wide',45)]:
        e=next(e for e in events if e['panel']==panel and e['T']==T and e['chain_ok'])
        result=old.profile(ref,e,600);rms=np.sqrt(result['loss'].mean(axis=1))*1000
        finite=rms<=np.min(rms)+1.;caps=np.array([ref.capacity(s) for s in result['sgrid'][finite]])
        cache=folder/'runs/v1/profiles'/f"{e['id'].replace(':','-')}_600_free.npz"
        diff=None
        if cache.exists():
            z=np.load(cache);diff=float(np.max(np.abs(z['loss']-result['loss'])))
        rows.append(dict(id=e['id'],panel=panel,T=T,q_Ah=e['q_total'],best_rms_mV=float(rms.min()),profile_width_Ah=float(np.ptp(caps)),
            cached_loss_max_difference=diff,old_capacity_update_gate=bool(np.ptp(caps)<=5),read_only_old_artifacts=True))
    pd.DataFrame(rows).to_csv(OUT/'prior_reproduction.csv',index=False)
    json_dump(OUT/'prior_reproduction_summary.json',dict(events=len(rows),rows=rows,definition='Single-event old failure subset; no reopening full old evaluation or tuning',
        exact_cached_profiles_reproduced=sum(r['cached_loss_max_difference'] is not None and r['cached_loss_max_difference']<1e-12 for r in rows)))
    print(rows,flush=True)

if __name__=='__main__':run()
