"""Stage 0: reproduce M4 and V2 through the round-3 harness inside this worktree."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
from common5a import H  # noqa: E402

df = H.run(H.BASELINES, scenarios=("real",))
m = H.metrics(df).set_index(["model", "delta"])
out = {mod: dict(MAE=float(m.loc[(mod, 0.4), "MAE"]), MAX=float(m.loc[(mod, 0.4), "MAX"])) for mod in ("M4", "V2")}
out["reproduced"] = bool(abs(out["V2"]["MAE"] - 0.215726) < 5e-7 and abs(out["V2"]["MAX"] - 0.669052) < 5e-7
                         and abs(out["M4"]["MAE"] - 0.291265) < 5e-7)
out["cache_dir"] = H.CACHE
os.makedirs(os.path.join(HERE, "stage0"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "stage0", "reproduce.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
