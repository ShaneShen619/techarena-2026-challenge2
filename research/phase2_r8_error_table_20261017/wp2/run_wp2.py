"""WP2: event table, one row per deep program x {cell1..cell4, pack_mean} (EXECUTION_PROMPT.md, WP2).
Diagnostic: built from the full operation data."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common8 import H  # noqa: E402
from events import CELLS, MAIN_STEP  # noqa: E402
from v2 import anchors_by_checkup, theil_sen  # noqa: E402
import eventcurves as EC  # noqa: E402

RESEARCH = os.path.dirname(STUDY)
EVENTS = os.path.join(RESEARCH, "phase2_r6_robust_20261016", "sources", "rebound_diagnosis", "outputs", "events_merged.csv")
OUT = os.path.join(STUDY, "outputs")
VARIANTS = list(H.VARIANTS)
UNITS = CELLS + ["pack_mean"]
SEED = 20261017
N_BOOT = 2000


def segment_table(op):
    g = op.groupby("segment").agg(t0=("timestamp", "min"), t1=("timestamp", "max"), sp=("chamber_temperature_C", "first"))
    g = g.sort_values("t0")
    g["prev_sp"] = g["sp"].shift(1)
    g["prev_gap_days"] = (g["t0"] - g["t1"].shift(1)).dt.total_seconds() / 86400.0
    # a gap of more than 2 days between visible segments holds a checkup (and possibly a missing segment); the chamber
    # temperature inside it is not observed. Direct 25 -> 45 C switches have gaps of 0.3-1.1 days.
    gap = g["prev_gap_days"] > 2.0
    g["switch_kind"] = np.where(g["prev_gap_days"].isna(), "campaign_start",
                                np.where(gap, "after_checkup_gap",
                                         np.where(g["prev_sp"] != g["sp"], "direct_switch", "same_setpoint")))
    return g


def discharge_cum(op):
    parts = []
    for seg, g in op.groupby("segment", sort=True):
        t = g["elapsed_s"].to_numpy(float)
        i = g["current_A"].to_numpy(float)
        dt = np.diff(t, prepend=t[0])
        dt[(dt > 600) | (dt <= 0)] = 0.0
        parts.append(pd.DataFrame({"ts": g["timestamp"].to_numpy(), "dis": np.where(i < 0, -i, 0.0) * dt / 3600.0}))
    d = pd.concat(parts, ignore_index=True).sort_values("ts", kind="stable")
    d["cum"] = d["dis"].cumsum()
    return d


def cum_at(d, t):
    i = int(np.searchsorted(d["ts"].to_numpy(), np.datetime64(t), side="right")) - 1
    return float(d["cum"].iloc[i]) if i >= 0 else 0.0


def use_flags():
    c = pd.read_csv(os.path.join(STUDY, "outputs", "table_cases.csv"))
    c = c[(c.scenario == "real") & (c.model == "SUB") & (c.delta == 0.4)]
    flags = {}
    for _, r in c.iterrows():
        for col, name in (("ev_E_cur", "end45_E_cur"), ("ev_E_prev", "end45_E_prev"), ("ev_rate_fit", "rate_fit"),
                          ("ev_after_first", "after_first"), ("ev_after_last", "after_last")):
            v = r[col]
            if isinstance(v, str) and v:
                for ts in v.split("|"):
                    flags.setdefault(pd.Timestamp(ts), {}).setdefault(name, []).append(r["checkup"])
    return flags


def build():
    op = H.full_op()
    fc, st, a4 = H.tables(op, "full")
    anc = anchors_by_checkup(fc, H.CK)
    em = pd.read_csv(EVENTS, parse_dates=["t_cv_end"])
    progs = EC.programs(op)
    pf = EC.as_frame(progs)
    assert len(progs) == 41 and (pf["t_cv_end"].to_numpy() == em["t_cv_end"].to_numpy()).all()
    for v in VARIANTS:
        assert (st[v]["t_cv_end"].to_numpy() == pf["t_cv_end"].to_numpy()).all(), v
    segs = segment_table(op)
    dis = discharge_cum(op)
    flags = use_flags()
    anc_t = np.array([anc[j]["t_end"] for j in range(8)])
    anc_q = np.array([anc[j]["Q_Ah"] for j in range(8)])
    rows = []
    for idx, p in enumerate(progs):
        ev = em.iloc[idx]
        t_cv = p["t_cv_end"]
        m = int((anc_t <= t_cv).sum()) - 1
        ck_i = int((H.CK < t_cv).sum()) - 1
        sg = segs.loc[p["segment"]]
        g, e, s, stop, V = p["g"], p["e"], p["s"], p["stop"], p["V"]
        d, band = p["depth"], p["band"]
        vb = V[e:e + stop][band]
        db = d[band]
        imax = e + int(np.argmax(d))
        v_max = V[imax]
        ranks = pd.Series(v_max).rank(method="min").to_numpy()
        tt = p["t"][s:e + stop]
        rest_v = V[s - 1] if s > 0 else np.full(4, np.nan)
        base = dict(event_id=f"E{idx:02d}", t_cv_end=str(t_cv), segment=p["segment"], setpoint=int(ev["setpoint_C"]),
                    month=m, ck_index=ck_i,
                    days_since_anchor=(t_cv - anc_t[m]).total_seconds() / 86400.0,
                    days_since_checkup=(t_cv - H.CK[ck_i]).total_seconds() / 86400.0,
                    T_cv_end=float(ev["T_cv_end"]), **{f"T_at{x}": float(ev[f"T_at{x}"]) for x in (15, 25, 35, 45)},
                    dT_cv_end=float(ev["T_cv_end"]) - float(ev["setpoint_C"]),
                    dT_at45=float(ev["T_at45"]) - float(ev["setpoint_C"]),
                    segment_start=str(sg["t0"]), switch_kind=sg["switch_kind"], prev_segment_gap_days=sg["prev_gap_days"],
                    days_since_switch=(t_cv - sg["t0"]).total_seconds() / 86400.0,
                    rest_before_chg_h=float(ev["rest_before_chg_h"]), chg_Ah=float(ev["chg_Ah"]),
                    chg_start_pack_V=float(ev["chg_start_V"]), cv_Ah=float(ev["cv_Ah"]), cv_h=float(ev["cv_h"]),
                    I_cv_end=float(ev["I_cv_end"]),
                    throughput_dis_Ah_since_anchor=cum_at(dis, t_cv) - cum_at(dis, anc_t[m]),
                    throughput_dis_Ah_since_start=cum_at(dis, t_cv),
                    has_recording_gap=bool((np.diff(tt) > 600).any()), max_depth_Ah=float(d.max()),
                    **{f"V_at{x}": float(ev[f"V_at{x}"]) for x in (15, 25, 35, 45)},
                    **{f"I_at{x}": float(ev[f"I_at{x}"]) for x in (15, 25, 35, 45)},
                    R_mean_mOhm=float(ev["R_mean_mOhm"]),
                    cell_spread_cv_end_V=float(V[e].max() - V[e].min()),
                    cell_spread_maxdepth_V=float(v_max.max() - v_max.min()),
                    weakest_cell_maxdepth=CELLS[int(np.argmin(v_max))][:-2],
                    Q_interp_Ah=float(np.interp(t_cv.value, [x.value for x in anc_t], anc_q))
                    if anc_t[0] <= t_cv <= anc_t[-1] else np.nan)
        fl = flags.get(t_cv, {})
        for name in ("end45_E_cur", "end45_E_prev", "rate_fit", "after_first", "after_last"):
            base[f"use_{name}"] = "|".join(fl.get(name, []))
        base["used_by_SUB_real"] = bool(fl)
        for unit in UNITS:
            r = dict(base, unit=unit)
            if unit == "pack_mean":
                vu, vu_b = V[e:e + stop].mean(axis=1), vb.mean(axis=1)
                for v in VARIANTS:
                    r[f"depth_{v}"] = float(st[v].iloc[idx]["step_mean"])
                r["R_pulse_mOhm"] = float(ev["R_mean_mOhm"])
                r["start_rest_V"] = float(rest_v.sum())
                r["V_rank_maxdepth"] = np.nan
            else:
                ci = CELLS.index(unit)
                vu_b = vb[:, ci]
                for v in VARIANTS:
                    r[f"depth_{v}"] = float(st[v].iloc[idx][f"step_{unit}"])
                r["R_pulse_mOhm"] = float(ev[f"R_{unit}"])
                r["start_rest_V"] = float(rest_v[ci])
                r["V_rank_maxdepth"] = float(ranks[ci])
            h, w, pk = EC.sharpness(db, vu_b)
            r.update(sharp_height_mV_per_Ah=h, sharp_fwhm_Ah=w, dvdq_peak_Ah=pk,
                     plateau_upper_V=EC.plateau(db, vu_b, MAIN_STEP["upper_window_Ah"]),
                     plateau_lower_V=EC.plateau(db, vu_b, MAIN_STEP["lower_window_Ah"]))
            rows.append(r)
    df = pd.DataFrame(rows)
    # program index after the anchor (per month, by time)
    ev1 = df[df.unit == "pack_mean"][["event_id", "month", "t_cv_end"]].sort_values("t_cv_end")
    ev1["program_index"] = ev1.groupby("month").cumcount() + 1
    df = df.merge(ev1[["event_id", "program_index"]], on="event_id")
    df["is_first_after_anchor"] = df["program_index"] == 1
    checks = dict(n_events=int(df.event_id.nunique()), n_rows=int(len(df)))
    pm = df[df.unit == "pack_mean"].set_index("event_id")
    emi = em.copy()
    emi.index = pm.index
    checks["variants_vs_events_merged_max_abs_Ah"] = {v: float((pm[f"depth_{v}"] - emi[v]).abs().max()) for v in VARIANTS}
    for c in ("segment", "setpoint_C", "chg_Ah", "cv_Ah", "cv_h", "I_cv_end", "T_cv_end", "rest_before_chg_h",
              "R_mean_mOhm"):
        mine = pm["setpoint"] if c == "setpoint_C" else pm[c]
        checks[f"{c}_equal"] = bool(np.allclose(mine.to_numpy(float), emi[c].to_numpy(float), atol=0, rtol=0, equal_nan=True))
    checks["chg_start_pack_V_equals_sum_of_cell_rest"] = float((pm["chg_start_pack_V"] - pm["start_rest_V"]).abs().max())
    checks["variants_match"] = bool(max(checks["variants_vs_events_merged_max_abs_Ah"].values()) <= 1e-12)
    return df, checks


# ------------------------------------------------------------------ residual definitions (frozen in WP5 protocol)
def theil_sen_line(x, y):
    b = theil_sen(x, y)
    return b, float(np.median(np.asarray(y) - b * np.asarray(x)))


def add_residuals(df):
    t0 = pd.Timestamp(df["t_cv_end"].min())
    df["t_days"] = (pd.to_datetime(df["t_cv_end"]) - t0).dt.total_seconds() / 86400.0
    df["R_seg"] = np.nan
    for (seg, unit), g in df.groupby(["segment", "unit"]):
        for i in g.index:
            o = g.drop(index=i)
            if len(o) < 3:
                continue
            b, a = theil_sen_line(o["t_days"], o["depth_main"])
            df.loc[i, "R_seg"] = df.loc[i, "depth_main"] - (a + b * df.loc[i, "t_days"])
    df["R_anc"] = np.nan
    df["a_anc_loo"] = np.nan
    ok = df["Q_interp_Ah"].notna()
    for (sp, unit), g in df[ok].groupby(["setpoint", "unit"]):
        for i in g.index:
            o = g[g["month"] != df.loc[i, "month"]]
            if not len(o):
                continue
            a = float((o["depth_main"] - o["Q_interp_Ah"]).mean())
            df.loc[i, "a_anc_loo"] = a
            df.loc[i, "R_anc"] = df.loc[i, "depth_main"] - (a + df.loc[i, "Q_interp_Ah"])
    med = df[df.unit != "pack_mean"].groupby("event_id")["depth_main"].median().rename("pack_median_depth")
    df = df.merge(med, on="event_id")
    df["R_cell"] = df["depth_main"] - df["pack_median_depth"]
    return df


def b_free_fit(df, seed=SEED, n_boot=N_BOOT):
    """depth = a_setpoint + b * Q_interp on pack_mean events (common b); block bootstrap over months."""
    p = df[(df.unit == "pack_mean") & df["Q_interp_Ah"].notna()].copy()

    def fit(q):
        X = np.column_stack([q["Q_interp_Ah"], (q["setpoint"] == 25).astype(float), (q["setpoint"] == 45).astype(float)])
        return float(np.linalg.lstsq(X, q["depth_main"].to_numpy(), rcond=None)[0][0])
    b = fit(p)
    months = np.array(sorted(p["month"].unique()))
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n_boot):
        pick = rng.choice(months, size=len(months), replace=True)
        q = pd.concat([p[p["month"] == mm] for mm in pick], ignore_index=True)
        if q["setpoint"].nunique() < 2 or q["Q_interp_Ah"].nunique() < 3:
            continue
        bs.append(fit(q))
    lo, hi = np.percentile(bs, [5, 95])
    return dict(b=b, ci90=[float(lo), float(hi)], n_events=int(len(p)), n_months=int(len(months)), n_boot_used=len(bs),
                seed=seed)


if __name__ == "__main__":
    df, checks = build()
    df = add_residuals(df)
    bf = b_free_fit(df)
    lead = ["event_id", "unit", "t_cv_end", "segment", "setpoint", "month", "program_index", "is_first_after_anchor"]
    df = df[lead + [c for c in df.columns if c not in lead]].sort_values(["t_cv_end", "unit"]).reset_index(drop=True)
    df.to_csv(os.path.join(OUT, "table_events.csv"), index=False)
    os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
    out = dict(checks=checks, b_free_fit=bf)
    json.dump(out, open(os.path.join(HERE, "outputs", "wp2_checks.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    if not checks["variants_match"]:
        raise SystemExit("variant depths do not match events_merged")
