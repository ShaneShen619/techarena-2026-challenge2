"""Registered Ah chain (round 14 WP1). Round 12's src/ahchain.py was not on origin at registration, so the same rule
is implemented here (prompt section 3, WP1):

* N_ij   = integral of current_A over (t_i, t_j] between two CV ends, package convention (_integrated_ah: steps with
           dt > MAX_DT_S or dt <= 0 get zero weight);
* thr_ij = discharged Ah over (t_i, t_j] (negative current only, same convention);
* a pair with any recording gap (dt > 60 s) in (t_i, t_j] is excluded;
* lambda_s = median of N/thr over segment s's top-up -> top-up (TT) pairs; no TT pair in s -> pooled median of the set
  point; that set point with < 2 TT pairs -> the other set point's pooled median (recorded);
* sigma_TT,sp = 1.4826 * MAD of the TT residuals N - lambda * thr, lambda computed without that pair.

Pairs are built only between CV ends of the same segment: AT1 (anchor -> first top-up), AT2 (anchor -> second top-up),
TT (consecutive top-ups)."""
import numpy as np
import pandas as pd
import data14 as D

MAD_K = 1.4826


def integrate(seg):
    """(net Ah cumsum, discharged Ah cumsum, elapsed s), both cumsums with the package's _integrated_ah weights."""
    i, ah = D.mt._integrated_ah(seg)
    t = seg["elapsed_s"].to_numpy(float)
    dt = np.diff(t, prepend=t[0])
    dt[(dt > D.mt.MAX_DT_S) | (dt <= 0)] = 0.0
    dis = np.cumsum(np.maximum(-i, 0.0) * dt / 3600.0)
    return ah, dis, t


def pair_values(seg, i0, i1, cum=None):
    """N, thr and recording-gap summary over (t_i0, t_i1] of one segment."""
    ah, dis, t = cum if cum is not None else integrate(seg)
    dts = np.diff(t[i0:i1 + 1])
    g = dts > D.GAP_S
    return {"N": float(ah[i1] - ah[i0]), "thr": float(dis[i1] - dis[i0]),
            "n_gaps": int(g.sum()), "gap_s": float(dts[g].sum()), "max_dt_s": float(dts.max()) if len(dts) else 0.0}


def build_pairs(segs, events):
    """events: DataFrame with segment, setpoint, row, kind ('A'/'T'), anchor (k or -1), order (0.. within segment).
    Returns one row per AT1, AT2 and TT pair with N, thr, ratio N/thr and gap fields; gap_free marks usable pairs."""
    rows = []
    for s, ev in events.sort_values(["segment", "row"]).groupby("segment", sort=True):
        seg = segs[int(s)]
        cum = integrate(seg)
        ev = ev.reset_index(drop=True)
        cand = []
        for m in range(len(ev) - 1):
            a, b = ev.iloc[m], ev.iloc[m + 1]
            if a["kind"] == "A":
                cand.append(("AT1", a, b))
            elif b["kind"] == "T":
                cand.append(("TT", a, b))
        if len(ev) >= 3 and ev.iloc[0]["kind"] == "A":
            cand.append(("AT2", ev.iloc[0], ev.iloc[2]))
        for ptype, a, b in cand:
            v = pair_values(seg, int(a["row"]), int(b["row"]), cum)
            rows.append({"pair_id": f"S{int(s):02d}_{ptype}_{int(a['order'])}-{int(b['order'])}", "segment": int(s),
                         "setpoint": int(a["setpoint"]), "type": ptype, "anchor": int(a["anchor"]),
                         "row_i": int(a["row"]), "row_j": int(b["row"]), "t_i": a["t_cv_end"], "t_j": b["t_cv_end"],
                         **v, "ratio": v["N"] / v["thr"] if v["thr"] > 0 else np.nan, "gap_free": v["n_gaps"] == 0})
    return pd.DataFrame(rows)


def _median(x):
    return float(np.median(x)) if len(x) else np.nan


def lambda_for(tt, segment, setpoint, exclude=None, reading="reduced"):
    """lambda for `segment` from gap-free TT pairs `tt` (DataFrame), optionally without pair `exclude`.
    reading='reduced': the '< 2 TT pairs' fallback test counts the pairs left after the exclusion (literal rule);
    reading='full': it counts the full TT set of that set point (the exclusion only removes the pair from the median).
    Returns (lambda, source)."""
    use = tt[tt["pair_id"] != exclude] if exclude is not None else tt
    own = use.loc[use["segment"] == segment, "ratio"].to_numpy()
    if len(own):
        return _median(own), "segment"
    same = use.loc[use["setpoint"] == setpoint, "ratio"].to_numpy()
    n_same = len(same) if reading == "reduced" else int((tt["setpoint"] == setpoint).sum())
    if n_same >= 2 and len(same):
        return _median(same), f"pooled_{setpoint}"
    other = use.loc[use["setpoint"] != setpoint, "ratio"].to_numpy()
    sp_other = int(use.loc[use["setpoint"] != setpoint, "setpoint"].iloc[0]) if len(other) else -1
    return _median(other), f"fallback_pooled_{sp_other}"


def lambdas(pairs, segment_setpoints):
    """{segment: (lambda, source)} for every segment in segment_setpoints ({segment: setpoint})."""
    tt = pairs[(pairs["type"] == "TT") & pairs["gap_free"]]
    return {s: lambda_for(tt, s, sp) for s, sp in segment_setpoints.items()}


def mad(x):
    x = np.asarray(x, float)
    return float(np.median(np.abs(x - np.median(x)))) if len(x) else np.nan


def tt_residuals(pairs, reading="reduced"):
    """Leave-that-pair-out residual r = N - lambda(-p) * thr for every gap-free TT pair."""
    tt = pairs[(pairs["type"] == "TT") & pairs["gap_free"]].copy()
    lam, src = [], []
    for _, p in tt.iterrows():
        l, s = lambda_for(tt, p["segment"], p["setpoint"], exclude=p["pair_id"], reading=reading)
        lam.append(l)
        src.append(s)
    tt["lambda_loo"] = lam
    tt["lambda_loo_source"] = src
    tt["resid"] = tt["N"] - tt["lambda_loo"] * tt["thr"]
    return tt


def sigma_tt(resid_table):
    """{setpoint: 1.4826 * MAD of the TT residuals}."""
    return {int(sp): MAD_K * mad(g["resid"]) for sp, g in resid_table.groupby("setpoint")}


def offsets(pairs, lam):
    """Ah offset N - lambda_s * thr for every pair (Term3 for AT1, Term3' for AT2; 0 by construction only for a
    segment's own TT pair when it is the segment's only TT pair)."""
    out = pairs.copy()
    out["lambda"] = [lam[s][0] for s in out["segment"]]
    out["lambda_source"] = [lam[s][1] for s in out["segment"]]
    out["offset"] = out["N"] - out["lambda"] * out["thr"]
    return out
