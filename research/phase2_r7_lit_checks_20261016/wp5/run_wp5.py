"""WP5: decision table and SOH tables from the registered WP1-WP3 outcomes (protocol.json)."""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
OUT = os.path.join(HERE, "outputs")
NOM = 102.0

w1 = json.load(open(os.path.join(STUDY, "wp1", "outputs", "wp1_predictions_P.json")))
w2 = json.load(open(os.path.join(STUDY, "wp2", "outputs", "wp2_real_summary.json")))
w3 = json.load(open(os.path.join(STUDY, "wp3", "outputs", "wp3_pooling.json")))
soh = pd.read_csv(os.path.join(STUDY, "wp2", "outputs", "wp2_real_SOH_d04.csv"), index_col="model")

d = w3["d_recommended"]
ck2 = "recommend switching to T_main (not wired)" if w2["T_main_passes"] else "keep SUB"
r6 = ["P_drift", "P_stress_early", "P_start"]
order = r6[1:] + r6[:1] if w3["recommendation"] == "sign_not_robust" else r6
tab = {}
for base in ("SUB", "T_main"):
    q = soh.loc[base] * NOM / 100
    tab[base] = soh.loc[base]
    tab[f"{base}+drift{d}"] = (q + d * (100.41 - q).clip(lower=0)) / NOM * 100
soh_t = pd.DataFrame(tab).T.round(3)
soh_t.to_csv(os.path.join(OUT, "wp5_SOH_table.csv"))
dec = {"CK2": ck2, "CK2_SOH": {"SUB": round(w2["CK2_SOH"]["SUB"], 3), "T_main": round(w2["CK2_SOH"]["T_main"], 3),
                               "T_ea37": round(w2["CK2_SOH"]["T_ea37"], 3), "T_seg25_sensitivity": round(w2["CK2_SOH"]["T_seg25"], 3)},
       "offset_interpretation": w1["classification"], "hidden_C20_order": w1["order_main"],
       "d_for_P_drift": d, "drift_recommendation": w3["recommendation"], "probe_order_round6": r6, "probe_order_round7": order,
       "probe_base": "T_main if adopted, else SUB"}
json.dump(dec, open(os.path.join(OUT, "wp5_decision.json"), "w"), indent=1)
print(json.dumps(dec, indent=1))
print(soh_t.to_string())
