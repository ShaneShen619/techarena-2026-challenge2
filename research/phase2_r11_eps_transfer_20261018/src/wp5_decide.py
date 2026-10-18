"""WP5: registered transfer, bounds, decision, SOH variants and the round-12 hand-off. Usage: python3 -B wp5_decide.py <study_dir>"""
import json, os, sys
import numpy as np
import pandas as pd

ST = sys.argv[1]; sys.path.insert(0, os.path.join(ST, "src"))
from drift import add_drift

lic = json.load(open(os.path.join(ST, "wp2/lic_stats.json")))
ext = json.load(open(os.path.join(ST, "wp3/ext_stats.json")))
fac = json.load(open(os.path.join(ST, "wp4/pack_driver_trends.json")))
FADE = 8.2
if fac["factor_1_condition"] and not fac["factor_0_condition"]:
    F = [1.0]
elif fac["factor_0_condition"] and not fac["factor_1_condition"]:
    F = [0.0]
else:
    F = [0.0, 1.0]                     # linear in f, so the extremes bound the interval


def terms(variant, lic_key="transfer_slope"):
    g = ext[variant]["groups"]
    lic_t = {t: (lic[t][lic_key] if lic_key == "transfer_slope" else lic[t]["no_flagged"]["transfer_slope"]) for t in ("T_CE", "T_path")}
    return {"LIC": lic_t, "Yagci35": {t: g["Yagci35"][t]["transfer"] for t in ("T_CE", "T_path")},
            "Yagci50": {t: g["Yagci50"][t]["transfer"] for t in ("T_CE", "T_path")}}


def bounds(tm):
    names = list(tm)
    pools = {"all": names, **{f"drop_{n}": [m for m in names if m != n] for n in names}}
    rows = []
    for pn, members in pools.items():
        dce = float(np.median([tm[m]["T_CE"] for m in members])); dpa = float(np.median([tm[m]["T_path"] for m in members]))
        for f in F:
            rows.append(dict(pool=pn, f=f, d_CE=dce, d_path=dpa, d=dce + f * dpa))
    r = pd.DataFrame(rows)
    allm = r[r.pool == "all"]
    dce, dpa = allm.d_CE.iloc[0], allm.d_path.iloc[0]
    share = {"T_CE": abs(dce) / (abs(dce) + abs(dpa)), "T_path": abs(dpa) / (abs(dce) + abs(dpa))}
    return dict(table=r.to_dict("records"), d_lo=float(r.d.min()), d_hi=float(r.d.max()),
                all_median_interval=[float(allm.d.min()), float(allm.d.max())], pooled=dict(d_CE=dce, d_path=dpa), share=share,
                dominant=max(share, key=share.get) if max(share.values()) > 0.6 else "mixed")


def decide(lo, hi):
    if -0.012 <= lo and hi <= 0.012:
        return "O1"
    if hi < -0.015:
        return "O2"
    return "O3"


main = bounds(terms("all_checkups"))
main["outcome"] = decide(main["d_lo"], main["d_hi"])
sens = {"yagci_without_checkup0": bounds(terms("without_checkup0")),
        "lic_without_flagged": bounds(terms("all_checkups", "no_flagged")),
        "both": bounds(terms("without_checkup0", "no_flagged"))}
for v in sens.values():
    v["outcome"] = decide(v["d_lo"], v["d_hi"]); v["outcome_all_median_only"] = decide(*v["all_median_interval"])
main["outcome_all_median_only"] = decide(*main["all_median_interval"])
step_info = {t: dict(winner=lic[t]["bic"]["winner"], step_c=lic[t]["bic"]["c"]["step"]) for t in ("T_CE", "T_path", "eps_total")}
point = None if len(F) > 1 else main["pooled"]["d_CE"] + F[0] * main["pooled"]["d_path"]
sub = pd.read_csv(os.path.join(ST, "wp0/SUB_SOH.csv"), index_col=0).iloc[0]
cks = [f"CK{k}" for k in range(1, 8)]
ds = sorted({round(main["d_lo"], 4), round(main["d_hi"], 4), -0.031} | ({round(point, 4)} if point is not None else set()))
tab = pd.DataFrame({"SUB": sub[cks].values, **{f"SUB+drift{d:+.4f}": add_drift(sub[cks].values, d) for d in ds}}, index=cks).T.round(3)
tab.to_csv(os.path.join(ST, "wp5/SOH_variants.csv"))
probe = {"O1": "keep SUB; move P_drift last or drop it", "O2": "P_drift becomes the first probe; report states the bias",
         "O3": "keep round 7's order: P_stress_early -> P_start -> P_drift"}[main["outcome"]]
