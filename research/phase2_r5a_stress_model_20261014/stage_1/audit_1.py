"""Stage 1 audit: stress-history extraction (no proxy metric is computed here)."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common5a import H  # noqa: E402
from stress import stress_table, cumulative, horizon_lag_days, segment_summary  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
EA = 37.3e3
CK = H.CK


def month_of(t):
    return int((CK <= t).sum()) - 1


def per_month(tab):
    t = tab.copy()
    t["month"] = [month_of(x) for x in t["t0"]]
    t["Tclass"] = np.where(t["kind"] == "observed", t["setpoint"].astype(str) + "C",
                           np.where(t["T_time"].fillna(25) > 35, "45C", "25C"))
    g = t.groupby(["month", "kind", "Tclass"]).agg(days=("days", "sum"), Ah=("thr_Ah", "sum")).reset_index()
    return g


# 1) full-data table
full = H.full_op()
tab_full = stress_table(full, full["timestamp"].max(), CK)
pm = per_month(tab_full)
pm.to_csv(os.path.join(OUT, "S1_per_month_full.csv"), index=False)

# 2) throughput definition check (counters vs integral of |I| on gap-free rows)
chk = []
for seg, g in full.groupby("segment"):
    ts = g["elapsed_s"].to_numpy(float); dt = np.r_[0, np.diff(ts)]
    ok = (dt > 0) & (dt <= 600)
    integ = float(np.sum(np.abs(g["current_A"].to_numpy()[ok]) * dt[ok] / 3600))
    ctr = (g["charge_Ah_cum"].diff().fillna(0) + g["discharge_Ah_cum"].diff().fillna(0)).to_numpy()
    chk.append(dict(segment=int(seg), int_absI_Ah=integ, counters_gapfree_Ah=float(ctr[ok].sum()),
                    counters_total_Ah=float(ctr.sum()), rel_diff=float(ctr[ok].sum() / integ - 1)))
pd.DataFrame(chk).to_csv(os.path.join(OUT, "S1_throughput_check.csv"), index=False)

# 3) extrapolation audit: hidden part of each cut vs the full data over the same interval
rows = []
for scen in ("real", "PC5", "PC10", "PG1", "PG2"):
    for k, spec in H.SCENARIOS[scen]:
        if k < 3:
            continue
        op, key = H.scenario_op(k, spec)
        if op is None:
            continue
        fc = H.full_charges(op)
        L = horizon_lag_days(fc, CK, CK[k])
        hz = CK[k] + pd.Timedelta(days=L)
        tab = stress_table(op, CK[k], CK, horizon=hz)
        t_last = op["timestamp"].max()
        hid = tab[tab["t0"] >= t_last]
        # truth over the same interval from the full table (observed + checkup kinds)
        tf = tab_full
        tr = tf[(tf["t1"] > t_last) & (tf["t0"] < hz)].copy()
        a0, a1 = tr["t0"].astype("int64"), tr["t1"].astype("int64")
        lo = np.maximum(a0, pd.Timestamp(t_last).value)
        hi = np.minimum(a1, pd.Timestamp(hz).value)
        span = (a1 - a0).clip(lower=1)
        f = ((hi - lo) / span).clip(lower=0).to_numpy()
        tr_days, tr_ah = tr["days"].to_numpy() * f, tr["thr_Ah"].to_numpy() * f
        a = cumulative(hid, EA)
        trs = tr.copy(); trs["days"] = tr_days; trs["thr_Ah"] = tr_ah
        b = cumulative(trs, EA)
        r = tab.attrs["rules"]
        rows.append(dict(scenario=scen, k=k, horizon_lag_d=L, t_last=str(t_last), horizon=str(hz),
                         offset45=r["offset45"], rate45_Ah_d=r["rate45"], end_off_h=r["end_off_h"],
                         hid_days=float(hid["days"].sum()), true_days=float(tr_days.sum()),
                         hid_Ah=float(hid["thr_Ah"].sum()), true_Ah=float(tr_ah.sum()),
                         hid_tau_eff=float(a[0]), true_tau_eff=float(b[0]),
                         hid_ah_eff=float(a[1]), true_ah_eff=float(b[1])))
aud = pd.DataFrame(rows)
aud["d_tau_eff"] = aud["hid_tau_eff"] - aud["true_tau_eff"]
aud["d_ah_eff"] = aud["hid_ah_eff"] - aud["true_ah_eff"]
aud.to_csv(os.path.join(OUT, "S1_extrapolation_audit.csv"), index=False)

# 4) horizon lag at every real cut (incl. k = 1, 2: rule parameters only, no proxy)
lags = []
for k in range(1, 8):
    op = H.cut_op(k)
    fc = H.full_charges(op)
    lags.append(dict(k=k, L_days=horizon_lag_days(fc, CK, CK[k])))
pd.DataFrame(lags).to_csv(os.path.join(OUT, "S1_horizon_lag.csv"), index=False)

summ = dict(
    full_total_days=float(tab_full["days"].sum()),
    full_total_Ah=float(tab_full["thr_Ah"].sum()),
    kinds=tab_full.groupby("kind")[["days", "thr_Ah"]].sum().to_dict(),
    extrapolation_abs_err=dict(
        tau_eff_median=float(aud["d_tau_eff"].abs().median()), tau_eff_max=float(aud["d_tau_eff"].abs().max()),
        ah_eff_median=float(aud["d_ah_eff"].abs().median()), ah_eff_max=float(aud["d_ah_eff"].abs().max())),
)
json.dump(summ, open(os.path.join(OUT, "S1_summary.json"), "w"), indent=1, default=str)
print(json.dumps(summ, indent=1, default=str))
print(pm.to_string())
print(aud[["scenario", "k", "horizon_lag_d", "hid_days", "true_days", "hid_Ah", "true_Ah",
           "d_tau_eff", "d_ah_eff"]].round(2).to_string())
