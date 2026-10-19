"""WP0.3-4: wp0/anchor_blocks.csv (one row per anchor k = 0..7) and wp0/facts.json (numbers for FACTS.md).
No Ah balance between CV ends is computed here (WP0 rule)."""
import json, os
import numpy as np
import pandas as pd
import data14 as D

ST = D.ST
VARIANT_NAMES = ["main", "band_narrow", "windows_minus3", "windows_plus3", "dvdq_peak", "ir_corrected"]


def event_cols(seg, e, tag):
    t = seg["timestamp"]
    i = seg["current_A"].to_numpy(float)
    u = seg["pack_voltage_V"].to_numpy(float)
    s = D.charge_start(i, e)
    c0, cv_ah, cv_s, i_end = D.cv_phase(seg, e)
    v30, ok = D.rest_voltage(seg, e)
    r = {f"{tag}_row": int(e), f"{tag}_charge_start_row": int(s),
         f"{tag}_t_cv_end": str(t.iloc[e]), f"{tag}_t_charge_start": str(t.iloc[s]),
         f"{tag}_pack_V_before_charge": float(u[s - 1]) if s > 0 else np.nan,
         f"{tag}_cv_Ah": round(cv_ah, 5), f"{tag}_cv_s": cv_s, f"{tag}_I_end_A": i_end,
         f"{tag}_T_mean_cv_end_C": float(seg["temp_mean_C"].iloc[e]), f"{tag}_V30_ok": ok,
         f"{tag}_V30_pack_V": v30["pack_voltage_V"]}
    for c in D.CELLS:
        r[f"{tag}_V30_{c}"] = v30[c]
    return r


def main():
    segs = D.segments()
    ck, names = D.checkup_dates()
    rows, prog = [], []
    k = 0
    for s, g in segs.items():
        ea, fc = D.anchor_index(g)
        ends = list(D.cv_ends(g))
        for e in ends:  # step depths of every deep program (for the first-program offset fact)
            sv = D.step_variants(g, e)
            if sv is not None:
                prog.append({"segment": s, "t_cv_end": str(g["timestamp"].iloc[e]), "is_anchor": e == ea,
                             "A3": sv["A3"], "dvdq": sv["dvdq"],
                             **{n: float(np.nanmedian(sv["variants"][j])) for j, n in enumerate(VARIANT_NAMES)}})
        if ea is None:
            continue
        nxt = [e for e in ends if e > ea][:2]
        r = {"anchor": k, "segment": s, "setpoint_C": fc["setpoint"], "checkup_before": names[int((ck < fc["t_end"]).sum()) - 1],
             "Q_fc_Ah": round(fc["q"], 5), "n_topups_in_segment": len([e for e in ends if e > ea])}
        r.update(event_cols(g, ea, "A"))
        prev = ea
        for tag, e in zip(("T1", "T2"), nxt + [None] * (2 - len(nxt))):
            if e is None:
                r[f"gaps_{'A' if tag == 'T1' else 'T1'}_{tag}_n"] = np.nan
                r[f"gaps_{'A' if tag == 'T1' else 'T1'}_{tag}_s"] = np.nan
                continue
            n, sec = D.gaps_between(g, prev, e)
            r[f"gaps_{'A' if tag == 'T1' else 'T1'}_{tag}_n"] = n
            r[f"gaps_{'A' if tag == 'T1' else 'T1'}_{tag}_s"] = sec
            r.update(event_cols(g, e, tag))
            prev = e
        rows.append(r)
        k += 1
    df = pd.DataFrame(rows)
    lead = ["anchor", "segment", "setpoint_C", "checkup_before", "Q_fc_Ah", "n_topups_in_segment"]
    cols = lead + [c for c in df.columns if c.startswith("A_")] \
        + ["gaps_A_T1_n", "gaps_A_T1_s"] + [c for c in df.columns if c.startswith("T1_")] \
        + ["gaps_T1_T2_n", "gaps_T1_T2_s"] + [c for c in df.columns if c.startswith("T2_")]
    df = df.reindex(columns=cols)
    df.to_csv(os.path.join(ST, "wp0", "anchor_blocks.csv"), index=False)
    pd.DataFrame(prog).to_csv(os.path.join(ST, "cache", "wp0_programs.csv"), index=False)
    print(df.T.to_string())
    print(pd.DataFrame(prog).to_string())


if __name__ == "__main__":
    main()
