"""WP3a: top-state mechanism check (protocol_3a.json). Diagnostic, full data, no proxies."""
import hashlib
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
import cellcand as CC  # noqa: E402
import diag10 as D  # noqa: E402
import gates10 as G  # noqa: E402

OUT = os.path.join(HERE, "outputs")
PROTO = os.path.join(HERE, "protocol_3a.json")
assert hashlib.sha256(open(PROTO, "rb").read()).hexdigest() == open(os.path.join(HERE, "protocol_3a.sha256")).read().split()[0]
ANCH = os.path.join(os.path.dirname(STUDY), "phase2_r8_error_table_20261017", "outputs", "table_anchors.csv")
SEED, NB = 20261017, 2000
CELLS = ["cell1", "cell2", "cell3", "cell4"]


def table():
    L = CC.variant_locs(D.full_steps(), "main")
    d = D.long_cells(L)
    d["R_cell"] = d["depth"] - d.groupby("t_cv_end")["depth"].transform("median")
    cv = pickle.load(open(os.path.join(STUDY, "cache", "cvv_full.pkl"), "rb")).set_index("t_cv_end")
    vm = cv[[f"V_{c}_V" for c in CELLS]].mean(axis=1)
    d["u"] = [1000.0 * (cv.loc[t, f"V_{u}_V"] - vm[t]) for t, u in zip(d["t_cv_end"], d["unit"])]
    a = pd.read_csv(ANCH).set_index("anchor")
    am = a[[f"step_to_top_{c}_V" for c in CELLS]].mean(axis=1)
    d["w"] = [a.loc[int(m), f"step_to_top_{u}_V"] - am[int(m)] for m, u in zip(d["month"], d["unit"])]
    return d


def fit(d, x):
    q = d[["unit", "month", "R_cell", x]].dropna().copy()
    q["y0"] = q["R_cell"] - q.groupby("unit")["R_cell"].transform("mean")
    q["x0"] = q[x] - q.groupby("unit")[x].transform("mean")
    sxx = float((q["x0"] ** 2).sum())
    b = float((q["x0"] * q["y0"]).sum() / sxx) if sxx > 0 else np.nan
    r2 = 1 - float(((q["y0"] - b * q["x0"]) ** 2).sum() / (q["y0"] ** 2).sum())
    return b, r2, q


def assess(d, x):
    b, r2, q = fit(d, x)
    signs = {}
    for u, g in q.groupby("unit"):
        sxx = float((g["x0"] ** 2).sum())
        signs[u] = float((g["x0"] * g["y0"]).sum() / sxx) if sxx > 0 else np.nan
    months = np.array(sorted(d["month"].unique()))
    rng = np.random.default_rng(SEED)
    bs = []
    for _ in range(NB):
        pick = rng.choice(months, len(months), replace=True)
        r = pd.concat([d[d.month == m] for m in pick], ignore_index=True)
        v = fit(r, x)[0]
        if np.isfinite(v):
            bs.append(v)
    lo, hi = np.percentile(bs, [5, 95])
    n_pos = int(sum(v > 0 for v in signs.values()))
    passed = bool(lo > 0 and n_pos >= 3 and r2 >= 0.30)
    return dict(slope=b, ci90=[float(lo), float(hi)], within_cell_R2=r2, per_cell_slope=signs, cells_positive=n_pos,
                n=int(len(q)), passed=passed)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    d = table()
    d.to_csv(os.path.join(OUT, "wp3a_table.csv"), index=False)
    res = {x: assess(d, x) for x in ("u", "w")}
    res["exit"] = not any(res[x]["passed"] for x in ("u", "w"))
    # descriptive: per-cell trend of u and w over months (do top states drift?)
    res["describe_month_means"] = {x: d.groupby(["unit", "month"])[x].mean().unstack().round(4).to_dict(orient="index")
                                   for x in ("u", "w", "R_cell")}
    json.dump(res, open(os.path.join(OUT, "wp3a_result.json"), "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k != "describe_month_means"}, indent=1, default=float))
    pd.set_option("display.width", 250)
    for x in ("u", "w", "R_cell"):
        print(x)
        print(d.groupby(["unit", "month"])[x].mean().unstack().round(3).to_string())
