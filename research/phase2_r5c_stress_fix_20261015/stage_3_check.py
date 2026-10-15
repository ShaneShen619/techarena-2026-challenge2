"""Stage 3: G-causal and G-impl for the round-5C candidate (harness.candidate_checks)."""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
sys.path.insert(0, os.path.join(HERE, "candidate_model"))
import pandas as pd  # noqa: E402
from common5c import H  # noqa: E402
from r5c_stress_ensemble_model import MyModel  # noqa: E402

df = pd.read_csv(os.path.join(HERE, "stage_2", "outputs", "S2_R3_real_predictions.csv"))
r = df[(df.model == "R3_TD_w0.75") & (df.delta == 0.4) & (df.step == "main") & (df.a4s == 2.0)].sort_values("k")
research = [round(float(x), 3) for x in r["SOH"]]
t = time.time()
from checks5c import candidate_checks
res = candidate_checks(MyModel, research)
res["runtime_s"] = time.time() - t
res["research_soh_ck1_7"] = research
res["python"] = sys.version.split()[0]
out = os.path.join(HERE, "stage_3", "outputs")
os.makedirs(out, exist_ok=True)
json.dump(res, open(os.path.join(out, f"S3_candidate_checks_py{sys.version_info.major}{sys.version_info.minor}.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
