"""Round 12 WP1: tests of the registered modules on synthetic curves only (no challenge data).

Run: python3 -B src/test_registered.py   (also collectable by pytest). Requirements: a known step location is
recovered within 0.02 Ah, a known Ah offset within 0.005 Ah. `resolution_diagnostic()` reports (not asserts) the
locators' errors under 1 mV voltage quantisation, also on synthetic curves."""
import json, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ahchain as AC  # noqa: E402
import locators as L  # noqa: E402

STEP_TOL_AH = 0.02
AH_TOL_AH = 0.005
DQ_CHARGE = 20.4 * 10 / 3600.0      # 20.4 A, 10 s sampling
DQ_C20 = 5.1 / 3600.0               # 5.1 A, 1 s sampling
DQ_PROG = 10.0 * 10 / 3600.0        # 10 A band, 10 s sampling


def charge_curve(q0, w=1.5, b=0.018, c=0.0012, quant=False, noise=0.0, seed=0):
    """Symmetric graphite-like step on a linear slope: dV/dQ maximum and midpoint crossing both at q0."""
    q = np.arange(DQ_CHARGE, 95.0, DQ_CHARGE)
    v = 3.25 + c * (q - q0) + b * np.tanh((q - q0) / w)
    if noise:
        v = v + np.random.default_rng(seed).normal(0.0, noise, len(v))
    return q, (np.round(v, 3) if quant else v)


def discharge_curve(d0, w=1.5, b=0.018, c=0.001, q_end=L.CK0_Q_AH, dq=DQ_C20, quant=False, noise=0.0, seed=0):
    q = np.arange(0.0, q_end, dq)
    v = 3.30 - c * (q - d0) - b * np.tanh((q - d0) / w)
    if noise:
        v = v + np.random.default_rng(seed).normal(0.0, noise, len(v))
    return q, (np.round(v, 3) if quant else v)


Q0S = (61.337, 62.9, 64.013, 65.871)
D0S = (31.5, 33.21, 34.977)
SHAPES = (dict(w=1.0, b=0.015), dict(w=1.5, b=0.018), dict(w=2.5, b=0.012))


# ---- locators -----------------------------------------------------------------------------------------------
def test_charge_locators_recover_step():
    for q0 in Q0S:
        for sh in SHAPES:
            for c in (0.0, 0.0012):
                q, v = charge_curve(q0, c=c, **sh)
                d = L.charge_variants(q, v)
                for k, x in d.items():
                    assert abs(x - q0) <= STEP_TOL_AH, (k, q0, sh, c, x)
                assert abs(L.cell_value(d) - q0) <= STEP_TOL_AH


def test_discharge_locators_recover_step():
    for d0 in D0S:
        for sh in SHAPES:
            q, v = discharge_curve(d0, **sh)
            d = L.discharge_variants(q, v)
            for k, x in d.items():
                assert abs(x - d0) <= STEP_TOL_AH, (k, d0, sh, x)


def test_program_dl1_recovers_step():
    for d0 in (27.456, 29.83, 31.0, 36.2):
        for sh in SHAPES:
            q, v = discharge_curve(d0, q_end=55.9, dq=DQ_PROG, **sh)
            sel = q > 11.8
            x = L.dvdq_peak(q[sel], v[sel], L.DL_SMOOTH_AH["DL1"], L.PROG_DL1_WINDOW_AH, -1)
            assert abs(x - d0) <= STEP_TOL_AH, (d0, sh, x)


def test_program_band_on_synthetic_segment():
    """CV end -> pulse -> 10 A program with a step at 30 Ah depth -> recharge: program_dl1 finds the step."""
    n_p, n_d = 180, int(56.0 / DQ_PROG)
    cur = np.r_[np.full(5, 20.4), [5.1], np.zeros(180), np.full(n_p, -20.4), np.full(n_d, -10.0), np.full(200, 20.0)]
    t = np.arange(len(cur)) * 10.0
    seg = pd.DataFrame(dict(elapsed_s=t, current_A=cur))
    e = 5
    _, ah = AC.integrated_ah(seg)
    depth = ah[e] - ah
    v = np.where(depth > 0, 3.30 - 0.001 * (depth - 40.0) - 0.018 * np.tanh((depth - 40.0) / 1.5), 3.4)
    for c in L.CELLS:
        seg[c] = v
    pb = L.program_band(seg, e)
    assert pb is not None and pb[0].min() > 10.0 and pb[0].max() > 55.0
    pack, cells = L.program_dl1(seg, e)
    assert abs(pack - 40.0) <= STEP_TOL_AH, pack


