"""Report the three required A4 windows without changing the registered A model.

The main model stays at its frozen 2-Ah setting. Required diagnostic variants
use 1/3-Ah A4 reference features, with separate cache keys. These late
supplementary variants cannot change the main configuration or selection.
"""
import sys
from pathlib import Path
import pandas as pd
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'src'))
import harness as H
import registration as R

if __name__=='__main__':
    predictors={**H.BASELINES,
                'V2_reg':lambda c:R.v2_reg(c,'V','full',ref_smooth=c['a4s']),
                'V2_reg_dvdq':lambda c:R.v2_reg(c,'dVdQ','full',ref_smooth=c['a4s']),
                'V2_reg_bottom':lambda c:R.v2_reg(c,'V','bottom',ref_smooth=c['a4s'])}
    original=pd.read_csv(HERE/'outputs/A_long.csv')
    extra=H.run(predictors,scenarios=tuple(H.SCENARIOS),variants=('main',),smooths=(1.,3.))
    df=pd.concat([original,extra],ignore_index=True)
    df.to_csv(HERE/'outputs/A_independent_smoothing_long.csv',index=False)
    H.metrics(df).to_csv(HERE/'outputs/A_independent_smoothing_metrics.csv',index=False)
    print(H.metrics(df).query("scenario=='real' and step=='main' and delta==.4").to_string(index=False))
