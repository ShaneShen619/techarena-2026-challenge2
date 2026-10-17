"""Round-6 WP3 audits 3a (start state) and 3c (path offsets), copied unchanged in logic from
research/phase2_r6_robust_20261016/wp3/audit_wp3.py (functions rest_voltages, audit_3a, audit_3c);
here they return DataFrames instead of writing files."""
import numpy as np
import pandas as pd

from common8 import H
from events import CELLS, tail_margin_Ah
from v2 import anchors_by_checkup


def rest_voltages(op, fc):
    rows = []
    for _, r in fc.sort_values("t_end").iterrows():
        g = op[op["segment"] == r["segment"]].reset_index(drop=True)
        s, e = r["_seg_index"]
        v = g[CELLS].iloc[s - 1 if s > 0 else s]
        rows.append(dict(t_end=r["t_end"], segment=int(r["segment"]), setpoint=int(r["setpoint_C"]), Q_fc=float(r["Q_Ah"]),
                         rest_before_h=float(r["rest_before_h"]), pack_rest_V=float(v.sum()), **{c: float(v[c]) for c in CELLS}))
    return pd.DataFrame(rows)


def table_3a():
    full = H.full_op()
    fc = H.full_charges(full)
    ref = H.load_dataset(H.DATA).reference_discharge
    rv = rest_voltages(full, fc)
    rv["r_upper"] = [tail_margin_Ah(ref, {c: row[c] for c in CELLS}) for _, row in rv.iterrows()]
    rv["r_half"] = rv["r_upper"] / 2
    rv["dr_upper"] = rv["r_upper"] - rv["r_upper"].iloc[0]
    anc = anchors_by_checkup(fc, H.CK)
    rv["anchor"] = [next((j for j, a in anc.items() if a["t_end"] == t), -1) for t in rv["t_end"]]
    return rv


def table_3c():
    full = H.full_op()
    fc = H.full_charges(full).sort_values("t_end")
    rows = []
    for v, cfg in H.STEP_VARIANTS.items():
        st = H.step_programs(full, **cfg).dropna(subset=["step_mean"]).sort_values("t_cv_end").reset_index(drop=True)
        for j, (_, a) in enumerate(fc.iterrows()):
            idx = np.where(st["t_cv_end"] >= a["t_end"] - pd.Timedelta(minutes=10))[0]
            if len(idx) < 2:
                continue
            i1 = idx[0]
            seg = st.loc[i1, "segment"]
            same = st[(st["segment"] == seg) & (st.index >= i1)]
            if len(same) < 2:
                continue
            d = np.diff(same["step_mean"].to_numpy())
            raw = float(same["step_mean"].iloc[0] - same["step_mean"].iloc[1])
            trend = float(np.median(-d[1:])) if len(d) >= 2 else 0.0
            rows.append(dict(variant=v, anchor_t_end=a["t_end"], segment=int(seg), setpoint=int(st.loc[i1, "setpoint_C"]),
                             lag_h=float((st.loc[i1, "t_cv_end"] - a["t_end"]).total_seconds() / 3600),
                             raw_offset=raw, trend_per_program=trend, adj_offset=raw - trend, n_after=len(same)))
    return pd.DataFrame(rows)
