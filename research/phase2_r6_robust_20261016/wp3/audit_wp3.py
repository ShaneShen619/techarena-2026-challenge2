"""WP3 audits (protocol.json): 3a start-state spread and 3c path-effect verification. No model metric."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common6 import H  # noqa: E402
from events import CELLS, tail_margin_Ah  # noqa: E402
from v2 import anchors_by_checkup  # noqa: E402

OUT = os.path.join(HERE, "outputs")


def rest_voltages(op, fc):
    rows = []
    for _, r in fc.sort_values("t_end").iterrows():
        g = op[op["segment"] == r["segment"]].reset_index(drop=True)
        s, e = r["_seg_index"]
        v = g[CELLS].iloc[s - 1 if s > 0 else s]
        rest_h = r["rest_before_h"]
        rows.append(dict(t_end=r["t_end"], segment=int(r["segment"]), setpoint=int(r["setpoint_C"]), Q_fc=float(r["Q_Ah"]),
                         rest_before_h=float(rest_h), pack_rest_V=float(v.sum()), **{c: float(v[c]) for c in CELLS}))
    return pd.DataFrame(rows)


def audit_3a():
    full = H.full_op()
    fc = H.full_charges(full)
    ref = H.load_dataset(H.DATA).reference_discharge
    rv = rest_voltages(full, fc)
    rv["r_upper"] = [tail_margin_Ah(ref, {c: row[c] for c in CELLS}) for _, row in rv.iterrows()]
    rv["r_half"] = rv["r_upper"] / 2
    rv["dr_upper"] = rv["r_upper"] - rv["r_upper"].iloc[0]
    anc = anchors_by_checkup(fc, H.CK)
    rv["anchor"] = [next((j for j, a in anc.items() if a["t_end"] == t), -1) for t in rv["t_end"]]
    rv.to_csv(os.path.join(OUT, "wp3a_start_state.csv"), index=False)
    spread = float(rv["dr_upper"].abs().max())
    return dict(max_abs_dr_upper_Ah=spread, exit=bool(spread < 0.1),
                r_upper=dict(zip(rv["anchor"].astype(int), rv["r_upper"].round(4))),
                pack_rest_V=dict(zip(rv["anchor"].astype(int), rv["pack_rest_V"].round(3))))


def audit_3c():
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
            trend = float(np.median(-d[1:])) if len(d) >= 2 else 0.0      # typical later decline per program
            rows.append(dict(variant=v, anchor_t_end=a["t_end"], segment=int(seg), setpoint=int(st.loc[i1, "setpoint_C"]),
                             lag_h=float((st.loc[i1, "t_cv_end"] - a["t_end"]).total_seconds() / 3600),
                             raw_offset=raw, trend_per_program=trend, adj_offset=raw - trend, n_after=len(same)))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "wp3c_path_offsets.csv"), index=False)
    med = df.groupby("variant")["adj_offset"].median()
    ok = int(((med >= 0.2) & (med <= 0.7)).sum())
    return dict(median_adj_offset_by_variant=med.round(3).to_dict(),
                median_raw_offset_by_variant=df.groupby("variant")["raw_offset"].median().round(3).to_dict(),
                variants_in_range=ok, verified=bool(ok >= 5), n_anchor_cases=int(len(df) / max(1, df["variant"].nunique())))


if __name__ == "__main__":
    a = audit_3a()
    c = audit_3c()
    out = {"3a": a, "3c": c}
    json.dump(out, open(os.path.join(OUT, "wp3_audits.json"), "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))
