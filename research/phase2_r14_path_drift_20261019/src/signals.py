"""Registered signals (round 14 WP1): event table, P1 (Term3_k), P1b (Term3'_k), the descriptive gap-bridged P1
(S_gap), P2 (top rest-voltage difference, in mV and in Ah via s_top) and P3 (descriptive path memory).
Every function takes its data as arguments (segments dict, CK0 reference curve), so WP1 can test it on synthetic
series without touching the challenge data."""
import numpy as np
import pandas as pd
import data14 as D
import ahchain as AC

S_TOP_WINDOW_AH = (0.5, 2.0)   # CK0 C/20 curve, discharged Ah window for s_top = dV/dQ


def events(segs):
    """All CV ends (package rule) with kind A (the package anchor of the segment) or T, anchor id k (0.. in time
    order), set point, row index, order within the segment, package Q_fc for anchors."""
    rows, k = [], 0
    for s in sorted(segs):
        g = segs[s]
        ea, fc = D.anchor_index(g)
        ends = list(D.cv_ends(g))
        if ea is not None:
            assert ends[0] == ea, "the anchor must be the first CV end of its segment"
        for m, e in enumerate(ends):
            is_a = ea is not None and e == ea
            rows.append({"segment": int(s), "setpoint": int(g["chamber_temperature_C"].iloc[e]), "row": int(e),
                         "order": m, "kind": "A" if is_a else "T", "anchor": k if is_a else -1,
                         "t_cv_end": str(g["timestamp"].iloc[e]), "Q_fc": fc["q"] if is_a else np.nan})
        if ea is not None:
            k += 1
    return pd.DataFrame(rows)


def chain(segs, ev):
    """Pairs, lambdas, TT LOO residuals (both readings) and sigma_TT. Returns a dict of tables and numbers."""
    pairs = AC.build_pairs(segs, ev)
    sp = ev.groupby("segment")["setpoint"].first().to_dict()
    lam = AC.lambdas(pairs, sp)
    pairs = AC.offsets(pairs, lam)
    res_r = AC.tt_residuals(pairs, reading="reduced")
    res_f = AC.tt_residuals(pairs, reading="full")
    sig_r, sig_f = AC.sigma_tt(res_r), AC.sigma_tt(res_f)
    pairs = pairs.merge(res_r[["pair_id", "lambda_loo", "lambda_loo_source", "resid"]], on="pair_id", how="left")
    pairs = pairs.merge(res_f[["pair_id", "lambda_loo", "lambda_loo_source", "resid"]].rename(
        columns={"lambda_loo": "lambda_loo_full", "lambda_loo_source": "lambda_loo_full_source",
                 "resid": "resid_full"}), on="pair_id", how="left")
    gate = max(sig_r.get(25, np.nan), sig_f.get(25, np.nan))
    return {"pairs": pairs, "lambda": lam, "sigma_reduced": sig_r, "sigma_full": sig_f, "sigma_tt25_gate": gate,
            "sigma_tt45": sig_r.get(45, np.nan)}


def term3_table(ev, pairs, ck0_date):
    """Per anchor k: Term3_k (AT1, main if gap-free), Term3'_k (AT2, if gap-free), the gap-bridged Term3 (S_gap,
    descriptive), fade_k = Q_fc,1 - Q_fc,k, days since CK0."""
    anc = ev[ev["kind"] == "A"].sort_values("anchor")
    q1 = float(anc.loc[anc["anchor"] == 1, "Q_fc"].iloc[0]) if (anc["anchor"] == 1).any() else np.nan
    rows = []
    for _, a in anc.iterrows():
        k = int(a["anchor"])
        p = pairs[pairs["anchor"] == k]
        at1, at2 = p[p["type"] == "AT1"], p[p["type"] == "AT2"]
        r = {"anchor": k, "segment": int(a["segment"]), "setpoint": int(a["setpoint"]), "Q_fc": float(a["Q_fc"]),
             "fade": q1 - float(a["Q_fc"]),
             "days_since_ck0": (pd.Timestamp(a["t_cv_end"]) - pd.Timestamp(ck0_date)).total_seconds() / 86400.0}
        if len(at1):
            x = at1.iloc[0]
            r.update({"T1_t": x["t_j"], "AT1_N": x["N"], "AT1_thr": x["thr"], "AT1_n_gaps": int(x["n_gaps"]),
                      "AT1_gap_s": x["gap_s"], "lambda": x["lambda"], "lambda_source": x["lambda_source"],
                      "term3": x["offset"] if x["gap_free"] else np.nan, "term3_gap_bridged": x["offset"],
                      "term3_excluded": "" if x["gap_free"] else "recording gap in A->T1"})
        else:
            r.update({"term3": np.nan, "term3_gap_bridged": np.nan, "term3_excluded": "no top-up in segment"})
        if len(at2):
            x = at2.iloc[0]
            r.update({"T2_t": x["t_j"], "AT2_N": x["N"], "AT2_thr": x["thr"], "AT2_n_gaps": int(x["n_gaps"]),
                      "term3b": x["offset"] if x["gap_free"] else np.nan,
                      "term3b_excluded": "" if x["gap_free"] else "recording gap in A->T2"})
        else:
            r.update({"term3b": np.nan, "term3b_excluded": "no second top-up in segment"})
        rows.append(r)
    return pd.DataFrame(rows)


