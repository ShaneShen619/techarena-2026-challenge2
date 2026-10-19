"""WP4.5: write wp4/R13_HANDOFF.json from the registered round-12 results."""
import json, os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
J = lambda p: json.load(open(os.path.join(ST, p)))


def r(x, n=4):
    return None if x is None else round(float(x), n)


def main():
    T, B, G2, B2 = J("wp3/T_top.json"), J("wp4/budget_decision.json"), J("wp2/gates.json"), J("wp2/b2_results.json")
    S3, E1 = J("wp2/ck0_split.json"), J("wp3/e1_chain.json")
    tm = pd.read_csv(os.path.join(ST, "wp3", "terms.csv"))
    e = pd.read_csv(os.path.join(ST, "wp3", "e2_e3.csv"))
    sv = pd.read_csv(os.path.join(ST, "wp4", "SOH_variants.csv")).set_index("variant")
    cks = [f"CK{k}" for k in range(1, 8)]
    h = dict(
        round="13", source="round 12 (exp/phase2-r12-eps-level-20261019), protocol v1 registered in b3f3e7a",
        scope_note="round 12 measured the eps LEVEL (user's choice); round 11's top-of-charge drift model moves to round 13",
        decision=dict(level=B["decision"]["level"], reason=B["decision"]["reason"], action="keep SUB (6525edf)",
                      submission_changed=False),
        EPS_EXTRA_hat=dict(point=r(B["EPS_EXTRA_hat"]["point"]), interval=[r(x) for x in B["EPS_EXTRA_hat"]["interval"]],
                           width=r(B["EPS_EXTRA_hat"]["width"]), assumption_in_SUB=0.4,
                           note="T_top + a_0, endpoints added; the point would put CK2 at 100.41 % SOH (> CK0), i.e. it is an artefact"),
        T_top=dict(point=r(T["T_top"]["point"]), interval=[r(x) for x in T["T_top"]["interval"]], status=T["T_top"]["status"],
                   terms={k: dict(point=r(v["point"]), interval=[r(v["lo"]), r(v["hi"])], se=r(v["se"]))
                          for k, v in T["terms"].items()},
                   event_values={t: {str(row.pair): r(row.value_main) for row in tm[tm["term"] == t].itertuples()}
                                 for t in ("Term1", "Term2", "Term3")},
                   gates=dict(G_noise=dict(sigma_TT_25=r(T["gates"]["G_noise"]["sigma_TT_25"]),
                                           sigma_TT_45=r(T["gates"]["G_noise"]["sigma_TT_45"]), passed=T["gates"]["G_noise"]["passed"]),
                              G_E2=dict(median_J_dvdq=r(T["gates"]["G_E2"]["median_J_dvdq"]),
                                        median_Term2=r(T["gates"]["G_E2"]["median_Term2"]), consistent=T["gates"]["G_E2"]["consistent"]),
                              G_T=dict(half_width=r(T["gates"]["G_T"]["half_width"]), identified=T["gates"]["G_T"]["identified"])),
                   excluded_AT_pairs=[x["pair"] + " (" + x["reason"] + ")" for x in E1["exclusions"]],
                   exploratory_time_matched_lambda=r(T["exploratory_not_registered"]["T_top"])),
        a0=dict(point=r(S3["a0"]), interval=[r(x) for x in S3["a0_interval"]], status=S3["G_B3"]["status"],
                Dbot_minus_Cbot=r(S3["split"]["Dbot_minus_Cbot"]), h=dict(point=r(S3["h"]["point"]), lo=r(S3["h"]["lo"]), hi=r(S3["h"]["hi"])),
                h_medians={k: r(v) for k, v in S3["h_medians"].items()},
                top_split_FCK0_minus_FA0=dict(point=r(S3["top_split"]["point"]), interval=[r(x) for x in S3["top_split"]["interval"]]),
                exploratory_h1_from_anchor0={k: r(v) for k, v in S3["exploratory_not_registered"]["h1_0"].items()},
                exploratory_a0_with_h1_0={k: r(v) for k, v in S3["exploratory_not_registered"]["a0_with_h1_0"].items()},
                diagnosis="the registered h comes from 25 degC anchors; at anchor 0's own 45 degC top it is 3.7-3.9 Ah "
                          "different, so a_0 is dominated by the temperature dependence of h"),
        a3_rel=dict(value=r(G2["G_a3"]["a3_rel"]), threshold=r(G2["G_a3"]["threshold"]), same_sign=G2["G_a3"]["same_sign"],
                    per_locator={k: r(v) for k, v in G2["G_a3"]["a3_rel_per_locator"].items()},
                    identified=G2["G_a3"]["identified"],
                    candidate="SUB_A3fix (leaderboard-only): " + ", ".join(f"{c} {sv.loc['SUB_A3fix', 'd' + c + '_pp']:+.3f} pp" for c in cks)),
        H_SB=dict(status=G2["H_SB"], sigma_LOO=r(G2["G_SB"]["sigma_LOO"]), threshold=r(G2["G_SB"]["threshold"]),
                  loo_residuals={k: r(v) for k, v in G2["G_SB"]["loo_residuals"].items()},
                  anomaly_list=G2["anomaly_list"], unrelaxed_starts=G2["unrelaxed_starts"],
                  note="necessary condition only; S_k for k >= 1 is not visible"),
        SOH=dict(SUB={c: float(sv.loc["SUB", c]) for c in cks},
                 SUB_A3fix={c: float(sv.loc["SUB_A3fix", c]) for c in cks} if "SUB_A3fix" in sv.index else None),
        open_terms=[
            dict(term="drift d = F^CK_k - F^CK_0", plan="round 11's top-of-charge model: extrapolate each anchor's CV decay "
                 "beyond 5.1 A to the checkup's top; estimate delta-eps_top(k)", status="not addressed in round 12"),
            dict(term="self-discharge during the checkup rests (3.1-6.0 d windows)", status="not measured; the 25->45 degC "
                 "switch idles (6.9-25.3 h) show no self-discharge signal in Term2 (rho -0.40, n = 5)"),
            dict(term="checkup protocol and temperature", status="unknown; CK0 discharges at 5.1 A while the operating "
                 "step band is ~10 A; the CK0 top region falls 330 mV in the first Ah"),
            dict(term="lambda non-stationarity", status="per-block net Ah between equal tops drifts from -0.36 to -1.13 Ah "
                 "(lambda -0.97e-3 -> -2.82e-3), wrong sign for side reactions: a time-varying measurement bias that sets "
                 "most of T_top's width; a registered time-dependent loss rule is needed"),
            dict(term="temperature dependence of h (charge-side vs discharge-side step position)",
                 status="h(25 degC) -5.46 Ah vs exploratory h1(45 degC, anchor 0) -1.6...-1.8 Ah; a 45 degC h with an "
                        "explicit first-program correction is the missing piece for a_0"),
            dict(term="locator resolution", status="1 mV quantisation makes dV/dQ-argmax variants unstable by ~+-1 Ah per "
                 "cell on the broad charge-side step; midpoint variants and cell medians are ~0.02-0.1 Ah (synthetic)"),
            dict(term="unrecorded events before anchors 0 and 3", status="anchor 0: +84 mV/h 3.4 d after its C/20, 2 K "
                 "above set point and cooling, cells within 7 mV; anchor 3: +53 mV/h after a 3.1 d window; segment 6 "
                 "also paused twice")],
        constraints=["do not retry absolute electrode-model (DMA) reconstruction of Q_C20 (round 5B: 8-10 Ah spans)",
                     "proxy scoring is blind to the eps level by construction (P_k = Q_fc,k + eps0 + Delta)",
                     "register any new loss rule / h estimator before evaluating it"],
        probe=dict(P_level="not recommended: L3, and the measured shift (+4.08 Ah) is an artefact",
                   order="P_stress_early -> P_start -> P_drift (unchanged)",
                   SUB_A3fix="a registered single-anchor instance of P_start's question; the user decides"))
    json.dump(h, open(os.path.join(ST, "wp4", "R13_HANDOFF.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(h, indent=1, ensure_ascii=False)[:4000])


if __name__ == "__main__":
    main()
