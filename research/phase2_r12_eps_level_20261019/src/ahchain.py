"""Round 12 registered Ah chain (WP1): integration, pairing, loss rule, chain terms, intervals and the WP3 gates.

WP2 and WP3 import this module unchanged; any change is a new registered version (notes/DECISIONS.md).
Quantities are charge contents in Ah. F_j - F_i = N_ij - lambda * thr_ij between two CV ends i -> j."""
import numpy as np
import pandas as pd

# ---- registered constants -------------------------------------------------------------------------------
MAX_DT_S = 600.0         # package convention (_integrated_ah): a sample with dt > 600 s or dt <= 0 contributes 0
GAP_DT_S = 60.0          # a pair with any sample spacing > 60 s inside (t_i, t_j] is excluded ...
COUNTER_FLAT_AH = 0.0005  # ... except the chamber-switch idle, where both counters must change by < 0.0005 Ah
MIN_POOLED_TT = 2        # a set point needs >= 2 TT pairs overall for its pooled median
MAD_K = 1.4826
SE_WIDEN = 2.0           # term intervals: [min, max] over lambda sensitivities widened by +-2 SE
G_NOISE_MAX_AH = 0.30
G_T_HALF_WIDTH_AH = 0.25
G_E2_MAX_AH = 0.20
SWITCH_SETPOINTS = (25, 45)


# ---- integration ------------------------------------------------------------------------------------------
def segment_arrays(seg):
    """Per-sample arrays of one segment: elapsed s, current, package-convention dt, cumulative net Ah and
    cumulative discharged Ah (both 0 at the first sample, whose dt is 0), counters."""
    t = seg["elapsed_s"].to_numpy(float)
    i = seg["current_A"].to_numpy(float)
    raw = np.diff(t, prepend=t[0])
    dt = raw.copy()
    dt[(dt > MAX_DT_S) | (dt <= 0)] = 0.0
    q = i * dt / 3600.0
    nan = np.full(len(t), np.nan)
    return dict(t=t, i=i, raw_dt=raw, dt=dt, net=np.cumsum(q), dis=np.cumsum(np.where(i < 0, -q, 0.0)),
                chg_cum=seg["charge_Ah_cum"].to_numpy(float) if "charge_Ah_cum" in seg else nan,
                dis_cum=seg["discharge_Ah_cum"].to_numpy(float) if "discharge_Ah_cum" in seg else nan)


def integrated_ah(seg):
    """(current, cumulative net Ah) exactly as the package's _integrated_ah."""
    a = segment_arrays(seg)
    return a["i"], a["net"]


def interval_sums(arrs, si, ei, sj, ej):
    """N, thr and the largest sample spacing over (t_i, t_j] where i = (segment si, index ei), j = (sj, ej).
    si == sj, or sj is the segment that follows si; the boundary between two segments contributes 0
    (its spacing is returned separately, with the two counter changes across it)."""
    a = arrs[si]
    if si == sj:
        n = a["net"][ej] - a["net"][ei]
        thr = a["dis"][ej] - a["dis"][ei]
        mx = float(a["raw_dt"][ei + 1:ej + 1].max()) if ej > ei else 0.0
        return dict(N=n, thr=thr, max_dt_inside_s=mx, boundary_s=np.nan, d_chg_boundary=np.nan, d_dis_boundary=np.nan)
    b = arrs[sj]
    n = (a["net"][-1] - a["net"][ei]) + b["net"][ej]
    thr = (a["dis"][-1] - a["dis"][ei]) + b["dis"][ej]
    mx = max(float(a["raw_dt"][ei + 1:].max(initial=0.0)), float(b["raw_dt"][1:ej + 1].max(initial=0.0)))
    return dict(N=n, thr=thr, max_dt_inside_s=mx, boundary_s=b["t"][0] - a["t"][-1],
                d_chg_boundary=b["chg_cum"][0] - a["chg_cum"][-1], d_dis_boundary=b["dis_cum"][0] - a["dis_cum"][-1])


