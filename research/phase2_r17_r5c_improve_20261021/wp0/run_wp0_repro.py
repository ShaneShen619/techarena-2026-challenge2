"""WP0: reproduce the section-2 reference rows (REF, R3_T, V2) and compute the noise floor."""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from eval17 import H, base_predictors, per_ck, run, summary  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

EXPECT = {
    "REF": dict(real=0.131, pseudo=0.123, cold=0.134, ck=[0.048, -0.311, -0.092, 0.132, 0.033, -0.197, 0.107]),
    "R3_T": dict(real=0.179, pseudo=0.119, cold=0.144, ck=[-0.008, -0.638, -0.150, 0.100, -0.007, -0.209, 0.144]),
    "V2": dict(real=0.216, pseudo=0.240, cold=0.252, ck=[0.217, 0.669, 0.080, 0.228, 0.150, -0.163, -0.004]),
}

t0 = time.time()
P = base_predictors()
scens = ("real", "PG1", "PG2", "PC5", "PC10", "CS", "CSE")
df = run(P, scenarios=scens, variants=H.VARIANTS, smooths=(2.0,))
df.to_csv(os.path.join(OUT, "wp0_base_predictions.csv"), index=False)
sm = summary(df)
rep = {"elapsed_s": round(time.time() - t0, 1), "rows": {}}
ok = True
for m, e in EXPECT.items():
    ck = per_ck(df, m).round(3).tolist()
    row = dict(real=round(sm.loc[m, "real"], 4), pseudo=round(sm.loc[m, "pseudo"], 4),
               cold=round(sm.loc[m, "cold"], 4), ck=ck)
    diffs = [abs(row[x] - e[x]) for x in ("real", "pseudo", "cold")] + [abs(a - b) for a, b in zip(ck, e["ck"])]
    row["max_abs_diff_vs_prompt"] = round(max(diffs), 4)
    row["reproduced"] = bool(max(diffs) <= 0.0015)   # prompt values are rounded to 3 decimals
    ok &= row["reproduced"] if m == "REF" else True
    rep["rows"][m] = row
rep["REF_reproduced"] = bool(ok)

# noise floor: SD of REF's predicted SOH across the 6 step variants per causal case (delta 0.4)
c = df[(df["model"] == "REF") & (df["delta"] == 0.4) & (df["scenario"] != "real")]
sd = c.groupby(["scenario", "k"])["SOH"].std(ddof=1)
med = float(sd.median())
noise = dict(n_cases=int(len(sd)), median_sd_pp=med, T_move=max(0.05, 2 * med), delta=max(0.005, 0.5 * med),
             per_case_sd={f"{s}_k{k}": float(v) for (s, k), v in sd.items()})
json.dump(noise, open(os.path.join(OUT, "noise.json"), "w"), indent=1)
json.dump(rep, open(os.path.join(OUT, "wp0_reproduction.json"), "w"), indent=1)
print(json.dumps(rep, indent=1))
print("noise", {k: v for k, v in noise.items() if k != "per_case_sd"})
