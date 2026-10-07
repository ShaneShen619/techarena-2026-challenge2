"""Planning sensitivity only; not a substitute for measured variance or power analysis."""
from pathlib import Path
import json, math
import pandas as pd
from scipy.stats import norm

TASK=Path(__file__).resolve().parents[1]
alpha=.05; power=.80
z=float(norm.ppf(1-alpha/2)+norm.ppf(power))
rows=[]
for sd in [0.5,1.0,2.0,3.0,5.0]:
    for delta in [0.5,1.0,2.0,3.0]:
        n=math.ceil((z*sd/delta)**2)
        rows.append({'assumed_SD_of_paired_method_difference_pp':sd,'minimum_detectable_mean_difference_pp':delta,
                     'alpha_two_sided':alpha,'power':power,'normal_approx_independent_groups_needed':max(2,n)})
out=pd.DataFrame(rows); out.to_csv(TASK/'outputs/r5_sample_size_sensitivity.csv',index=False)
summary={'formula':'ceil(((z_0.975 + z_0.80) * assumed_SD / delta)^2)',
         'warning':'planning sensitivity only; update with pilot group-level paired differences and account for protocol strata before fixing confirmation n',
         'startup_plan_groups':12,'minimum_sealed_groups':4}
(TASK/'outputs/r5_sample_size_sensitivity.json').write_text(json.dumps(summary,indent=2)+'\n')
print(out.to_string(index=False))
