"""WP0.5: numbers behind wp0/FACTS.md (switch table, checkup windows, integration check, fact re-verification).

Descriptive only: no Ah balance between CV ends, no step location and no epsilon-related estimate is computed.
Step-related facts are cited from the copied source outputs, not recomputed."""
import json, os, sys
import numpy as np
import pandas as pd
import data12 as D

OUT = os.path.join(D.ST, "wp0")
PULSE_I_A = -15.0
BAND_A = (-12.5, -8.0)
RECHARGE_AH = 2.0
SWITCHES = [(4, 5), (6, 7), (8, 9), (10, 11), (12, 13)]
CK_SEGS = {1: (1, 2), 2: (2, 4), 3: (5, 6), 4: (7, 8), 5: (9, 10), 6: (11, 12), 7: (13, 14)}


def r(x, n=4):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


def boundary(S, s0, s1):
    a, b = S[s0].iloc[-1], S[s1].iloc[0]
    return dict(seg_before=s0, seg_after=s1, t_last=a["timestamp"], t_first=b["timestamp"],
                idle_h=(b["timestamp"] - a["timestamp"]).total_seconds() / 3600.0,
                elapsed_gap_h=(b["elapsed_s"] - a["elapsed_s"]) / 3600.0,
                d_charge_cum_Ah=b["charge_Ah_cum"] - a["charge_Ah_cum"],
                d_discharge_cum_Ah=b["discharge_Ah_cum"] - a["discharge_Ah_cum"],
                setpoint_before=int(a["chamber_temperature_C"]), setpoint_after=int(b["chamber_temperature_C"]),
                temp_mean_before_C=a["temp_mean_C"], temp_mean_after_C=b["temp_mean_C"],
                I_last_A=a["current_A"], I_first_A=b["current_A"],
                pack_V_last=a["pack_voltage_V"], pack_V_first=b["pack_voltage_V"])


def rest_stats(g, a):
    """Rest (|I| <= 0.5 A) right before sample a: duration, first/last pack V, slopes, spreads, temperatures."""
    el = g["elapsed_s"].to_numpy(float); i = g["current_A"].to_numpy(float)
    u = g["pack_voltage_V"].to_numpy(float); V = g[D.CELLS].to_numpy(float); T = g["temp_mean_C"].to_numpy(float)
    k = a - 1
    while k >= 0 and abs(i[k]) <= 0.5:
        k -= 1
    idx = np.arange(k + 1, a)
    h = (el[idx] - el[idx[0]]) / 3600.0
    last30 = idx[el[idx] >= el[a - 1] - 1800.0]
    h30 = (el[last30] - el[last30[0]]) / 3600.0
    return dict(rest_h=(el[a - 1] - el[idx[0]]) / 3600.0, from_segment_start=bool(idx[0] == 0),
                pack_V_first=u[idx[0]], pack_V_last=u[a - 1],
                slope_last30_mV_h=1000.0 * np.polyfit(h30, u[last30], 1)[0],
                slope_all_mV_h=1000.0 * np.polyfit(h, u[idx], 1)[0],
                spread_first_V=V[idx[0]].max() - V[idx[0]].min(), spread_last_V=V[a - 1].max() - V[a - 1].min(),
                temp_first_C=T[idx[0]], temp_last_C=T[a - 1])


def pulses_and_programs(S, ev):
    """Per CV end: rest, pulse (integrated vs counters), deep-program depth below the CV end and band coverage."""
    rows = []
    for _, e in ev.iterrows():
        g = S[e["segment"]]; i, ah = D.integrated_ah(g)
        el = g["elapsed_s"].to_numpy(float); chg = g["charge_Ah_cum"].to_numpy(float)
        dis = g["discharge_Ah_cum"].to_numpy(float)
        k = int(np.where(g["timestamp"] == e["t_cv_end"])[0][-1])
        k = k if i[k] > 0.5 else k - 1
        while i[k] <= 0.5:
            k -= 1
        p0 = k + 1 + int(np.argmax(i[k + 1:] < PULSE_I_A))
        p1 = p0
        while p1 + 1 < len(i) and i[p1 + 1] < PULSE_I_A:
            p1 += 1
        depth = ah[k] - ah[k:]
        peak = np.maximum.accumulate(depth)
        back = np.where(peak - depth > RECHARGE_AH)[0]
        d = depth[:back[0]] if len(back) else depth
        cur = i[k:k + len(d)]
        band = (cur > BAND_A[0]) & (cur < BAND_A[1])
        rows.append(dict(event_id=e["event_id"], segment=e["segment"], setpoint=e["setpoint"], type=e["type"],
                         rest_after_cv_min=(el[p0] - el[k]) / 60.0, pulse_min=(el[p1] - el[p0 - 1]) / 60.0,
                         pulse_I_median_A=float(np.median(i[p0:p1 + 1])),
                         pulse_Ah_integrated=ah[p1] - ah[p0 - 1],
                         pulse_d_charge_cum_Ah=chg[min(p1 + 1, len(i) - 1)] - chg[p0 - 1],
                         pulse_d_discharge_cum_Ah=dis[min(p1 + 1, len(i) - 1)] - dis[p0 - 1],
                         program_max_depth_Ah=d.max(), program_max_depth_after_pulse_Ah=d.max() - (ah[k] - ah[p1]),
                         band_samples=int(band.sum()),
                         band_depth_from_Ah=float(d[band].min()) if band.any() else np.nan,
                         band_depth_to_Ah=float(d[band].max()) if band.any() else np.nan))
    return pd.DataFrame(rows)


