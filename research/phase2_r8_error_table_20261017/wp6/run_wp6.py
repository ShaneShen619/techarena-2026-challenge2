"""WP6: descriptive error budget for SUB at delta 0.4 (real scenario), split into offset_part and inc_resid and the
contributions of the WP5 patterns. Diagnostic-only: nothing here is a candidate or a proxy score."""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
OUT = os.path.join(HERE, "outputs")
B_STEP = 0.745          # WP2 free-slope fit: step depth per Ah of anchor Q_fc
PP = 100.0 / 102.0

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    c = pd.read_csv(os.path.join(STUDY, "outputs", "table_cases.csv"))
    sub = c[(c.model == "SUB") & (c.delta == 0.4)]
    real = sub[sub.scenario == "real"].sort_values("k")
    ev = pd.read_csv(os.path.join(STUDY, "outputs", "table_events.csv"))
    pk = ev[ev.unit == "pack_mean"].set_index("t_cv_end")
    a = pd.read_csv(os.path.join(STUDY, "outputs", "table_anchors.csv")).set_index("anchor")
    ex = json.load(open(os.path.join(STUDY, "wp5", "outputs", "wp5_extra.json")))
    # H4 trend line on all SUB cases (same fit as WP5, refitted for the intercept)
    slope, icpt = np.polyfit(sub["cum_fade_at_anchor_Ah"], sub["inc_resid_Ah"], 1)
    assert abs(slope - ex["H4_slopes_Ah_per_Ah"]["cases"]["slope"]) < 1e-9
    rows = []
    for _, r in real.iterrows():
        d = dict(checkup=r.checkup, branch=r.branch, err_Ah=r.err_Ah, err_pp=r.err_pp, offset_part_Ah=r.offset_part_Ah,
                 inc_resid_Ah=r.inc_resid_Ah, inc_resid_pp=r.inc_resid_pp)
        beta = cell = first = np.nan
        if r.branch == "phase":
            raw = r.x
            beta = r.increment_pred - raw / B_STEP                    # beta_used vs 1/b
            mm = lambda t: float(pk.loc[t, "R_cell"])                  # pack mean minus cell median  # noqa: E731
            cell = r.beta_used * (mm(r.ev_E_cur) - mm(r.ev_E_prev))   # increment(mean) - increment(median)
            first = 0.0
        elif r.branch == "fallback":
            raw = r.increment_pred
            beta = raw - raw / B_STEP                                  # beta = 1 vs 1/b
            cell = float(pk.loc[r.ev_after_last, "R_cell"] - pk.loc[r.ev_after_first, "R_cell"])
            first = -float(a.loc[int(r.anchor_used), "off_main"])      # first program sits deeper -> more negative
        d.update(contrib_beta_vs_step_scaling_Ah=beta, contrib_first_program_offset_Ah=first,
                 contrib_cell_mean_vs_median_Ah=cell, H4_trend_fitted_Ah=icpt + slope * r.cum_fade_at_anchor_Ah)
        d["rest_Ah"] = r.inc_resid_Ah - np.nansum([beta, first, cell])
        rows.append(d)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "error_budget_real_d04.csv"), index=False)
    pd.set_option("display.width", 250)
    print(t.round(3).to_string())
