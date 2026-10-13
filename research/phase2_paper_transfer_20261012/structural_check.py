"""Exploratory structural checks, not an official-data performance evaluation.

CK0 templates generate their own synthetic observations. This verifies numerical
recovery under the assumed model, not whether aging actually obeys that model.
No CK1-7 labels, official operating voltages, or frozen test results are fitted.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def main():
    raw = pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
    raw['bin'] = (raw.discharged_Ah/.1).round().astype(int)
    table = raw.groupby('bin')[[f'cell{i}_V' for i in range(1,5)]].median()
    x = table.index.to_numpy(float)*.1
    curves = table.to_numpy(float)
    scales = [.94, .96, .92, .95]
    shifts = [7., 9., 8., 6.]
    offsets = [.008, -.006, .004, .010]
    q = np.linspace(0,60,301)
    results = []
    for contaminated in [False, True]:
        for loss in ['L2', 'LAD']:
            for c in range(4):
                # Bias is known independently in this favourable sanity case.
                y = np.interp(q/scales[c]+shifts[c],x,curves[:,c])+offsets[c]
                if contaminated:
                    y = y.copy(); y[::17] += .05
                def objective(p):
                    s,d = p
                    index = q/s+d
                    if index.max()>x[-1]:
                        return 1e3+(index.max()-x[-1])**2
                    r = np.interp(index,x,curves[:,c])+offsets[c]-y
                    return np.mean(r*r) if loss=='L2' else np.mean(np.abs(r))
                fits = [minimize(objective,[s,d],method='Nelder-Mead',
                    bounds=[(.7,1.05),(0,30)],
                    options={'xatol':1e-9,'fatol':1e-13,'maxiter':3000})
                    for s in [.8,.95,1.03] for d in [2,10,20]]
                best = min(fits,key=lambda v:v.fun)
                results.append(dict(case='outliers' if contaminated else 'exact',
                    loss=loss,cell=c+1,s_true=scales[c],s_fit=float(best.x[0]),
                    d_true_Ah=shifts[c],d_fit_Ah=float(best.x[1]),
                    s_absolute_error=float(abs(best.x[0]-scales[c])),
                    d_absolute_error_Ah=float(abs(best.x[1]-shifts[c])),
                    optimizer_success=bool(best.success)))

    # Independent analytical counterexample: a locally linear, flat LFP-like
    # voltage law. Allow a free voltage offset and profile the scale.
    qflat = np.linspace(0,10,101)
    slope = -.0004  # V/Ah; illustrative, not a fitted CK0 property.
    yflat = 3.3+slope*(qflat/.94+8)+.008
    witnesses=[]
    for s in np.linspace(.70,1.05,71):
        pred = 3.3+slope*(qflat/s+8)
        b = float(np.median(yflat-pred))
        r = pred+b-yflat
        if np.max(np.abs(r))<=.001:
            witnesses.append(dict(s=float(s),offset_V=b,
                                  max_residual_mV=float(np.max(np.abs(r))*1000)))
    output = dict(scope='Synthetic same-template recovery plus analytic counterexample only',
        recovery=results,flat_plateau_witnesses=witnesses,
        accepted_flat_s_range=[witnesses[0]['s'],witnesses[-1]['s']],
        interpretation='LAD limits outlier influence; it cannot supply missing voltage information.')
    (HERE/'structural_results.json').write_text(json.dumps(output,indent=2)+'\n')
    for case in ['exact','outliers']:
        for loss in ['L2','LAD']:
            subset=[r for r in results if r['case']==case and r['loss']==loss]
            print(case,loss,'max s error:',max(r['s_absolute_error'] for r in subset),
                  'max d error Ah:',max(r['d_absolute_error_Ah'] for r in subset))
    print('Illustrative flat segment within 1mV: s range',output['accepted_flat_s_range'])

if __name__=='__main__': main()
