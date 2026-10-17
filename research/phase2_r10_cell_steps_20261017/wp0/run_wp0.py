"""WP0: re-baseline SUB, round 9's P2a and the per-variant table; per-cell caches; detection-noise scale σ_det."""
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common10 import H  # noqa: E402
import cellcand as CC  # noqa: E402
import eventcurves as EC  # noqa: E402
import gates10 as G  # noqa: E402
from residuals10 import r_seg, robust_sd  # noqa: E402
from runner5c import SCEN  # noqa: E402

OUT = os.path.join(HERE, "outputs")
R9 = os.path.join(os.path.dirname(STUDY), "phase2_r9_fixes_20261017", "outputs", "r9_robust_variants.csv")
PKG = os.path.join(STUDY, "cache", "submitted_package", "TechArena_Challenge2_Team_Package")
TOL = 0.001


def cvend_volts(op):
    """Per-cell voltages at the CV end of every deep program (main event definition)."""
    rows = []
    for p in EC.programs(op):
        rows.append(dict(t_cv_end=p["t_cv_end"], **{f"V_{c}": float(p["V"][p["e"], i]) for i, c in enumerate(CC.CELLS)}))
    return pd.DataFrame(rows)


def base_spec(spec):
    """Operation cut behind a runner5c scenario spec (CS uses the real cut, CSE the 10-day cut)."""
    if spec is not None and spec[0] == "cs":
        return None if spec[1] is None else ("cut", spec[1])
    return spec


def per_cell_caches():
    """CV-end per-cell voltages for every scenario cut (cached); anchors' per-cell quantities are in H.tables."""
    ops = {}
    for scen, cases in SCEN.items():
        for k, spec in cases:
            op, key = H.scenario_op(k, base_spec(spec))
            if op is not None:
                ops[key] = op
    ops["full"] = H.full_op()
    return {key: H._cache("cvv_" + key, lambda op=op: cvend_volts(op)) for key, op in ops.items()}


