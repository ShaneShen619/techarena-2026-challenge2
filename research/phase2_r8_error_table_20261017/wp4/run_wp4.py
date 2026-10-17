"""WP4: daily cycle table (EXECUTION_PROMPT.md, WP4). Diagnostic, from the full operation data.

A cycle is one SOC swing of the usage profile: from an SOC top (local maximum of integrated Ah with prominence
>= 10 Ah) through the lowest point to the next top, inside one segment (D4.1)."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common8 import H  # noqa: E402
from events import CELLS, _cv_ends, iter_segments, segment_arrays  # noqa: E402
from v2 import anchors_by_checkup  # noqa: E402

OUT = os.path.join(STUDY, "outputs")
PROM_AH = 10.0
WIN = 7


def build():
    op = H.full_op()
    fc = H.full_charges(op)
    anc = anchors_by_checkup(fc, H.CK)
    anc_t = np.array([anc[j]["t_end"] for j in range(8)])
    ev = pd.read_csv(os.path.join(STUDY, "outputs", "table_events.csv"))
    ev = ev[ev.unit == "pack_mean"]
    prog_t = pd.to_datetime(ev["t_cv_end"]).to_numpy()
    rows = []
    for seg, g in iter_segments(op):
        t, i, ah = segment_arrays(g)
        u = g["pack_voltage_V"].to_numpy(float)
        V = g[CELLS].to_numpy(float)
        T = g["temp_mean_C"].to_numpy(float)
        ts = g["timestamp"].to_numpy()
        sp = int(g["chamber_temperature_C"].iloc[0])
        cve = _cv_ends(i, u)
        tops, _ = find_peaks(ah, prominence=PROM_AH)
        dt = np.diff(t, prepend=t[0])
        dt[(dt > 600) | (dt <= 0)] = 0.0
        q = i * dt / 3600.0
        for a, b in zip(tops[:-1], tops[1:]):
            m = a + int(np.argmin(ah[a:b + 1]))
            tt = pd.Timestamp(ts[a])
            prev_cv = cve[cve <= b]
            after = np.where((t > t[a]) & (t <= t[a] + 3600.0))[0]
            rest1h = (u[after[-1]] if len(after) and np.all(np.abs(i[a + 1:after[-1] + 1]) < 0.5)
                      and t[after[-1]] - t[a] >= 3000 else np.nan)
            mm = int((anc_t <= tt).sum()) - 1
            pi = np.where(prog_t <= np.datetime64(tt))[0]
            rows.append(dict(
                t_top=str(tt), t_bottom=str(pd.Timestamp(ts[m])), t_next_top=str(pd.Timestamp(ts[b])), segment=int(seg),
                setpoint=sp, month=mm, ck_index=int((H.CK < tt).sum()) - 1,
                hours_since_program=((tt - pd.Timestamp(prog_t[pi[-1]])).total_seconds() / 3600.0) if len(pi) else np.nan,
                hours_since_segment_start=(tt - pd.Timestamp(ts[0])).total_seconds() / 3600.0,
                V_top_pack=float(u[a]), I_top=float(i[a]), V_bottom_pack=float(u[m]), I_bottom=float(i[m]),
                V_next_top_pack=float(u[b]), V_rest_1h_after_top=float(rest1h),
                Ah_discharged=float(-q[a + 1:m + 1][q[a + 1:m + 1] < 0].sum()),
                Ah_charged=float(q[m + 1:b + 1][q[m + 1:b + 1] > 0].sum()),
                swing_down_Ah=float(ah[a] - ah[m]), swing_up_Ah=float(ah[b] - ah[m]),
                cv_reached=bool(((u[m:b + 1] >= 13.95) & (i[m:b + 1] > 0)).any()),
                top_Ah_rel_last_cv_end=float(ah[b] - ah[prev_cv[-1]]) if len(prev_cv) else np.nan,
                cell_spread_top_V=float(V[b].max() - V[b].min()), cell_spread_bottom_V=float(V[m].max() - V[m].min()),
                T_mean_C=float(T[a:b + 1].mean()), dT_mean=float(T[a:b + 1].mean() - sp),
                duration_h=(t[b] - t[a]) / 3600.0))
    df = pd.DataFrame(rows).sort_values("t_top").reset_index(drop=True)
    df["cycle_id"] = [f"C{k:04d}" for k in range(len(df))]
    # slot: order of the cycle inside its program block (between consecutive deep-program CV ends)
    blk = np.searchsorted(prog_t, pd.to_datetime(df["t_top"]).to_numpy(), side="right")
    df["program_block"] = blk
    df["slot"] = df.groupby("program_block").cumcount()
    return df


def r_cyc(df, col, win=WIN):
    """Value minus the leave-one-out median of the centred 7-cycle window of the same set point."""
    out = pd.Series(np.nan, index=df.index)
    for sp, g in df.groupby("setpoint"):
        g = g.sort_values("t_top")
        idx = g.index.to_numpy()
        v = g[col].to_numpy(float)
        h = win // 2
        for p in range(len(idx)):
            lo, hi = max(0, p - h), min(len(idx), p + h + 1)
            o = np.r_[v[lo:p], v[p + 1:hi]]
            o = o[np.isfinite(o)]
            if len(o) >= 3 and np.isfinite(v[p]):
                out[idx[p]] = v[p] - np.median(o)
    return out


def r_cyc_slot(df, col, k=3):
    """Phase-matched variant: value minus the median of the same slot in the k blocks before and after, same set point."""
    out = pd.Series(np.nan, index=df.index)
    for (sp, sl), g in df.groupby(["setpoint", "slot"]):
        g = g.sort_values("t_top")
        idx, v = g.index.to_numpy(), g[col].to_numpy(float)
        for p in range(len(idx)):
            o = np.r_[v[max(0, p - k):p], v[p + 1:p + 1 + k]]
            o = o[np.isfinite(o)]
            if len(o) >= 3 and np.isfinite(v[p]):
                out[idx[p]] = v[p] - np.median(o)
    return out


if __name__ == "__main__":
    df = build()
    for col in ("top_Ah_rel_last_cv_end", "V_bottom_pack", "swing_down_Ah"):
        df[f"R_cyc_{col}"] = r_cyc(df, col)
        df[f"R_cyc_slot_{col}"] = r_cyc_slot(df, col)
    lead = ["cycle_id", "t_top", "segment", "setpoint", "month", "program_block", "slot"]
    df = df[lead + [c for c in df.columns if c not in lead]]
    df.to_csv(os.path.join(OUT, "table_cycles.csv"), index=False)
    os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
    s = dict(n_cycles=int(len(df)), per_segment=df.groupby("segment").size().to_dict(),
             cv_reached_share=float(df["cv_reached"].mean()), median_duration_h=float(df["duration_h"].median()),
             slot_counts=df.groupby("program_block").size().value_counts().to_dict())
    json.dump({k: ({str(a): b for a, b in v.items()} if isinstance(v, dict) else v) for k, v in s.items()},
              open(os.path.join(HERE, "outputs", "wp4_summary.json"), "w"), indent=1)
    print(json.dumps({k: ({str(a): b for a, b in v.items()} if isinstance(v, dict) else v) for k, v in s.items()}, indent=1))
