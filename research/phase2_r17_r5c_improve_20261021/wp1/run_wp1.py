"""WP1: external parameters (frozen before any design run) and the P2 k_SOC data check.

Reads only literature values (transcribed below with page/equation) and the TUM Sony LFP calendar data.
No pack data, no proxies.  Usage: python3 -I -B run_wp1.py TUM_DIR
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
TUM = sys.argv[1]
R = 8.314462618
F = 96485.0


# ---------------------------------------------------------------- P2 functional forms
def k_soc_naumann(soc):
    """Naumann 2018 Eq. (12), Table 7 (Q_loss column): c (SOC - 0.5)^3 + d, SOC as a fraction."""
    return 2.8575 * (np.asarray(soc, float) - 0.5) ** 3 + 0.60225


def _ua_safari(x):
    """Schimpe 2018 Eq. (A1): graphite OCP vs lithiation (Safari et al.)."""
    return (0.6379 + 0.5416 * np.exp(-305.5309 * x) + 0.044 * np.tanh(-(x - 0.1958) / 0.1088)
            - 0.1978 * np.tanh((x - 1.0571) / 0.0854) - 0.6875 * np.tanh((x + 0.0117) / 0.0529)
            - 0.0175 * np.tanh((x - 0.5692) / 0.0875))


def k_soc_schimpe(soc):
    """Schimpe 2018 Eqs. (8)/(9) with (A2) and Table AI, up to the constant k_Cal,Ref."""
    xa = 8.5e-3 + np.asarray(soc, float) * (7.8e-1 - 8.5e-3)
    ua_ref = 0.123
    return np.exp(0.384 * F * (ua_ref - _ua_safari(xa)) / (R * 298.15)) + 0.142


# ---------------------------------------------------------------- TUM data check
def tum_amplitudes():
    raw = pd.read_excel(os.path.join(TUM, "DischargeCapacity.xlsx"), header=None)
    names = raw.iloc[1, 1:].tolist()
    body = raw.iloc[2:].astype(float)
    t = body.iloc[:, 0].to_numpy() / 24.0
    q = body.iloc[:, 1:].to_numpy()
    rows = []
    for j, n in enumerate(names):
        T = float(n.split("_")[1].split("°C")[0])
        soc = float(n.split(",")[1].replace("%SOC", "")) / 100
        loss = q[0, j] - q[:, j]
        m = (t > 0) & (t <= 400) & np.isfinite(loss)
        b = float((np.sqrt(t[m]) * loss[m]).sum() / t[m].sum())   # pure sqrt(t) through the origin
        rows.append(dict(name=n, T_C=T, soc=soc, amp_Ah_per_sqrtd=b, n_pts=int(m.sum())))
    return pd.DataFrame(rows)


def main():
    amp = tum_amplitudes()
    tab = []
    for T in (25.0, 40.0):
        a = amp[amp["T_C"] == T].set_index("soc")["amp_Ah_per_sqrtd"]
        for s, v in a.items():
            tab.append(dict(T_C=T, soc=s, norm=v / a.loc[0.5]))
    tab = pd.DataFrame(tab)
    cmp = []
    for s in sorted(tab["soc"].unique()):
        v = tab[tab["soc"] == s]
        tum = float(v["norm"].mean())
        cmp.append(dict(soc=s, tum_norm=tum, n_temps=int(len(v)), temps="/".join(f"{x:g}" for x in v["T_C"]),
                        naumann_norm=float(k_soc_naumann(s) / k_soc_naumann(0.5)),
                        schimpe_norm=float(k_soc_schimpe(s) / k_soc_schimpe(0.5))))
    cmp = pd.DataFrame(cmp)
    cmp["naumann_over_tum"] = cmp["naumann_norm"] / cmp["tum_norm"]
    cmp["schimpe_over_tum"] = cmp["schimpe_norm"] / cmp["tum_norm"]
    sel = cmp[cmp["soc"] >= 0.125]
    naumann_ok = bool(((sel["naumann_over_tum"] - 1).abs() <= 0.30).all())
    amp.to_csv(os.path.join(OUT, "tum_sqrt_amplitudes.csv"), index=False)
    cmp.to_csv(os.path.join(OUT, "k_soc_comparison.csv"), index=False)

    # ---------------------------------------------------------------- P1
    ea_schimpe, ea_naumann = 20.592, 17.126
    rel = abs(ea_schimpe - ea_naumann) / ea_schimpe
    p1 = ea_schimpe if rel <= 0.20 else ea_naumann

    # ---------------------------------------------------------------- P3
    tf = {50.0: 100.0, 40.0: 250.0, 30.0: 490.0}           # Lewerenz 2018 p. 157 (sec. 4.6, Fig. 12b)
    invT = np.array([1 / (T + 273.15) for T in tf])
    lnd = np.log(np.array(list(tf.values())))
    slope, icpt = np.polyfit(invT, lnd, 1)
    ea_fit = slope * R / 1e3

    def t_full_stated(T):
        return 100.0 * np.exp(64.5e3 / R * (1 / (T + 273.15) - 1 / 323.15))

    def t_full_fit(T):
        return float(np.exp(icpt + slope / (T + 273.15)))

    p3 = {
        "f_oh_sony": dict(value=0.062, unit="fraction of coated anode area", source="Naumann 2018 p. 156 sec. 2.1, Table 3",
                          note="stated 6.2 %; Table 3 areas sum 88.46 cm2 over (150.2+142.1) x 5.7 cm2 = 5.3 %; stated value used"),
        "f_oh_lewerenz": dict(value=0.09, source="Lewerenz 2018 p. 151 sec. 2.2, Eq. (3), Fig. 3", cell="25 Ah NMC prismatic"),
        "reversible_relation": "Delta C = (SOC_t0 - SOC_test) * (A_anode/A_cathode - 100 %); Lewerenz 2018 p. 155 Eq. (3)/(4), Table 4 (SOC_t0 = 6 %)",
        "t_full_days": dict(value=tf, source="Lewerenz 2018 p. 157 sec. 4.6: PH^MinHi rises after ~100 d (50 C), ~250 d (40 C), ~490 d (30 C)",
                            note="the 2026-10-16 notes said 150 d at 50 C; the PDF text says 100 d"),
        "Ea_comp_kJ": dict(value=64.5, source="Lewerenz 2018 p. 157 Eq. (5)", on="compensation duration d (Arrhenius)"),
        "Ea_comp_fit_three_points_kJ": float(ea_fit),
        "tau_rule": "tau_oh(T) = t_full(T)/3 from the stated-Ea line through (50 C, 100 d); fitted line = sensitivity",
        "tau_oh_days": {f"{T:g}C": dict(stated=float(t_full_stated(T) / 3), fitted=float(t_full_fit(T) / 3)) for T in (25.0, 45.0)},
        "Ea_tau_kJ_main": 64.5, "t_full_ref": dict(T_C=50.0, days=100.0),
        "Ea_tau_kJ_sens": float(ea_fit), "t_full_fit_line": dict(slope_K=float(slope), intercept=float(icpt)),
        "A_oh_prior": "logA_oh ~ N(ln(f_oh * (SOC_op_mean - SOC_0) * Q_nom), ln 2), f_oh = 0.062, SOC_0 = 0.30",
    }

    params = {
        "frozen": "2026-10-21, WP1 of round 17; do not edit after commit",
        "P1_calendar_Ea_on_k": dict(
            schimpe=dict(value_kJ=ea_schimpe, source="Schimpe 2018 JES 165 A181, p. A184 Eq. (4)",
                         note="fitted to stress factors at SOC = 100 %; Q_L,Cal = k_Cal(T, SOC) sqrt(t), Eq. (2)", on="k"),
            naumann=dict(value_kJ=ea_naumann, source="Naumann 2018 J. Energy Storage 17:153, p. 163 Table 7, Eq. (5)",
                         note="Q_loss = k_temp(T) k_SOC(SOC) sqrt(t), Eq. (3)", on="k"),
            rel_diff_vs_primary=rel, rule="use Schimpe unless the values differ by > 20 % of the primary (Schimpe)",
            chosen_kJ=p1, Ea_time_for_C_kJ=2 * p1,
            why_double="with Naumann's virtual-time rule (Eq. 17) Q = sqrt(sum k^2 dt), so a factor on k enters the clock squared"),
        "P2_k_SOC": dict(
            naumann=dict(form="c (SOC - 0.5)^3 + d", c=2.8575, d=0.60225,
                         source="Naumann 2018 p. 164 Eq. (12), Table 7; fitted at 40 C, t_end = 29 months"),
            schimpe=dict(form="exp(alpha F (Ua_ref - Ua(SOC)) / (R T_ref)) + k0", alpha=0.384, k0=0.142, Ua_ref_V=0.123,
                         xa0=8.5e-3, xa100=0.78, source="Schimpe 2018 p. A184 Eqs. (8)-(9), Appendix Eqs. (A1)-(A2), Table AI"),
            tum_check=dict(file="DischargeCapacity.xlsx (sha c684bdb2...)", fit="pure sqrt(t) through origin, 0-400 d",
                           rule="paper function if |naumann/TUM - 1| <= 0.30 at every TUM SOC 12.5-100 %",
                           naumann_ok=naumann_ok,
                           max_abs_dev=float((sel["naumann_over_tum"] - 1).abs().max())),
            chosen="naumann" if naumann_ok else "tum_table",
            alt="tum_table" if naumann_ok else "naumann",
            tum_table={f"{s:g}": float(v) for s, v in zip(cmp["soc"], cmp["tum_norm"])},
            clock_use="the clock weight is k_SOC(SOC)^2 (virtual-time consistency, see P1.why_double); linear k_SOC = sensitivity"),
        "P3_overhang": p3,
        "P4_cycle": dict(
            source="Naumann 2020 J. Power Sources 451:227666, sec. 3.2.1, 3.3.2",
            finding="partly reversible accelerated loss only in static shallow cycles (DOC < 80 %); 'a phenomenon which needs to be "
                    "investigated more thoroughly' (p. 6-7); dynamic profiles at 40 C: pure cycle share 28.35 % (PV-HESS) and "
                    "2.61 % (PV-PCR-BESS) of combined loss; calendar part matches the 40 C / 50 % SOC static test",
            use="label for D only"),
        "P5_transfer": {
            "P1": "Sony US26650FTC1 3 Ah LFP/C (both sources); pack is 102 Ah prismatic LFP of unknown make",
            "P2": "Sony 3 Ah; k_SOC shape follows graphite potential, expected to transfer in shape, not amplitude",
            "P3": "Lewerenz: 25 Ah NMC/C prismatic, 9 % overhang; anode-side mechanism transfers, geometry does not",
            "P4": "Sony 3 Ah, 40 C; pack runs 25/45 C with deep 56 Ah discharges every block",
        },
    }
    with open(os.path.join(OUT, "external_params.json"), "w") as f:
        json.dump(params, f, indent=1, ensure_ascii=False)
    print(cmp.round(3).to_string())
    print(json.dumps({k: params["P2_k_SOC"]["tum_check"][k] for k in ("naumann_ok", "max_abs_dev")}))
    print("P1", p1, rel, "P3 tau", p3["tau_oh_days"], "Ea fit", ea_fit)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        s = np.linspace(0, 1, 101)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(s * 100, k_soc_naumann(s) / k_soc_naumann(0.5), label="Naumann 2018 Eq. 12")
        ax.plot(s * 100, k_soc_schimpe(s) / k_soc_schimpe(0.5), label="Schimpe 2018 Eq. 8")
        for T, mk in ((25.0, "s"), (40.0, "o")):
            v = tab[tab["T_C"] == T]
            ax.plot(v["soc"] * 100, v["norm"], mk, label=f"TUM data {T:g} C (sqrt fit, 0-400 d)")
        ax.set_xlabel("SOC / %")
        ax.set_ylabel("k_SOC / k_SOC(50 %)")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, "k_soc_comparison.png"), dpi=120)
    except Exception as e:  # plotting is optional
        print("plot skipped:", e)


if __name__ == "__main__":
    main()