# ---- pairing ----------------------------------------------------------------------------------------------
def build_pairs(events, segments, ck_dates):
    """All consecutive CV-end pairs i -> j with their type, N, thr and admissibility.

    events: DataFrame with event_id, segment, setpoint, type ('A'/'T'), anchor_k, t_cv_end (one row per CV end).
    segments: {segment number: DataFrame}. ck_dates: checkup dates (Timestamps).
    Types: AT anchor -> next top-up (same segment), TT top-up -> top-up (same segment),
    X last 25 degC CV end -> first 45 degC CV end across a chamber switch (consecutive segments, counters flat)."""
    ev = events.sort_values("t_cv_end").reset_index(drop=True)
    arrs = {s: segment_arrays(g) for s, g in segments.items()}
    idx = {}
    for _, r in ev.iterrows():
        g = segments[r["segment"]]
        k = np.where(g["timestamp"].to_numpy() == np.datetime64(r["t_cv_end"]))[0]
        cand = [x for x in k if g["current_A"].iloc[x] > 0.5]
        idx[r["event_id"]] = int(cand[-1] if cand else k[0])
    ck = pd.DatetimeIndex(ck_dates)
    seg_order = sorted(segments)
    rows = []
    for a in range(len(ev) - 1):
        i, j = ev.iloc[a], ev.iloc[a + 1]
        row = dict(pair=f"{i['event_id']}-{j['event_id']}", i=i["event_id"], j=j["event_id"],
                   seg_i=int(i["segment"]), seg_j=int(j["segment"]), sp_i=int(i["setpoint"]), sp_j=int(j["setpoint"]),
                   t_i=i["t_cv_end"], t_j=j["t_cv_end"], anchor_k=int(i["anchor_k"]) if i["type"] == "A" else -1,
                   type="", admissible=False, reason="")
        if ((ck > i["t_cv_end"]) & (ck <= j["t_cv_end"])).any():
            row.update(type="none", reason="checkup between")
            rows.append(row); continue
        same = i["segment"] == j["segment"]
        if same:
            row["type"] = "AT" if i["type"] == "A" else "TT"
        else:
            nxt = seg_order.index(i["segment"]) + 1
            if (nxt < len(seg_order) and seg_order[nxt] == j["segment"]
                    and (int(i["setpoint"]), int(j["setpoint"])) == SWITCH_SETPOINTS):
                row["type"] = "X"
            else:
                row.update(type="none", reason="segment boundary that is not a chamber switch")
                rows.append(row); continue
        sums = interval_sums(arrs, i["segment"], idx[i["event_id"]], j["segment"], idx[j["event_id"]])
        row.update(sums)
        reasons = []
        if sums["max_dt_inside_s"] > GAP_DT_S:
            reasons.append(f"recording gap {sums['max_dt_inside_s']:.0f} s")
        if row["type"] == "X" and not (abs(sums["d_chg_boundary"]) < COUNTER_FLAT_AH
                                       and abs(sums["d_dis_boundary"]) < COUNTER_FLAT_AH):
            reasons.append("counters not flat across the switch idle")
        if row["type"] == "TT" and j["type"] != "T":
            reasons.append("j is not a top-up")
        row["admissible"] = not reasons
        row["reason"] = "; ".join(reasons)
        rows.append(row)
    return pd.DataFrame(rows)


# ---- loss rule --------------------------------------------------------------------------------------------
def lam(pairs, segment, setpoint, exclude=None):
    """(lambda, source) for a segment: median N/thr of its admissible TT pairs (without `exclude`); if none, the
    pooled median of the same set point (needs >= 2 TT pairs overall); otherwise the other set point's pooled median."""
    tt = pairs[(pairs["type"] == "TT") & pairs["admissible"]]
    ratio = tt["N"] / tt["thr"]
    keep = tt["pair"] != exclude
    own = keep & (tt["seg_i"] == segment)
    if own.any():
        return float(np.median(ratio[own])), "segment"
    same = tt["sp_i"] == setpoint
    if same.sum() >= MIN_POOLED_TT and (same & keep).any():
        return float(np.median(ratio[same & keep])), "pooled same set point"
    other = (tt["sp_i"] != setpoint) & keep
    return (float(np.median(ratio[other])), "pooled other set point") if other.any() else (np.nan, "none")


