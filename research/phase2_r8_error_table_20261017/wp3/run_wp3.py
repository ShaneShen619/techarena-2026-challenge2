"""WP3: anchor table, one row per anchor 0..7 (EXECUTION_PROMPT.md, WP3). Diagnostic, built from the full data."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common8 import H  # noqa: E402
from events import CELLS, charge_step_split, segment_arrays  # noqa: E402
from v2 import anchors_by_checkup  # noqa: E402

RESEARCH = os.path.dirname(STUDY)
R7 = os.path.join(RESEARCH, "phase2_r7_lit_checks_20261016")
EVENTS = os.path.join(RESEARCH, "phase2_r6_robust_20261016", "sources", "rebound_diagnosis", "outputs", "events_merged.csv")
OUT = os.path.join(STUDY, "outputs")
CV_V = 13.95
I_CUT_2 = 6.0


def charge_profile(op, r):
    g = op[op["segment"] == r["segment"]].reset_index(drop=True)
    s, e = r["_seg_index"]
    t, i, ah = segment_arrays(g)
    base = ah[s - 1 if s > 0 else s]
    u = g["pack_voltage_V"].to_numpy(float)
    return g, s, e, t, i, ah, base, u


def q_at_cut(i, ah, base, u, s, e, i_cut):
    """Charge integrated up to the first CV sample whose current is <= i_cut (the end sample if none)."""
    cv0 = s + int(np.argmax(u[s:e + 1] >= CV_V))
    idx = np.where(i[cv0:e + 1] <= i_cut + 1e-12)[0]
    j = cv0 + int(idx[0]) if len(idx) else e
    return float(ah[j] - base), j


def build():
    op = H.full_op()
    fc = H.full_charges(op).sort_values("t_end").reset_index(drop=True)
    anc = anchors_by_checkup(fc, H.CK)
    assert sorted(anc) == list(range(8)) and len(fc) == 8
    base = pd.read_csv(os.path.join(R7, "wp1", "outputs", "anchor_state_table.csv"))
    s3a = pd.read_csv(os.path.join(R7, "wp0", "outputs", "wp0_3a_start_state.csv"))
    ev = pd.read_csv(EVENTS, parse_dates=["t_cv_end"])
    a4 = charge_step_split(op, fc, smooth_Ah=2.0)
    i_cut = float(fc["I_end_A"].max())
    rows = []
    for j in range(8):
        r = anc[j]
        g, s, e, t, i, ah, b0, u = charge_profile(op, r)
        q1, j1 = q_at_cut(i, ah, b0, u, s, e, i_cut)
        q2, j2 = q_at_cut(i, ah, b0, u, s, e, I_CUT_2)
        cv0 = s + int(np.argmax(u[s:e + 1] >= CV_V))
        st = a4[a4["segment"] == r["segment"]].iloc[0]
        tops = [float(st[f"step_to_top_{c}"]) for c in CELLS]
        e_near = ev.iloc[(ev["t_cv_end"] - r["t_end"]).abs().argmin()]
        sa = s3a[s3a["anchor"] == j].iloc[0]
        end_v = [float(r[f"end_{c}"]) for c in CELLS]
        row = dict(anchor=j, Q_fc_check=float(r["Q_Ah"]), I_end_A_check=float(r["I_end_A"]),
                   I_cut_common_A=i_cut, Q_fc_cut_common=q1, dQ_cut_common=q1 - float(r["Q_Ah"]),
                   Q_fc_cut6A=q2, dQ_cut6A=q2 - float(r["Q_Ah"]),
                   cv_Ah=float(ah[e] - ah[cv0 - 1]), cv_h=float((t[e] - t[cv0]) / 3600.0),
                   cc_Ah=float(ah[cv0 - 1] - b0), T_charge_mean_C=float(r["temp_C"]),
                   T_charge_max_C=float(g["temp_mean_C"].iloc[s:e + 1].max()),
                   **{f"start_rest_{c}": float(sa[c]) for c in CELLS},
                   start_rest_spread_V=float(max(sa[c] for c in CELLS) - min(sa[c] for c in CELLS)),
                   **{f"step_to_top_{c}": x for c, x in zip(CELLS, tops)},
                   step_to_top_mean_check=float(np.mean(tops)), step_to_top_spread_Ah=float(max(tops) - min(tops)),
                   pulse_event_t_cv_end=str(e_near["t_cv_end"]),
                   pulse_event_lag_h=float((e_near["t_cv_end"] - r["t_end"]).total_seconds() / 3600.0),
                   R_mean_mOhm=float(e_near["R_mean_mOhm"]),
                   **{f"R_{c[:-2]}_mOhm": float(e_near[f"R_{c}"]) for c in CELLS},
                   **{f"end_{c}": x for c, x in zip(CELLS, end_v)},
                   cv_end_spread_V=float(max(end_v) - min(end_v)))
        rows.append(row)
    t = pd.DataFrame(rows)
    out = base.merge(t, on="anchor", how="left")
    assert np.allclose(out["Q_fc"], out["Q_fc_check"], atol=1e-9)
    assert np.allclose(out["step_to_top"], out["step_to_top_mean_check"], atol=1e-9)
    out["dR_mean_from_anchor0_mOhm"] = out["R_mean_mOhm"] - out["R_mean_mOhm"].iloc[0]
    for c in CELLS:
        k = f"R_{c[:-2]}_mOhm"
        out[f"d{k}_from_anchor0"] = out[k] - out[k].iloc[0]
    out["dQ_fc_next"] = out["Q_fc"].shift(-1) - out["Q_fc"]
    out["dQ_fc_cut_common_next"] = out["Q_fc_cut_common"].shift(-1) - out["Q_fc_cut_common"]
    out["dQ_fc_cut6A_next"] = out["Q_fc_cut6A"].shift(-1) - out["Q_fc_cut6A"]
    out["cum_fade_Ah"] = H.Q_CK0 - out["Q_fc"] - H.EPS0
    return out.drop(columns=["Q_fc_check", "step_to_top_mean_check"])


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    tab = build()
    tab.to_csv(os.path.join(OUT, "table_anchors.csv"), index=False)
    os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
    num = tab.select_dtypes("number")
    desc = dict(I_cut_common_A=float(tab["I_cut_common_A"].iloc[0]),
                dQ_cut_common_range=[float(tab["dQ_cut_common"].min()), float(tab["dQ_cut_common"].max())],
                dQ_cut6A_range=[float(tab["dQ_cut6A"].min()), float(tab["dQ_cut6A"].max())],
                sd_dQ_next=float(tab["dQ_fc_next"].std()), sd_dQ_next_25C=float(tab["dQ_fc_next"].iloc[1:].std()),
                sd_dQ_next_cut6A_25C=float(tab["dQ_fc_cut6A_next"].iloc[1:].std()),
                pulse_lag_h_max=float(tab["pulse_event_lag_h"].abs().max()))
    json.dump(desc, open(os.path.join(HERE, "outputs", "wp3_describe.json"), "w"), indent=1)
    pd.set_option("display.width", 250)
    print(json.dumps(desc, indent=1))
    print(tab.T.to_string())
