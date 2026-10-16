"""WP2 G_causal / G_impl part 1 for the T_main candidate class (research environment).
Part 2 (Python 3.11 venv, validate_submission.py on a package copy) is run by check_package.sh."""
import importlib.util
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common6 import H  # noqa: E402
from checks5c import candidate_checks  # noqa: E402

spec = importlib.util.spec_from_file_location("cand_tmain", os.path.join(HERE, "candidate_model", "model_template.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["cand_tmain"] = mod   # needed for the pickle round trip in candidate_checks
spec.loader.exec_module(mod)
soh = pd.read_csv(os.path.join(HERE, "outputs", "wp2_real_SOH_d04.csv"), index_col="model")
research = [float(soh.loc["T_main", c]) for c in H.CK_NAMES[1:]]
res = candidate_checks(mod.MyModel, research)
res["research_soh"] = research
json.dump(res, open(os.path.join(HERE, "outputs", "wp2_candidate_checks.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
