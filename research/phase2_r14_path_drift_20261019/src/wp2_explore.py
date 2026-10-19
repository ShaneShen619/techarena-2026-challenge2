"""WP2 EXPLORATORY (not registered, decides nothing): why does registered P1 fall with fade?
1. lambda by segment and checkup cycle (TT ratio N/thr over time).
2. Term3 with a same-cycle lambda: anchor k's lambda taken from the 45 degC segment of the same checkup cycle.
3. P2 per cell (dV trend in mV against fade).
Reads wp2/pairs.csv, wp2/term3.csv, wp2/p2_voltage.csv, wp2/events.csv; writes wp2/explore_lambda_segments.csv,
wp2/explore_same_cycle_term3.csv and wp2/explore.json."""
import json, os
import numpy as np
import pandas as pd
import data14 as D
import stats14 as SS
from wp2_measure import jsonable

ST = D.ST
OUT = os.path.join(ST, "wp2")


def main():
    ck, names = D.checkup_dates()
    pairs = pd.read_csv(os.path.join(OUT, "pairs.csv"))
    t3 = pd.read_csv(os.path.join(OUT, "term3.csv"))
    p2 = pd.read_csv(os.path.join(OUT, "p2_voltage.csv"))
    ev = pd.read_csv(os.path.join(OUT, "events.csv"))
    segs = D.segments()
    cycle = {s: int((ck < g["timestamp"].iloc[0]).sum()) - 1 for s, g in segs.items()}

    # 1. lambda per segment over time
    tt = pairs[(pairs["type"] == "TT") & pairs["gap_free"]].copy()
    tt["t_mid"] = pd.to_datetime(tt["t_i"]) + (pd.to_datetime(tt["t_j"]) - pd.to_datetime(tt["t_i"])) / 2
    rows = []
    for s, g in tt.groupby("segment"):
        rows.append({"segment": s, "setpoint": int(g["setpoint"].iloc[0]), "cycle_after": names[cycle[s]],
                     "t_mid": str(g["t_mid"].mean().floor("h")), "n_TT": len(g), "lambda_median": g["ratio"].median(),
                     "lambda_min": g["ratio"].min(), "lambda_max": g["ratio"].max(),
                     "within_spread_Ah_per_block": (g["ratio"].max() - g["ratio"].min()) * g["thr"].median()})
    ls = pd.DataFrame(rows)
    ls.to_csv(os.path.join(OUT, "explore_lambda_segments.csv"), index=False)
    days = (pd.to_datetime(tt["t_mid"]) - ck[0]).dt.total_seconds().to_numpy() / 86400
    lam_slope = SS.theil_sen(days, tt["ratio"].to_numpy())

    # 2. same-cycle lambda Term3 (45 degC segment of the same checkup cycle)
    lam45 = {cycle[s]: v for s, v in zip(ls["segment"], ls["lambda_median"])
             if int(ls.loc[ls["segment"] == s, "setpoint"].iloc[0]) == 45}
    at1 = pairs[pairs["type"] == "AT1"].set_index("anchor")
    sc = []
    for _, r in t3[t3["anchor"] >= 1].iterrows():
        k = int(r["anchor"]); s = int(r["segment"]); c = cycle[s]
        p = at1.loc[k]
        l = lam45.get(c, np.nan)
        sc.append({"anchor": k, "segment": s, "cycle_after": names[c], "fade": r["fade"],
                   "days_since_ck0": r["days_since_ck0"], "gap_free": bool(p["gap_free"]),
                   "lambda_registered": r["lambda"], "lambda_source_registered": r["lambda_source"],
                   "term3_registered": r["term3"], "term3_gap_bridged": r["term3_gap_bridged"],
                   "lambda_same_cycle_45C": l,
                   "same_cycle_45C_segment": next((x for x in ls["segment"] if cycle[x] == c and
                                                   int(ls.loc[ls["segment"] == x, "setpoint"].iloc[0]) == 45), None),
                   "term3_same_cycle": p["N"] - l * p["thr"] if np.isfinite(l) else np.nan,
                   "lambda_error_Ah_registered_minus_same_cycle": (l - r["lambda"]) * p["thr"] if np.isfinite(l) else np.nan})
    sc = pd.DataFrame(sc)
    sc.to_csv(os.path.join(OUT, "explore_same_cycle_term3.csv"), index=False)
    fits = {}
    for name, mask in [("same_cycle_gap_free", sc["gap_free"] & np.isfinite(sc["term3_same_cycle"])),
                       ("same_cycle_incl_gap_bridged", np.isfinite(sc["term3_same_cycle"]))]:
        q = sc[mask]
        a = SS.analyze(q["anchor"].tolist(), q["fade"].to_numpy(), q["days_since_ck0"].to_numpy(),
                       q["term3_same_cycle"].to_numpy())
        b, _ = SS.ts_fit(q["fade"].to_numpy(), q["term3_same_cycle"].to_numpy())
        fits[name] = {"n": len(q), "theil_sen_d": b, "E": b * SS.E_SCALE_AH, "registered_statistics": a,
                      "values": dict(zip(q["anchor"].astype(int), q["term3_same_cycle"]))}
    # same-cycle transfer check where a 25 degC segment has its own TT lambda (segments 10, 12)
    transfer = []
    for s in (10, 12):
        own = float(ls.loc[ls["segment"] == s, "lambda_median"].iloc[0])
        l = lam45.get(cycle[s], np.nan)
        thr = float(at1.loc[int(ev.loc[(ev["segment"] == s) & (ev["kind"] == "A"), "anchor"].iloc[0]), "thr"])
        transfer.append({"segment": s, "lambda_own_25C": own, "lambda_same_cycle_45C": l,
                         "difference_Ah_per_block": (own - l) * thr})

    # 3. P2 per cell
    cells = {}
    q = p2[(p2["anchor"] >= 1)]
    for key in ["pack"] + D.CELLS:
        y = q[f"dV_{key}_mV"].to_numpy(); x = t3.set_index("anchor").loc[q["anchor"], "fade"].to_numpy()
        b, a = SS.ts_fit(x, y)
        cells[key] = {"dV_mV": dict(zip(q["anchor"].astype(int), map(float, y))), "theil_sen_mV_per_Ah_fade": b,
                      "first_last_mV": [float(y[0]), float(y[-1])]}
    out = {"label": "EXPLORATORY - not registered, decides nothing",
           "lambda_time_slope_per_day_all_TT": lam_slope,
           "lambda_segments": ls.to_dict(orient="records"), "same_cycle_fits": fits,
           "same_cycle_transfer_check": transfer, "p2_per_cell": cells}
    json.dump(jsonable(out), open(os.path.join(OUT, "explore.json"), "w"), indent=1, default=str)
    print(ls.to_string(index=False))
    print(sc[["anchor", "cycle_after", "fade", "gap_free", "lambda_registered", "lambda_same_cycle_45C",
              "term3_registered", "term3_gap_bridged", "term3_same_cycle", "lambda_error_Ah_registered_minus_same_cycle"]].to_string(index=False))
    for k, v in fits.items():
        print(k, v["n"], round(v["theil_sen_d"], 4), round(v["E"], 3), v["values"])
    print(transfer)
    for k, v in cells.items():
        print(k, round(v["theil_sen_mV_per_Ah_fade"], 2), v["dV_mV"])
    print("lambda slope per day", lam_slope)


if __name__ == "__main__":
    main()
