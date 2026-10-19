"""WP0: catalogue of every full CCCV charge (anchors and top-ups) and the numbers behind wp0/FACTS.md.

No tail model is fitted here (prompt WP0). Usage:
    python3 -B wp0_catalogue.py <study_dir> <package_data_dir>
Writes wp0/cv_catalogue.csv and wp0/facts.json.
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

ST, DATA = sys.argv[1], sys.argv[2]
CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]
V_CV, I_CV = 13.95, 19.9            # CV start: first sample with pack >= 13.95 V and I < 19.9 A (prompt WP0.3)
I_ON, I_OFF = 15.0, 1.0             # charge step: starts when I > 15 A, ends at the first sample with I < 1 A
ANCHOR_SEGS = (1, 2, 4, 6, 8, 10, 12, 14)   # first full charge after CK0..CK7 (round 8/11 convention)


def charges(d):
    """Yield (i0, cv0, iend) for each full CCCV charge: i0 first charge row, cv0 CV start row, iend CV end row."""
    I = d.current_A.to_numpy(float); V = d.pack_voltage_V.to_numpy(float)
    on = np.flatnonzero((I[1:] > I_ON) & (I[:-1] <= I_ON)) + 1
    for i0 in on:
        rel = np.flatnonzero(I[i0:] < I_OFF)
        if not len(rel):
            continue
        i1 = i0 + int(rel[0])                       # first row after the charge step
        m = (V[i0:i1] >= V_CV) & (I[i0:i1] < I_CV)
        if not m.any():
            continue                                 # never reached CV: not a full charge
        yield i0, i0 + int(np.argmax(m)), i1 - 1


rows, enter = [], []
for f in sorted(glob.glob(os.path.join(DATA, "operation", "*.csv.gz"))):
    seg = int(os.path.basename(f).split("_")[1])
    d = pd.read_csv(f)
    t = d.elapsed_s.to_numpy(float); I = d.current_A.to_numpy(float); V = d.pack_voltage_V.to_numpy(float)
    net = (d.charge_Ah_cum - d.discharge_Ah_cum).to_numpy(float)
    ends = [ie for _, _, ie in charges(d)]
    rest = np.flatnonzero(np.abs(I) < 0.5)
    enter.append(dict(segment=seg, setpoint_C=int(d.chamber_temperature_C.iloc[0]), first_ts=d.timestamp.iloc[0],
                      last_ts=d.timestamp.iloc[-1], V_first=float(V[0]), V_last=float(V[-1]), I_last=float(I[-1]),
                      **{f"{c[:5]}_last": float(d[c].iloc[-1]) for c in CELLS},
                      Ah_below_last_cv_end=float(net[ends[-1]] - net[-1]) if ends else np.nan,
                      last_rest_ts=d.timestamp.iloc[rest[-1]] if len(rest) else "", last_rest_V=float(V[rest[-1]]) if len(rest) else np.nan))
    first_in_seg = True
    for i0, cv0, ie in charges(d):
        tcv = t[cv0:ie + 1] - t[cv0]; icv = I[cv0:ie + 1]
        # rest after the CV end, up to the pulse: last |I| < 0.5 A sample before the first sample with I < -15 A
        after = np.flatnonzero(I[ie + 1:] < -15.0)
        ip = ie + 1 + int(after[0]) if len(after) else None        # first pulse row (step-start duplicate)
        j30 = ip - 1 if ip is not None else None
        rest_ok = ip is not None and bool(np.all(np.abs(I[ie + 1:ip]) < 0.5))
        gap_ok = bool(np.all(np.diff(t[i0:ie + 1]) <= 600))
        end_cells = d[CELLS].iloc[ie].to_numpy(float)
        r30 = d[CELLS].iloc[j30].to_numpy(float) if j30 is not None else np.full(4, np.nan)
        rows.append(dict(
            segment=seg, setpoint_C=int(d.chamber_temperature_C.iloc[i0]),
            type="A" if (seg in ANCHOR_SEGS and first_in_seg) else "T",
            t_chg_start=d.timestamp.iloc[i0], chg_start_pack_V=float(V[i0 - 1]),
            chg_Ah_counter=float(d.charge_Ah_cum.iloc[ie] - d.charge_Ah_cum.iloc[i0 - 1]),
            I_cc_median=float(np.median(I[i0:cv0])) if cv0 > i0 else np.nan,
            t_cv_start=d.timestamp.iloc[cv0], t_cv_end=d.timestamp.iloc[ie],
            elapsed_cv_start_s=float(t[cv0]), elapsed_cv_end_s=float(t[ie]),
            n_cv=int(ie - cv0 + 1), cv_s=float(tcv[-1]),
            cv_Ah=float(np.trapezoid(icv, tcv) / 3600),
            cv_Ah_counter=float(d.charge_Ah_cum.iloc[ie] - d.charge_Ah_cum.iloc[cv0]),
            I_cv_start=float(icv[0]), I_cv_end=float(icv[-1]),
            V_cv_mean=float(np.mean(V[cv0:ie + 1])), V_cv_min=float(np.min(V[cv0:ie + 1])), V_cv_max=float(np.max(V[cv0:ie + 1])),
            V_pack_end=float(V[ie]), **{f"{c[:5]}_end": float(v) for c, v in zip(CELLS, end_cells)},
            top_cell_end=CELLS[int(np.argmax(end_cells))][:5],
            t_30=d.timestamp.iloc[j30] if j30 is not None else "", lag_30_s=float(t[j30] - t[ie]) if j30 is not None else np.nan,
            rest_ok=rest_ok, V_pack_30=float(V[j30]) if j30 is not None else np.nan,
            **{f"{c[:5]}_30": float(v) for c, v in zip(CELLS, r30)},
            top_cell_30=CELLS[int(np.argmax(r30))][:5] if j30 is not None else "",
            V_pulse_first=float(V[ip + 1]) if ip is not None else np.nan, I_pulse=float(I[ip + 1]) if ip is not None else np.nan,
            T_cv_end=float(d.temp_mean_C.iloc[ie]), T_cv_mean=float(np.mean(d.temp_mean_C.iloc[cv0:ie + 1])),
            max_dt_s_charge=float(np.max(np.diff(t[i0:ie + 1]))), no_gap=gap_ok,
            # descriptive (non-model) CV-window shape: current at 1/3 and 2/3 of the CV time, and 60 s before the end
            I_at_third=float(np.interp(tcv[-1] / 3, tcv, icv)), I_at_two_thirds=float(np.interp(2 * tcv[-1] / 3, tcv, icv)),
            I_60s_before_end=float(np.interp(tcv[-1] - 60, tcv, icv))))
        first_in_seg = False

cat = pd.DataFrame(rows)
cat.insert(0, "event_id", [f"E{i:02d}" for i in range(len(cat))])
anc = cat.index[cat.type == "A"]
cat.insert(4, "anchor", "")
cat.loc[anc, "anchor"] = [str(ANCHOR_SEGS.index(s)) for s in cat.loc[anc, "segment"]]

# pulse resistance from round 8 (events table, unit rows: pack_mean and per cell), matched on the CV-end timestamp
r8 = pd.read_csv(os.path.join(ST, "sources", "r8_table_events.csv"))
piv = r8.pivot_table(index="t_cv_end", columns="unit", values="R_pulse_mOhm", aggfunc="first")
cat["R_pulse_mOhm_r8_cellmean"] = cat.t_cv_end.map(piv["pack_mean"])
for c in CELLS:
    cat[f"R_pulse_mOhm_r8_{c[:5]}"] = cat.t_cv_end.map(piv[c])
cat["R_pulse_mOhm_r8_pack"] = cat[[f"R_pulse_mOhm_r8_{c[:5]}" for c in CELLS]].sum(axis=1, min_count=4)
cat["r8_event_id"] = cat.t_cv_end.map(r8.drop_duplicates("t_cv_end").set_index("t_cv_end").event_id)
cat.to_csv(os.path.join(ST, "wp0", "cv_catalogue.csv"), index=False)

# ---- numbers for FACTS.md ----
ck0 = pd.read_csv(os.path.join(DATA, "checkups", "CK0_reference_discharge.csv.gz"))
r11 = pd.read_csv(os.path.join(ST, "sources", "r11_wp4_pack_drivers.csv"))
en = pd.DataFrame(enter)
A = cat[cat.type == "A"].copy(); T = cat[cat.type == "T"]
a17 = A[A.anchor.astype(int).between(1, 7)]
facts = dict(
    n_full_charges=int(len(cat)), n_anchor=int(len(A)), n_topup=int(len(T)),
    n_topup_25C=int((T.setpoint_C == 25).sum()), n_topup_45C=int((T.setpoint_C == 45).sum()),
    r8_match_all=bool(cat.r8_event_id.notna().all() and (cat.r8_event_id == cat.event_id).all()),
    anchor_Ah=A.chg_Ah_counter.round(2).tolist(), topup_Ah_range=[float(T.chg_Ah_counter.min()), float(T.chg_Ah_counter.max())],
    anchor_cv=A[["anchor", "n_cv", "cv_s", "cv_Ah", "I_cv_end", "T_cv_end"]].to_dict("records"),
    anchors_1_7_cv_s_range=[float(a17.cv_s.min()), float(a17.cv_s.max())],
    anchors_1_7_n_cv_range=[int(a17.n_cv.min()), int(a17.n_cv.max())],
    anchors_1_7_I_end_range=[float(a17.I_cv_end.min()), float(a17.I_cv_end.max())],
    anchors_1_7_V30_range=[float(a17.V_pack_30.min()), float(a17.V_pack_30.max())],
    topup_cv_s_range_by_setpoint={int(k): [float(g.cv_s.min()), float(g.cv_s.max())] for k, g in T.groupby("setpoint_C")},
    topup_n_cv_range=[int(T.n_cv.min()), int(T.n_cv.max())],
    all_lag_30_s=[float(cat.lag_30_s.min()), float(cat.lag_30_s.max())], all_rest_ok=bool(cat.rest_ok.all()),
    all_no_gap=bool(cat.no_gap.all()),
    r11_fit_anchor1=dict(tau_s=float(r11.tau_CV_s[1]), I_inf_A=float(r11.I_inf_fit[1]), CV_Ah=float(r11.CV_Ah[1]), CV_h=float(r11.CV_h[1])),
    r11_fit_anchor7=dict(tau_s=float(r11.tau_CV_s[7]), I_inf_A=float(r11.I_inf_fit[7]), CV_Ah=float(r11.CV_Ah[7])),
    r11_fit_anchor0=dict(tau_s=float(r11.tau_CV_s[0]), I_inf_A=float(r11.I_inf_fit[0]), CV_h_s=float(r11.CV_h[0] * 3600)),
    r11_backenv_Iend_tau_Ah={k: float(r11.I_end[k] * r11.tau_CV_s[k] / 3600) for k in range(1, 8)},
    ck0_first=dict(V=float(ck0.voltage_V.iloc[0]), I=float(ck0.current_A.iloc[0]),
                   **{c: float(ck0[c].iloc[0]) for c in CELLS}, ts=str(ck0.timestamp.iloc[0])),
    ck0_last=dict(V=float(ck0.voltage_V.iloc[-1]), Ah=float(ck0.discharged_Ah.iloc[-1])),
    segment_ends=en.to_dict("records"))
json.dump(facts, open(os.path.join(ST, "wp0", "facts.json"), "w"), indent=1, default=str)

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60); pd.set_option("display.max_rows", 60)
print(cat[["event_id", "segment", "setpoint_C", "type", "anchor", "chg_Ah_counter", "n_cv", "cv_s", "cv_Ah", "cv_Ah_counter",
           "I_cv_start", "I_cv_end", "V_pack_end", "V_pack_30", "lag_30_s", "top_cell_end", "top_cell_30", "T_cv_end",
           "R_pulse_mOhm_r8_pack", "r8_event_id"]].round(3).to_string(index=False))
print(json.dumps({k: v for k, v in facts.items() if k not in ("segment_ends", "anchor_cv")}, indent=0, default=str))
print(en.round(3).to_string(index=False))
