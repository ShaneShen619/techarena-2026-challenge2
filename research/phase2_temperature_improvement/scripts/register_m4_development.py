"""Register complete M4 wave-residual development ablations for one scorer."""
from pathlib import Path

import pandas as pd

TASK = Path(__file__).resolve().parents[1]
source = pd.read_csv(TASK / "runs/M4_wave_residual_v1/predictions.csv")
if len(source) != 360:
    raise AssertionError("two M4 methods need full 180 targets each")
current = pd.read_csv(TASK / "outputs/predictions.csv")
current = current.loc[~current.method.isin(source.method.unique())]
pd.concat([current, source], ignore_index=True).to_csv(TASK / "outputs/predictions.csv", index=False)
