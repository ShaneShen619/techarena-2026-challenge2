"""WP0 reproduction check: drift function on the 21a7a55 package vs round 7's table; apply to current SUB."""
import os, sys, json
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from drift import add_drift

old = pd.read_csv(os.path.join(ST, "cache/out_21a7a55/output.csv")).set_index("checkup")["SOH_est"]
cur = pd.read_csv(os.path.join(ST, "cache/out_6525edf/output.csv")).set_index("checkup")["SOH_est"]
r7 = pd.read_csv(os.path.join(ST, "sources/r7_wp3_SUB_drift_SOH.csv")).set_index("model")
cks = [f"CK{k}" for k in range(1, 8)]
rows = {}
for name, d in [("SUB", 0.0), ("SUB+drift-0.031", -0.031), ("SUB+drift-0.02", -0.020), ("SUB+drift-0.033", -0.033)]:
    mine = pd.Series(add_drift(old[cks].values, d), index=cks)
    diff = (mine - r7.loc[name, cks]).abs()
    rows[name] = dict(max_abs_diff_pp=float(diff.max()))
# old outputs are rounded to 0.001 pp, so a 0.001 tolerance (plus float slack) is the registered bound
ok = all(v["max_abs_diff_pp"] <= 0.001 + 1e-9 for v in rows.values())
pd.DataFrame({"SUB_6525edf": cur[cks]}).T.to_csv(os.path.join(ST, "wp0/SUB_SOH.csv"))
ref = pd.DataFrame({f"SUB+drift{d}": add_drift(cur[cks].values, d) for d in (0.0, -0.020, -0.031, -0.033)}, index=cks).T.round(3)
ref.index = ["SUB"] + list(ref.index[1:])
ref.to_csv(os.path.join(ST, "wp0/SUB_drift_reference.csv"))
json.dump(dict(check_vs_round7=rows, passed=ok, note="21a7a55 package run through its own CLI (python3 -B, system Python 3.13, pandas 3.0)"),
          open(os.path.join(ST, "wp0/reproduction_check.json"), "w"), indent=1)
print(json.dumps(rows, indent=1), "PASSED" if ok else "FAILED"); print(ref.to_string())
