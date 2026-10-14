"""Stage 2a audit (no proxy metric): coverage, program reproduction, coulomb closure."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from common4 import H  # noqa: E402
import dyncross as D  # noqa: E402

OUT = os.path.join(HERE, "outputs")
op = H.full_op()
cr, cl = D.crossings(op)
cr["month"] = np.searchsorted(H.CK.values, cr["t_start"].values) - 1
cr.to_csv(os.path.join(OUT, "audit_crossings.csv"), index=False)
cl.to_csv(os.path.join(OUT, "audit_closure.csv"), index=False)
loc = cr.dropna(subset=["loc_mean"])
prog = loc[loc.program]
rep = (prog["loc_mean"] - prog["program_step"]).abs()
add45 = loc[(~loc.program) & (loc.setpoint == 45)]
cnt = add45.groupby(["month", "band"]).size().unstack(fill_value=0)
months_ok = int((cnt.max(axis=1) >= 3).sum()) if len(cnt) else 0
summ = dict(n_candidate=len(cr), n_located=len(loc), n_program_runs=int(cr.program.sum()),
            program_repro_median_abs=float(rep.median()) if len(rep) else None,
            program_repro_p90_abs=float(rep.quantile(0.9)) if len(rep) else None,
            closure_median_abs=float(cl["closure_Ah"].abs().median()), closure_p90_abs=float(cl["closure_Ah"].abs().quantile(0.9)),
            n_closure_pairs=len(cl), median_four_cell_range=float(loc["loc_range"].median()) if len(loc) else None,
            additional_45C_by_month_band=cnt.to_dict(), months_with_ge3_additional_45C=months_ok)
summ["exit_passed"] = bool(summ["program_repro_median_abs"] is not None and summ["program_repro_median_abs"] <= 0.3
                           and summ["closure_median_abs"] <= 0.2 and months_ok >= 5)
json.dump(summ, open(os.path.join(OUT, "audit_summary.json"), "w"), indent=1, default=str)
pd.set_option("display.width", 200)
print(cr.groupby(["setpoint", "band", "program"]).agg(n=("loc_mean", "size"), located=("loc_mean", "count"), rng=("loc_range", "median")).round(3))
print(cnt)
print(json.dumps(summ, indent=1, default=str))