def sign_booking(S):
    """Per segment: integrated charge (I > 0) and discharge (I < 0, pulses separately) vs the two counters."""
    rows = []
    for s, g in S.items():
        i, ah = D.integrated_ah(g)
        t = g["elapsed_s"].to_numpy(float); dt = np.diff(t, prepend=t[0]); dt[(dt > D.MAX_DT_S) | (dt <= 0)] = 0.0
        q = i * dt / 3600.0
        rows.append(dict(segment=s, int_pos_Ah=q[i > 0].sum(), int_neg_nonpulse_Ah=-q[(i < 0) & (i >= PULSE_I_A)].sum(),
                         int_pulse_Ah=-q[i < PULSE_I_A].sum(),
                         d_charge_cum_Ah=g["charge_Ah_cum"].iloc[-1] - g["charge_Ah_cum"].iloc[0],
                         d_discharge_cum_Ah=g["discharge_Ah_cum"].iloc[-1] - g["discharge_Ah_cum"].iloc[0],
                         n_dt_gt_600s=int((np.diff(t) > D.MAX_DT_S).sum())))
    b = pd.DataFrame(rows)
    b["chg_counter_minus_pos_minus_pulse_Ah"] = b["d_charge_cum_Ah"] - b["int_pos_Ah"] - b["int_pulse_Ah"]
    b["dis_counter_minus_neg_nonpulse_Ah"] = b["d_discharge_cum_Ah"] - b["int_neg_nonpulse_Ah"]
    return b


def in_segment_gaps(S):
    rows = []
    for s, g in S.items():
        el = g["elapsed_s"].to_numpy(float); d = np.diff(el)
        for j in np.where(d > 60)[0]:
            rows.append(dict(segment=s, t_before=g["timestamp"].iloc[j], t_after=g["timestamp"].iloc[j + 1],
                             dt_s=d[j], I_before_A=g["current_A"].iloc[j], I_after_A=g["current_A"].iloc[j + 1],
                             d_charge_cum_Ah=g["charge_Ah_cum"].iloc[j + 1] - g["charge_Ah_cum"].iloc[j],
                             d_discharge_cum_Ah=g["discharge_Ah_cum"].iloc[j + 1] - g["discharge_Ah_cum"].iloc[j]))
    return pd.DataFrame(rows)


