"""Stage A: event extraction and audit on the full released data (audit only)."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "TechArena_Challenge2_Team_Package"))
sys.path.insert(0, os.path.join(HERE, "src"))
sys.path.insert(0, ROOT)

from framework.data import load_dataset  # noqa: E402
from events import (CELLS, STEP_VARIANTS, charge_step_split, ck0_reference_step,  # noqa: E402
                    full_charges, step_programs, tail_margin_Ah)

OUT = os.path.join(HERE, "outputs")


def main():
    ds = load_dataset(os.path.join(ROOT, "data"))
    op, ref = ds.operation, ds.reference_discharge

    fc = full_charges(op)
    fc["tail_margin_upper_Ah"] = [tail_margin_Ah(ref, {c: r[f"start_{c}"] for c in CELLS})
                                  for _, r in fc.iterrows()]
    fc["integral_minus_counter_Ah"] = fc["Q_Ah"] - fc["counter_Ah"]
    fc.drop(columns="_seg_index").to_csv(os.path.join(OUT, "A1_full_charges.csv"), index=False)

    steps = {}
    for name, ov in STEP_VARIANTS.items():
        st = step_programs(op, **ov)
        st["variant"] = name
        steps[name] = st
    allst = pd.concat(steps.values(), ignore_index=True)
    allst.to_csv(os.path.join(OUT, "A2_step_programs_all_variants.csv"), index=False)

    main_st = steps["main"]
    wide = pd.DataFrame({n: s.set_index("t_cv_end")["step_mean"] for n, s in steps.items()})
    wide.to_csv(os.path.join(OUT, "A2_step_mean_by_variant.csv"))

    # jumps across checkups: last 45 C measurement before a checkup vs first 25 C after
    jumps = []
    ms = main_st.sort_values("t_cv_end").reset_index(drop=True)
    for i in range(1, len(ms)):
        if ms.loc[i, "segment"] != ms.loc[i - 1, "segment"] and ms.loc[i, "setpoint_C"] == 25:
            jumps.append(dict(before=ms.loc[i - 1, "t_cv_end"], after=ms.loc[i, "t_cv_end"],
                              gap_days=(ms.loc[i, "t_cv_end"] - ms.loc[i - 1, "t_cv_end"]).days,
                              jump_Ah=ms.loc[i, "step_mean"] - ms.loc[i - 1, "step_mean"]))
    pd.DataFrame(jumps).to_csv(os.path.join(OUT, "A2_checkup_jumps.csv"), index=False)

    # same-time temperature check: 45 C last vs 25 C first are separated by a checkup,
    # so compare consecutive same-segment differences per temperature as a drift rate
    rate = []
    for seg, g in ms.groupby("segment"):
        if len(g) >= 2:
            days = (g["t_cv_end"].iloc[-1] - g["t_cv_end"].iloc[0]).total_seconds() / 86400
            rate.append(dict(segment=seg, setpoint_C=g["setpoint_C"].iloc[0], n=len(g),
                             drift_Ah_per_day=(g["step_mean"].iloc[-1] - g["step_mean"].iloc[0]) / days))
    pd.DataFrame(rate).to_csv(os.path.join(OUT, "A2_in_segment_drift.csv"), index=False)

    ck0 = ck0_reference_step(ref)
    splits = pd.concat([charge_step_split(op, fc, s) for s in (1.0, 2.0, 3.0)], ignore_index=True)
    splits.to_csv(os.path.join(OUT, "A4_charge_step_split.csv"), index=False)

    # A4 summary: 25 C change Feb -> Sep in each section, per smoothing width
    a4 = []
    for s, g in splits.groupby("smooth_Ah"):
        g25 = g[g["segment"] != 1].sort_values("segment")
        dq = g25["Q_Ah"].iloc[-1] - g25["Q_Ah"].iloc[0]
        a4.append(dict(smooth_Ah=s, dQ=dq,
                       d_bottom_to_step=g25["bottom_to_step_mean"].iloc[-1] - g25["bottom_to_step_mean"].iloc[0],
                       d_step_to_top=g25["step_to_top_mean"].iloc[-1] - g25["step_to_top_mean"].iloc[0],
                       slope_top_vs_Q=float(np.polyfit(g25["Q_Ah"], g25["step_to_top_mean"], 1)[0]),
                       slope_bottom_vs_Q=float(np.polyfit(g25["Q_Ah"], g25["bottom_to_step_mean"], 1)[0])))

    n_prog = len(main_st)
    located = main_st["step_mean"].notna().mean() if n_prog else 0.0
    variant_spread = (wide.max(axis=1) - wide.min(axis=1))
    summary = dict(
        n_full_charges=len(fc),
        full_charge_Q=fc[["segment", "setpoint_C", "Q_Ah"]].round(3).to_dict("records"),
        max_abs_integral_minus_counter_Ah=float(fc["integral_minus_counter_Ah"].abs().max()),
        max_tail_margin_upper_Ah=float(fc["tail_margin_upper_Ah"].max()),
        n_step_programs=n_prog, located_fraction=float(located),
        median_four_cell_range_Ah=float(main_st["step_range"].median()),
        p90_four_cell_range_Ah=float(main_st["step_range"].quantile(0.9)),
        variant_spread_median_Ah=float(variant_spread.median()),
        variant_spread_max_Ah=float(variant_spread.max()),
        mean_checkup_jump_Ah=float(pd.DataFrame(jumps)["jump_Ah"].mean()) if jumps else None,
        ck0_reference_step=ck0, a4_section_changes=a4,
        first_program_step_mean=float(ms["step_mean"].iloc[0]))
    with open(os.path.join(OUT, "A_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
