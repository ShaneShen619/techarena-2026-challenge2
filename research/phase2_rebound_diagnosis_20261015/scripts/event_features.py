"""Per deep-program event: pulse resistance, temperatures, CV-end state, loaded voltages at fixed depths."""
import os, sys, numpy as np, pandas as pd
R = "/Users/shane/Desktop/Arena_1013_model/research/phase2_anchor_step_20261013"
PKG = "/Users/shane/Desktop/Arena_1013_model/TechArena_Challenge2_Team_Package"
sys.path.insert(0, R + "/src"); sys.path.insert(0, PKG)
from framework.data import load_dataset
from events import CELLS, iter_segments, segment_arrays, _cv_ends, _pulse_resistance
op = load_dataset(PKG + "/data").operation
rows = []
for seg, g in iter_segments(op):
    t, cur, ah = segment_arrays(g)
    pack = g["pack_voltage_V"].to_numpy(float); V = g[CELLS].to_numpy(float)
    T = g["temp_mean_C"].to_numpy(float); ts = pd.to_datetime(g["timestamp"]).to_numpy()
    for e in _cv_ends(cur, pack):
        depth = ah[e] - ah[e:]
        if depth[: min(len(depth), 20000)].max() < 50: continue
        # CCCV charge that ended at e: walk back over positive current
        s = e
        while s > 0 and cur[s - 1] > 0.5: s -= 1
        cv = (pack[s:e + 1] > 13.95) & (cur[s:e + 1] > 0.5)
        r = dict(segment=seg, t_cv_end=pd.Timestamp(ts[e]), setpoint_C=int(g["chamber_temperature_C"].iloc[e]),
                 chg_Ah=float(ah[e] - ah[s]), chg_start_V=float(pack[s - 1] if s > 0 else np.nan),
                 cv_Ah=float(np.sum(cur[s:e + 1][cv] * np.diff(t[s:e + 2])[cv]) / 3600) if cv.any() else np.nan,
                 cv_h=float(cv.sum() * 10 / 3600), I_cv_end=float(cur[e]), T_cv_end=float(T[e]),
                 rest_before_chg_h=np.nan)
        # rest before the charge
        k = s - 1
        while k > 0 and abs(cur[k]) < 0.5: k -= 1
        r["rest_before_chg_h"] = float((t[s - 1] - t[k]) / 3600) if s > 0 else np.nan
        rp = _pulse_resistance(g, e, cur, depth)
        for c, x in zip(CELLS, rp): r[f"R_{c}"] = float(x) * 1000
        r["R_mean_mOhm"] = float(np.nanmean(rp)) * 1000
        # loaded cell-mean voltage and temperature at fixed depths in the 8-12.5 A band
        for dd in (15, 25, 35, 45):
            i = np.where(depth >= dd)[0]
            if len(i):
                j = e + i[0]; r[f"V_at{dd}"] = float(V[j].mean()); r[f"I_at{dd}"] = float(cur[j]); r[f"T_at{dd}"] = float(T[j])
        rows.append(r)
pd.DataFrame(rows).to_csv("event_features.csv", index=False)
print(len(rows))
