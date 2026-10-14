"""Stage 1c: real anchor-1 fits per cell (main, alt graphite, dV/dq variant); residual RMS and autocorrelation."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common5b import H  # noqa: E402
from edata import anchor_curve  # noqa: E402
from emodel import OCP, fit_charge  # noqa: E402
from v2 import anchors_by_checkup  # noqa: E402

OUT = os.path.join(HERE, "outputs")
op = H.full_op()
anc = anchors_by_checkup(H.full_charges(op), H.CK)
q, I, V, vr, qt = anchor_curve(op, anc[1])
rows = []
for name, which, extra in (("main", "main", None), ("alt_graphite", "alt_graphite", None),
                           ("dvdq_variant", "main", {"weight": 2.0})):
    ocp = OCP(which)
    for c in range(4):
        x, info = fit_charge(q, I, V[:, c], ocp, extra=extra)
        r = info["resid_mV"][: len(q)]
        rho = [float(np.corrcoef(r[:-L], r[L:])[0, 1]) for L in (1, 5, 20)]
        acf = [1.0] + [float(np.corrcoef(r[:-L], r[L:])[0, 1]) for L in range(1, 200)]
        s = 0.0
        for a in acf[1:]:
            if a <= 0:
                break
            s += a
        neff = len(r) / (1 + 2 * s)
        thp0 = (x[2] - x[3] * x[0]) / x[1]
        bins = [2, 10, 50, 80, 90, 100]
        reg = {f"rms_{a}_{b}": float(np.sqrt(np.mean(r[(q >= a) & (q < b)] ** 2))) for a, b in zip(bins[:-1], bins[1:])}
        rows.append(dict(fit=name, cell=c + 1, Qn=x[0], Qp=x[1], QLi=x[2], theta_n0=x[3], theta_p0=thp0, R=x[4], h=x[5],
                         rms_mV=info["rms_mV"], rho1=rho[0], rho5=rho[1], rho20=rho[2], n=len(r), n_eff=neff,
                         at_bound=bool(np.isclose(x[1], 200) or np.isclose(abs(x[5]), 0.2) or np.isclose(x[0], 200)), **reg))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "S1_anchor1_fits.csv"), index=False)
print(df.round(4).to_string())
