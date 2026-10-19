"""WP0.4: catalogue of every CCCV charge that reaches CV (pack >= 13.95 V, ending with 0 < I < 6 A).

Descriptive only: no Ah balance, step location or epsilon-related quantity is computed here."""
import os
import numpy as np
import pandas as pd
import data12 as D

CHARGE_I_MIN_A = 0.5     # a charge is a maximal run of samples with I > 0.5 A (package CHARGE_I_MIN_A)
CV_V_MIN = 13.95
END_I_MAX_A = 6.0
REST_I_MAX_A = 0.5       # |I| <= 0.5 A counts as rest
ANCHOR_START_V_MAX = 12.3  # package START_V_MAX
ANCHOR_Q_MIN_AH = 50.0     # package ANCHOR_Q_MIN_AH
TAPER_I_A = 20.0         # sensitivity CV start: first sample after reaching 13.95 V with I < 20.0 A
PULSE_I_A = -15.0
GAP_DT_S = 60


def charge_runs(i):
    pos = i > CHARGE_I_MIN_A
    starts = np.where(pos & ~np.r_[False, pos[:-1]])[0]
    ends = np.where(pos & ~np.r_[pos[1:], False])[0]
    return list(zip(starts, ends))


def catalogue():
    rows, near = [], []
    for s, g in D.segments().items():
        i, ah = D.integrated_ah(g)
        t = g["timestamp"]; el = g["elapsed_s"].to_numpy(float)
        u = g["pack_voltage_V"].to_numpy(float); V = g[D.CELLS].to_numpy(float)
        T = g["temp_mean_C"].to_numpy(float)
        chg = g["charge_Ah_cum"].to_numpy(float); dis = g["discharge_Ah_cum"].to_numpy(float)
        n_anchor_seg = 0
        for a, e in charge_runs(i):
            if u[a:e + 1].max() < CV_V_MIN:
                continue
            if not (0 < i[e] < END_I_MAX_A):
                near.append(dict(segment=s, t_start=t.iloc[a], t_end=t.iloc[e], I_end_A=i[e], q=ah[e] - ah[a - 1]))
                continue
            cv0 = a + int(np.argmax(u[a:e + 1] >= CV_V_MIN))
            tap = cv0 + int(np.argmax(i[cv0:e + 1] < TAPER_I_A))
            q = ah[e] - ah[max(a - 1, 0)]
            # rest before the charge
            r = a - 1
            while r >= 0 and abs(i[r]) <= REST_I_MAX_A:
                r -= 1
            r0 = r + 1
            rest_h = (el[a] - el[r0]) / 3600.0 if r0 < a else 0.0
            rest_gap = bool((np.diff(el[r0:a + 1]) > GAP_DT_S).any()) if r0 < a else False
            # first activity after the CV end (normally the 20 A pulse after 30 min of rest)
            nxt = e + 1 + int(np.argmax(np.abs(i[e + 1:]) > REST_I_MAX_A)) if (np.abs(i[e + 1:]) > REST_I_MAX_A).any() else None
            p = (nxt - 1) if nxt is not None else len(i) - 1
            typ = "A" if (u[a] < ANCHOR_START_V_MAX and q >= ANCHOR_Q_MIN_AH and n_anchor_seg == 0) else "T"
            n_anchor_seg += typ == "A"
            row = dict(segment=s, setpoint=int(g["chamber_temperature_C"].iloc[a]), type=typ,
                       t_charge_start=t.iloc[a], t_cv_start=t.iloc[cv0], t_cv_end=t.iloc[e],
                       charge_Ah=q, cc_I_A=float(np.median(i[a:cv0 + 1])), I_cv_end_A=i[e],
                       cv_Ah=ah[e] - ah[cv0], cv_s=el[e] - el[cv0],
                       cv_Ah_taper=ah[e] - ah[tap], cv_s_taper=el[e] - el[tap],
                       rest_before_h=rest_h, rest_from_segment_start=bool(r0 == 0), rest_has_gap=rest_gap,
                       pack_V_before=u[a - 1] if a > 0 else np.nan, pack_V_charge_start=u[a])
            for c in range(4):
                row[f"cell{c + 1}_V_before"] = V[a - 1, c] if a > 0 else np.nan
            row["pack_V_cv_end"] = u[e]
            for c in range(4):
                row[f"cell{c + 1}_V_cv_end"] = V[e, c]
            row["spread_V_cv_end"] = V[e].max() - V[e].min()
            row["temp_mean_cv_end_C"] = T[e]
            row["t_prepulse"] = t.iloc[p]
            row["prepulse_offset_min"] = (el[p] - el[e]) / 60.0
            row["pulse_follows"] = bool(nxt is not None and i[nxt] < PULSE_I_A)
            row["pack_V_prepulse"] = u[p]
            for c in range(4):
                row[f"cell{c + 1}_V_prepulse"] = V[p, c]
            row["spread_V_prepulse"] = V[p].max() - V[p].min()
            row["top_cell_prepulse"] = D.CELLS[int(np.argmax(V[p]))][:5]
            row["temp_mean_prepulse_C"] = T[p]
            row.update(chg_cum_start=chg[a - 1] if a > 0 else chg[a], dis_cum_start=dis[a - 1] if a > 0 else dis[a],
                       chg_cum_end=chg[e], dis_cum_end=dis[e], _seg_end_idx=e)
            rows.append(row)
    ev = pd.DataFrame(rows).sort_values("t_cv_end").reset_index(drop=True)
    ev.insert(0, "event_id", [f"E{j + 1:02d}" for j in range(len(ev))])
    # anchor index k = index of the last checkup date before the CV end
    ck = D.CK_DATES.to_numpy()
    ev.insert(4, "anchor_k", [int((ck < np.datetime64(t)).sum()) - 1 if ty == "A" else -1
                              for t, ty in zip(ev["t_cv_end"], ev["type"])])
    # recording gap (dt > 60 s) between this CV end and the next one
    S = D.segments()
    nxt_id, same, gap, maxdt, segb = [], [], [], [], []
    for j, r in ev.iterrows():
        if j + 1 == len(ev):
            nxt_id.append(""); same.append(False); gap.append(np.nan); maxdt.append(np.nan); segb.append(np.nan)
            continue
        n = ev.iloc[j + 1]
        nxt_id.append(n["event_id"])
        g = S[r["segment"]]; el = g["elapsed_s"].to_numpy(float)
        if n["segment"] == r["segment"]:
            e2 = int(n["_seg_end_idx"])
            d = np.diff(el[r["_seg_end_idx"]:e2 + 1])
            same.append(True); maxdt.append(d.max()); gap.append(bool((d > GAP_DT_S).any())); segb.append(np.nan)
        else:
            g2 = S[n["segment"]]; el2 = g2["elapsed_s"].to_numpy(float)
            d1 = np.diff(el[r["_seg_end_idx"]:]); d2 = np.diff(el2[:int(n["_seg_end_idx"]) + 1])
            b = el2[0] - el[-1]
            same.append(False); maxdt.append(max(d1.max(initial=0), d2.max(initial=0), b)); gap.append(True)
            segb.append(b / 3600.0)
    ev["next_event_id"] = nxt_id
    ev["next_in_same_segment"] = same
    ev["gap_dt60_before_next"] = gap
    ev["max_dt_s_before_next"] = maxdt
    ev["segment_boundary_h_before_next"] = segb
    ev = ev.drop(columns="_seg_end_idx")
    return ev, pd.DataFrame(near)


if __name__ == "__main__":
    ev, near = catalogue()
    out = os.path.join(D.ST, "wp0", "events.csv")
    ev.to_csv(out, index=False, float_format="%.6g")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(ev[["event_id", "segment", "setpoint", "type", "anchor_k", "t_cv_end", "charge_Ah", "cv_Ah", "cv_s",
              "I_cv_end_A", "rest_before_h", "pack_V_prepulse", "spread_V_prepulse", "prepulse_offset_min",
              "pulse_follows", "gap_dt60_before_next", "max_dt_s_before_next"]].to_string())
    print("excluded charges reaching 13.95 V without 0 < I_end < 6 A:\n", near.to_string())
