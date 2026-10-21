"""Round-17 registered designs (wp2/protocol.json) as predictor factories ``f(ctx) -> (Q, info)``."""
import numpy as np

from eval17 import H, R3_T_CFG, W_REF
from preds5c import _MEMO, _TAB, ens, s_pred
from smodel17 import LawFit17

TAU_B0 = float(np.exp(4.901437698447246))          # prior2 mean, 134.48 d
TAU_GRID = tuple(TAU_B0 * 2.0 ** e for e in (-2, -1, 0, 1))
EA_C = 2 * 20.592                                    # WP1 P1, on time

MAIN = {
    "B0": dict(switch_fix=True),
    "S": dict(switch_fix=True, cal_soc="tum2", ck_soc="half"),
    "C": dict(cal_Ea_kJ=EA_C),
    "O2": dict(switch_fix=True, breakin="overhang", ck_soc="half"),
    "D": dict(use_cyc=False),
}
SENS = {
    "S_ckentry": dict(switch_fix=True, cal_soc="tum2", ck_soc="entry"),
    "S_ckzero": dict(switch_fix=True, cal_soc="tum2", ck_soc="zero"),
    "S_lin": dict(switch_fix=True, cal_soc="tum1", ck_soc="half"),
    "S_naumann": dict(switch_fix=True, cal_soc="naumann2", ck_soc="half"),
    "C_yagci_k": dict(cal_Ea_kJ=74.6),               # exposed-CK2
    "C_naumann": dict(cal_Ea_kJ=2 * 17.126),
    "O2_soc0_010": dict(switch_fix=True, breakin="overhang", ck_soc="half", oh=dict(soc0=0.10)),
    "O2_soc0_050": dict(switch_fix=True, breakin="overhang", ck_soc="half", oh=dict(soc0=0.50)),
    "O2_fitline": dict(switch_fix=True, breakin="overhang", ck_soc="half", oh=dict(line="fitted")),
    "O2_x0eq": dict(switch_fix=True, breakin="overhang", ck_soc="half", oh=dict(x0="eq")),
}


def law(name, r17):
    return s_pred(name, cls=LawFit17, cfg=dict(R3_T_CFG, **r17), uses_steps=True)


_O1 = {}


def o1_fit(ctx):
    """Per case: predictions and Laplace log-evidence at every tau_b of the grid."""
    key = (ctx["key"], ctx["delta"], ctx["step"], ctx["a4s"])
    if key not in _O1:
        qs, lz = [], []
        for tb in TAU_GRID:
            m = LawFit17(dict(R3_T_CFG, tau_b_days=tb))
            q, info = m.run(ctx["op"], ctx["fc"], ctx["ck"], ctx["at_date"], ctx["eps"], tab_cache=_TAB,
                            key=ctx["key"], steps=ctx["steps"][ctx["step"]], a4=ctx["a4"][ctx["a4s"]], return_fit=True)
            qs.append(q)
            lz.append(info["logZ"])
        lz = np.array(lz)
        w = np.exp(lz - lz.max())
        _O1[key] = (np.array(qs), w / w.sum())
    return _O1[key]


def o1(uniform=False):
    def f(ctx):
        qs, w = o1_fit(ctx)
        if uniform:
            w = np.full(len(qs), 1 / len(qs))
        return float(qs @ w), {"w_top": float(w.max()), "tau_top": float(TAU_GRID[int(np.argmax(w))])}
    return f


def predictors(names=None, with_ens=True, sens=False):
    P = {"R3_T": law("R3_T", {})}
    for n, c in MAIN.items():
        P[n] = law(n, c)
    P["O1"] = o1()
    if sens:
        for n, c in SENS.items():
            P[n] = law(n, c)
        P["O1_uniform"] = o1(uniform=True)
    if names is not None:
        P = {n: f for n, f in P.items() if n in names or n == "R3_T"}
    if with_ens:
        for n in list(P):
            P[n + "_ens"] = ens(P[n], W_REF)
    if "R3_T_ens" in P:
        P["REF"] = P.pop("R3_T_ens")
    P["V2"] = H.v2_pred
    return P


def tau_grid_preds():
    """Each tau_b grid member as its own predictor (for O1 reporting)."""
    return {f"O1_tb{tb:.1f}": law(f"O1_tb{tb:.1f}", dict(tau_b_days=tb)) for tb in TAU_GRID}