def s_top(ref):
    """OLS slope dV/dQ (V per discharged Ah) of the CK0 C/20 curve over discharged Ah in S_TOP_WINDOW_AH, for the
    pack (voltage_V) and per cell. Negative for a discharge curve."""
    q = ref["discharged_Ah"].to_numpy(float)
    w = (q >= S_TOP_WINDOW_AH[0]) & (q <= S_TOP_WINDOW_AH[1])
    out = {"n_samples": int(w.sum())}
    for c in ["voltage_V"] + D.CELLS:
        out["pack" if c == "voltage_V" else c] = float(np.polyfit(q[w], ref[c].to_numpy(float)[w], 1)[0])
    return out


def p2_table(segs, ev, st):
    """Per anchor: V30 of the anchor and of T1, dV = V30(T1) - V30(A) in mV (pack and cells), converted to Ah as
    -dV / s_top (pack: pack curve; cell: that cell's curve), so the sign matches Term3 (T1 top higher -> > 0)."""
    rows = []
    for _, a in ev[ev["kind"] == "A"].sort_values("anchor").iterrows():
        g = segs[int(a["segment"])]
        nxt = ev[(ev["segment"] == a["segment"]) & (ev["order"] == a["order"] + 1)]
        r = {"anchor": int(a["anchor"]), "segment": int(a["segment"]), "setpoint": int(a["setpoint"])}
        if not len(nxt):
            rows.append(r)
            continue
        va, oka = D.rest_voltage(g, int(a["row"]))
        vt, okt = D.rest_voltage(g, int(nxt["row"].iloc[0]))
        r["V30_ok"] = bool(oka and okt)
        for c, key in [("pack_voltage_V", "pack")] + [(c, c) for c in D.CELLS]:
            dv = vt[c] - va[c]
            r[f"V30_A_{key}"] = va[c]
            r[f"V30_T1_{key}"] = vt[c]
            r[f"dV_{key}_mV"] = 1000.0 * dv
            r[f"P2_{key}_Ah"] = -dv / st[key]
        r["P2_cellmean_Ah"] = float(np.mean([r[f"P2_{c}_Ah"] for c in D.CELLS]))
        rows.append(r)
    return pd.DataFrame(rows)


def p3_table(segs, ev, t3):
    """Descriptive path memory per anchor: o_k = D1 - D2 (A3 robust step and its dV/dQ variant, 0.25 Ah grid) with
    D1 the anchor's own deep program and D2 T1's; the absolute shift o_k + Term3_k (main Term3; gap-bridged Term3 in
    a separate column); anchor minus T1 CV Ah, CV duration and end current."""
    rows = []
    for _, a in ev[ev["kind"] == "A"].sort_values("anchor").iterrows():
        g = segs[int(a["segment"])]
        k = int(a["anchor"])
        r = {"anchor": k, "segment": int(a["segment"]), "setpoint": int(a["setpoint"]),
             "month": pd.Timestamp(a["t_cv_end"]).strftime("%Y-%m")}
        nxt = ev[(ev["segment"] == a["segment"]) & (ev["order"] == a["order"] + 1)]
        _, cva, cvsa, ia = D.cv_phase(g, int(a["row"]))
        r.update({"A_cv_Ah": cva, "A_cv_s": cvsa, "A_I_end": ia})
        if len(nxt):
            e1 = int(nxt["row"].iloc[0])
            _, cvt, cvst, it = D.cv_phase(g, e1)
            r.update({"T1_cv_Ah": cvt, "T1_cv_s": cvst, "T1_I_end": it, "dCV_Ah_A_minus_T1": cva - cvt,
                      "dCV_s_A_minus_T1": cvsa - cvst, "dI_end_A_minus_T1": ia - it})
            s1, s2 = D.step_variants(g, int(a["row"])), D.step_variants(g, e1)
            if s1 is not None and s2 is not None:
                r.update({"D1_A3": s1["A3"], "D2_A3": s2["A3"], "o_A3": s1["A3"] - s2["A3"],
                          "D1_dvdq": s1["dvdq"], "D2_dvdq": s2["dvdq"], "o_dvdq": s1["dvdq"] - s2["dvdq"]})
                t = t3.loc[t3["anchor"] == k].iloc[0]
                r["abs_shift_A3"] = r["o_A3"] + t["term3"]
                r["abs_shift_dvdq"] = r["o_dvdq"] + t["term3"]
                r["abs_shift_A3_gap_bridged"] = r["o_A3"] + t["term3_gap_bridged"]
                r["abs_shift_dvdq_gap_bridged"] = r["o_dvdq"] + t["term3_gap_bridged"]
        rows.append(r)
    return pd.DataFrame(rows)
