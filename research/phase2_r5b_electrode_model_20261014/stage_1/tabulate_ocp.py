"""Stage 1a: tabulate open-source half-cell OCPs from PyBaMM (run with cache/venv_ocp/bin/python)."""
import inspect
import json
import os

import numpy as np
import pybamm
from pybamm.input.parameters.lithium_ion.Chen2020 import graphite_LGM50_ocp_Chen2020
from pybamm.input.parameters.lithium_ion.Ecker2015 import graphite_ocp_Ecker2015
from pybamm.input.parameters.lithium_ion.Prada2013 import LFP_ocp_Afshar2017

HERE = os.path.dirname(os.path.abspath(__file__))
OCP = os.path.join(os.path.dirname(HERE), "ocp")
os.makedirs(OCP, exist_ok=True)
sto = np.round(np.arange(0.0, 1.0 + 1e-9, 0.001), 3)
tabs = {"lfp_afshar2017.csv": LFP_ocp_Afshar2017,
        "graphite_chen2020.csv": graphite_LGM50_ocp_Chen2020,
        "graphite_ecker2015.csv": graphite_ocp_Ecker2015}
meta = {"pybamm_version": pybamm.__version__, "grid": "stoichiometry 0..1 step 0.001", "files": {}}
for f, fn in tabs.items():
    u = np.asarray(fn(sto), float)
    np.savetxt(os.path.join(OCP, f), np.c_[sto, u], delimiter=",", header="sto,U_V", comments="", fmt="%.3f,%.8f")
    meta["files"][f] = dict(function=fn.__name__, module=inspect.getmodule(fn).__name__,
                            U_min=float(u.min()), U_max=float(u.max()))
json.dump(meta, open(os.path.join(OCP, "ocp_meta.json"), "w"), indent=1)
print(json.dumps(meta, indent=1))
