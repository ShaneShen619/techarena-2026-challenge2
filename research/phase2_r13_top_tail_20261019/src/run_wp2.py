"""WP2 measurements with the registered src/tail.py (wp1/protocol.json). No decision is applied here (WP3).

Usage: python3 -B run_wp2.py <study_dir> <package_data_dir>
Writes wp2/fits.csv, tails.csv, pairs.csv, top_state.csv, top_state_slopes.csv, topup_monthly.csv,
topup_monthly_slopes.csv, ck0_comparison.csv, measurements.json and cache/traces.npz (for the figures).
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail  # noqa: E402

ST, DATA = sys.argv[1], sys.argv[2]
OUT = os.path.join(ST, "wp2"); os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(ST, "cache"), exist_ok=True)

fits, tails, traces = tail.fit_all(ST, DATA)
fade = tail.fade_table(ST)
anc_tails, pairs = tail.anchor_drift(tails, fade)
ts_rows, ts_slopes, topcell = tail.top_state(ST, DATA)
mon, mon_sl = tail.topup_monthly(tails, fade)
ck0 = tail.ck0_comparison(ST, DATA)

# tails.csv: every charge, with Delta_tail and fade for anchors 1..7
tails_out = tails.merge(anc_tails[["event_id", "model", "scenario", "Delta_tail_Ah"]], on=["event_id", "model", "scenario"], how="left")
af = tails_out.anchor.astype(float)
tails_out["fade_Ah"] = af.map(lambda k: fade.get(int(k), np.nan) if np.isfinite(k) else np.nan)

fits.to_csv(os.path.join(OUT, "fits.csv"), index=False)
tails_out.to_csv(os.path.join(OUT, "tails.csv"), index=False)
pairs.to_csv(os.path.join(OUT, "pairs.csv"), index=False)
ts_rows.to_csv(os.path.join(OUT, "top_state.csv"), index=False)
ts_slopes.merge(topcell.assign(estimator="T2").groupby("estimator").agg(
    top_cell_end=("top_cell_end", lambda s: ",".join(sorted(set(s)))),
    top_cell_30=("top_cell_30", lambda s: ",".join(sorted(set(s))))).reset_index(), on="estimator", how="left") \
    .to_csv(os.path.join(OUT, "top_state_slopes.csv"), index=False)
mon.to_csv(os.path.join(OUT, "topup_monthly.csv"), index=False)
mon_sl.to_csv(os.path.join(OUT, "topup_monthly_slopes.csv"), index=False)
ck0.to_csv(os.path.join(OUT, "ck0_comparison.csv"), index=False)
np.savez(os.path.join(ST, "cache", "traces.npz"), **{f"{k}_t": v[0] for k, v in traces.items()}, **{f"{k}_I": v[1] for k, v in traces.items()})

# summary numbers for the report
fa = fits[(fits.type == "A")].copy(); fa["anchor"] = fa.anchor.astype(float).astype(int)
adm = fa.pivot_table(index="anchor", columns="model", values="admitted", aggfunc="first")
m1 = fa[fa.model == "M1"].set_index("anchor")
ft = fits[fits.type == "T"]
summ = dict(
    admission_anchors=adm.astype(bool).astype(int).to_dict(),
    admission_counts_anchors_1_7={m: int(adm.loc[1:7, m].sum()) for m in tail.MODELS},
    admission_topups={m: dict(n=int((ft.model == m).sum()), admitted=int(ft[ft.model == m].admitted.sum()),
                              admitted_25C=int(ft[(ft.model == m) & (ft.setpoint_C == 25)].admitted.sum()),
                              n_25C=int(((ft.model == m) & (ft.setpoint_C == 25)).sum())) for m in tail.MODELS},
    rmse_anchors_1_7={m: [float(fa[(fa.model == m) & fa.anchor.between(1, 7)].rmse.min()),
                          float(fa[(fa.model == m) & fa.anchor.between(1, 7)].rmse.max())] for m in tail.MODELS},
    last_third_anchors_1_7={m: [float(fa[(fa.model == m) & fa.anchor.between(1, 7)].last_third_mean_resid.min()),
                                float(fa[(fa.model == m) & fa.anchor.between(1, 7)].last_third_mean_resid.max())] for m in tail.MODELS},
    backenv_M1={str(k): dict(tau_M1_s=float(m1.tau.loc[k]), I_end=float(m1.I_end.loc[k]), Iend_x_tau_Ah=float(m1.Iend_x_tau_Ah.loc[k]),
                             admitted=bool(m1.admitted.loc[k]), rmse=float(m1.rmse.loc[k]),
                             last_third=float(m1.last_third_mean_resid.loc[k])) for k in (1, 7)},
    pairs_member=pairs[pairs.member_of_A][["model", "scenario", "slope", "loo_min", "loo_max", "effect_CK7_Ah"]].to_dict("records"),
    pairs_not_member=pairs[~pairs.member_of_A & (pairs.scenario != "C1")][["model", "scenario", "ref_admitted_defined", "n_usable_2_7"]].to_dict("records"),
    undefined=tails[(tails.type == "A") & ~tails.defined][["event_id", "model", "scenario"]].to_dict("records"),
    T2_T3=ts_slopes.to_dict("records"),
    top_cells=topcell.to_dict("records"),
    fade=fade.to_dict())
json.dump(summ, open(os.path.join(OUT, "measurements.json"), "w"), indent=1, default=float)

pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
print(fa[fa.anchor.between(0, 7)][["anchor", "model", "rmse", "last_third_mean_resid", "converged", "at_bound", "admitted",
                                   "A", "tau", "Iinf", "t0", "A1", "tau1", "A2", "tau2", "Iend_x_tau_Ah"]].round(4).to_string(index=False))
print(pairs.round(5).to_string(index=False))
print(ts_slopes.round(5).to_string(index=False))
print(json.dumps({k: summ[k] for k in ("admission_counts_anchors_1_7", "admission_topups", "backenv_M1")}, indent=0))