def sigma_det():
    full = H.full_op()
    fc, st, a4 = H.tables(full, "full")
    ev = G.full_events().reset_index()
    seg_n = ev.groupby("segment").size()
    segs45 = [s for s in seg_n.index if seg_n[s] >= 4 and int(ev[ev.segment == s].setpoint.iloc[0]) == 45]
    res = {}
    for v in G.VARIANTS:
        L = CC.variant_locs(st, v)
        rows = []
        for c in CC.COLS:
            d = ev.copy()
            d["unit"] = c
            d["depth"] = L.reindex(d["t_cv_end"])[c].to_numpy(float)
            rows.append(d)
        d = pd.concat(rows, ignore_index=True)
        d["R"] = r_seg(d, "depth")
        d45 = d[d.segment.isin(segs45)]
        res[v] = dict(pooled=robust_sd(d45["R"]), **{c[5:-2]: robust_sd(d45[d45.unit == c]["R"]) for c in CC.COLS},
                      n=int(d45["R"].notna().sum()))
        if v == "main":
            r8 = pd.read_csv(G.R8_EVENTS, parse_dates=["t_cv_end"])
            r8 = r8[r8.unit != "pack_mean"].set_index(["t_cv_end", "unit"])["R_seg"]
            mine = d.assign(unit=d.unit.str[5:]).set_index(["t_cv_end", "unit"])["R"]
            res["main_vs_round8_R_seg_max_abs"] = float((mine - r8.reindex(mine.index)).abs().max())
    res["segments_45C"] = [int(s) for s in segs45]
    return res


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    checks, info = {}, {}
    P = {"SUB": G.SUB, "CC_mean": CC.make(CC.provider_variant(), agg="mean"),
         "P2a_median": CC.make(CC.provider_variant(), agg="median")}
    dm = G.predict(P, variants=("main",))
    dv = G.predict(P, variants=G.VARIANTS, deltas=(0.4,))
    df = pd.concat([dm, dv[dv.step != "main"]], ignore_index=True)
    df.to_csv(os.path.join(OUT, "wp0_predictions.csv"), index=False)
    a = df[df.model == "SUB"].set_index(["scenario", "k", "delta", "step"])["Q"]
    b = df[df.model == "CC_mean"].set_index(["scenario", "k", "delta", "step"])["Q"]
    checks["framework_mean_equals_SUB_1e-9"] = bool(float((a - b).abs().max()) < 1e-9)
    info["framework_max_abs_Ah"] = float((a - b).abs().max())
    met = H.metrics(df)
    m = met[(met.scenario == "real") & (met.model == "SUB") & (met.step == "main")].set_index("delta")
    got = dict(MAE=[float(m.loc[d, "MAE"]) for d in H.DELTAS], MAX=[float(m.loc[d, "MAX"]) for d in H.DELTAS],
               pseudo=G.causal(met, "SUB")[0], cold=G.causal(met, "SUB")[1])
    tgt = dict(MAE=[0.1972, 0.1257, 0.1464], MAX=[0.6090, 0.2277, 0.2277], pseudo=0.1439, cold=0.1703)
    checks["SUB_real"] = all(abs(x - y) <= TOL for k in ("MAE", "MAX") for x, y in zip(got[k], tgt[k]))
    checks["SUB_pseudo_cold"] = abs(got["pseudo"] - tgt["pseudo"]) <= TOL and abs(got["cold"] - tgt["cold"]) <= TOL
    per = df[(df.scenario == "real") & (df.delta == 0.4) & (df.step == "main") & (df.model == "SUB")].set_index("checkup")["err_pp"]
    tck = dict(CK1=0.217, CK2=0.039, CK3=0.080, CK4=0.228, CK5=0.150, CK6=-0.163, CK7=-0.004)
    checks["SUB_per_checkup"] = all(abs(per[c] - v) <= TOL for c, v in tck.items())
    p2 = dict(pseudo=G.causal(met, "P2a_median")[0], cold=G.causal(met, "P2a_median")[1], real=G.real_mae(met, "P2a_median"))
    checks["P2a_round9"] = abs(p2["pseudo"] - 0.1385) <= TOL and abs(p2["cold"] - 0.1511) <= TOL and abs(p2["real"] - 0.1135) <= TOL
    r9 = pd.read_csv(R9).set_index("variant")
    diffs = []
    for v in G.VARIANTS:
        for mm, col in (("SUB", "SUB"), ("P2a_median", "P2a_median")):
            ps, cs, _ = G.causal(met, mm, v)
            diffs += [abs(G.real_mae(met, mm, v) - r9.loc[v, f"{col}_real"]), abs(ps - r9.loc[v, f"{col}_pseudo"]),
                      abs(cs - r9.loc[v, f"{col}_cold"])]
    checks["round9_variant_table"] = bool(max(diffs) <= TOL)
    info["round9_variant_table_max_diff"] = float(max(diffs))
    # submitted class
    sys.path.insert(0, PKG)
    spec = importlib.util.spec_from_file_location("sub10", os.path.join(PKG, "my_model", "model_template.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    src = open(os.path.join(STUDY, "cache", "package_submission_5cd305c.py"), encoding="utf-8").read()
    i = src.index("EXPECTED_SOH = {")
    expected = eval(src[i + len("EXPECTED_SOH = "):src.index("}", i) + 1])
    model = mod.MyModel()
    model.fit(H.load_dataset(H.DATA))
    res = dm[(dm.scenario == "real") & (dm.delta == 0.4) & (dm.model == "SUB")].set_index("checkup")["SOH"]
    sub_rows = []
    for k, d in enumerate(H.CK):
        s = float(model.estimate_soh(H.load_dataset(H.DATA, until=d), d))
        sub_rows.append(dict(checkup=H.CK_NAMES[k], submitted=s, research=float(res.get(H.CK_NAMES[k], np.nan)),
                             expected=expected[H.CK_NAMES[k]]))
    sr = pd.DataFrame(sub_rows)
    checks["submitted_vs_research"] = bool((sr["submitted"] - sr["research"]).abs().max() <= 0.0005)
    checks["submitted_equals_EXPECTED"] = bool((sr["submitted"].round(3) == sr["expected"]).all())
    sr.to_csv(os.path.join(OUT, "wp0_submitted_vs_research.csv"), index=False)
    # caches and noise scale
    cv = per_cell_caches()
    info["cvend_cache_keys"] = len(cv)
    info["full_programs_with_cvend_volts"] = int(len(cv["full"]))
    sig = sigma_det()
    checks["sigma_main_matches_round8_R_seg"] = bool(sig["main_vs_round8_R_seg_max_abs"] < 1e-9)
    json.dump(sig, open(os.path.join(OUT, "noise_scale.json"), "w"), indent=1)
    out = dict(checks=checks, all_checks=bool(all(checks.values())), info=info, SUB=got, P2a=p2)
    json.dump(out, open(os.path.join(OUT, "reproduce.json"), "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))
    print(json.dumps(sig, indent=1))
    print("NaN selections:", len(CC.NAN_LOG), CC.NAN_LOG[:10])
    if not out["all_checks"]:
        raise SystemExit("WP0 reproduction failed")
