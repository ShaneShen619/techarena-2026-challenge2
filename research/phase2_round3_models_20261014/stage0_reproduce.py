"""Stage 0: the harness must reproduce M4 and V2 (0.216 / 0.669 at delta 0.4)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
import harness as H  # noqa: E402

df = H.run(H.BASELINES, scenarios=tuple(H.SCENARIOS), variants=H.VARIANTS)
met = H.metrics(df)
os.makedirs(os.path.join(HERE, "stage0"), exist_ok=True)
met.to_csv(os.path.join(HERE, "stage0", "baseline_metrics.csv"), index=False)
df.to_csv(os.path.join(HERE, "stage0", "baseline_long.csv"), index=False)
m = met.set_index(["scenario", "model", "step", "a4s", "delta"])
v2 = m.loc[("real", "V2", "main", 2.0, 0.4)]
ok = abs(v2["MAE"] - 0.216) < 0.0006 and abs(v2["MAX"] - 0.669) < 0.0006
summary = {"V2_real_d0.4": dict(MAE=v2["MAE"], MAX=v2["MAX"]), "reproduced": bool(ok)}
for s in H.SCENARIOS:
    for mod in ("M4", "V2"):
        r = m.loc[(s, mod, "main", 2.0, 0.4)]
        summary[f"{s}_{mod}"] = dict(MAE=round(r["MAE"], 3), MAX=round(r["MAX"], 3), n=int(r["n"]))
json.dump(summary, open(os.path.join(HERE, "stage0", "reproduce.json"), "w"), indent=1, default=float)
print(json.dumps(summary, indent=1, default=float))
print(H.per_ck(df).round(3))
for s in ("PG1", "PG2", "PC5", "PC10"):
    print(s, H.per_ck(df, scenario=s).round(3).to_dict())