def test_anchor_charge_on_synthetic_segment():
    """Rest -> 20.4 A CC with a step at q0 -> CV taper to 5.1 A -> rest, with duplicate timestamps at both
    transitions (as in the data): q base = ah[start - 1], Q_fc = package q, CL family recovers q0."""
    q0 = 63.4612
    n_cc = int(95.0 / DQ_CHARGE)
    taper = np.linspace(20.0, 5.1, 120)
    cur = np.r_[np.zeros(50), 0.0, np.full(n_cc, 20.4), taper, 0.0, np.zeros(30)]
    dt = np.full(len(cur), 10.0); dt[0] = 0.0
    dt[50] = 0.0                                   # rest row sharing the charge start's timestamp
    dt[-31] = 0.0                                  # rest row sharing the CV end's timestamp
    t = np.cumsum(dt)
    seg = pd.DataFrame(dict(elapsed_s=t, current_A=cur))
    seg["timestamp"] = pd.Timestamp("2025-02-11 21:08:25") + pd.to_timedelta(seg["elapsed_s"], unit="s")
    _, ah = AC.integrated_ah(seg)
    start, end = 51, len(cur) - 32
    qq = ah - ah[start - 1]
    v = 3.25 + 0.0012 * (qq - q0) + 0.018 * np.tanh((qq - q0) / 1.5)
    for c in L.CELLS:
        seg[c] = v
    q, V, qfc = L.anchor_charge(seg, seg["timestamp"].iloc[start], seg["timestamp"].iloc[end])
    assert abs(qfc - (ah[end] - ah[start - 1])) < 1e-12 and abs(q[0] - DQ_CHARGE) < 1e-12 and len(q) == n_cc
    d = L.charge_variants(q, V[:, 0])
    assert all(abs(x - q0) <= STEP_TOL_AH for x in d.values()), d


def test_window_edge_and_coverage_give_nan():
    q, v = charge_curve(50.02)            # maximum on the window edge (open interval 50-80)
    assert np.isnan(L.dvdq_peak(q, v, 2.0, L.CL_WINDOW_AH, +1))
    q, v = charge_curve(64.0)
    keep = q < 70.0                        # data stop inside the window
    assert np.isnan(L.dvdq_peak(q[keep], v[keep], 2.0, L.CL_WINDOW_AH, +1))
    assert np.isnan(L.midpoint_crossing(q, v, np.nan, 5.0, 15.0, +1))


def test_combination_rules():
    assert np.isnan(L.cell_value(dict(a=1.0, b=2.0, c=3.0, d=np.nan, e=np.nan)))   # < 4 finite variants
    assert L.cell_value(dict(a=1.0, b=2.0, c=3.0, d=10.0, e=np.nan)) == 2.5
    assert np.isnan(L.pack_value([1.0, 2.0, np.nan, np.nan]))                       # < 3 finite cells
    assert L.pack_value([1.0, 2.0, 4.0, np.nan]) == 2.0
    cells = [dict(CL1=60.0 + c, CL2=60.1 + c, CL3=59.9 + c, CL4=60.0 + c, CL5=np.nan) for c in range(4)]
    comb, cv, per = L.combine(cells)
    assert cv == [60.0, 61.0, 62.0, 63.0] and comb == 61.5 and np.isnan(per["CL5"]) and abs(per["CL2"] - 61.6) < 1e-9


