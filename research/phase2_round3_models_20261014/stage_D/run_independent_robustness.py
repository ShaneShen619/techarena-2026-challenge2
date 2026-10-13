"""Complete six step variants and three A4 windows under the frozen D rules.

This is supplementary reporting; it cannot change the already committed D0 selection.
"""
import json
import sys
from pathlib import Path
import pandas as pd
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'src'))
import harness as H
import gapx

if __name__=='__main__':
    selection=json.loads((HERE/'selection.json').read_text())
    assert selection['chosen']=='D0'
    predictors={**H.BASELINES, **{r:gapx.make(r) for r in gapx.RULES}}
    frames=[H.run(predictors, scenarios=tuple(H.SCENARIOS), variants=H.VARIANTS, smooths=(2.,)),
            H.run(predictors, scenarios=tuple(H.SCENARIOS), variants=('main',), smooths=(1.,3.))]
    df=pd.concat(frames,ignore_index=True)
    df.to_csv(HERE/'outputs/D_independent_robustness_long.csv',index=False)
    H.metrics(df).to_csv(HERE/'outputs/D_independent_robustness_metrics.csv',index=False)
    print(H.metrics(df).query("scenario=='real' and step=='main' and a4s==2 and delta==.4").to_string(index=False))
