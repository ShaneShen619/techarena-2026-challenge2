"""WP3: top — Ah chain (E1), step jump (E2), physics diagnostic (E3), T_top with the registered gates.

Uses the registered modules src/ahchain.py and src/locators.py unchanged (protocol v1, wp1/protocol.sha256).
Run: python3 -B src/wp3_run.py e1|e2e3|ttop"""
import json, os, sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import data12 as D
import locators as L
import ahchain as AC

OUT = os.path.join(D.ST, "wp3")


def events():
    return pd.read_csv(os.path.join(D.ST, "wp0", "events.csv"),
                       parse_dates=["t_charge_start", "t_cv_start", "t_cv_end", "t_prepulse"]).sort_values("t_cv_end").reset_index(drop=True)


def month_of(t):
    """index m of the last checkup date before t (month m runs from CK_m to CK_m+1)."""
    return int((D.CK_DATES < pd.Timestamp(t)).sum()) - 1


def jdump(obj, name):
    def conv(x):
        if isinstance(x, (np.floating,)):
            return float(x)
        if isinstance(x, (np.integer,)):
            return int(x)
        if isinstance(x, (np.bool_,)):
            return bool(x)
        return str(x)
    json.dump(obj, open(os.path.join(OUT, name), "w"), indent=1, default=conv)


def chain():
    S = D.segments(); ev = events()
    pairs = AC.build_pairs(ev, S, D.CK_DATES)
    pairs["month"] = [month_of(t) for t in pairs["t_i"]]
    pairs["N_over_thr"] = pairs["N"] / pairs["thr"]
    return S, ev, pairs


# ---- E1 ----------------------------------------------------------------------------------------------------
def e1():
    S, ev, pairs = chain()
    pairs.to_csv(os.path.join(OUT, "pairs.csv"), index=False, float_format="%.6g")
    lam_rows = []
    for s in sorted(S):
        sp = int(S[s]["chamber_temperature_C"].iloc[0])
        lm, src = AC.lam(pairs, s, sp)
        n_tt = int(((pairs["type"] == "TT") & pairs["admissible"] & (pairs["seg_i"] == s)).sum())
        lam_rows.append(dict(segment=s, setpoint=sp, lam=lm, source=src, n_TT=n_tt))
    lam = pd.DataFrame(lam_rows)
    res = AC.tt_residuals(pairs)
    noise = AC.g_noise(res)
    tm = AC.terms(pairs)
    tm["month"] = [month_of(pairs.set_index("pair").loc[p, "t_i"]) for p in tm["pair"]]
    tm.to_csv(os.path.join(OUT, "terms.csv"), index=False, float_format="%.6g")
    excl = pairs[(pairs["type"] != "none") & ~pairs["admissible"]][["pair", "type", "reason"]]
    out = dict(protocol="v1 (wp1/protocol.sha256)", lam=lam.to_dict("records"), tt_residuals=res.to_dict("records"),
               G_noise=noise, n_pairs=dict(pairs["type"].value_counts()),
               n_admissible={t: int(((pairs["type"] == t) & pairs["admissible"]).sum()) for t in ("AT", "TT", "X")},
               exclusions=excl.to_dict("records"),
               not_paired=pairs[pairs["type"] == "none"][["pair", "reason"]].to_dict("records"))
    jdump(out, "e1_chain.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(pairs[["pair", "type", "seg_i", "seg_j", "month", "admissible", "reason", "N", "thr", "N_over_thr",
                 "max_dt_inside_s", "boundary_s"]].round(5).to_string())
    print(lam.to_string()); print(res.to_string()); print(noise)
    print(tm.round(4).to_string())


# ---- E2 and E3 -----------------------------------------------------------------------------------------------
def cv_index(seg, t):
    i = seg["current_A"].to_numpy(float)
    return int([x for x in np.where(seg["timestamp"].to_numpy() == np.datetime64(t))[0] if i[x] > 0.5][-1])


def package_steps(S):
    sys.path.insert(0, D.PKG)
    from my_model import model_template as mt
    out = {}
    for _, g in S.items():
        for t, _, dep, _ in mt._step_depths(g.reset_index(drop=True)):
            out[pd.Timestamp(t)] = dep
    return out