def test_trend_loo_and_gates():
    x = np.array([30.0, 60.0, 120.0, 150.0, 190.0, 225.0]); y = 66.0 - 0.02 * x
    b, a = L.theil_sen(x, y)
    assert abs(b + 0.02) < 1e-12 and abs(a - 66.0) < 1e-9
    g = L.g_sb(x, y, list(L.RELAXED_ANCHORS))
    assert g["passed"] and g["sigma_LOO"] < 1e-9 and abs(g["threshold"] - 0.15) < 1e-12
    y2 = y.copy(); y2[2] += 0.5                       # one outlier on an exact line
    g2 = L.g_sb(x, y2, list(L.RELAXED_ANCHORS))
    assert not g2["passed"] and g2["failed_anchors"] == [4]
    a3 = L.anomaly(x, y, 90.0, 66.0 - 0.02 * 90.0 + 0.4)
    assert abs(a3 - 0.4) < 1e-9
    per = dict(CL1=0.3, CL2=0.5, CL3=0.2, CL4=0.45, CL5=-0.1)
    assert L.g_a3(0.4, per, 0.05)["identified"]
    assert not L.g_a3(0.4, dict(per, CL3=-0.2), 0.05)["identified"]        # only 3 of 5 with the same sign
    assert not L.g_a3(0.12, per, 0.05)["identified"]                       # below the 0.15 Ah floor
    r = L.r8_check([66.24, 66.0, 66.6, 66.9], 66.375)
    assert r["passed"] and abs(r["cl1_rounded_mean"] - 66.4375) < 1e-12


def test_ck0_split_identities():
    q_fc0, h0 = 100.122, dict(point=0.10, lo=0.05, hi=0.20)
    d_cells = [{f"DL{i}": 33.0 + 0.1 * c + 0.01 * i for i in range(1, 6)} for c in range(4)]
    c_cells = [{f"CL{i}": 66.4 - 0.1 * c - 0.02 * i for i in range(1, 6)} for c in range(4)]
    s = L.ck0_split(d_cells, c_cells, q_fc0, h0)
    assert abs(s["eps0"] - (L.CK0_Q_AH - q_fc0)) < 1e-9
    assert abs(s["a0"] - (-s["Dbot_minus_Cbot"] - 0.10)) < 1e-12
    assert s["a0_lo"] <= s["a0"] <= s["a0_hi"]
    assert abs(s["top_split"] - s["a0"] - s["eps0"]) < 1e-9          # (Dtop - Ctop) + (Dbot - Cbot) = eps0
    assert s["G_B3"]["status"] in ("identified", "not identified")
    s_nan = L.ck0_split(d_cells, c_cells, q_fc0, dict(point=np.nan, lo=np.nan, hi=np.nan))
    assert s_nan["G_B3"]["status"] == "no finite interval"
    hv = L.h_interval({("h1", "A3"): 0.1, ("h1", "DL1"): 0.3, ("h2", "A3"): 0.2, ("h2", "DL1"): np.nan})
    assert hv == dict(point=0.2, lo=0.1, hi=0.3)
    assert np.isnan(L.median_over_k([0.1, np.nan, 0.2])) and L.median_over_k([0.1, 0.3, 0.2]) == 0.2


def test_step_jump():
    t0 = pd.Timestamp("2025-03-19 19:06:27")
    days = np.array([0.0, 5.0, 10.0, 15.0]); dep = 30.0 - 0.03 * days
    j = L.step_jump(29.8, t0, 30.0 + 0.0, t0 + pd.Timedelta(days=6.0), days, dep)
    assert abs(j["r45"] + 0.03) < 1e-12 and abs(j["J"] - (0.2 + 0.03 * 6.0)) < 1e-9


# ---- Ah chain ---------------------------------------------------------------------------------------------------
LAM25, LAM45 = -0.0020, -0.0010
DELTA1, DELTA2, DELTA3 = 0.217, 0.163, 0.311     # known Term1, Term2, Term3 offsets


class _Builder:
    """Synthetic segments from phases of constant current at 10 s sampling (exact backward-rectangle sums)."""

    def __init__(self):
        self.t, self.chg, self.dis, self.segs, self.events = 0.0, 1000.0, 900.0, {}, []

    def segment(self, no, sp, phases):
        rows, cv = [], []
        first = True
        for n, cur, tag in phases:
            for k in range(int(n)):
                if first:                 # first sample of a segment: dt = 0, nothing booked (package convention)
                    first, dt = False, 0.0
                else:
                    dt = tag["dt"] if (k == 0 and isinstance(tag, dict)) else 10.0
                    self.t += dt
                q = cur * dt / 3600.0
                self.chg += max(q, 0.0); self.dis += max(-q, 0.0)
                rows.append((self.t, cur, self.chg, self.dis))
            if tag == "cv" or (isinstance(tag, dict) and tag.get("cv")):
                cv.append(len(rows) - 1)
        df = pd.DataFrame(rows, columns=["elapsed_s", "current_A", "charge_Ah_cum", "discharge_Ah_cum"])
        df["timestamp"] = pd.Timestamp("2025-01-01") + pd.to_timedelta(df["elapsed_s"], unit="s")
        df["segment"] = no; df["chamber_temperature_C"] = sp
        self.segs[no] = df
        return df, cv

    def gap(self, seconds):
        self.t += seconds


