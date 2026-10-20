"""Registered round-15 machinery (WP1): hypothesis grids, truth vectors T_k(h), the metric family, delta-s,
readability, ranking, the surviving set and the reading rules.

T_k(h) is built exactly as round 6 builds it (sources/r6/wp1_run_wp1.py):
    T_k(h) = Q_fc,k + eps0 + Delta - f * R_k + d * L_k,   L_k = max(0, 100.41 - (Q_fc,k + eps0)),
with Q_fc,k + eps0 taken from round 6's own harness output (sources/r6/wp1_predictions.csv, proxy at Delta = 0.4)
and R_k from round 4 (sources/r6/round4_jumps.csv, recovery_Ah_with_aging).
"""
import itertools
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.dirname(HERE)
SRC = os.path.join(ST, "sources")
NOM = 102.0
Q_CK0 = 100.41
KS = list(range(1, 8))
CKS = [f"CK{k}" for k in KS]
METRICS = ("s", "nMAE", "nRMSE", "nMAX")
SIGN_EPS = 1e-12          # |x| below this counts as sign 0
READABLE_FRACTION = 0.80
DEFAULT_TOL = 0.005

# round 6 grid, copied exactly (sources/r6/wp1_protocol.json)
DELTA_R6 = (0.0, 0.4, 0.8)
F_R6 = (0.0, 0.5, 1.0)
D_R6 = (0.0, -0.031)
# gate grid: round 11's registered O3 interval for d (with 0), used because rounds 13 and 14 are present but
# neither is identifiable (case not covered by the prompt; D-rule in notes/DECISIONS.md)
D_R11 = (-0.036, 0.0, 0.052)
# descriptive grid only: the non-identified envelopes reported by rounds 13 (d_tail) and 14 (d_path, d_top)
D_ENV = (-0.167, -0.105, -0.045, 0.0, 0.013, 0.050)


def anchors():
    """p_k = Q_fc,k + eps0 (Ah) for k = 1..7 from round 6's harness output."""
    pr = pd.read_csv(os.path.join(SRC, "r6", "wp1_predictions.csv"))
    pr = pr[(pr.scenario == "real") & (pr.step == "main") & (pr.a4s == 2.0) & (pr.delta == 0.4)]
    p = pr.groupby("k")["proxy"].agg(["min", "max"])
    assert (p["max"] - p["min"]).abs().max() < 1e-9
    return {k: float(p.loc[k, "min"]) - 0.4 for k in KS}


def recoveries():
    j = pd.read_csv(os.path.join(SRC, "r6", "round4_jumps.csv"))
    r = dict(zip(j["checkup"], j["recovery_Ah_with_aging"].astype(float)))
    return {k: r[f"CK{k}"] for k in KS}


P_K = anchors()
R_K = recoveries()


def grid(d_axis, delta_axis=DELTA_R6, f_axis=F_R6):
    return [dict(Delta=a, f=b, d=c) for a, b, c in itertools.product(delta_axis, f_axis, d_axis)]


def hname(h):
    return f"D{h['Delta']}_f{h['f']}_d{h['d']}"


GRIDS = {"G_main": grid(D_R6), "G_r11": grid(D_R11), "G_env": grid(D_ENV)}
GRID_ROLE = {"G_main": "decides", "G_r11": "readability gate", "G_env": "descriptive only"}


def target(k, h):
    p = P_K[k]
    L = max(0.0, Q_CK0 - p)
    return p + h["Delta"] - h["f"] * R_K[k] + h["d"] * L


def raw_metrics(soh, h):
    """soh: {CKk: SOH %} (CLI output). Errors in pp of the nominal 102 Ah against T_k(h)."""
    e = np.array([float(soh[f"CK{k}"]) - target(k, h) / NOM * 100.0 for k in KS])
    return dict(MAE=float(np.mean(np.abs(e))), RMSE=float(np.sqrt(np.mean(e ** 2))), MAX=float(np.max(np.abs(e))))


def scores(soh, soh_ex, h):
    """The metric family for one model under one hypothesis, each normalised by ExampleModel under the same h."""
    m, x = raw_metrics(soh, h), raw_metrics(soh_ex, h)
    out = dict(nMAE=m["MAE"] / x["MAE"], nRMSE=m["RMSE"] / x["RMSE"], nMAX=m["MAX"] / x["MAX"])
    out["s"] = (out["nMAE"] + out["nRMSE"] + out["nMAX"]) / 3.0
    return out


def score_table(models, soh_ex, gname):
    """Long table: grid, h, model, metric, value."""
    rows = []
    for h in GRIDS[gname]:
        for name, soh in models.items():
            for m, v in scores(soh, soh_ex, h).items():
                rows.append(dict(grid=gname, h=hname(h), Delta=h["Delta"], f=h["f"], d=h["d"], model=name,
                                 metric=m, value=v))
    return pd.DataFrame(rows)


def delta_table(sc, probe, base="SUB"):
    """delta-s_m(h) = m_h(probe) - m_h(base) from a score_table."""
    a = sc[sc.model == probe].set_index(["grid", "h", "metric"])["value"]
    b = sc[sc.model == base].set_index(["grid", "h", "metric"])["value"]
    d = (a - b).rename("delta_s").reset_index()
    d.insert(0, "probe", probe)
    return d


def sgn(x):
    return 0 if abs(x) < SIGN_EPS else (1 if x > 0 else -1)


