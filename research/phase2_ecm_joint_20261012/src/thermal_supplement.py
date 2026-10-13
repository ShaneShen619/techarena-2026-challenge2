"""Complete the temperature-return control with separate seeds; never retunes primary scoring."""
from __future__ import annotations
import numpy as np
import pandas as pd
from common import OUT,json_dump
from mechanisms import reference,event
from ecm import Reference
from joint_estimation import Window
from identifiability import profile

def run():
    if (OUT/'THERMAL_SUPPLEMENT_COMPLETE').exists():raise RuntimeError('Supplement already completed; use new ECM_RUN_ID')
    seeds=list(range(1301,1311));temps=[25,45,25]
    json_dump(OUT/'thermal_supplement_protocol.json',dict(seeds=seeds,temperature_sequence_C=temps,capacity_constant=True,
        operation='Independent full-charge control reset at each temperature; no claim of continuous uncontrolled thermal-path validation',
        tau_s=600,delta_mV=1,selection_use=False,
        reason='Primary temperature scenario tested 45C transfer. This separately completes the prescribed return-to25 control without changing the primary model/test.'))
    rows=[]
    for seed in seeds:
        rng=np.random.default_rng(seed);Q=np.full(4,102.)
        R=np.vstack([rng.uniform(.0007,.0011,4),rng.uniform(.00008,.00016,4),rng.uniform(.0004,.0007,4)])
        start=rng.uniform(.18,.24,4);x,v,pk,q0=reference(Q,R,25,start)
        ref=Reference(x,v,pk,q0=q0)
        for k,T in enumerate(temps):
            Ri=R*np.exp(-.02*(T-25))
            e=event(seed,k,Q,Ri,T,start,5.,60.)
            pr=profile(Window(ref,[e],600),1.,fine=True)
            rows.append(dict(seed=seed,step=k,temperature_C=T,reference_capacity_Ah=q0,best_capacity_Ah=pr['best_capacity_Ah'],
                local_gate=pr['accepted'],width_Ah=pr['width_Ah'],constant_true_protocol_capacity_Ah=q0,
                best_error_Ah=abs(pr['best_capacity_Ah']-q0)))
        print('temperature-return control',seed,flush=True)
    df=pd.DataFrame(rows);df.to_csv(OUT/'thermal_return_controls.csv',index=False)
    pair=df.pivot(index='seed',columns='step',values='best_capacity_Ah')
    json_dump(OUT/'thermal_return_summary.json',dict(paired_seeds=10,conditional_warm_minus_initial_mean_Ah=float((pair[1]-pair[0]).mean()),
        conditional_return_minus_initial_mean_Ah=float((pair[2]-pair[0]).mean()),conditional_return_abs_mean_Ah=float(abs(pair[2]-pair[0]).mean()),
        accepted_local_updates=int(df.local_gate.sum()),measured_temperature_visits=len(df),
        inference='Conditional point estimates under controlled full-charge resets; neither true capacity update nor continuous path validation',
        supplementary_after_primary_scoring=True,primary_model_threshold_and_test_unchanged=True))
    (OUT/'THERMAL_SUPPLEMENT_COMPLETE').write_text('Supplement completed. No primary retuning.\n')

if __name__=='__main__':run()
