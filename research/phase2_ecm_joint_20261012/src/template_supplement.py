"""CK7 template/raw-table and small shape sensitivities, never selects a main model."""
from __future__ import annotations
import copy,json
import numpy as np
import pandas as pd
from common import OUT,json_dump
from audit_events import load
from ecm import Reference,predict
from joint_estimation import Window
from identifiability import profile

def run():
    if (OUT/'TEMPLATE_SUPPLEMENT_COMPLETE').exists():raise RuntimeError('Template supplement already complete')
    json_dump(OUT/'template_supplement_protocol.json',dict(date='2026-10-13',query='CK7 midnight',
        scenarios=['raw_CK0_table','constant_plus1mV','midshape_plus2mV','midshape_minus2mV'],
        scope='Post-scoring structural diagnostic required by prompt; perturbations are hypotheses, not measured OCV ageing; no primary model selection'))
    es=load();ref=Reference();selected=json.loads((OUT/'selected_configuration.json').read_text());rows=[];curves=[];stage=[]
    original=json.loads((OUT/'checkup_parameters.json').read_text())
    for T in [25,45]:
        hh=[e for e in es if e['T']==T and e['chain_ok'] and e['available_after']<='2025-08-28T00:00:00'][-4:]
        tau=selected[str(T)]['tau']
        base=next(p for p in original if p['checkup']=='CK7' and p['T']==T and p['model']=='base')
        fit=dict(alpha=base['alpha'],params=np.asarray(base['params']),tau=tau,charge_history=True,temperature=True)
        for e in hh:
            pred=predict(ref,e,fit)
            for ph,name in [(0,'pre_rest'),(1,'discharge'),(2,'post_rest')]:
                use=e['phase']==ph
                if use.any():stage.append(dict(id=e['id'],T=T,phase=name,rows=int(use.sum()),reconstruction_mae_mV=float(abs(pred[use]-e['y'][use]).mean()*1000)))
        for name in ['raw_CK0_table','constant_plus1mV','midshape_plus2mV','midshape_minus2mV']:
            changed=copy.deepcopy(ref)
            if name=='raw_CK0_table':changed.x=changed.raw_x;changed.v=changed.raw_v
            elif name=='constant_plus1mV':changed.v=changed.v+.001
            else:changed.v=changed.v+(.002 if name=='midshape_plus2mV' else -.002)*np.tanh((changed.x[:,None]-50)/5)
            pr=profile(Window(changed,hh,tau),1.)
            rows.append(dict(T=T,scenario=name,best_capacity_Ah=pr['best_capacity_Ah'],width_Ah=pr['width_Ah'],minimum_rms_mV=pr['minimum_rms_mV'],accepted=False))
            for C,r in zip(pr['capacity'],pr['rms']):curves.append(dict(T=T,scenario=name,capacity_Ah=C,rms_mV=r))
            print('template sensitivity',T,name,flush=True)
    pd.DataFrame(rows).to_csv(OUT/'template_supplement.csv',index=False)
    pd.DataFrame(curves).to_csv(OUT/'template_supplement_profiles.csv',index=False)
    pd.DataFrame(stage).to_csv(OUT/'CK7_stage_reconstruction.csv',index=False)
    (OUT/'TEMPLATE_SUPPLEMENT_COMPLETE').write_text('Supplement complete. Main model/scoring unchanged.\n')

if __name__=='__main__':run()
