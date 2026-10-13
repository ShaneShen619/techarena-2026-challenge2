"""Freeze final source-domain config by whole-cell development selection."""
import json,sys
from pathlib import Path
import pandas as pd
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/"src"));sys.path.insert(0,str(TASK/"scripts"))
from source_model import fit_source
from reproduce_source import load_records

scores=pd.read_csv(TASK/"outputs/metrics_E3.csv")
eligible=scores.loc[scores.method.str.startswith("dynamic_")&~scores.method.str.contains("noKnee")]
best=eligible.sort_values(["macro_MAE_pp","method"]).iloc[0]
name,xi=best.method.split("_xi")
model=fit_source(load_records(),name)
artifact={"model":model,"xi0":float(xi),"selection":"source six-cell LOCO development mean; not independent test score",
          "selection_MAE_pp":float(best.macro_MAE_pp),"nominal_capacity_Ah":102.,
          "phase2_numeric_A_enabled":False,"source_identity_confirmed":"102Ah LFP specification only",
          "source_label_protocol":"single-cell high-rate discharge to 2.5V","target_label_protocol":"4S 5.1A to pack first11.2V",
          "calendar_term":"not independently identifiable; not added","prior_license":"Che D3 CC BY4.0; source target data reused under challenge permission"}
(TASK/"artifacts/source_prior.json").write_text(json.dumps(artifact,indent=2)+"\n")
print('Frozen source prior:',name,'xi0',xi,flush=True)
