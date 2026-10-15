"""Stage 0: reproduce V2/M4/S_main/ENS50 and run the cold-start baselines (protocol.json)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from common5c import H  # noqa: E402
from preds5c import ens, s_pred  # noqa: E402
from runner5c import COLD, PSEUDO, run, scen_mean  # noqa: E402

OUT = os.path.join(HERE, "outputs")
S = s_pred("S_main")
P = dict(H.BASELINES)
P.update({"S_main": S, "ENS50": ens(S, 0.5)})
real = run(P, ("real",))
met = H.metrics(real)
m = met.set_index(["model", "delta"])
rep = {mod: dict(MAE=float(m.loc[(mod, 0.4), "MAE"]), MAX=float(m.loc[(mod, 0.4), "MAX"])) for mod in P}
ok = (abs(rep["V2"]["MAE"] - 0.215726) < 5e-7 and abs(rep["V2"]["MAX"] - 0.669052) < 5e-7 and
      abs(rep["M4"]["MAE"] - 0.291265) < 5e-7 and abs(rep["S_main"]["MAE"] - 0.326) < 5e-4 and
      abs(rep["ENS50"]["MAE"] - 0.214) < 5e-4)
rep["reproduced"] = bool(ok)
real.to_csv(os.path.join(OUT, "S0_real_predictions.csv"), index=False)
if not ok:
    json.dump(rep, open(os.path.join(OUT, "S0_reproduce.json"), "w"), indent=1)
    raise SystemExit("reproduction failed")
cold = run(P, COLD + PSEUDO)
cold.to_csv(os.path.join(OUT, "S0_cold_pseudo_predictions.csv"), index=False)
cm = H.metrics(cold)
cm.to_csv(os.path.join(OUT, "S0_cold_pseudo_metrics.csv"), index=False)
rep["cold_start_mean_MAE"] = {mod: scen_mean(cm, COLD, mod) for mod in P}
rep["pseudo_mean_MAE"] = {mod: scen_mean(cm, PSEUDO, mod) for mod in P}
rep["per_scenario_d04"] = cm[(cm["delta"] == 0.4)].pivot_table(index="model", columns="scenario", values="MAE").round(4).to_dict()
rep["T6_reference_V2_cs_MAE"] = rep["cold_start_mean_MAE"]["V2"]
json.dump(rep, open(os.path.join(OUT, "S0_reproduce_and_coldstart.json"), "w"), indent=1)
print(json.dumps(rep, indent=1))
c = cold[(cold.delta == 0.4) & cold.scenario.isin(COLD)].pivot_table(index=["scenario", "checkup"], columns="model", values="err_pp")
print(c.round(3).to_string())
