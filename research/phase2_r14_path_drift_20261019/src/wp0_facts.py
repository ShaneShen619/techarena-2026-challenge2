"""WP0.4: numbers for wp0/FACTS.md -> wp0/facts.json. Uses wp0/anchor_blocks.csv and cache/wp0_programs.csv
(written by wp0_blocks.py). No Ah balance between CV ends is computed (WP0 rule)."""
import json, os
import numpy as np
import pandas as pd
import data14 as D

ST = D.ST
VARIANTS = ["main", "band_narrow", "windows_minus3", "windows_plus3", "dvdq_peak", "ir_corrected"]


def r(x, n=4):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def main():
    ab = pd.read_csv(os.path.join(ST, "wp0", "anchor_blocks.csv"))
    pr = pd.read_csv(os.path.join(ST, "cache", "wp0_programs.csv"))
    segs = D.segments()
    ck, names = D.checkup_dates()
    f = {}

    # F1: top rest voltage after the anchor vs after the next top-up (V30 = pre-pulse rest sample)
    rows = []
    for _, a in ab.iterrows():
        dv = {c: 1000 * (a[f"T1_V30_{c}"] - a[f"A_V30_{c}"]) for c in D.CELLS}
        rows.append({"anchor": int(a["anchor"]), "setpoint": int(a["setpoint_C"]),
                     "dV_pack_mV": r(1000 * (a["T1_V30_pack_V"] - a["A_V30_pack_V"]), 1),
                     **{f"dV_{c}_mV": r(v, 1) for c, v in dv.items()},
                     "dV_cell_mean_mV": r(np.mean(list(dv.values())), 2)})
    t = pd.DataFrame(rows)
    t25 = t[t["setpoint"] == 25]
    f["F1_top_rest_voltage"] = {"per_anchor": rows,
                                "cell_mean_mV_25C_range": [r(t25["dV_cell_mean_mV"].min(), 2), r(t25["dV_cell_mean_mV"].max(), 2)],
                                "pack_mV_25C_range": [r(t25["dV_pack_mV"].min(), 1), r(t25["dV_pack_mV"].max(), 1)],
                                "median_per_cell_mV_25C": {c: r(t25[f"dV_{c}_mV"].median(), 1) for c in D.CELLS}}

    # F2: first-program offset o_k = D1 - D2 (raw), per variant and A3; D2 - D3 where a third program exists
    out = []
    for _, a in ab.iterrows():
        p = pr[pr["segment"] == a["segment"]].reset_index(drop=True)
        i0 = int(np.where(p["is_anchor"])[0][0])
        row = {"anchor": int(a["anchor"]), "segment": int(a["segment"]), "n_programs_in_segment_from_anchor": len(p) - i0}
        for v in ["A3", "dvdq"] + VARIANTS:
            row[f"o_{v}"] = r(p[v].iloc[i0] - p[v].iloc[i0 + 1]) if len(p) > i0 + 1 else None
            row[f"d23_{v}"] = r(p[v].iloc[i0 + 1] - p[v].iloc[i0 + 2]) if len(p) > i0 + 2 else None
        out.append(row)
    o = pd.DataFrame(out)
    o25 = o[o["anchor"] >= 1]
    # 45 degC within-segment program-to-program change (no anchor in these segments), for scale
    d45 = []
    for s, p in pr.groupby("segment"):
        if segs[s]["chamber_temperature_C"].iloc[0] == 45 and not p["is_anchor"].any():
            d45 += list(-np.diff(p["A3"].to_numpy()))
    f["F2_first_program_offset"] = {
        "per_anchor": out,
        "median_o_25C_by_variant": {v: r(o25[f"o_{v}"].median()) for v in ["A3", "dvdq"] + VARIANTS},
        "range_o_A3_25C": [r(o25["o_A3"].min()), r(o25["o_A3"].max())],
        "d23_A3_anchors_5_6": [r(x) for x in o25["d23_A3"].dropna()],
        "program_to_program_A3_45C_no_anchor": {"median": r(np.median(d45)), "min": r(min(d45)), "max": r(max(d45)), "n": len(d45)},
        "note": "raw D1 - D2; the 2026-10-15 figure (+0.39-0.46 Ah) and round 6 3c (0.41-0.56 Ah) are trend-adjusted"}

    # F3: set points and measured temperatures of the anchors
    f["F3_anchor_temperatures"] = [{"anchor": int(a["anchor"]), "segment": int(a["segment"]), "setpoint_C": int(a["setpoint_C"]),
                                    "T_mean_cv_end_C": r(a["A_T_mean_cv_end_C"], 2), "T1_T_mean_cv_end_C": r(a["T1_T_mean_cv_end_C"], 2)}
                                   for _, a in ab.iterrows()]

    # F5: counters book the 20 A pulse as charge (counter change vs integrated current during each pulse)
    pul = []
    for s, g in segs.items():
        i = g["current_A"].to_numpy(float)
        _, ah = D.mt._integrated_ah(g)
        on = i < D.mt.PULSE_I_A
        starts = np.where(on & ~np.r_[False, on[:-1]])[0]
        for p0 in starts:
            p1 = p0
            while p1 + 1 < len(i) and on[p1 + 1]:
                p1 += 1
            pul.append({"segment": s, "int_Ah": ah[p1] - ah[p0 - 1],
                        "d_charge_cum": g["charge_Ah_cum"].iloc[p1] - g["charge_Ah_cum"].iloc[p0 - 1],
                        "d_discharge_cum": g["discharge_Ah_cum"].iloc[p1] - g["discharge_Ah_cum"].iloc[p0 - 1]})
    pu = pd.DataFrame(pul)
    f["F5_pulse_booking"] = {"n_pulses": len(pu), "int_Ah_median": r(pu["int_Ah"].median()),
                             "d_charge_cum_median": r(pu["d_charge_cum"].median()),
                             "d_discharge_cum_median": r(pu["d_discharge_cum"].median()),
                             "d_charge_cum_range": [r(pu["d_charge_cum"].min()), r(pu["d_charge_cum"].max())]}

    # F6: pack voltage when entering each checkup (last sample before the checkup date) and anchor start states
    ent = []
    for k in range(1, len(ck)):
        # the segment that precedes the checkup gap: latest segment starting before the checkup date; if the next
        # segment number is missing (segment 3 before CK2), the entering state is not visible
        before = [(s, g) for s, g in segs.items() if g["timestamp"].iloc[0] < ck[k]]
        s, g = before[-1]
        if s + 1 not in segs and any(x > s + 1 for x in segs):
            ent.append({"checkup": names[k], "last_segment": None, "note": f"segment {s + 1} missing; not visible"})
            continue
        ent.append({"checkup": names[k], "last_segment": s, "t_last": str(g["timestamp"].iloc[-1]),
                    "pack_V_last": r(g["pack_voltage_V"].iloc[-1], 3), "I_last_A": r(g["current_A"].iloc[-1], 3),
                    "days_to_checkup": r((ck[k] - g["timestamp"].iloc[-1]).total_seconds() / 86400, 2)})
    f["F6_entering_checkup"] = ent
    st = []
    for _, a in ab.iterrows():
        g = segs[int(a["segment"])]
        i = g["current_A"].to_numpy(float); u = g["pack_voltage_V"].to_numpy(float)
        tt = g["elapsed_s"].to_numpy(float)
        s0 = int(a["A_charge_start_row"])
        rest = np.where(np.abs(i[:s0]) <= D.mt.CHARGE_I_MIN_A)[0]
        h = (tt[s0 - 1] - tt[0]) / 3600.0
        last_h = tt[s0 - 1] - 3600.0
        j = int(np.searchsorted(tt, last_h))
        slope = 1000 * (u[s0 - 1] - u[j]) / ((tt[s0 - 1] - tt[j]) / 3600.0) if s0 - 1 > j else np.nan
        st.append({"anchor": int(a["anchor"]), "rest_from_segment_start_h": r(h, 2), "pack_V_start": r(u[s0 - 1], 3),
                   "slope_last_hour_mV_per_h": r(slope, 1), "all_rest_before_charge": bool(len(rest) == s0)})
    f["F7_anchor_start"] = st
    # F9: recording gaps inside segments and the counter change across each (a counter check, not an Ah balance)
    gp = []
    for s, g in segs.items():
        tt = g["elapsed_s"].to_numpy(float)
        for j in np.where(np.diff(tt) > D.GAP_S)[0]:
            gp.append({"segment": s, "t_before": str(g["timestamp"].iloc[j]), "t_after": str(g["timestamp"].iloc[j + 1]),
                       "dt_s": float(tt[j + 1] - tt[j]), "I_before_A": float(g["current_A"].iloc[j]),
                       "I_after_A": float(g["current_A"].iloc[j + 1]),
                       "d_charge_cum_Ah": r(g["charge_Ah_cum"].iloc[j + 1] - g["charge_Ah_cum"].iloc[j]),
                       "d_discharge_cum_Ah": r(g["discharge_Ah_cum"].iloc[j + 1] - g["discharge_Ah_cum"].iloc[j]),
                       "first_sample_after_Ah": r(g["current_A"].iloc[j + 1] * 10.0 / 3600.0)})
    f["F9_recording_gaps"] = gp
    # V30 timing: offset of the pre-pulse rest sample used for V30
    offs = []
    for _, a in ab.iterrows():
        g = segs[int(a["segment"])]
        tt = g["elapsed_s"].to_numpy(float); i = g["current_A"].to_numpy(float)
        for tag in ("A", "T1", "T2"):
            if np.isfinite(a[f"{tag}_row"]):
                e = int(a[f"{tag}_row"])
                j = int(np.searchsorted(tt, tt[e] + D.V30_S, side="right")) - 1
                busy = np.where(np.abs(i[e + 1:j + 1]) > D.mt.CHARGE_I_MIN_A)[0]
                j = e + busy[0] if len(busy) else j
                offs.append(tt[j] - tt[e])
    f["V30_offset_s"] = {"min": min(offs), "max": max(offs), "n": len(offs)}
    f["F8_topup_charge_start_pack_V"] ={"min": r(ab["T1_pack_V_before_charge"].min(), 3), "max": r(ab["T1_pack_V_before_charge"].max(), 3)}
    json.dump(f, open(os.path.join(ST, "wp0", "facts.json"), "w"), indent=1)
    print(json.dumps(f, indent=1))


if __name__ == "__main__":
    main()
