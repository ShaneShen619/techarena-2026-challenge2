"""Fit all real anchor cells with the frozen stage1 configuration and cache provenance."""
import hashlib
import json
import pickle
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
sys.path.insert(0,str(STUDY/'src'))
from common5b import H,CACHE5
from edata import anchor_curve
from emodel import OCP,fit_charge,charge_residual
from audit5b import dump,clean_json,neff,physical_charge,update_status
from v2 import anchors_by_checkup

def cache_key(q,I,V,fixed=None):
    h=hashlib.sha256()
    for a in (q,I,V):h.update(np.ascontiguousarray(a).tobytes())
    for p in [STUDY/'stage_1/protocol.json',HERE/'protocol.json',STUDY/'src/emodel.py',
              STUDY/'ocp/lfp_afshar2017.csv',STUDY/'ocp/graphite_chen2020.csv']:
        h.update(p.read_bytes())
    h.update(json.dumps(fixed or {},sort_keys=True).encode())
    return h.hexdigest()

def elapsed():
    return time.time()-json.loads((HERE/'outputs/runtime.json').read_text())['start_epoch']

if __name__=='__main__':
    (HERE/'outputs').mkdir(exist_ok=True)
    runtime=HERE/'outputs/runtime.json'
    if not runtime.exists():dump(runtime,{'start_epoch':time.time(),'cap_seconds':5400})
    op=H.full_op();anc=anchors_by_checkup(H.full_charges(op),H.CK)
    ocp=OCP('main');rows=[];all_fits={}
    for j in range(8):
        if elapsed()>5400:break
        q,I,V,rest,qtotal=anchor_curve(op,anc[j])
        cells=[]
        for c in range(4):
            key=cache_key(q,I,V[:,c])
            cache=Path(CACHE5)/f'fit_{key}.pkl'
            if cache.exists():
                x,info=pickle.loads(cache.read_bytes());origin='hashed cache'
            elif j in (0,1):
                label='main_anchor0' if j==0 else 'variant_anchor1'
                prior=pickle.loads((Path(CACHE5)/f'bol_{label}.pkl').read_bytes())
                x=np.asarray(prior['cells'][c],float)
                residual=charge_residual(x,q,I,V[:,c],ocp)[:-1]
                full_res=charge_residual(x,q,I,V[:,c],ocp)
                cost=float(4*np.sum(np.sqrt(1+(full_res/2)**2)-1))
                info={'cost':cost,'rms_mV':float(np.sqrt(np.mean(residual**2))),'resid_mV':residual}
                origin='completed stage2 fit'
                cache.write_bytes(pickle.dumps((x,info),protocol=5))
            else:
                x,info=fit_charge(q,I,V[:,c],ocp)
                origin='new frozen main fit'
                cache.write_bytes(pickle.dumps((x,info),protocol=5))
            residual=np.asarray(info['resid_mV'],float)[:len(q)]
            effective,rho=neff(residual)
            cells.append(x)
            rows.append({'anchor':j,'cell':c+1,'segment':int(anc[j].segment),'Q_fc_obs':qtotal,
                'Qn':float(x[0]),'Qp':float(x[1]),'QLi':float(x[2]),'theta_n0':float(x[3]),
                'theta_p0':float((x[2]-x[3]*x[0])/x[1]),'R':float(x[4]),'h':float(x[5]),
                'rms_mV':float(info['rms_mV']),'cost':float(info['cost']),'n':len(q),'n_eff':effective,
                'rho1':float(rho[1]),'rho5':float(rho[5]),'rho20':float(rho[20]),
                'physical_charge_valid':physical_charge(x,qtotal,ocp),'origin':origin,'cache_key':key,
                'pack_start_V':float(anc[j].pack_start_V),'start_time':str(anc[j].t_start),
                'end_time':str(anc[j].t_end)})
            pd.DataFrame(rows).to_csv(HERE/'outputs/S3_main_fits.csv',index=False)
            print(f'anchor {j} cell {c+1}: RMS={info["rms_mV"]:.3f} mV; n_eff={effective:.2f}; elapsed={elapsed():.1f}s',flush=True)
        all_fits[j]=cells
        (Path(CACHE5)/'all_main_fits.pkl').write_bytes(pickle.dumps(all_fits,protocol=5))
    result=pd.DataFrame(rows)
    baseline=result[result.anchor==0].set_index('cell')
    for name,col in [('LLI','QLi'),('LAM_NE','Qn'),('LAM_PE','Qp')]:
        result[name]=[float(baseline.loc[int(r.cell),col]-getattr(r,col)) for r in result.itertuples()]
    result.to_csv(HERE/'outputs/S3_main_fits.csv',index=False)
    dump(HERE/'outputs/S3_fit_completion.json',{'fit_rows':len(result),'expected':32,'complete':len(result)==32,
         'elapsed_seconds':elapsed(),'cap_reached':elapsed()>5400,'all_charge_states_valid':bool(result.physical_charge_valid.all())})
