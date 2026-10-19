"""Synthetic tests of src/tail.py (wp1/protocol.json "synthetic_tests"). No challenge data is read.

Usage: python3 -B test_tail.py   (exit code 0 = all pass)
"""
import os, sys
import numpy as np
from scipy import integrate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail  # noqa: E402

GEN = {
    "M1": [19.0, 290.0],
    "M2": [2.0, 16.0, 230.0],
    "M3": [150.0, 60.0],
    "M4": [9.0, 40.0, 11.0, 400.0],
}
M2_UNDEF = [4.2, 15.0, 180.0]
T = np.arange(0.0, 481.0, 10.0)          # 49 samples, 10 s
FAIL = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
    if not ok:
        FAIL.append(name)


def trace(m, p):
    return np.round(tail.current(m, p, T), 3)     # 1 mA resolution like the data


# 1) each model recovers its own generating parameters and tail charges
for m, p in GEN.items():
    I = trace(m, p)
    f = tail.fit(m, T, I)
    rel = np.abs(np.array(f["params"]) - np.array(p)) / np.abs(np.array(p))
    check(f"{m} parameters within 1 %", bool(np.all(rel <= 0.01)),
          f"fit={np.round(f['params'], 4).tolist()} gen={p} max_rel={rel.max():.2e}")
    check(f"{m} admitted", f["admitted"], f"rmse={f['rmse']:.2e} last_third={f['last_third']:.2e}")
    for c in tail.SCENARIOS:
        q_gen, ok_gen = tail.q_tail(m, p, T[-1], c)
        q_fit, ok_fit = tail.q_tail(m, f["params"], T[-1], c)
        if not ok_gen:
            check(f"{m} {c} undefined in both", not ok_fit)
            continue
        check(f"{m} {c} Q_tail within 0.01 Ah", ok_fit and abs(q_fit - q_gen) <= 0.01,
              f"gen={q_gen:.5f} fit={q_fit:.5f} diff={q_fit - q_gen:+.2e}")

# 2) M2 with Iinf >= I_cut: current cutoffs undefined, holds defined
I = trace("M2", M2_UNDEF)
f = tail.fit("M2", T, I)
check("M2-undefined parameters within 1 %",
      bool(np.all(np.abs(np.array(f["params"]) - M2_UNDEF) / np.array(M2_UNDEF) <= 0.01)), str(np.round(f["params"], 4).tolist()))
for c in ("C2", "C3", "C4"):
    check(f"M2-undefined {c} undefined", not tail.q_tail("M2", f["params"], T[-1], c)[1])
for c in ("C5", "C6", "C7"):
    q, ok = tail.q_tail("M2", f["params"], T[-1], c); qg, _ = tail.q_tail("M2", M2_UNDEF, T[-1], c)
    check(f"M2-undefined {c} defined, within 0.01 Ah", ok and abs(q - qg) <= 0.01, f"gen={qg:.5f} fit={q:.5f}")
check("M2 generator with Iinf = 2.0 is defined at C2 and undefined at C3/C4",
      tail.q_tail("M2", GEN["M2"], 480.0, "C2")[1] and not tail.q_tail("M2", GEN["M2"], 480.0, "C3")[1]
      and not tail.q_tail("M2", GEN["M2"], 480.0, "C4")[1])

# 3) closed-form integrals and cutoff times against numerical quadrature / root
for m, p in GEN.items():
    for a, b in ((0.0, 480.0), (480.0, 2280.0), (480.0, 7680.0)):
        num = integrate.quad(lambda x: float(tail.current(m, p, x)), a, b, epsabs=1e-10, epsrel=1e-12, limit=500)[0]
        check(f"{m} integral [{a:.0f},{b:.0f}] closed form = quad", abs(tail.integral(m, p, a, b) - num) / 3600 <= 1e-6,
              f"diff={(tail.integral(m, p, a, b) - num) / 3600:+.1e} Ah")
    for ic in tail.I_CUT.values():
        tc = tail.t_cut(m, p, ic)
        if tc is None:
            continue
        check(f"{m} I(t_cut({ic})) = {ic}", abs(float(tail.current(m, p, tc)) - ic) <= 1e-6, f"t_cut={tc:.1f} s")

# 4) Theil-Sen + LOO recover a known linear slope exactly
x = np.array([0.0, 1.34, 2.36, 3.26, 3.92, 4.37, 5.05]); y = 0.05 * x
s, lo, hi = tail.slope_loo(x, y)
check("Theil-Sen slope and LOO exact", abs(s - 0.05) < 1e-12 and abs(lo - 0.05) < 1e-12 and abs(hi - 0.05) < 1e-12,
      f"{s} [{lo}, {hi}]")
y2 = 0.05 * x; y2[3] += 10.0                       # one outlier does not move the Theil-Sen slope
check("Theil-Sen robust to one outlier", abs(tail.theil_sen(x, y2) - 0.05) < 1e-12, f"{tail.theil_sen(x, y2)}")

# 5) decision function on hand-made inputs
z = dict(slope=0.0, loo_min=0.0, loo_max=0.0)
mk = lambda s, lo=None, hi=None: dict(slope=s, loo_min=s if lo is None else lo, loo_max=s if hi is None else hi)
cases = {
    "O1": {"C1": z, "T2": mk(0.005), "M1/C5": mk(-0.01), "M2/C6": mk(0.012, 0.0, 0.015)},
    "O2": {"C1": z, "T2": mk(0.02), "M1/C5": mk(0.015), "M2/C6": mk(0.03)},
    "O3-inconclusive": {"C1": z, "T2": mk(-0.005), "M1/C5": mk(0.015), "M2/C6": mk(0.02)},
    "O3-not-identifiable": {"C1": z, "T2": mk(0.0), "M3/C4": mk(0.05)},
    "O3-LOO-wide": {"C1": z, "T2": mk(0.005), "M1/C5": mk(0.01, -0.03, 0.02)},
}
expect = {"O1": ("O1", "tail drift small"), "O2": ("O2", "tail drift material"),
          "O3-inconclusive": ("O3", "inconclusive"), "O3-not-identifiable": ("O3", "not identifiable"),
          "O3-LOO-wide": ("O3", "inconclusive")}
for k, mem in cases.items():
    r = tail.decide(mem)
    check(f"decide {k}", (r["outcome"], r["label"]) == expect[k], f"-> {r['outcome']} {r['label']} env={r['envelope_Ah']}")
r = tail.decide(cases["O2"])
check("decide O2 d_tail = median without C1", abs(r["d_tail"] - 0.02) < 1e-12, f"{r['d_tail']}")
check("decide envelope boundary 0.30 is identifiable",
      tail.decide({"C1": z, "T2": mk(0.30 / 8.2)})["identifiable"])

print(f"\n{len(FAIL)} failures" + (": " + ", ".join(FAIL) if FAIL else ""))
sys.exit(1 if FAIL else 0)