def _charge_phases(c_ah, n_cc=600):
    """CC samples plus one 5.1 A CV-end sample delivering exactly c_ah."""
    i_cc = (c_ah * 3600.0 / 10.0 - 5.1) / n_cc
    return [(n_cc, i_cc, ""), (1, 5.1, "cv")]


def _block(d_ah, lam, delta, n_d=1800, extra_dis=0.0):
    """rest, 20.4 A pulse, discharge d_ah, rest, recharge so that N = lam * thr + delta."""
    pulse = 180 * 20.4 * 10 / 3600.0
    thr = pulse + d_ah + extra_dis
    return [(180, 0.0, ""), (180, -20.4, ""), (n_d, -d_ah * 3600.0 / 10.0 / n_d, ""), (30, 0.0, "")] \
        + _charge_phases(thr * (1.0 + lam) + delta)


def synthetic_campaign(gap_in_seg4=True, flat_switch=True):
    B = _Builder()
    ev = []

    def add(no, sp, phases, types, anchor_k):
        df, cv = B.segment(no, sp, phases)
        for n, (e, ty) in enumerate(zip(cv, types)):
            ev.append(dict(event_id=f"S{no}E{n}", segment=no, setpoint=sp, type=ty,
                           anchor_k=anchor_k if ty == "A" else -1, t_cv_end=df["timestamp"].iloc[e]))

    # segment 1 (45 degC): anchor 0, three top-ups; AT carries -DELTA1 so that Term1 = +DELTA1
    p = [(10, 0.0, "")] + _charge_phases(95.0, 1700) + _block(50.0, LAM45, -DELTA1) \
        + _block(48.0, LAM45, 0.0) + _block(52.0, LAM45, 0.0) + [(20, 0.0, "")]
    add(1, 45, p, ["A", "T", "T", "T"], 0)
    B.gap(3 * 86400.0)                                    # checkup CK1
    # segment 2 (25 degC): anchor 1, two top-ups; then the switch idle; segment 3 (45 degC): three top-ups
    pulse = 180 * 20.4 * 10 / 3600.0
    d_a, d_b = 20.0, 30.0
    p = [(10, 0.0, "")] + _charge_phases(92.0, 1700) + _block(50.0, LAM25, DELTA3) + _block(49.0, LAM25, 0.0) \
        + [(180, 0.0, ""), (180, -20.4, ""), (720, -d_a * 360.0 / 720, "")]
    add(2, 25, p, ["A", "T", "T"], 1)
    B.gap(6 * 3600.0)
    if not flat_switch:
        B.chg += 0.3
    lam_bar = 0.5 * (LAM25 + LAM45)
    thr_x = pulse + d_a + d_b
    p = [(1, 0.0, ""), (1080, -d_b * 360.0 / 1080, ""), (30, 0.0, "")] + _charge_phases(thr_x * (1.0 + lam_bar) + DELTA2) \
        + _block(50.0, LAM45, 0.0) + _block(47.0, LAM45, 0.0) + [(20, 0.0, "")]
    add(3, 45, p, ["T", "T", "T"], -1)
    B.gap(3 * 86400.0)                                    # checkup CK2
    # segment 4 (25 degC): anchor 2 and one top-up with a 120 s recording gap inside the AT pair
    blk = _block(50.0, LAM25, DELTA3)
    if gap_in_seg4:
        blk[2] = (blk[2][0], blk[2][1], {"dt": 120.0})
    p = [(10, 0.0, "")] + _charge_phases(91.0, 1700) + blk + [(20, 0.0, "")]
    add(4, 25, p, ["A", "T"], 2)
    B.gap(3 * 86400.0)                                    # checkup CK3
    # segment 6 (25 degC): anchor 3, two top-ups (a second 25 degC TT pair)
    p = [(10, 0.0, "")] + _charge_phases(90.0, 1700) + _block(50.0, LAM25, DELTA3) + _block(51.0, LAM25, 0.0) \
        + [(20, 0.0, "")]
    add(6, 25, p, ["A", "T", "T"], 3)
    ev = pd.DataFrame(ev)
    t0 = pd.Timestamp("2025-01-01")
    seg_t = {s: (g["timestamp"].iloc[0], g["timestamp"].iloc[-1]) for s, g in B.segs.items()}
    cks = [t0 - pd.Timedelta(days=1), seg_t[1][1] + pd.Timedelta(days=1), seg_t[3][1] + pd.Timedelta(days=1),
           seg_t[4][1] + pd.Timedelta(days=1)]
    return B.segs, ev, cks