def pooled_lam(pairs, setpoint):
    tt = pairs[(pairs["type"] == "TT") & pairs["admissible"] & (pairs["sp_i"] == setpoint)]
    return float(np.median(tt["N"] / tt["thr"])) if len(tt) else np.nan


def sigma_mad(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(MAD_K * np.median(np.abs(x - np.median(x)))) if len(x) else np.nan


def se_mad(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return sigma_mad(x) / np.sqrt(len(x)) if len(x) else np.nan


def tt_residuals(pairs):
    """Leave-one-out residuals r = N - lambda(without the pair) * thr of the admissible TT pairs."""
    tt = pairs[(pairs["type"] == "TT") & pairs["admissible"]].copy()
    out = []
    for _, p in tt.iterrows():
        lm, src = lam(pairs, p["seg_i"], p["sp_i"], exclude=p["pair"])
        out.append(dict(pair=p["pair"], segment=p["seg_i"], setpoint=p["sp_i"], lam_loo=lm, lam_source=src,
                        r=p["N"] - lm * p["thr"]))
    return pd.DataFrame(out)


def g_noise(res):
    s25 = sigma_mad(res.loc[res["setpoint"] == 25, "r"])
    s45 = sigma_mad(res.loc[res["setpoint"] == 45, "r"])
    ok = bool(np.isfinite(s25) and np.isfinite(s45) and s25 <= G_NOISE_MAX_AH and s45 <= G_NOISE_MAX_AH)
    return dict(sigma_TT_25=s25, sigma_TT_45=s45, passed=ok)


# ---- chain terms ------------------------------------------------------------------------------------------
def terms(pairs):
    """Event values of Term1 (anchor 0), Term3_k (25 degC anchors k >= 1) and Term2_j (switches), with every
    lambda used. Term3 and Term2 use admissible pairs only."""
    adm = pairs[pairs["admissible"]]
    rows = []
    for _, p in adm[adm["type"] == "AT"].iterrows():
        lm, src = lam(pairs, p["seg_i"], p["sp_i"])
        v = p["N"] - lm * p["thr"]
        if p["anchor_k"] == 0:
            rows.append(dict(term="Term1", pair=p["pair"], k=0, segment=p["seg_i"], lam_main=lm, lam_source=src,
                             value_main=-v, lam_pooled=pooled_lam(pairs, p["sp_i"]),
                             value_pooled=-(p["N"] - pooled_lam(pairs, p["sp_i"]) * p["thr"]), N=p["N"], thr=p["thr"]))
        elif p["sp_i"] == 25:
            lp = pooled_lam(pairs, 25)
            rows.append(dict(term="Term3", pair=p["pair"], k=int(p["anchor_k"]), segment=p["seg_i"], lam_main=lm,
                             lam_source=src, value_main=v, lam_pooled=lp, value_pooled=p["N"] - lp * p["thr"],
                             N=p["N"], thr=p["thr"]))
    for _, p in adm[adm["type"] == "X"].iterrows():
        l25, s25 = lam(pairs, p["seg_i"], 25)
        l45, s45 = lam(pairs, p["seg_j"], 45)
        lb = 0.5 * (l25 + l45)
        rows.append(dict(term="Term2", pair=p["pair"], k=-1, segment=p["seg_i"], lam_main=lb,
                         lam_source=f"mean({s25}, {s45})", value_main=p["N"] - lb * p["thr"],
                         lam_25=l25, value_lam25=p["N"] - l25 * p["thr"], lam_45=l45, value_lam45=p["N"] - l45 * p["thr"],
                         N=p["N"], thr=p["thr"], boundary_h=p["boundary_s"] / 3600.0))
    return pd.DataFrame(rows)


def term_interval(points, event_values, se=None):
    """Registered interval: [min, max] of the point over the lambda sensitivities, widened by +-2 SE.
    SE = 1.4826 MAD / sqrt(n) of the event values unless given (Term1: sigma_TT,45)."""
    pts = np.asarray([p for p in points if np.isfinite(p)], float)
    se = se_mad(event_values) if se is None else se
    if not len(pts) or not np.isfinite(se):
        return dict(lo=np.nan, hi=np.nan, se=se)
    return dict(lo=float(pts.min() - SE_WIDEN * se), hi=float(pts.max() + SE_WIDEN * se), se=float(se))


def t_top(tm, noise, j_dvdq_median=np.nan, exclude_k=()):
    """T_top = Term1 + median_j Term2_j + median_k Term3_k with its interval; G_noise, G_E2 (widening), G_T."""
    out = dict(G_noise=noise)
    if not noise["passed"]:
        out.update(status="not identifiable (G_noise failed)", point=np.nan, lo=np.nan, hi=np.nan)
        return out
    t1 = tm[tm["term"] == "Term1"]
    t2 = tm[tm["term"] == "Term2"]
    t3 = tm[(tm["term"] == "Term3") & ~tm["k"].isin(list(exclude_k))]
    if len(t1) != 1 or not len(t2) or not len(t3):
        out.update(status="not identifiable (missing term)", point=np.nan, lo=np.nan, hi=np.nan)
        return out
    p1 = float(t1["value_main"].iloc[0])
    p2 = float(np.median(t2["value_main"]))
    p3 = float(np.median(t3["value_main"]))
    i1 = term_interval([p1], [p1], se=noise["sigma_TT_45"])
    i2 = term_interval([p2, float(np.median(t2["value_lam25"])), float(np.median(t2["value_lam45"]))], t2["value_main"])
    i3 = term_interval([p3], t3["value_main"])
    g_e2 = dict(median_J_dvdq=j_dvdq_median, median_Term2=p2,
                diff=float(j_dvdq_median - p2) if np.isfinite(j_dvdq_median) else np.nan)
    if np.isfinite(j_dvdq_median):
        g_e2["consistent"] = bool(abs(j_dvdq_median - p2) <= G_E2_MAX_AH)
        if not g_e2["consistent"]:
            i2 = dict(i2, lo=min(i2["lo"], j_dvdq_median), hi=max(i2["hi"], j_dvdq_median), widened=True)
    else:
        g_e2["consistent"] = None
    lo, hi = i1["lo"] + i2["lo"] + i3["lo"], i1["hi"] + i2["hi"] + i3["hi"]
    half = 0.5 * (hi - lo)
    out.update(Term1=dict(point=p1, **i1), Term2=dict(point=p2, n=len(t2), **i2), Term3=dict(point=p3, n=len(t3), **i3),
               point=p1 + p2 + p3, lo=lo, hi=hi, half_width=half, G_E2=g_e2,
               G_T=dict(half_width=half, identified=bool(half <= G_T_HALF_WIDTH_AH)),
               status="identified" if half <= G_T_HALF_WIDTH_AH else "not identified (G_T)")
    return out


# ---- E3 physics diagnostic -------------------------------------------------------------------------------
N_CELLS = 4
DUDT_ASSUMED_V_PER_K = 3e-4      # +-0.3 mV/K per cell, an assumption (no cited LFP/graphite high-SOC value)
S_WINDOWS_AH = ((0.5, 2.0), (0.25, 1.0), (1.0, 3.0))   # main first


def ck0_top_slope(discharged_ah, pack_v, window):
    """s > 0: pack-voltage change per Ah of charge content near the top of the CK0 curve (OLS on the window)."""
    sel = (discharged_ah >= window[0]) & (discharged_ah <= window[1])
    return float(-np.polyfit(discharged_ah[sel], pack_v[sel], 1)[0])


def term2_e3(dv, dtemp, slopes):
    """Term2_E3 = (dV - 4 dU/dT dT) / s; point at dU/dT = 0 and the main window, interval over +-dU/dT x windows."""
    vals = [(dv - N_CELLS * u * dtemp) / s for s in slopes for u in (-DUDT_ASSUMED_V_PER_K, DUDT_ASSUMED_V_PER_K)]
    return dict(point=dv / slopes[0], lo=float(min(vals)), hi=float(max(vals)))
