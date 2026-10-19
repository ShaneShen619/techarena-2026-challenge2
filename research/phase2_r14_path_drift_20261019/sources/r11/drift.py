"""'SUB + drift d' exactly as round 7 WP3 run_wp3.py: Q' = Q + d * max(0, 100.41 - Q)."""
import numpy as np

NOM, Q0 = 102.0, 100.41


def add_drift(soh, d):
    q = np.asarray(soh, float) * NOM / 100.0
    return (q + d * np.maximum(0.0, Q0 - q)) / NOM * 100.0
