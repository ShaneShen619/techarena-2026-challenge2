"""Stage D step 2: real-data and leave-one-anchor-out (LOA) results for D0-D3; gates."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
import harness as H  # noqa: E402
import gapx  # noqa: E402

sel = json.load(open(os.path.join(HERE, "selection.json")))
preds = {"V2": H.v2_pred, "M4": H.m4_pred, **{r: gapx.make(r) for r in gapx.RULES}}
real = H.run(preds, scenarios=("real",))


def loa(f):
    def g(ctx):
        k, fc = ctx["k"], ctx["fc"]
        drop = (fc["t_end"] > H.CK[k - 1]) & (fc["t_end"] < H.CK[k])
        return f(dict(ctx, fc=fc[~drop].reset_index(drop=True)))
    return g


lo = H.run({n: loa(f) for n, f in preds.items()}, scenarios=("real",), deltas=(0.4,))
lo = lo[lo["k"] >= 2].assign(scenario="LOA")
real.to_csv(os.path.join(HERE, "outputs", "D_real_long.csv"), index=False)
lo.to_csv(os.path.join(HERE, "outputs", "D_loa_long.csv"), index=False)
met = H.metrics(real)
met.to_csv(os.path.join(HERE, "outputs", "D_real_metrics.csv"), index=False)
pck = H.per_ck(real)
ch = sel["chosen"]
g = H.gates_vs_v2(met, pck, ch)
ck2 = float(pck.loc["CK2", ch])
g["CK2_abs_decreases"] = dict(chosen=abs(ck2), V2=abs(float(pck.loc["CK2", "V2"])), passed=abs(ck2) < abs(float(pck.loc["CK2", "V2"])))
g["PG_MAE_improves"] = dict(chosen=sel["PG_MAE"][ch], D0=sel["PG_MAE"]["D0"], passed=sel["PG_MAE"][ch] < sel["PG_MAE"]["D0"])
g["note"] = "chosen rule is D0 (identical to V2); stage D adds no change" if ch == "D0" else ""
json.dump(g, open(os.path.join(HERE, "outputs", "D_gates.json"), "w"), indent=1, default=float)
print(pck.round(3))
print(met[(met.step == "main") & (met.delta == 0.4)][["model", "MAE", "MAX", "CK2_7_MAE"]].round(3).to_string(index=False))
print("LOA\n", lo.pivot_table(index="checkup", columns="model", values="err_pp").round(3))
print("LOA MAE", lo.groupby("model")["err_pp"].apply(lambda e: e.abs().mean()).round(3).to_dict())
print(json.dumps(g, indent=1, default=float))