def e2e3():
    S, ev, pairs = chain()
    tm = pd.read_csv(os.path.join(OUT, "terms.csv"))
    a3 = package_steps(S)
    dl1 = {}
    for _, e in ev.iterrows():
        g = S[e["segment"]]
        dl1[pd.Timestamp(e["t_cv_end"])] = L.program_dl1(g, cv_index(g, e["t_cv_end"]))[0]
    ck0 = D.ck0_curve()
    qd, vp = ck0["discharged_Ah"].to_numpy(float), ck0["voltage_V"].to_numpy(float)
    slopes = [AC.ck0_top_slope(qd, vp, w) for w in AC.S_WINDOWS_AH]
    first_after_anchor = set(pd.Timestamp(t) for t in ev.loc[ev["type"] == "A", "t_cv_end"])
    rows = []
    for _, p in pairs[pairs["type"] == "X"].iterrows():
        ei = ev[ev["event_id"] == p["i"]].iloc[0]; ej = ev[ev["event_id"] == p["j"]].iloc[0]
        t25, t45 = pd.Timestamp(ei["t_cv_end"]), pd.Timestamp(ej["t_cv_end"])
        seg45 = ev[ev["segment"] == p["seg_j"]]
        days45 = np.array([(pd.Timestamp(t) - t45).total_seconds() / 86400.0 for t in seg45["t_cv_end"]])
        row = dict(switch=p["pair"], seg_25=p["seg_i"], seg_45=p["seg_j"], month=p["month"],
                   idle_h=p["boundary_s"] / 3600.0, event_25=p["i"], event_45=p["j"], t_25=t25, t_45=t45,
                   X_admissible=bool(p["admissible"]))
        for name, src in (("A3", a3), ("DL1", dl1)):
            d25, d45 = src.get(t25, np.nan), src.get(t45, np.nan)
            ok = t25 not in first_after_anchor and t45 not in first_after_anchor and np.isfinite(d25) and np.isfinite(d45)
            dep45 = np.array([src.get(pd.Timestamp(t), np.nan) for t in seg45["t_cv_end"]])
            jj = L.step_jump(d25, t25, d45, t45, days45, dep45)
            row.update({f"d25_{name}": d25, f"d45_{name}": d45, f"r45_{name}": jj["r45"], f"dt_days": jj["dt_days"],
                        f"J_raw_{name}": jj["raw"], f"J_{name}": jj["J"] if ok else np.nan,
                        f"n45_{name}": int(np.isfinite(dep45).sum())})
        t2 = tm[tm["pair"] == p["pair"]]
        row["Term2"] = float(t2["value_main"].iloc[0]) if len(t2) else np.nan
        row["Term2_lam25"] = float(t2["value_lam25"].iloc[0]) if len(t2) else np.nan
        row["Term2_lam45"] = float(t2["value_lam45"].iloc[0]) if len(t2) else np.nan
        dv = ej["pack_V_prepulse"] - ei["pack_V_prepulse"]
        dtemp = ej["temp_mean_prepulse_C"] - ei["temp_mean_prepulse_C"]
        e3 = AC.term2_e3(dv, dtemp, slopes)
        cells_cv = lambda e: D.CELLS[int(np.argmax([e[f"cell{c}_V_cv_end"] for c in range(1, 5)]))][:5]
        row.update(dV_mV=1000.0 * dv, dT_K=dtemp, s_main_V_per_Ah=slopes[0], Term2_E3=e3["point"],
                   Term2_E3_lo=e3["lo"], Term2_E3_hi=e3["hi"],
                   top_cell_cv_end_25=cells_cv(ei), top_cell_cv_end_45=cells_cv(ej),
                   top_cell_prepulse_25=ei["top_cell_prepulse"], top_cell_prepulse_45=ej["top_cell_prepulse"],
                   spread_prepulse_25_mV=1000.0 * ei["spread_V_prepulse"], spread_prepulse_45_mV=1000.0 * ej["spread_V_prepulse"])
        rows.append(row)
    e = pd.DataFrame(rows)
    e.to_csv(os.path.join(OUT, "e2_e3.csv"), index=False, float_format="%.6g")
    a0 = ev[(ev["type"] == "A") & (ev["anchor_k"] == 0)].iloc[0]
    extra = dict(s_windows=dict(zip([str(w) for w in AC.S_WINDOWS_AH], slopes)),
                 dUdT_assumption_mV_per_K_per_cell=1000.0 * AC.DUDT_ASSUMED_V_PER_K,
                 anchor0_top_cell=dict(cv_end=D.CELLS[int(np.argmax([a0[f"cell{c}_V_cv_end"] for c in range(1, 5)]))][:5],
                                       prepulse=a0["top_cell_prepulse"]),
                 top_cell_by_setpoint={str(sp): dict(cv_end=ev[ev["setpoint"] == sp].apply(
                     lambda r: D.CELLS[int(np.argmax([r[f"cell{c}_V_cv_end"] for c in range(1, 5)]))][:5], axis=1).value_counts().to_dict(),
                     prepulse=ev.loc[ev["setpoint"] == sp, "top_cell_prepulse"].value_counts().to_dict()) for sp in (25, 45)},
                 median_J_A3=float(np.nanmedian(e["J_A3"])), median_J_DL1=float(np.nanmedian(e["J_DL1"])),
                 median_Term2=float(np.nanmedian(e["Term2"])),
                 median_Term2_E3=float(np.nanmedian(e["Term2_E3"])),
                 median_Term2_E3_interval=[float(np.nanmedian(e["Term2_E3_lo"])), float(np.nanmedian(e["Term2_E3_hi"]))])
    jdump(extra, "e2_e3_summary.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
    print(e.T.to_string()); print(json.dumps(extra, indent=1, default=str))


# ---- T_top ---------------------------------------------------------------------------------------------------
def time_matched_lam(pairs, S):
    """Exploratory, NOT registered: lambda of the segment with admissible TT pairs whose mid-time is nearest to the
    pair's mid-time, regardless of set point."""
    tt = pairs[(pairs["type"] == "TT") & pairs["admissible"]]
    mids = {s: S[s]["timestamp"].iloc[0] + (S[s]["timestamp"].iloc[-1] - S[s]["timestamp"].iloc[0]) / 2
            for s in sorted(tt["seg_i"].unique())}
    lams = {s: float(np.median((tt["N"] / tt["thr"])[tt["seg_i"] == s])) for s in mids}

    def f(p):
        if (tt["seg_i"] == p["seg_i"]).any() and p["type"] != "X":
            return lams[p["seg_i"]], p["seg_i"]
        tmid = pd.Timestamp(p["t_i"]) + (pd.Timestamp(p["t_j"]) - pd.Timestamp(p["t_i"])) / 2
        s = min(mids, key=lambda x: abs((mids[x] - tmid).total_seconds()))
        return lams[s], s
    return f


def ttop():
    S, ev, pairs = chain()
    tm = pd.read_csv(os.path.join(OUT, "terms.csv"))
    e = pd.read_csv(os.path.join(OUT, "e2_e3.csv"))
    res = AC.tt_residuals(pairs)
    noise = AC.g_noise(res)
    j_dvdq = float(np.nanmedian(e["J_DL1"]))
    main = AC.t_top(tm, noise, j_dvdq_median=j_dvdq)
    sens_k3 = AC.t_top(tm, noise, j_dvdq_median=j_dvdq, exclude_k=(3,))
    nog = AC.t_top(tm, noise)                              # without the G_E2 step, to show its effect
    # descriptive (registered as descriptive): pooled-lambda Term1/Term3, terms vs month, Term2 vs idle hours
    t2 = tm[tm["term"] == "Term2"].merge(e[["switch", "idle_h"]], left_on="pair", right_on="switch")
    t3 = tm[tm["term"] == "Term3"]
    sl_idle = L.theil_sen(t2["idle_h"].to_numpy(), t2["value_main"].to_numpy())[0]
    desc = dict(
        Term1_pooled_lambda=float(tm.loc[tm["term"] == "Term1", "value_pooled"].iloc[0]),
        Term3_pooled_lambda_median=float(np.median(t3["value_pooled"])),
        Term3_by_month={int(r.month): float(r.value_main) for r in t3.itertuples()},
        Term2_by_month={int(r.month): float(r.value_main) for r in t2.itertuples()},
        Term2_vs_idle_h=dict(spearman_rho=float(spearmanr(t2["idle_h"], t2["value_main"]).statistic),
                             theil_sen_slope_Ah_per_h=sl_idle,
                             table=[dict(switch=r.pair, idle_h=float(r.idle_h), Term2=float(r.value_main)) for r in t2.itertuples()]),
        Term3_vs_month_spearman=float(spearmanr(t3["month"], t3["value_main"]).statistic),
        Term2_vs_month_spearman=float(spearmanr(t2["month"], t2["value_main"]).statistic),
        lambda_by_segment={int(s): AC.lam(pairs, s, int(S[s]["chamber_temperature_C"].iloc[0]))[0] for s in sorted(S)})
    # exploratory, not registered: time-matched lambda
    f = time_matched_lam(pairs, S)
    rows = []
    for r in tm.itertuples():
        p = pairs.set_index("pair").loc[r.pair]
        lm, s = f(dict(p, pair=r.pair))
        v = p["N"] - lm * p["thr"]
        rows.append(dict(term=r.term, pair=r.pair, k=int(r.k), lam_time_matched=lm, lam_segment=int(s),
                         value=-v if r.term == "Term1" else v))
    tmx = pd.DataFrame(rows)
    expl = dict(note="exploratory, NOT registered, not used in any gate: lambda from the TT-bearing segment nearest in "
                     "time (any set point) instead of the pooled 25 degC median; shows the non-stationarity of lambda",
                Term1=float(tmx.loc[tmx["term"] == "Term1", "value"].iloc[0]),
                Term2_median=float(np.median(tmx.loc[tmx["term"] == "Term2", "value"])),
                Term3_median=float(np.median(tmx.loc[tmx["term"] == "Term3", "value"])),
                rows=tmx.to_dict("records"))
    expl["T_top"] = expl["Term1"] + expl["Term2_median"] + expl["Term3_median"]
    out = dict(protocol="v1 (wp1/protocol.sha256)",
               T_top=dict(point=main["point"], interval=[main["lo"], main["hi"]], half_width=main["half_width"],
                          status=main["status"]),
               terms=dict(Term1=main["Term1"], Term2=main["Term2"], Term3=main["Term3"]),
               gates=dict(G_noise=main["G_noise"], G_E2=main["G_E2"], G_T=main["G_T"]),
               before_G_E2=dict(point=nog["point"], interval=[nog["lo"], nog["hi"]]),
               sensitivity_exclude_k3=dict(point=sens_k3["point"], interval=[sens_k3["lo"], sens_k3["hi"]],
                                           note="identical to the main estimate: k = 3 has no admissible AT pair (recording gap)"),
               term3_event_ks=sorted(int(k) for k in t3["k"]), term2_events=list(t2["pair"]),
               E2=dict(median_J_A3=float(np.nanmedian(e["J_A3"])), median_J_DL1=j_dvdq,
                       median_J_raw_A3=float(np.nanmedian(e["J_raw_A3"]))),
               E3=dict(median_Term2_E3=float(np.nanmedian(e["Term2_E3"])),
                       median_interval=[float(np.nanmedian(e["Term2_E3_lo"])), float(np.nanmedian(e["Term2_E3_hi"]))],
                       note="not gating; s on [1.0, 3.0] Ah is negative, so the interval is unbounded below"),
               descriptive=desc, exploratory_not_registered=expl)
    jdump(out, "T_top.json")
    print(json.dumps({k: v for k, v in out.items() if k not in ("descriptive", "exploratory_not_registered")}, indent=1, default=str))
    print(json.dumps(desc, indent=1, default=str)); print(json.dumps({k: v for k, v in expl.items() if k != "rows"}, indent=1))
    print(tmx.round(4).to_string())


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    {"e1": e1, "e2e3": e2e3, "ttop": ttop}[sys.argv[1]]()
