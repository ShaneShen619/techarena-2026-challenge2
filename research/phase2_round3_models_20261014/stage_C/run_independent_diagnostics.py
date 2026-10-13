"""Full monthly MAP states, pseudo-scenario calibration and A4 reporting.

The main 2-Ah implementation is unchanged apart from metadata. Diagnostic
variants pass beta explicitly from 1/3-Ah A4 windows; they cannot retune the
registered main configuration.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'src'))
import harness as H
import statespace as S
from v2 import beta_a4

def with_smoothing(**config):
    def predict(ctx):
        options=dict(config)
        beta=options.pop('beta',None)
        if beta is None:
            beta=beta_a4(ctx['fc'],ctx['a4'][ctx['a4s']],ctx['ck'],ctx['k'],1.,1.)
        return S.fit_predict(ctx,beta=beta,**options)
    return predict

if __name__=='__main__':
    predictors={**H.BASELINES,'SS':with_smoothing(),'SS_tau3':with_smoothing(tau=3.),'SS_tau8':with_smoothing(tau=8.),
                'SS_beta1':with_smoothing(beta=1.),'SS_rw01':with_smoothing(rw=.01),'SS_rw04':with_smoothing(rw=.04)}
    df=H.run(predictors,scenarios=tuple(H.SCENARIOS),smooths=(1.,2.,3.))
    df.to_csv(HERE/'outputs/C_independent_long.csv',index=False)
    H.metrics(df).to_csv(HERE/'outputs/C_independent_metrics.csv',index=False)
    states=[]
    ss=df[(df.model=='SS')&(df.delta==.4)&(df.a4s==2.)]
    for row in ss.to_dict('records'):
        for m,r25,r45,amp in zip(row['all_months'],row['all_r25'],row['all_r45'],row['all_A']):
            states.append({'scenario':row['scenario'],'k':row['k'],'month':m,'r25_Ah_per_day':r25,
                           'r45_Ah_per_day':r45,'transient_Ah':amp,'delta_Ah':row['delta_fit']})
    pd.DataFrame(states).to_csv(HERE/'outputs/C_independent_monthly_states.csv',index=False)
    calibration=[]
    for scenario,g in ss.groupby('scenario'):
        z=g.err_pp.to_numpy()/(g.pred_sd.to_numpy()/102*100)
        calibration.append({'scenario':scenario,'n':len(g),'mean_abs_z':float(np.mean(np.abs(z))),
                            'fraction_within_1sd':float(np.mean(np.abs(z)<=1)),
                            'fraction_within_2sd':float(np.mean(np.abs(z)<=2)),
                            'interpretation':'descriptive, exposed proxies and dependent scenarios; not calibrated coverage'})
    pd.DataFrame(calibration).to_csv(HERE/'outputs/C_independent_calibration.csv',index=False)
    print(pd.DataFrame(calibration).to_string(index=False))
