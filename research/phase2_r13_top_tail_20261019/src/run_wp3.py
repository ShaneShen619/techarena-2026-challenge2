"""WP3: apply the registered decision rules (tail.decide) to the WP2 measurements; leaderboard-only SOH variants with the
copied round 11 drift.py; R13_RESULT.json. Usage: python3 -B run_wp3.py <study_dir>"""
import importlib.util, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail  # noqa: E402

ST = sys.argv[1]
W2, W3 = os.path.join(ST, "wp2"), os.path.join(ST, "wp3")
os.makedirs(W3, exist_ok=True)
spec = importlib.util.spec_from_file_location("r11_drift", os.path.join(ST, "sources", "r11_drift.py"))
drift = importlib.util.module_from_spec(spec); spec.loader.exec_module(drift)

pairs = pd.read_csv(os.path.join(W2, "pairs.csv"))
tsl = pd.read_csv(os.path.join(W2, "top_state_slopes.csv"))
tails = pd.read_csv(os.path.join(W2, "tails.csv"))
ts = pd.read_csv(os.path.join(W2, "top_state.csv"))
fits = pd.read_csv(os.path.join(W2, "fits.csv"))

# 1) registered decision
A = tail.admitted_set(pairs, tsl)
dec = tail.decide(A)
slopes = {n: m["slope"] for n, m in A.items()}
d_min, d_max = min(slopes.values()), max(slopes.values())
d_med = dec["d_tail"]                                  # median over A without C1 (D12)
others = [n for n in A if n != "C1"]

# 2) leaderboard-only SOH variants (never scored against proxies)
sub = pd.read_csv(os.path.join(ST, "wp0", "SUB_SOH.csv"))
ck = sub.checkup.tolist()
rows = [dict(variant="SUB", d=0.0, **dict(zip(ck, sub.SOH_est.round(3))))]
for lab, d in (("SUB + d_min (min over A)", d_min), ("SUB + d_median (median over A without C1 = d_tail)", d_med),
               ("SUB + d_max (max over A)", d_max)):
    rows.append(dict(variant=lab, d=d, **dict(zip(ck, np.round(drift.add_drift(sub.SOH_est.to_numpy(float), d), 3)))))
var = pd.DataFrame(rows)
var.to_csv(os.path.join(W3, "SOH_variants.csv"), index=False)

# 3) unregistered diagnostics (reported, never used for the outcome)
diag = {}
no_t2 = {n: m for n, m in A.items() if n != "T2"}
diag["without_T2"] = {k: tail.decide(no_t2)[k] for k in ("outcome", "label", "envelope_Ah", "median_abs_effect_Ah_without_C1", "d_tail")}
for win in ("w025_1",):
    r = tsl[(tsl.estimator == "T2") & (tsl.unit == "pack") & (tsl.window == win)].iloc[0]
    alt = dict(A); alt["T2"] = dict(slope=float(r.slope), loo_min=float(r.loo_min), loo_max=float(r.loo_max))
    diag[f"T2_window_{win}"] = {k: tail.decide(alt)[k] for k in ("outcome", "label", "envelope_Ah", "median_abs_effect_Ah_without_C1", "d_tail")}
diag["envelope_tail_models_only_Ah"] = round(max(slopes[n] for n in A if n.startswith("M")) * tail.FADE_CK7 - 0.0, 6)

# 4) per-anchor table
a = tails[(tails.type == "A") & tails.anchor.notna()].copy(); a["anchor"] = a.anchor.astype(float).astype(int)
a = a[a.anchor.between(1, 7) & (a.model == "M4")]
qt = a.pivot_table(index="anchor", columns="scenario", values="Q_tail_Ah")
dt = a.pivot_table(index="anchor", columns="scenario", values="Delta_tail_Ah")
t2 = ts[(ts.estimator == "T2") & (ts.unit == "pack") & (ts.window == "main")].set_index("anchor")
t3 = ts[ts.estimator == "T3"].set_index("anchor")
fa = fits[fits.type == "A"].copy(); fa["anchor"] = fa.anchor.astype(float).astype(int)
per_anchor = []
for k in tail.ANCHORS:
    per_anchor.append(dict(anchor=k, fade_Ah=float(t2.fade_Ah[k]),
                           admitted_models=",".join(fa[(fa.anchor == k) & fa.admitted].model),
                           M4_Q_tail_Ah={c: float(qt.loc[k, c]) for c in tail.SCENARIOS},
                           M4_Delta_tail_Ah={c: float(dt.loc[k, c]) for c in tail.SCENARIOS},
                           V30_pack_V=float(t2.V30[k]), T2_minus_dF_V_Ah=float(t2.d_eps_Ah[k]),
                           R_pack_mOhm=float(t3.R_pack_mOhm[k]), T3_d_eps_Ah=float(t3.d_eps_Ah[k])))

