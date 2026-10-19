"""WP4: epsilon-level budget, registered decision, leaderboard-only SOH variants (research copies through the
package CLI). Run: python3 -B src/wp4_run.py"""
import difflib, json, os, shutil, subprocess, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(ST, "..", ".."))
PKG = os.path.join(WT, "TechArena_Challenge2_Team_Package")
DATA = os.path.join(PKG, "data")
VAR = os.path.join(ST, "cache", "variants")
OUT = os.path.join(ST, "wp4")
CODE = ("run_model.py", "framework", "my_model")
EPS_LINE = "EPS_EXTRA_AH = 0.4          # 25 degC anchor offset beyond EPS0 (assumption)"
L_WIDTH_MAX = 0.50
SUB_EPS = 0.4


def run_cli(pkg_dir, out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    cli = os.path.join(pkg_dir, "run_model.py")
    for args in (["--model", "train", "--input", DATA, "--output-dir", out_dir],
                 ["--model", "test", "--input", DATA, "--state-dir", out_dir, "--output-dir", out_dir, "--eval-point", "all"]):
        subprocess.run([sys.executable, "-B", cli] + args, check=True, capture_output=True, text=True)
    return pd.read_csv(os.path.join(out_dir, "output.csv")).set_index("checkup")["SOH_est"]


def build_variant(name, replacements):
    """Copy of the package code with exact text replacements in model_template.py; returns (dir, diff lines)."""
    d = os.path.join(VAR, name)
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for c in CODE:
        src = os.path.join(PKG, c)
        (shutil.copytree(src, os.path.join(d, c), ignore=shutil.ignore_patterns("__pycache__"))
         if os.path.isdir(src) else shutil.copy2(src, os.path.join(d, c)))
    path = os.path.join(d, "my_model", "model_template.py")
    old = open(path).read()
    new = old
    for a, b in replacements:
        assert new.count(a) == 1, a
        new = new.replace(a, b)
    open(path, "w").write(new)
    diff = [l for l in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
            if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    return d, diff


def eps_variant(v):
    return [(EPS_LINE, f"EPS_EXTRA_AH = {v:.3f}        # research copy (round 12 WP4), not wired")]


def a3fix_variant(a3_rel, segment=6):
    """Subtract a_3^rel from anchor 3's Q_fc (the first full charge of segment 6) after its step-to-top distance is
    computed, so the bottom correction reaches every use of q (anchor term, beta) and leaves 'top' unchanged."""
    old = '''    return {
        "t_start": seg["timestamp"].iloc[start],
        "t_end": seg["timestamp"].iloc[end],
        "q": q,
        "setpoint": int(seg["chamber_temperature_C"].iloc[start]),
        "top": _charge_step_to_top(seg, i, ah, start, end, q),
    }'''
    new = f'''    top = _charge_step_to_top(seg, i, ah, start, end, q)
    if int(seg["segment"].iloc[0]) == {segment}:   # research copy (round 12 WP4): anchor-3 bottom correction a_3^rel
        q = q - {a3_rel:.4f}
    return {{
        "t_start": seg["timestamp"].iloc[start],
        "t_end": seg["timestamp"].iloc[end],
        "q": q,
        "setpoint": int(seg["chamber_temperature_C"].iloc[start]),
        "top": top,
    }}'''
    return [(old, new)]


def main():
    os.makedirs(OUT, exist_ok=True)
    T = json.load(open(os.path.join(ST, "wp3", "T_top.json")))
    B3 = json.load(open(os.path.join(ST, "wp2", "ck0_split.json")))
    G2 = json.load(open(os.path.join(ST, "wp2", "gates.json")))
    # ---- budget (registered) ----
    t_pt, (t_lo, t_hi) = T["T_top"]["point"], T["T_top"]["interval"]
    a_pt, (a_lo, a_hi) = B3["a0"], B3["a0_interval"]
    finite = all(np.isfinite(x) for x in (t_pt, t_lo, t_hi, a_pt, a_lo, a_hi))
    pt, lo, hi = t_pt + a_pt, t_lo + a_lo, t_hi + a_hi
    width = hi - lo
    g_noise = T["gates"]["G_noise"]["passed"]
    g_sb_failed = not G2["G_SB"]["passed"]
    inside = lo <= SUB_EPS <= hi
    if not finite:
        level, why = "L3", "no finite interval (T_top unmeasured or a_0 without finite interval)"
    elif inside and width <= L_WIDTH_MAX:
        level, why = "L1", "0.4 inside the interval and width <= 0.50 Ah"
    elif (not inside) and width <= L_WIDTH_MAX and g_noise and not g_sb_failed:
        level, why = "L2", "0.4 outside, width <= 0.50 Ah, G_noise passed, G_SB not failed"
    else:
        reasons = []
        if width > L_WIDTH_MAX:
            reasons.append(f"width {width:.3f} Ah > 0.50 Ah")
        if not inside:
            reasons.append("0.4 outside the interval")
        if g_sb_failed:
            reasons.append("G_SB failed (blocks L2)")
        level, why = "L3", "; ".join(reasons)
    a3 = G2["G_a3"]
    budget = dict(
        protocol="v1 (wp1/protocol.sha256)",
        T_top=dict(point=t_pt, interval=[t_lo, t_hi], status=T["T_top"]["status"]),
        a0=dict(point=a_pt, interval=[a_lo, a_hi], status=B3["G_B3"]["status"]),
        EPS_EXTRA_hat=dict(point=pt, interval=[lo, hi], width=width,
                           note="interval endpoints add; non-identified components enter with their full intervals"),
        decision=dict(level=level, reason=why, contains_0p4=bool(inside), G_noise_passed=bool(g_noise),
                      G_SB_failed=bool(g_sb_failed), action="keep SUB" if level != "L2" else "candidate SUB_L"),
        anchor3_rule=dict(G_a3_identified=bool(a3["identified"]), a3_rel=a3["a3_rel"],
                          candidate="SUB_A3fix (leaderboard-only, not wired)" if a3["identified"] else None),
        exploratory_not_registered=dict(
            T_top_time_matched_lambda=T["exploratory_not_registered"]["T_top"],
            a0_with_h1_from_anchor0=B3["exploratory_not_registered"]["a0_with_h1_0"],
            note=("not a decision input. h1_0 still carries the first-program offset (exposed: D1 reads 0.39-0.46 Ah "
                  "deeper), which lowers these a_0 values by about that amount.")))
    # ---- SOH variants (leaderboard-only research copies through the package CLI) ----
    specs = [("SUB", None, "submission at base 6525edf (package itself)"),
             ("SUB_eps_point", eps_variant(round(pt, 3)), f"EPS_EXTRA_AH = {pt:.3f} (budget point)"),
             ("SUB_eps_lo", eps_variant(round(lo, 3)), f"EPS_EXTRA_AH = {lo:.3f} (budget lower end)"),
             ("SUB_eps_hi", eps_variant(round(hi, 3)), f"EPS_EXTRA_AH = {hi:.3f} (budget upper end)")]
    if level == "L2":
        specs.append(("SUB_L", eps_variant(round(round(pt / 0.05) * 0.05, 2)), "point rounded to 0.05 Ah"))
    if a3["identified"]:
        specs.append(("SUB_A3fix", a3fix_variant(a3["a3_rel"]), f"anchor 3 Q_fc − a_3^rel ({a3['a3_rel']:.4f} Ah)"))
    if level == "L2" and a3["identified"]:
        specs.append(("SUB_L_A3fix", eps_variant(round(round(pt / 0.05) * 0.05, 2)) + a3fix_variant(a3["a3_rel"]),
                      "SUB_L and SUB_A3fix combined"))
    rows, diffs = [], {}
    for name, rep, desc in specs:
        if rep is None:
            soh = run_cli(PKG, os.path.join(ST, "cache", "out_wp4_SUB"))
        else:
            d, diff = build_variant(name, rep)
            diffs[name] = diff
            soh = run_cli(d, os.path.join(ST, "cache", f"out_wp4_{name}"))
        rows.append(dict(variant=name, description=desc, **{c: float(soh[c]) for c in soh.index}))
    sv = pd.DataFrame(rows)
    cks = [f"CK{k}" for k in range(8)]
    sub = sv.set_index("variant").loc["SUB", cks]
    for c in cks[1:]:
        sv[f"d{c}_pp"] = (sv[c] - sub[c]).round(3)
    sv["leaderboard_only"] = sv["variant"] != "SUB"
    sv.to_csv(os.path.join(OUT, "SOH_variants.csv"), index=False)
    budget["variant_diffs"] = diffs
    budget["SOH_variants_file"] = "wp4/SOH_variants.csv (leaderboard-only; never scored against proxies)"
    json.dump(budget, open(os.path.join(OUT, "budget_decision.json"), "w"), indent=1, default=float)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(json.dumps({k: v for k, v in budget.items() if k != "variant_diffs"}, indent=1, default=float))
    print(json.dumps(diffs, indent=1)); print(sv.to_string())


if __name__ == "__main__":
    main()
