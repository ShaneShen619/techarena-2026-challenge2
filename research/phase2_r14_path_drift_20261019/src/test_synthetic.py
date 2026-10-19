"""WP1 synthetic tests of the registered code (no challenge data). Writes wp1/synthetic_test.json; exit code 1 on
any failure. A known Ah offset planted between an anchor's CV end and the next top-up's CV end must be recovered to
within 0.005 Ah."""
import json, os, sys
import numpy as np
import pandas as pd
import data14 as D
import ahchain as AC
import signals as SG
import stats14 as SS
import decide as DC

TOL_AH = 0.005
DT = 10.0
I_CC, I_DIS, I_PULSE = 20.4, -10.0, -20.4
CV_TAPER = np.linspace(15.0, 5.1, 30)            # CV current samples at 14.0 V; the last one is the CV end
V_REST_A, V_REST_T = 13.435, 13.465              # pack rest voltage after an anchor / a top-up CV end


class Seg:
    """Sample-by-sample builder of one synthetic segment (10 s sampling)."""

    def __init__(self, number, setpoint, t0):
        self.n, self.sp, self.t = number, setpoint, t0
        self.T, self.I, self.V = [], [], []

    def add(self, cur, volts, dt=DT):
        for c, v in zip(np.atleast_1d(cur), np.atleast_1d(volts)):
            self.t += dt
            self.T.append(self.t); self.I.append(float(c)); self.V.append(float(v))

    def rest(self, n, v):
        self.add(np.zeros(n), np.full(n, v))

    def gap(self, seconds):
        self.t += seconds  # paused recording: the next sample comes `seconds` later

    def frame(self):
        V = np.array(self.V)
        df = pd.DataFrame({"elapsed_s": np.array(self.T, float), "current_A": self.I, "pack_voltage_V": V,
                           "chamber_temperature_C": self.sp, "segment": self.n, "temp_mean_C": float(self.sp) + 1.5})
        for m, c in enumerate(D.CELLS):
            df[c] = V / 4.0 + 0.001 * (m - 1.5)
        df["timestamp"] = pd.Timestamp("2025-01-01") + pd.to_timedelta(df["elapsed_s"], unit="s")
        return df


def ah(cur):
    return float(np.sum(cur) * DT / 3600.0)