def test_integration_matches_package():
    sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(ST, "..", "..")), "TechArena_Challenge2_Team_Package"))
    from my_model import model_template as mt
    rng = np.random.default_rng(1)
    t = np.cumsum(np.r_[0.0, rng.choice([0.0, 1.0, 10.0, 10.0, 700.0, 30.0], 500)])
    seg = pd.DataFrame(dict(elapsed_s=t, current_A=rng.normal(0, 10, len(t))))
    i1, a1 = mt._integrated_ah(seg)
    i2, a2 = AC.integrated_ah(seg)
    assert np.array_equal(i1, i2) and np.allclose(a1, a2, rtol=0, atol=1e-12)


def test_ah_chain_recovers_offsets():
    segs, ev, cks = synthetic_campaign()
    pairs = AC.build_pairs(ev, segs, cks)
    typ = dict(zip(pairs["pair"], pairs["type"]))
    assert typ["S1E3-S2E0"] == "none" and typ["S3E2-S4E0"] == "none"           # checkups
    assert typ["S2E2-S3E0"] == "X"
    seg4 = pairs[pairs["pair"] == "S4E0-S4E1"].iloc[0]
    assert not seg4["admissible"] and "recording gap 120 s" in seg4["reason"]
    # loss rule: own segment, pooled same set point (25 degC has 2 TT pairs overall)
    l1, src1 = AC.lam(pairs, 1, 45)
    assert src1 == "segment" and abs(l1 - LAM45) < 1e-12
    l4, src4 = AC.lam(pairs, 4, 25)
    assert src4 == "pooled same set point" and abs(l4 - LAM25) < 1e-12
    res = AC.tt_residuals(pairs)
    assert (res["r"].abs() < AH_TOL_AH).all()
    noise = AC.g_noise(res)
    assert noise["passed"] and noise["sigma_TT_25"] < 1e-9
    tm = AC.terms(pairs)
    t1 = tm[tm["term"] == "Term1"]["value_main"].iloc[0]
    t2 = tm[tm["term"] == "Term2"]["value_main"].iloc[0]
    t3 = tm[tm["term"] == "Term3"].set_index("k")["value_main"]
    assert abs(t1 - DELTA1) <= AH_TOL_AH and abs(t2 - DELTA2) <= AH_TOL_AH
    assert set(t3.index) == {1, 3} and (np.abs(t3 - DELTA3) <= AH_TOL_AH).all()   # k = 2 excluded by the gap
    tt = AC.t_top(tm, noise)
    assert abs(tt["point"] - (DELTA1 + DELTA2 + DELTA3)) <= AH_TOL_AH
    assert tt["lo"] <= tt["point"] <= tt["hi"] and tt["G_T"]["identified"]
    tw = AC.t_top(tm, noise, j_dvdq_median=DELTA2 + 0.5)                           # G_E2 widening
    assert tw["G_E2"]["consistent"] is False and tw["Term2"]["hi"] >= DELTA2 + 0.5 - 1e-12
    bad = AC.t_top(tm, dict(noise, passed=False))
    assert np.isnan(bad["point"]) and bad["status"].startswith("not identifiable")


def test_switch_requires_flat_counters_and_other_set_point_fallback():
    segs, ev, cks = synthetic_campaign(flat_switch=False)
    pairs = AC.build_pairs(ev, segs, cks)
    x = pairs[pairs["pair"] == "S2E2-S3E0"].iloc[0]
    assert x["type"] == "X" and not x["admissible"] and "counters not flat" in x["reason"]
    # drop segment 6 -> 25 degC has 1 TT pair overall -> segment 4 falls back to the 45 degC pooled median
    keep = ev["segment"] != 6
    segs2 = {s: g for s, g in segs.items() if s != 6}
    p2 = AC.build_pairs(ev[keep], segs2, cks)
    l4, src4 = AC.lam(p2, 4, 25)
    assert src4 == "pooled other set point" and abs(l4 - LAM45) < 1e-12