m1 = json.load(open(os.path.join(W2, "measurements.json")))["backenv_M1"]
t2r = {w: tsl[(tsl.estimator == "T2") & (tsl.unit == "pack") & (tsl.window == w)].iloc[0] for w in ("main", "w025_1", "w1_3")}
t3r = tsl[tsl.estimator == "T3"].iloc[0]
res = dict(
    round=13, source="exp/phase2-r13-top-tail-20261019", protocol_commit="7960a99",
    outcome=dec["outcome"], label=dec["label"], identifiable=dec["identifiable"],
    envelope_Ah=dec["envelope_Ah"], envelope_threshold_Ah=0.30,
    admitted_set={n: dict(slope=A[n]["slope"], effect_CK7_Ah=dec["effects_Ah"][n], loo_effect_CK7_Ah=dec["loo_Ah"][n]) for n in A},
    d_tail=dict(median_without_C1=d_med, min_over_A=d_min, max_over_A=d_max,
                effect_CK7_Ah=dict(median=d_med * tail.FADE_CK7, min=d_min * tail.FADE_CK7, max=d_max * tail.FADE_CK7),
                median_abs_effect_without_C1_Ah=dec["median_abs_effect_Ah_without_C1"]),
    T2=dict(main=dict(s_top_V_per_Ah=float(t2r["main"].s_top_V_per_Ah), slope=float(t2r["main"].slope),
                      loo=[float(t2r["main"].loo_min), float(t2r["main"].loo_max)], effect_CK7_Ah=float(t2r["main"].effect_CK7_Ah)),
            sensitivity_w025_1=dict(s_top_V_per_Ah=float(t2r["w025_1"].s_top_V_per_Ah), slope=float(t2r["w025_1"].slope),
                                    effect_CK7_Ah=float(t2r["w025_1"].effect_CK7_Ah)),
            sensitivity_w1_3=dict(s_top_V_per_Ah=float(t2r["w1_3"].s_top_V_per_Ah), note="s_top < 0 on the CK0 plateau: not invertible"),
            V30_resolution_note="1 mV of V30 = 0.045 Ah under the main-window s_top"),
    T3=dict(slope=float(t3r.slope), loo=[float(t3r.loo_min), float(t3r.loo_max)], effect_CK7_Ah=float(t3r.effect_CK7_Ah), role="check only"),
    models_admitted_on_anchors_1_7={m: int(fa[(fa.model == m) & fa.anchor.between(1, 7)].admitted.sum()) for m in tail.MODELS},
    M1_back_of_envelope=m1,
    undefined_pairs="M2 x C2-C4 at every anchor (Iinf 3.6-4.2 A >= cutoff); M2 is not admitted on anchors 1-7 anyway",
    topup_cross_check="M4 monthly median Q_tail of 25 C top-ups flat (C4 0.31-0.36 Ah, months 1-6); descriptive slope +0.003 Ah at CK7; not used",
    ck0_top_cell="cell3 is the top cell at CK0's start (lead 137 mV) and at every anchor's CV end (51->20 mV), +30 min (14->7 mV) and pulse (12->5 mV)",
    per_anchor=per_anchor,
    soh_variants=var.to_dict("records"),
    unregistered_diagnostics=dict(diag, note="post-hoc; reported for rounds 14/15, never used for the outcome"),
    recommendation=("SUB unchanged. No candidate (O3). The top-tail part of the eps drift is bounded by the admitted set to "
                    "[0, +0.41] Ah at CK7; the tail models alone give +0.04..+0.12 Ah, all positive, and exactly 0 if the checkup "
                    "terminates its CV at 5.1 A like the anchor (C1). The top-tail motivation for P_drift is not removed."),
    for_round_14="the anchor tail grows (step anchor 1 -> 2, then slow rise) while 25 C top-up tails do not: a from-empty path effect candidate",
    for_round_15="the open variable is the checkup's CV termination; a probe or organiser answer on it collapses the envelope to one scenario",
    no_proxy_statement="No rule or output used P_k or any proxy error.")
json.dump(res, open(os.path.join(W3, "R13_RESULT.json"), "w"), indent=1, default=float)
json.dump(dict(dec, admitted_members=list(A)), open(os.path.join(W3, "decision.json"), "w"), indent=1, default=float)

pd.set_option("display.width", 250)
print(json.dumps({k: dec[k] for k in ("outcome", "label", "envelope_Ah", "identifiable", "d_tail", "median_abs_effect_Ah_without_C1", "effects_Ah", "loo_Ah")}, indent=1))
print("d_min", d_min, "d_med", d_med, "d_max", d_max)
print(var.to_string(index=False))
print(json.dumps(diag, indent=1))