def readability(dt, hs=None):
    """Fraction of hypotheses (optionally restricted to the names in hs) where sign(delta-s) is the same under all
    four metrics.  dt: delta_table rows of one probe and one grid."""
    w = dt.pivot_table(index="h", columns="metric", values="delta_s")[list(METRICS)]
    if hs is not None:
        w = w.loc[[h for h in w.index if h in set(hs)]]
    agree = w.apply(lambda r: len({sgn(v) for v in r}) == 1, axis=1)
    tol_det = w.apply(lambda r: all(abs(v) > DEFAULT_TOL for v in r) and len({sgn(v) for v in r}) == 1, axis=1)
    return dict(n=int(len(w)), agree_fraction=float(agree.mean()) if len(w) else float("nan"),
                detectable_fraction=float(tol_det.mean()) if len(w) else float("nan"),
                readable=bool(len(w) and agree.mean() >= READABLE_FRACTION))


def summary(dt, hs=None):
    """Expected (uniform) and worst-case delta-s per metric, plus the registered ranking keys."""
    w = dt.pivot_table(index="h", columns="metric", values="delta_s")[list(METRICS)]
    if hs is not None:
        w = w.loc[[h for h in w.index if h in set(hs)]]
    e, worst, best = w.mean(), w.max(), w.min()
    wins_all = int((w < -DEFAULT_TOL).all(axis=1).sum())
    out = {f"E_{m}": float(e[m]) for m in METRICS}
    out.update({f"worst_{m}": float(worst[m]) for m in METRICS})
    out.update({f"best_{m}": float(best[m]) for m in METRICS})
    out["key1_max_E"] = float(e.max())
    out["key2_max_worst"] = float(worst.max())
    out["wins_all_metrics_beyond_tol"] = wins_all
    return out


def choose(rows):
    """rows: list of dicts with probe, eligible, readable_main, readable_r11, key1_max_E, key2_max_worst.
    Registered selection: eligible, readable on G_main (surviving set) and on G_r11, key1 < 0; rank by key1, then
    key2; at most two."""
    ok = [r for r in rows if r["eligible"] and r["readable_main"] and r["readable_r11"] and r["key1_max_E"] < 0]
    ok.sort(key=lambda r: (r["key1_max_E"], r["key2_max_worst"]))
    return [r["probe"] for r in ok[:2]]


# ---------------------------------------------------------------------------------------------- observations
def decimals(text):
    t = str(text).strip()
    return len(t.split(".")[1]) if "." in t else 0


def surviving(pred, observations, gname="G_main"):
    """Free information first.  pred: score_table rows (all models incl. logged packages) for one grid.
    observations: list of dict(model=<name in pred>, values={metric label: shown string}).  A hypothesis survives if,
    for every observation and every shown value, at least one metric of the family predicts the shown value within
    one unit of its last displayed digit.  An empty result is reported as 'grid inconsistent' and the full grid is
    kept (conservative)."""
    hs = [hname(h) for h in GRIDS[gname]]
    if not observations:
        return hs, "no observations"
    keep = []
    for h in hs:
        ok = True
        for o in observations:
            p = pred[(pred.h == h) & (pred.model == o["model"])].set_index("metric")["value"]
            for _, shown in o["values"].items():
                u = 10.0 ** (-decimals(shown))
                if not any(abs(float(p[m]) - float(shown)) <= u + 1e-12 for m in METRICS):
                    ok = False
        if ok:
            keep.append(h)
    if not keep:
        return hs, "grid inconsistent with the observations: full grid kept"
    return keep, f"{len(keep)} of {len(hs)} survive"


def drop_branch(dt, hs, tol=DEFAULT_TOL):
    """After a 'revert, drop branch' reading: remove the hypotheses under which every metric predicted
    delta-s < -tol (a clear predicted win whatever the shown metric is).  dt: delta_table rows of one probe/grid."""
    w = dt.pivot_table(index="h", columns="metric", values="delta_s")[list(METRICS)]
    won = set(w.index[(w < -tol - SIGN_EPS).all(axis=1)])
    return [h for h in hs if h not in won]


def reading(obs_probe, obs_sub, tol=None):
    """Registered reading rule.  obs_probe, obs_sub: {metric label: shown string} from boards that evaluated the
    probe and SUB (same labels).  Returns per-metric readings and the verdict."""
    labels = [m for m in obs_probe if m in obs_sub]
    if not labels:
        return dict(verdict="no information", reason="no common shown metric (rank-only boards carry no information)")
    per = {}
    for m in labels:
        # tol = the display precision (one unit of the last shown digit); 0.005 if it cannot be read
        n_dec = min(decimals(obs_probe[m]), decimals(obs_sub[m]))
        t = tol if tol is not None else (10.0 ** -n_dec if n_dec > 0 else DEFAULT_TOL)
        d = float(obs_probe[m]) - float(obs_sub[m])
        # |delta| <= tol (up to float noise) is "no information"
        per[m] = dict(delta=d, tol=t, reading="adopt" if d < -t - SIGN_EPS else (
            "revert, drop branch" if d > t + SIGN_EPS else "no information"))
    worse = any(v["reading"].startswith("revert") for v in per.values())
    better = any(v["reading"] == "adopt" for v in per.values())
    verdict = "probe wins: adopt its scalar" if better and not worse else (
        "probe loses: revert to SUB, drop the branch" if worse else "no information: revert to SUB")
    return dict(verdict=verdict, per_metric=per)
