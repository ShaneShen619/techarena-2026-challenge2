"""WP4 G_impl / G_causal for the A3 candidate class (research environment). Package part: check_package.sh."""
import importlib.util
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common10 import H  # noqa: E402
from checks5c import candidate_checks  # noqa: E402

spec = importlib.util.spec_from_file_location("cand_a3", os.path.join(HERE, "candidate_model", "model_template.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["cand_a3"] = mod   # needed for the pickle round trip in candidate_checks
spec.loader.exec_module(mod)
soh = pd.read_csv(os.path.join(STUDY, "wp1", "outputs", "wp1_real_SOH_d04.csv"), index_col="model")
research = [float(soh.loc["A3", c]) for c in H.CK_NAMES[1:]]
res = candidate_checks(mod.MyModel, research)
res["research_soh"] = research
# unrounded comparison as well
m = mod.MyModel()
m.fit(H.load_dataset(H.DATA))
unr = [float(m.estimate_soh(H.load_dataset(H.DATA, until=d), d)) for d in H.CK[1:]]
res["max_abs_diff_unrounded_pp"] = float(max(abs(a - b) for a, b in zip(unr, research)))
os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
json.dump(res, open(os.path.join(HERE, "outputs", "wp4_candidate_checks.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