def full_charge(sg, target_ah, v_start, v_rest):
    """CC at 20.4 A (one boosted sample takes the remainder) then the CV taper; exactly target_ah is charged."""
    need = target_ah - ah(CV_TAPER)
    n = int(need // (I_CC * DT / 3600.0))
    cc = np.full(n, I_CC)
    cc[n // 2] += (need - ah(cc)) * 3600.0 / DT
    sg.add(cc, np.linspace(v_start, 13.9, n))
    sg.add(CV_TAPER, np.full(len(CV_TAPER), 14.0))
    sg.rest(179, v_rest)  # rest samples at +10 .. +1790 s; the pulse starts at +1800 s


def block(sg, net_ah, n_sub=4, gap_s=None, duplicate=False):
    """From one CV end to the next: pulse, n_sub discharge/partial-charge sub-cycles, final CCCV charge. The net
    integrated Ah over (CV end, next CV end] is net_ah. Returns the block's discharged Ah."""
    start = len(sg.I)
    sg.add(np.full(180, I_PULSE), np.full(180, 13.17))
    for m in range(n_sub):
        sg.add(np.full(2160, I_DIS), np.linspace(13.25, 13.05, 2160))     # 60 Ah
        sg.rest(60, 13.15)
        if gap_s is not None and m == 1:
            sg.gap(gap_s)
            sg.rest(5, 13.15)
        if duplicate and m == 2:
            sg.add([I_DIS], [13.15], dt=0.0)                              # dt = 0 row: zero weight
        sg.add(np.full(1800, 10.0), np.linspace(13.1, 13.3, 1800))       # 50 Ah
        sg.rest(60, 13.3)
    seen = np.array(sg.I[start:]); tt = np.diff(np.r_[sg.T[start - 1], sg.T[start:]])
    w = np.where((tt > D.mt.MAX_DT_S) | (tt <= 0), 0.0, tt)
    net_so_far = float(np.sum(seen * w) / 3600.0)
    dis = float(np.sum(np.maximum(-seen, 0) * w) / 3600.0)
    sg.rest(360, 13.25)
    full_charge(sg, net_ah - net_so_far, 13.3, V_REST_T)
    return dis


def anchor_start(sg, q=95.0):
    sg.rest(720, 11.8)
    full_charge(sg, q, 12.0, V_REST_A)


def topup_start(sg):
    sg.rest(360, 13.3)
    sg.add(np.full(1080, I_DIS), np.linspace(13.3, 13.2, 1080))
    sg.rest(60, 13.2)
    full_charge(sg, 30.0, 13.25, V_REST_T)


def build(lam45, lam25, plant, drop_s5_tt=False, noise=0.0, seed=0):
    """Synthetic data set. plant: {segment: offset (Ah) of the A -> T1 pair}. Returns segs, truth table."""
    rng = np.random.default_rng(seed)
    segs, t0, truth = {}, 0.0, []

    def tt_net(lam, sg, gap_s=None, duplicate=False):
        e = rng.normal(0, noise) if noise else 0.0
        # first pass to learn thr of this block layout (deterministic): thr = pulse + 4 x 60 Ah
        thr = 10.2 + 240.0
        block(sg, lam * thr + e, gap_s=gap_s, duplicate=duplicate)
        return thr

    def seg(number, sp, anchor, n_tt, offset=None, gap=None, duplicate=False):
        nonlocal t0
        sg = Seg(number, sp, t0)
        lam = lam45 if sp == 45 else lam25
        if anchor:
            anchor_start(sg)
            thr = 10.2 + 240.0
            block(sg, lam * thr + offset, gap_s=gap, duplicate=duplicate)
            truth.append({"segment": number, "offset": offset, "thr": thr})
        else:
            topup_start(sg)
        for _ in range(n_tt):
            tt_net(lam, sg)
        segs[number] = sg.frame()
        t0 = sg.t + 86400.0

    seg(1, 45, True, 3, plant[1])
    seg(2, 25, True, 0, plant[2])
    seg(3, 45, False, 3)
    seg(4, 25, True, 1, plant[4], duplicate=True)
    seg(5, 25, True, 0 if drop_s5_tt else 1, plant[5])
    seg(6, 25, True, 0, plant[6], gap=3600.0)
    return segs, pd.DataFrame(truth)


def check(name, ok, detail, log):
    log.append({"test": name, "pass": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + " :: " + json.dumps(detail, default=float))


def main():
    log = []
    plant = {1: 0.150, 2: 0.100, 4: 0.120, 5: 0.130, 6: 0.110}
    lam45, lam25 = -0.0020, -0.0010

    # T1: exact recovery, lambda sources, gap exclusion, gap-bridged value, identity Term3' = Term3
    segs, truth = build(lam45, lam25, plant)
    ev = SG.events(segs)
    check("events: anchors detected in segments 1, 2, 4, 5, 6 only",
          ev.loc[ev["kind"] == "A", "segment"].tolist() == [1, 2, 4, 5, 6], ev.groupby("segment")["kind"].apply("".join).to_dict(), log)
    ch = SG.chain(segs, ev)
    t3 = SG.term3_table(ev, ch["pairs"], "2025-01-01")
    lam = {s: v for s, v in ch["lambda"].items()}
    check("lambda recovered (segment / pooled)",
          abs(lam[1][0] - lam45) < 1e-9 and abs(lam[4][0] - lam25) < 1e-9 and lam[2][1] == "pooled_25" and lam[6][1] == "pooled_25"
          and lam[3][1] == "segment", {s: [v[0], v[1]] for s, v in lam.items()}, log)
    rec = {int(r["segment"]): r for _, r in t3.iterrows()}
    errs = {s: abs(rec[s]["term3_gap_bridged" if s == 6 else "term3"] - plant[s]) for s in plant}
    check("planted A->T1 offsets recovered within 0.005 Ah (incl. 45 C anchor 0 and gap-bridged seg 6)",
          max(errs.values()) < TOL_AH, errs, log)
    check("gap pair excluded from P1 (seg 6) and recorded", np.isnan(rec[6]["term3"]) and rec[6]["AT1_n_gaps"] == 1
          and rec[6]["term3_excluded"] == "recording gap in A->T1", {"term3": rec[6]["term3"], "n_gaps": rec[6]["AT1_n_gaps"]}, log)
    check("Term3' = Term3 when the segment has a single TT pair (algebraic identity)",
          abs(rec[4]["term3b"] - rec[4]["term3"]) < 1e-9 and abs(rec[5]["term3b"] - rec[5]["term3"]) < 1e-9,
          {"seg4": [rec[4]["term3"], rec[4]["term3b"]], "seg5": [rec[5]["term3"], rec[5]["term3b"]]}, log)
    check("sigma_TT = 0 on noise-free TT pairs", ch["sigma_tt25_gate"] < 1e-6 and ch["sigma_tt45"] < 1e-6,
          {"sigma_tt25_gate": ch["sigma_tt25_gate"], "sigma_tt45": ch["sigma_tt45"]}, log)
    fade_ok = abs(rec[2]["fade"]) < 1e-12
    check("fade_k = Q_fc,1 - Q_fc,k is 0 for anchor 1", fade_ok, {"fade_anchor1": rec[2]["fade"]}, log)

    # T2: fallback chain: 25 C with < 2 TT pairs -> 45 C pooled median
    segs2, _ = build(lam45, lam25, plant, drop_s5_tt=True)
    ev2 = SG.events(segs2); ch2 = SG.chain(segs2, ev2)
    t32 = SG.term3_table(ev2, ch2["pairs"], "2025-01-01")
    r2 = t32[t32["segment"] == 2].iloc[0]
    expect = plant[2] + (lam25 - lam45) * r2["AT1_thr"]
    check("fallback: 25 C has 1 TT pair -> seg 2 uses pooled 45 C lambda (recorded)",
          ch2["lambda"][2][1] == "fallback_pooled_45" and abs(r2["term3"] - expect) < TOL_AH,
          {"source": ch2["lambda"][2][1], "term3": r2["term3"], "expected": expect}, log)

    # T3: noise on TT pairs: sigma estimates of the right size, offsets within noise
    segs3, _ = build(lam45, lam25, plant, noise=0.08, seed=7)
    ev3 = SG.events(segs3); ch3 = SG.chain(segs3, ev3)
    check("noisy TT pairs (sd 0.08 Ah): sigma_TT,45 in [0.02, 0.20] Ah", 0.02 <= ch3["sigma_tt45"] <= 0.20,
          {"sigma_tt45": ch3["sigma_tt45"], "sigma_tt25_gate": ch3["sigma_tt25_gate"],
           "reduced": ch3["sigma_reduced"], "full": ch3["sigma_full"]}, log)
    rr = ch3["pairs"]; rr = rr[(rr["type"] == "TT") & (rr["setpoint"] == 25)]
    check("25 C LOO lambda readings: reduced -> fallback 45 C, full -> other 25 C pair",
          set(rr["lambda_loo_source"]) == {"fallback_pooled_45"} and set(rr["lambda_loo_full_source"]) == {"pooled_25"},
          {"reduced": sorted(set(rr["lambda_loo_source"])), "full": sorted(set(rr["lambda_loo_full_source"]))}, log)

    # T4: P2 conversion with a synthetic CK0 curve V = 13.6 - 0.12 Q (cells: /4)
    q = np.arange(0, 5, 0.05)
    ref = pd.DataFrame({"discharged_Ah": q, "voltage_V": 13.6 - 0.12 * q})
    for m, c in enumerate(D.CELLS):
        ref[c] = (13.6 - 0.12 * q) / 4.0 + 0.001 * (m - 1.5)
    st = SG.s_top(ref)
    p2 = SG.p2_table(segs, ev, st)
    p = p2[p2["segment"] == 2].iloc[0]
    expect_ah = (V_REST_T - V_REST_A) / 0.12
    check("P2: s_top recovered and dV converted to Ah with the sign of Term3",
          abs(st["pack"] + 0.12) < 1e-9 and abs(p["dV_pack_mV"] - 30.0) < 1e-6 and abs(p["P2_pack_Ah"] - expect_ah) < 1e-9
          and abs(p["P2_cell1_V_Ah"] - expect_ah) < 1e-9 and bool(p["V30_ok"]),
          {"s_top_pack": st["pack"], "dV_pack_mV": p["dV_pack_mV"], "P2_pack_Ah": p["P2_pack_Ah"], "expected": expect_ah}, log)
    p3 = SG.p3_table(segs, ev, t3)
    check("P3 table runs; CV differences anchor - T1 are 0 for identical synthetic tapers",
          np.allclose(p3["dCV_Ah_A_minus_T1"].dropna(), 0.0, atol=1e-9) and len(p3) == 5,
          {"n": len(p3), "dCV_Ah": p3["dCV_Ah_A_minus_T1"].tolist()}, log)

    # T5: statistics
    x = np.array([0.0, 1.3, 2.4, 3.3, 3.9, 4.4, 5.0]); labels = [1, 2, 3, 4, 5, 6, 7]
    y = 0.10 + 0.05 * x
    a = SS.analyze(labels, x, x * 30, y)
    check("Theil-Sen exact line: slope 0.05, LOO width 0, E = 0.41", abs(a["main"]["d"] - 0.05) < 1e-12
          and a["main"]["loo_width_E"] < 1e-12 and abs(a["main"]["E"] - 0.41) < 1e-12, {"d": a["main"]["d"], "E": a["main"]["E"]}, log)
    rng = np.random.default_rng(3)
    yb = 0.10 + 0.05 * x + rng.normal(0, 0.005, len(x))
    ya = 0.10 + rng.normal(0, 0.05, len(x))
    b1, b0 = SS.analyze(labels, x, x, yb), SS.analyze(labels, x, x, ya)
    check("BIC: strong slope prefers linear by >= 2; flat noise does not", b1["bic"]["dBIC_const_minus_linear"] >= 2
          and b0["bic"]["dBIC_const_minus_linear"] < 2,
          {"dBIC_slope": b1["bic"]["dBIC_const_minus_linear"], "dBIC_flat": b0["bic"]["dBIC_const_minus_linear"]}, log)
    yo = yb.copy(); yo[4] += 0.5
    o = SS.analyze(labels, x, x, yo)
    # 3 raw MAD is about 2 sigma for Gaussian noise, so a noise point may be flagged as well; the planted one must be
    check("outlier flag (3 raw MAD) catches a planted +0.5 Ah point and gives a sensitivity without it",
          5 in o["outliers"] and "without_outliers" in o["sensitivity"] and abs(o["sensitivity"]["without_outliers"]["d"] - 0.05) < 0.01,
          {"outliers": o["outliers"], "d_without": o["sensitivity"]["without_outliers"].get("d")}, log)
    s4 = SS.analyze([1, 2, 4, 5], x[[0, 1, 3, 4]], x[[0, 1, 3, 4]], y[[0, 1, 3, 4]])
    check("fewer than 5 points: not estimable", s4["main"]["estimable"] is False, {"n": s4["main"]["n"]}, log)
    check("sensitivity without anchor 3 when anchor 3 is absent is marked same_as_main",
          SS.analyze([1, 2, 4, 5, 6], x[:5], x[:5], y[:5])["sensitivity"]["without_anchor_3"].get("same_as_main") is True, {}, log)

    # T6: decision rules on synthetic statistics
    def p1_of(d, lo, hi, dbic, est=True):
        if not est:
            return {"main": {"estimable": False, "n": 2}}
        return {"main": {"estimable": True, "d": d, "E": d * 8.2, "loo_range_E": [lo * 8.2, hi * 8.2],
                         "loo_width_E": (hi - lo) * 8.2}, "bic": {"dBIC_const_minus_linear": dbic}}
    cases = [
        ("noise gate fails", 0.35, p1_of(0.0, -0.005, 0.005, 0), p1_of(0.0, 0, 0, 0), "not identifiable"),
        ("P1 not estimable", 0.1, p1_of(0, 0, 0, 0, est=False), p1_of(0.0, 0, 0, 0), "O3 not identifiable"),
        ("LOO too wide", 0.1, p1_of(0.0, -0.02, 0.02, 0), p1_of(0.0, 0, 0, 0), "O3 not identifiable"),
        ("O1", 0.1, p1_of(0.002, -0.005, 0.008, 0), p1_of(0.01, 0, 0, 0), "O1 path drift small"),
        ("O1 blocked: P1b not estimable", 0.1, p1_of(0.002, -0.005, 0.008, 0), p1_of(0, 0, 0, 0, est=False), "O3 inconclusive"),
        ("O2", 0.1, p1_of(0.03, 0.02, 0.04, 5), p1_of(0.02, 0, 0, 0), "O2 path drift material"),
        ("O2 blocked: P1b opposite sign", 0.1, p1_of(0.03, 0.02, 0.04, 5), p1_of(-0.02, 0, 0, 0), "O3 inconclusive"),
        ("O2 blocked: BIC", 0.1, p1_of(0.03, 0.02, 0.04, 1.0), p1_of(0.02, 0, 0, 0), "O3 inconclusive"),
        ("O2 blocked: P1b not estimable", 0.1, p1_of(0.03, 0.02, 0.04, 5), p1_of(0, 0, 0, 0, est=False), "O3 inconclusive"),
    ]
    res = {name: DC.decide(s, p1, p1b)["outcome"] for name, s, p1, p1b, _ in cases}
    check("decision rules on 9 synthetic scenarios", all(res[n] == exp for n, *_, exp in cases), res, log)
    cb = DC.combine_top(0.01, [0.0, 0.02], -0.005, [-0.01, 0.0])
    check("d_top = d_tail + d_path, ranges endpoint-wise", abs(cb["d_top"] - 0.005) < 1e-12 and cb["d_top_range"] == [-0.01, 0.02], cb, log)

    out = os.path.join(D.ST, "wp1", "synthetic_test.json")
    json.dump({"n_tests": len(log), "n_pass": sum(t["pass"] for t in log), "tests": log}, open(out, "w"), indent=1, default=float)
    print(f"{sum(t['pass'] for t in log)}/{len(log)} passed")
    sys.exit(0 if all(t["pass"] for t in log) else 1)


if __name__ == "__main__":
    main()
