"""WP4 part 1: evaluate the registered combination and choose the final candidate (protocol.json)."""
import hashlib
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common10 import H  # noqa: E402
import cellcand as CC  # noqa: E402
import diag10 as D  # noqa: E402
import gates10 as G  # noqa: E402

OUT = os.path.join(HERE, "outputs")
PROTO = os.path.join(HERE, "protocol.json")
assert hashlib.sha256(open(PROTO, "rb").read()).hexdigest() == open(os.path.join(HERE, "protocol.sha256")).read().split()[0]
V = list(G.VARIANTS)
TAU3 = json.load(open(os.path.join(STUDY, "wp2", "protocol.json")))["B3_tau_Ah"]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    comb = CC.make(CC.provider_ensemble(V, "median"), mode="change", combine=CC.combine_reject(TAU3), selection_step="main")
    df = G.predict({"SUB": G.SUB, "COMBO": comb})
    w2 = pd.read_csv(os.path.join(STUDY, "wp2", "outputs", "wp2_predictions.csv"))
    a = df[df.model == "COMBO"].set_index(["scenario", "k", "delta"])["Q"]
    b = w2[(w2.model == "B3") & (w2.step == "main")].set_index(["scenario", "k", "delta"])["Q"]
    same_as_B3 = bool(float((a - b.reindex(a.index)).abs().max()) < 1e-12)
    g2 = pd.read_csv(os.path.join(STUDY, "wp2", "outputs", "wp2_gates.csv"), index_col=0)
    g1 = pd.read_csv(os.path.join(STUDY, "wp1", "outputs", "wp1_gates.csv"), index_col=0)
    combo_g = g2.loc["B3"].to_dict()      # identical predictor -> identical gates (asserted above)
    singles = {"A3": float(g1.loc["A3", "causal"]), "B3": float(g2.loc["B3", "causal"])}
    combo_ok = bool(combo_g["passes"]) and combo_g["causal"] < min(singles.values())
    final = "COMBO" if combo_ok else min(singles, key=singles.get)
    out = dict(combination_equals_B3=same_as_B3, combination_passes=bool(combo_g["passes"]),
               combination_causal=float(combo_g["causal"]), singles_causal=singles, final=final)
    json.dump(out, open(os.path.join(OUT, "wp4_decision.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    if not same_as_B3:
        raise SystemExit("combination differs from B3")
