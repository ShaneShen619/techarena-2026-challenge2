"""WP2: bottom section — start audit (B1), charge-side step locators and trend (B2), CK0 split (B3), gates.

Uses the registered modules src/locators.py and src/ahchain.py unchanged (protocol v1, wp1/protocol.sha256).
Run: python3 -B src/wp2_run.py b1|b2|b3|gates"""
import json, os, sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import data12 as D
import locators as L
import ahchain as AC

OUT = os.path.join(D.ST, "wp2")
CK0_DATE = D.CK_DATES[0]
RELAXED_SLOPE_MV_H = 6.0


def events():
    return pd.read_csv(os.path.join(D.ST, "wp0", "events.csv"),
                       parse_dates=["t_charge_start", "t_cv_start", "t_cv_end", "t_prepulse"])


def anchors():
    return events().query("type == 'A'").sort_values("anchor_k").reset_index(drop=True)


def jdump(obj, name):
    json.dump(obj, open(os.path.join(OUT, name), "w"), indent=1, default=lambda x: None if x is None else
              (float(x) if isinstance(x, (np.floating, float)) else (int(x) if isinstance(x, np.integer) else str(x))))


def t_days(ts):
    return (pd.Timestamp(ts) - CK0_DATE).total_seconds() / 86400.0


# ---- B1 ----------------------------------------------------------------------------------------------------
def b1():
    S = D.segments()
    cw = pd.read_csv(os.path.join(D.ST, "wp0", "checkup_windows.csv"))
    rows = []
    for _, a in anchors().iterrows():
        g = S[a["segment"]]
        el = g["elapsed_s"].to_numpy(float); i = g["current_A"].to_numpy(float)
        u = g["pack_voltage_V"].to_numpy(float); V = g[D.CELLS].to_numpy(float); T = g["temp_mean_C"].to_numpy(float)
        s = int([x for x in np.where(g["timestamp"].to_numpy() == np.datetime64(a["t_charge_start"]))[0] if i[x] > 0.5][0])
        k = s - 1
        while k >= 0 and abs(i[k]) <= 0.5:
            k -= 1
        idx = np.arange(k + 1, s)
        h = (el[idx] - el[idx[0]]) / 3600.0
        last30 = idx[el[idx] >= el[s - 1] - 1800.0]
        h30 = (el[last30] - el[last30[0]]) / 3600.0
        slope30 = 1000.0 * np.polyfit(h30, u[last30], 1)[0]
        w = cw[cw["checkup"] == f"CK{int(a['anchor_k'])}"].iloc[0]
        row = dict(anchor_k=int(a["anchor_k"]), segment=int(a["segment"]), setpoint=int(a["setpoint"]),
                   checkup=w["checkup"], window_days=w["window_days"], window_known=bool(w["window_known"]),
                   window_from=w["t_last"], segment_start=g["timestamp"].iloc[0], charge_start=a["t_charge_start"],
                   rest_h=(el[s - 1] - el[idx[0]]) / 3600.0, rest_from_segment_start=bool(idx[0] == 0),
                   days_since_window_start=(pd.Timestamp(a["t_charge_start"]) - pd.Timestamp(w["t_last"])).total_seconds() / 86400.0,
                   pack_V_rest_first=u[idx[0]], pack_V_start=u[s - 1])
        for c in range(4):
            row[f"cell{c + 1}_V_start"] = V[s - 1, c]
        row.update(slope_last30_mV_h=slope30, slope_whole_rest_mV_h=1000.0 * np.polyfit(h, u[idx], 1)[0],
                   slope_window_h=min(0.5, row["rest_h"]),
                   temp_start_C=T[s - 1], temp_rest_first_C=T[idx[0]],
                   temp_trend_K_h=float(np.polyfit(h, T[idx], 1)[0]),
                   spread_start_V=V[s - 1].max() - V[s - 1].min(), spread_rest_first_V=V[idx[0]].max() - V[idx[0]].min(),
                   lowest_cell_start=D.CELLS[int(np.argmin(V[s - 1]))][:5],
                   relaxed=bool(slope30 <= RELAXED_SLOPE_MV_H))
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT, "start_audit.csv"), index=False, float_format="%.6g")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(out.T.to_string())


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    {"b1": b1}[sys.argv[1]]()