def test_e3_term2():
    s = [AC.ck0_top_slope(np.linspace(0, 3, 301), 13.59 - 0.02 * np.linspace(0, 3, 301), w) for w in AC.S_WINDOWS_AH]
    assert np.allclose(s, 0.02)
    r = AC.term2_e3(0.004, 20.0, s)
    assert abs(r["point"] - 0.2) < 1e-12 and r["lo"] < 0.2 < r["hi"]


# ---- protocol consistency ---------------------------------------------------------------------------------
def test_constants_match_protocol():
    p = json.load(open(os.path.join(ST, "wp1", "protocol.json")))
    c = p["constants"]
    mods = dict(locators=L, ahchain=AC)
    for key, val in c.items():
        mod, name = key.split(".")
        got = getattr(mods[mod], name)
        got = [list(x) if isinstance(x, tuple) else x for x in got] if isinstance(got, tuple) else got
        if isinstance(got, dict):
            got = {k: (list(v) if isinstance(v, tuple) else v) for k, v in got.items()}
        assert got == val, (key, got, val)


# ---- resolution diagnostic (reported, not asserted) ----------------------------------------------------------
def resolution_diagnostic():
    out = {}
    for label, kw in (("clean", {}), ("quantised_1mV", dict(quant=True)), ("quantised_1mV_noise_0.5mV", dict(quant=True, noise=0.0005))):
        ce, de, pe = [], [], []
        for seed in range(3):
            for q0 in Q0S:
                for sh in SHAPES:
                    q, v = charge_curve(q0, seed=seed, **sh, **kw)
                    d = L.charge_variants(q, v)
                    ce.append([d[k] - q0 for k in ("CL1", "CL2", "CL3", "CL4", "CL5")] + [L.cell_value(d) - q0])
            for d0 in D0S:
                for sh in SHAPES:
                    q, v = discharge_curve(d0, seed=seed, **sh, **kw)
                    d = L.discharge_variants(q, v)
                    de.append([d[k] - d0 for k in ("DL1", "DL2", "DL3", "DL4", "DL5")] + [L.cell_value(d) - d0])
                    q, v = discharge_curve(d0 - 3.0, q_end=55.9, dq=DQ_PROG, seed=seed, **sh, **kw)
                    sel = q > 11.8
                    pe.append(L.dvdq_peak(q[sel], v[sel], 2.0, L.PROG_DL1_WINDOW_AH, -1) - (d0 - 3.0))
        ce, de, pe = np.abs(np.array(ce)), np.abs(np.array(de)), np.abs(np.array(pe))
        out[label] = dict(
            charge_max_abs_err_Ah=dict(zip(["CL1", "CL2", "CL3", "CL4", "CL5", "cell_median"], np.round(ce.max(0), 4).tolist())),
            charge_median_abs_err_Ah=dict(zip(["CL1", "CL2", "CL3", "CL4", "CL5", "cell_median"], np.round(np.median(ce, 0), 4).tolist())),
            discharge_max_abs_err_Ah=dict(zip(["DL1", "DL2", "DL3", "DL4", "DL5", "cell_median"], np.round(de.max(0), 4).tolist())),
            discharge_median_abs_err_Ah=dict(zip(["DL1", "DL2", "DL3", "DL4", "DL5", "cell_median"], np.round(np.median(de, 0), 4).tolist())),
            program_dl1_max_abs_err_Ah=round(float(pe.max()), 4), program_dl1_median_abs_err_Ah=round(float(np.median(pe)), 4))
    out["note"] = ("synthetic symmetric tanh steps (w 1.0-2.5 Ah, height 24-36 mV) on a linear slope, single cell; "
                   "charge 20.4 A/10 s, C/20 5.1 A/1 s, program 10 A/10 s; seeds 0-2; no challenge data")
    return out


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for f in tests:
        try:
            f(); print("PASS", f.__name__)
        except Exception as e:  # noqa: BLE001
            failed += 1; print("FAIL", f.__name__, repr(e))
    if "--diagnostic" in sys.argv:
        d = resolution_diagnostic()
        json.dump(d, open(os.path.join(ST, "wp1", "synthetic_resolution.json"), "w"), indent=1)
        print(json.dumps(d, indent=1))
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