out = dict(factor_set=F, main=main, sensitivities=sens, lic_step_models=step_info, point_value=point,
           ck7_shift_pp=dict(d_lo=main["d_lo"] * FADE / 1.02, d_hi=main["d_hi"] * FADE / 1.02),
           gotion_total_consistency=ext["gotion_cell"]["eps_total"]["transfer"], probe_recommendation=probe)
json.dump(out, open(os.path.join(ST, "wp5/decision.json"), "w"), indent=1)
handoff = dict(
    round="12", source="round 11 (exp/phase2-r11-eps-transfer-20261018)", outcome=main["outcome"],
    dominant_term=main["dominant"] + (" (LIC alone: T_path 97 %)" if main["dominant"] == "T_path" else ""),
    d_interval=[main["d_lo"], main["d_hi"]], all_median_interval=main["all_median_interval"],
    terms={"T_CE": dict(identifiable_in=["LIC", "Yagci35", "Yagci50"], lic_slope=lic["T_CE"]["transfer_slope"],
                        pack_drivers="none measurable (pack CE not measurable: per-block balance does not close)"),
           "T_path": dict(identifiable_in=["LIC", "Yagci35", "Yagci50"], lic_slope=lic["T_path"]["transfer_slope"],
                          lic_drivers="top state of the operating charge: CV duration/Ah, end current, relaxed top voltage (start voltage not a driver)",
                          pack_drivers={"CV_Ah": "trends like LIC (rho +0.93)", "I_end": "flat 5.094-5.100 A (LIC falls)",
                                        "V_pack_30min": "13.439 -> 13.435 V (LIC rises)", "tau_CV_s": "179 -> 217 s"},
                          round12_model="top-of-charge model: extrapolate each anchor's CV decay beyond 5.1 A to the checkup's top; estimate delta-eps_top(k)")},
    not_assessed_this_round=["cell imbalance under pack-voltage cutoffs (bottom spread 22 -> 35 mV, top spread 88 -> 52 mV)",
                             "the 25 C offset Delta (EPS_EXTRA_AH 0.4)", "coulombic efficiency of this pack",
                             "bottom (start) state: start voltage rises 11.805 -> 11.921 V over anchors 1-7",
                             "checkup charge protocol (CV voltage / cutoff) and checkup temperature"],
    flagged_anchors={"0": "seg1: 45 C, 0.5 h rest, unrelaxed (+84 mV/h); CV fit fails (36 s CV)", "3": "seg6: unrelaxed start (+53 mV/h)"},
    constraints=["do not retry absolute electrode-model (DMA) reconstruction of Q_C20 (round 5B: 8-10 Ah spans)",
                 "model only delta-eps_k of one term at a time with the pack's own CK0 per-cell C/20 curves and measured drivers",
                 "identifiability gate first: envelope of delta-eps_k < 0.3 Ah or exit"])
json.dump(handoff, open(os.path.join(ST, "wp5/R12_HANDOFF.json"), "w"), indent=1)
print(json.dumps({k: main[k] for k in ("d_lo", "d_hi", "all_median_interval", "pooled", "share", "dominant", "outcome", "outcome_all_median_only")}, indent=1))
for k, v in sens.items(): print(k, round(v["d_lo"], 4), round(v["d_hi"], 4), [round(x, 4) for x in v["all_median_interval"]], v["outcome"], v["outcome_all_median_only"], v["dominant"])
print(pd.DataFrame(main["table"]).round(4).to_string(index=False)); print(tab.to_string()); print(out["ck7_shift_pp"], probe)
