"""Stage 1d: synthetic identifiability (protocol.json synthetic_1d). No real-data proxy is used."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from emodel import OCP, fit_charge, start_state  # noqa: E402
from epack import beta_E, pack_quantities, restart, start_ocv  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
P = json.load(open(os.path.join(HERE, "protocol.json")))["synthetic_1d"]
rng = np.random.default_rng(20261014)
ocp = OCP("main")
R_TRUE, H_TRUE, ETA = 0.002, 0.010, 0.015
OFFS = [-0.004, 0.0, 0.002, 0.005]


def truth_bol():
    cells = []
    for o in OFFS:
        qn, qp, tn, tp = 143.0, 106.0, 0.16 + o, 0.93
        cells.append(np.array([qn, qp, tn * qn + tp * qp, tn, R_TRUE, H_TRUE]))
    return cells


def generate(cells, dt=10.0, I_cc=20.4):
    """Model CCCV at 10 s steps (CC 20.4 A, CV at 14.0 V until 5.1 A); returns q, I, V (n x 4)."""
    q, qs, Is, Vs = 0.0, [], [], []
    hps = [tuple(x[:4]) for x in cells]
    cv = False
    for _ in range(100000):
        U = np.array([ocp.ocv(q, hp) for hp in hps])
        if not cv:
            I = I_cc
            if U.sum() + I * sum(x[4] for x in cells) + sum(x[5] for x in cells) >= 14.0:
                cv = True
        if cv:
            I = (14.0 - U.sum() - sum(x[5] for x in cells)) / sum(x[4] for x in cells)
            if I <= 5.1:
                break
        V = U + np.array([x[4] for x in cells]) * I + np.array([x[5] for x in cells])
        qs.append(q); Is.append(I); Vs.append(V)
        q += I * dt / 3600.0
    return np.array(qs), np.array(Is), np.array(Vs)


def noisy(V):
    n = V.shape[0]
    out = V.copy()
    for c in range(V.shape[1]):
        w = rng.normal(0, 0.002, n)
        ar = np.zeros(n)
        e = rng.normal(0, 0.002 * np.sqrt(1 - 0.9 ** 2), n)
        for i in range(1, n):
            ar[i] = 0.9 * ar[i - 1] + e[i]
        out[:, c] += w + ar + rng.uniform(-0.003, 0.003)
    return out


def fit_event(cells_true):
    q, I, V = generate(cells_true)
    Vn = noisy(V)
    keep = q >= 2.0
    fits = [fit_charge(q[keep], I[keep], Vn[keep, c], ocp)[0] for c in range(4)]
    return fits


ref_true = truth_bol()
v_start_ref = [start_ocv(x, ocp) for x in ref_true]
ref_fit = fit_event(ref_true)
v_start_fit = [start_ocv(x, ocp) for x in ref_fit]
rows = []
for s in range(30):
    lli = rng.uniform(0, 8)
    lne = rng.uniform(0, 0.05)
    lpe = rng.uniform(0, 0.05)
    shift = rng.uniform(-0.030, 0.030)
    deg = []
    for x, v0 in zip(ref_true, v_start_ref):
        y = x.copy()
        y[0] *= (1 - lne)
        y[1] *= (1 - lpe)
        y[2] -= lli
        y[3] = start_state(None, ocp, v0 + shift, y[0], y[1], y[2])
        deg.append(y)
    if any(not np.isfinite(y[3]) for y in deg):
        rows.append(dict(state=s, LLI=lli, LAM_NE=lne, LAM_PE=lpe, shift_mV=shift * 1e3, valid=False))
        continue
    fit = fit_event(deg)
    tq = pack_quantities([restart(y, v, ocp) for y, v in zip(deg, v_start_ref)], ocp, etas=[ETA] * 4)
    fq = pack_quantities([restart(y, v, ocp) for y, v in zip(fit, v_start_fit)], ocp, etas=[ETA] * 4)
    bt, it = beta_E(ref_true, deg, v_start_ref, ocp)
    bf, iff = beta_E(ref_fit, fit, v_start_fit, ocp)
    rows.append(dict(state=s, LLI=lli, LAM_NE=lne, LAM_PE=lpe, shift_mV=shift * 1e3, valid=True,
                     Q_C20_true=tq["Q_C20"], Q_C20_fit=fq["Q_C20"], Q_fc_true=tq["Q_fc"], Q_fc_fit=fq["Q_fc"],
                     beta_true=bt, beta_fit=bf, dD_true=it.get("dD_prog"), dD_fit=iff.get("dD_prog"),
                     LLI_fit=float(np.mean([a[2] - b[2] for a, b in zip(ref_fit, fit)])),
                     LAMNE_fit=float(np.mean([(a[0] - b[0]) / a[0] for a, b in zip(ref_fit, fit)])),
                     LAMPE_fit=float(np.mean([(a[1] - b[1]) / a[1] for a, b in zip(ref_fit, fit)]))))
    print(s, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
df = pd.DataFrame(rows)
df["err_Q_C20"] = df["Q_C20_fit"] - df["Q_C20_true"]
df["err_Q_fc"] = df["Q_fc_fit"] - df["Q_fc_true"]
df["err_beta"] = df["beta_fit"] - df["beta_true"]
df["err_LLI"] = df["LLI_fit"] - df["LLI"]
df.to_csv(os.path.join(OUT, "S1_synthetic.csv"), index=False)
ok = df[df["valid"]]
summ = dict(n_valid=int(len(ok)),
            median_abs_err_Q_C20=float(ok["err_Q_C20"].abs().median()),
            median_abs_err_beta=float(ok["err_beta"].abs().median()),
            median_abs_err_Q_fc=float(ok["err_Q_fc"].abs().median()),
            median_abs_err_LLI=float(ok["err_LLI"].abs().median()),
            n_small_dD_true=int((ok["dD_true"].abs() < 0.5).sum()),
            ref_fit=[list(map(float, x)) for x in ref_fit], ref_true=[list(map(float, x)) for x in ref_true])
summ["pass"] = bool(summ["median_abs_err_Q_C20"] <= 0.2 and summ["median_abs_err_beta"] <= 0.10)
json.dump(summ, open(os.path.join(OUT, "S1_synthetic_summary.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in summ.items() if not k.startswith("ref_")}, indent=1))