def main():
    S = D.segments()
    ev = pd.read_csv(os.path.join(OUT, "events.csv"), parse_dates=["t_charge_start", "t_cv_start", "t_cv_end", "t_prepulse"])
    facts = {}
    # CK0 curve
    c = D.ck0_curve()
    facts["ck0"] = dict(t_start=str(c["timestamp"].iloc[0]), t_end=str(c["timestamp"].iloc[-1]),
                        I_median_A=r(c["current_A"].median(), 3), I_mean_A=r(c["current_A"].mean(), 4),
                        V_start=r(c["voltage_V"].iloc[0], 3), Ah_end=r(c["discharged_Ah"].iloc[-1], 3),
                        Ah_at_11p2V=r(float(np.interp(11.2, c["voltage_V"].to_numpy()[::-1], c["discharged_Ah"].to_numpy()[::-1])), 3),
                        V_end=r(c["voltage_V"].iloc[-1], 3),
                        cells_end=[r(c[x].iloc[-1], 3) for x in D.CELLS],
                        cells_start=[r(c[x].iloc[0], 3) for x in D.CELLS],
                        duration_h=r((c["timestamp"].iloc[-1] - c["timestamp"].iloc[0]).total_seconds() / 3600.0, 3))
    # anchors
    sys.path.insert(0, D.PKG)
    from my_model import model_template as mt
    A = ev[ev["type"] == "A"].sort_values("anchor_k")
    rows = []
    for _, e in A.iterrows():
        g = S[e["segment"]]
        a = int(np.where(g["timestamp"] == e["t_charge_start"])[0][0])
        rs = rest_stats(g, a)
        fc = mt._first_full_charge(g.reset_index(drop=True))
        q_counter = e["chg_cum_end"] - e["chg_cum_start"]
        rows.append(dict(anchor_k=int(e["anchor_k"]), segment=int(e["segment"]), setpoint=int(e["setpoint"]),
                         t_segment_start=g["timestamp"].iloc[0], t_charge_start=e["t_charge_start"], t_cv_end=e["t_cv_end"],
                         Q_pkg_first_full_charge=fc["q"], Q_integrated_events=e["charge_Ah"], Q_counter=q_counter,
                         counter_minus_pkg_Ah=q_counter - fc["q"],
                         d_discharge_cum_during_charge_Ah=e["dis_cum_end"] - e["dis_cum_start"],
                         cv_Ah=e["cv_Ah"], cv_s=e["cv_s"], cv_Ah_taper=e["cv_Ah_taper"], cv_s_taper=e["cv_s_taper"],
                         I_cv_end_A=e["I_cv_end_A"], pack_V_cv_end=e["pack_V_cv_end"], spread_V_cv_end=e["spread_V_cv_end"],
                         cell3_V_cv_end=e["cell3_V_cv_end"], pack_V_prepulse=e["pack_V_prepulse"],
                         spread_V_prepulse=e["spread_V_prepulse"], cell3_V_prepulse=e["cell3_V_prepulse"],
                         top_cell_prepulse=e["top_cell_prepulse"], temp_cv_end_C=e["temp_mean_cv_end_C"],
                         **{f"rest_{k}": v for k, v in rs.items()}))
    anc = pd.DataFrame(rows)
    anc.to_csv(os.path.join(OUT, "integration_check.csv"), index=False, float_format="%.6g")
    # switches and checkup windows
    sw = pd.DataFrame([boundary(S, a, b) for a, b in SWITCHES])
    sw.to_csv(os.path.join(OUT, "switches.csv"), index=False, float_format="%.6g")
    cw = []
    c_end = c["timestamp"].iloc[-1]; s1 = S[1].iloc[0]
    cw.append(dict(checkup="CK0", ck_date=str(D.CK_DATES[0].date()), seg_before="CK0 C/20 curve", seg_after=1,
                   t_last=c_end, t_first=s1["timestamp"], window_days=(s1["timestamp"] - c_end).total_seconds() / 86400.0,
                   window_known=True, d_charge_cum_Ah=np.nan, d_discharge_cum_Ah=np.nan,
                   temp_mean_after_C=s1["temp_mean_C"], pack_V_first=s1["pack_voltage_V"],
                   note="C/20 end to first operating sample"))
    for k, (s0, s_1) in CK_SEGS.items():
        b = boundary(S, s0, s_1)
        known = k != 2
        cw.append(dict(checkup=f"CK{k}", ck_date=str(D.CK_DATES[k].date()), seg_before=s0, seg_after=s_1,
                       t_last=b["t_last"], t_first=b["t_first"],
                       window_days=b["idle_h"] / 24.0 if known else (b["t_first"] - D.CK_DATES[k]).total_seconds() / 86400.0,
                       window_known=known, d_charge_cum_Ah=b["d_charge_cum_Ah"], d_discharge_cum_Ah=b["d_discharge_cum_Ah"],
                       temp_mean_after_C=b["temp_mean_after_C"], pack_V_first=b["pack_V_first"],
                       note="" if known else "segment 3 (45 degC) missing; value = CK2 date 00:00 to segment 4 start "
                                            "(upper bound); counters include segment 3's throughput"))
    cw = pd.DataFrame(cw)
    cw.to_csv(os.path.join(OUT, "checkup_windows.csv"), index=False, float_format="%.6g")
    pp = pulses_and_programs(S, ev)
    pp.to_csv(os.path.join(OUT, "pulses_programs.csv"), index=False, float_format="%.6g")
    sb = sign_booking(S)
    sb.to_csv(os.path.join(OUT, "counter_booking_by_segment.csv"), index=False, float_format="%.6g")
    gaps = in_segment_gaps(S)
    gaps.to_csv(os.path.join(OUT, "in_segment_gaps.csv"), index=False, float_format="%.6g")
    # month structure
    blocks = ev.groupby("segment").agg(setpoint=("setpoint", "first"), n_cv=("event_id", "size"),
                                       n_anchor=("type", lambda x: int((x == "A").sum())))
    same = ev[ev["next_in_same_segment"]].copy()
    nxt = ev.set_index("event_id")["t_cv_end"]
    same["block_h"] = [(nxt[n] - t).total_seconds() / 3600.0 for n, t in zip(same["next_event_id"], same["t_cv_end"])]
    facts["structure"] = dict(blocks_per_segment={int(s): dict(setpoint=int(b.setpoint), n_cv=int(b.n_cv), n_anchor=int(b.n_anchor))
                                                  for s, b in blocks.iterrows()},
                              block_h_min=r(same["block_h"].min(), 3), block_h_median=r(same["block_h"].median(), 3),
                              block_h_max=r(same["block_h"].max(), 3),
                              block_h_without_gap={"min": r(same.loc[~same["gap_dt60_before_next"].astype(bool), "block_h"].min(), 3),
                                                   "max": r(same.loc[~same["gap_dt60_before_next"].astype(bool), "block_h"].max(), 3)},
                              cc_I_A=[r(ev["cc_I_A"].min(), 3), r(ev["cc_I_A"].max(), 3)],
                              I_cv_end_A=[r(ev["I_cv_end_A"].min(), 3), r(ev["I_cv_end_A"].max(), 3)],
                              rest_after_cv_min=[r(pp["rest_after_cv_min"].min(), 3), r(pp["rest_after_cv_min"].max(), 3)],
                              pulse_min=[r(pp["pulse_min"].min(), 3), r(pp["pulse_min"].max(), 3)],
                              pulse_I_A=[r(pp["pulse_I_median_A"].min(), 3), r(pp["pulse_I_median_A"].max(), 3)],
                              pulse_Ah=[r(pp["pulse_Ah_integrated"].min(), 3), r(pp["pulse_Ah_integrated"].max(), 3)],
                              program_max_depth_Ah=[r(pp["program_max_depth_Ah"].min(), 3), r(pp["program_max_depth_Ah"].median(), 3),
                                                    r(pp["program_max_depth_Ah"].max(), 3)],
                              program_depth_after_pulse_Ah=[r(pp["program_max_depth_after_pulse_Ah"].min(), 3),
                                                            r(pp["program_max_depth_after_pulse_Ah"].median(), 3),
                                                            r(pp["program_max_depth_after_pulse_Ah"].max(), 3)],
                              band_depth_from_to_Ah=[r(pp["band_depth_from_Ah"].median(), 2), r(pp["band_depth_to_Ah"].median(), 2)],
                              band_samples_min=int(pp["band_samples"].min()),
                              all_cv_followed_by_pulse=bool(ev["pulse_follows"].all()),
                              prepulse_offset_min=[r(ev["prepulse_offset_min"].min(), 3), r(ev["prepulse_offset_min"].max(), 3)])
    facts["pulse_booking"] = dict(n=len(pp), integrated_Ah=[r(pp["pulse_Ah_integrated"].min(), 4), r(pp["pulse_Ah_integrated"].max(), 4)],
                                  d_charge_cum_Ah=[r(pp["pulse_d_charge_cum_Ah"].min(), 4), r(pp["pulse_d_charge_cum_Ah"].max(), 4)],
                                  d_discharge_cum_Ah=[r(pp["pulse_d_discharge_cum_Ah"].min(), 4), r(pp["pulse_d_discharge_cum_Ah"].max(), 4)])
    # top rest voltage per cell: anchor vs the next top-up in the same 25 degC segment (voltages only)
    t25 = []
    for _, e in A[A["setpoint"] == 25].iterrows():
        n = ev[ev["event_id"] == e["next_event_id"]].iloc[0]
        if n["segment"] == e["segment"]:
            t25.append(dict(anchor_k=int(e["anchor_k"]), dV_cell_mean_mV=1000.0 * (e["pack_V_prepulse"] - n["pack_V_prepulse"]) / 4.0,
                            dV_pack_mV=1000.0 * (e["pack_V_prepulse"] - n["pack_V_prepulse"])))
    facts["top_rest_anchor_minus_next_topup"] = t25
    facts["rebound_first_program_offset_cited"] = dict(
        value="0.39-0.46 Ah deeper on all six step-detection methods; gone by the next program",
        source="commit 8429b53 message (phase2_rebound_diagnosis_20261015); package README: 0.4-0.46 Ah",
        note="definition of the reference not stored in the copied outputs; not recomputed (WP0 forbids step locations)")
    facts["v2_switch_step_jump_cited"] = dict(
        value="+0.14 to +0.22 Ah at each 25->45 degC switch (CK1->CK2 month +0.60)",
        source="sources/base/v2_phase_matched/FINAL_REPORT.md section 1", note="not recomputed (WP0 rule)")
    json.dump(facts, open(os.path.join(OUT, "facts.json"), "w"), indent=1, default=str)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(json.dumps(facts, indent=1, default=str))
    print(anc.T.to_string()); print(sw.T.to_string()); print(cw.to_string()); print(sb.to_string()); print(gaps.to_string())


if __name__ == "__main__":
    main()
