"""Anchor-charge curves and CK0 reference curve for the electrode model."""
import numpy as np
import pandas as pd

from events import CELLS, segment_arrays


def anchor_curve(op, row, skip_Ah=2.0):
    """q (Ah from start), I (A), V (n x 4) of one anchor charge; first ``skip_Ah`` excluded.
    Also returns the per-cell rest voltage just before the charge."""
    g = op[op["segment"] == row["segment"]].reset_index(drop=True)
    s, e = row["_seg_index"]
    _, I, ah = segment_arrays(g)
    base = ah[s - 1 if s > 0 else s]
    q = ah[s:e + 1] - base
    V = g[CELLS].to_numpy(float)[s:e + 1]
    Ii = I[s:e + 1]
    v_rest = g[CELLS].to_numpy(float)[s - 1] if s > 0 else V[0]
    # duplicate timestamps mark step transitions: keep strictly increasing q in the CC/CV part
    keep = (q >= skip_Ah) & (Ii > 0.5)
    return q[keep], Ii[keep], V[keep], v_rest, float(q[-1])


def ck0_curve(ref):
    d = ref["discharged_Ah"].to_numpy(float)
    V = ref[CELLS].to_numpy(float)
    c_pack = float(np.median(ref["voltage_V"].to_numpy(float) - V.sum(axis=1)))
    return d, V, c_pack
