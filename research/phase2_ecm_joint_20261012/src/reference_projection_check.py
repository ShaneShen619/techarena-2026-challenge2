"""Targeted reference-coordinate fix; primary frozen predictions/scale roots are unchanged."""
from __future__ import annotations
import importlib.util,json
import numpy as np
import pandas as pd
from common import TASK,OUT,digest,json_dump
from ecm import Reference

def run():
    old_path=OUT/'source_snapshot/ecm_before_reference_shift_correction.py'
    spec=importlib.util.spec_from_file_location('reference_before_correction',old_path)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    before=old.Reference();after=Reference();dif=[]
    for a in [.7,.8,.9,1.,1.05]:
        q=np.linspace(0,a*100.41,201)
        dif.append(float(np.max(abs(before.pack_voltage(q,a)-after.pack_voltage(q,a)))))
        dif.append(abs(before.capacity(a)-after.capacity(a)))
    assert max(dif)<1e-10
    params=json.loads((OUT/'checkup_parameters.json').read_text());rows=[]
    for p in [p for p in params if p['model']=='base']:
        for label,shift,R,chain in [('baseline',None,None,0.),('all_cells_0p5Ah_underfull',np.full(4,.5),None,0.),
            ('one_cell_1Ah_underfull',np.array([0.,1.,0.,0.]),None,0.),('aging_R_all_0p1mOhm',None,np.full(4,.0001),0.),
            ('CK0_chain_minus4mV',None,None,-.004),('CK0_chain_plus4mV',None,None,.004)]:
            try:value=after.capacity(p['alpha'],shift,R,chain);status='conditional_projection'
            except ValueError as exc:value=None;status=str(exc)
            rows.append(dict(checkup=p['checkup'],T=p['T'],assumption=label,capacity_Ah=value,status=status,not_inferred_from_running_offset=True))
    pd.DataFrame(rows).to_csv(OUT/'reference_assumptions.csv',index=False)
    json_dump(OUT/'reference_projection_correction.json',dict(reason='A common reference-position shift must also shift the CK0 pack-sum residual mapping; original unshifted mapping could lose a bracket from millivolt rounding.',
        original_source_sha256=digest(old_path),corrected_source_sha256=digest(TASK/'src/ecm.py'),
        primary_zero_shift_voltage_and_capacity_max_difference=max(dif),primary_prediction_estimation_and_thresholds_changed=False,
        rerun_scope='reference perturbation projections and scientific invariants only',unequal_cell_mapping='mean reference coordinate remains a conditional assumption',
        frozen_original_preserved=str(old_path)))
    print('reference mapping correction: primary zero-shift outputs unchanged',max(dif),flush=True)

if __name__=='__main__':run()
