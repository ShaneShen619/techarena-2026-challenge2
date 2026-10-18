"""WP1 LIC protocol audit: label the segments of every RPT and of the first cycles after it. No eps values.
Usage: python3 -I -B lic_audit.py <segments_all.csv> <lic.npz> <out_sequence.csv> <out_rpt_summary.csv>"""
import sys
import numpy as np
import pandas as pd

s = pd.read_csv(sys.argv[1]); z = np.load(sys.argv[2]); t, V, I = z["t"], z["V"].astype(float), z["I"]
nz = (s.sign != 0)
cap = s.index[(s.sign == -1) & s.I_med.between(-35, -20) & (s.Ah < -200)].tolist()
rows, summ, k = [], [], 0
for r in cap:
    empty_end = s.V1[r] <= 2.51
    # walk back to the last 1C discharge before this test
    a = r
    while a > 0 and not (s.sign[a - 1] == -1 and s.I_med[a - 1] < -200 and s.dur_h[a - 1] > 0.5):
        a -= 1
    a = max(a - 1, 0)
    # forward: the first three 1C charges after the test
    b, n1c = r, 0
    while b + 1 < len(s) and n1c < 3:
        b += 1
        if s.sign[b] == 1 and s.I_med[b] > 200:
            n1c += 1
    role = {}
    if empty_end:
        role[r] = "ref_dis_0.1C"
        if s.sign[r - 2] == 1 and 20 < s.I_med[r - 2] < 35 and s.Vmax[r - 2] >= 3.64: role[r - 2] = "ref_ch_0.1C_CCCV"
        if s.sign[r + 2] == 1 and s.I_med[r + 2] > 200: role[r + 2] = "op_ch_first_1C_CCCV"
        for j in range(a, r):
            if s.sign[j] == -1 and 20 < -s.I_med[j] < 35 and s.dur_h[j] > 4: role[j] = "dis_to_empty_0.1C_from_50pct"
            elif s.sign[j] == 1 and 20 < s.I_med[j] < 35 and abs(s.dur_h[j] - 5.387) < 0.05: role[j] = "set_50pct_0.1C_CC"
            elif s.sign[j] != 0 and s.dur_h[j] < 0.01: role[j] = "pulse_10s"
            elif s.sign[j] == -1 and 20 < -s.I_med[j] < 35 and s.dur_h[j] < 1: role[j] = "pre_dis_to_empty_0.1C"
    else:
        role[r] = "extra_0.1C_dis_TRUNCATED_10h"
    # unrecorded voltage jumps at I~0 in the pre-test rests
    jumps = []
    for j in range(a, r + 1):
        if s.sign[j] == 0:
            m = (t >= s.t0[j]) & (t <= s.t1[j]); v = V[m]
            if len(v) > 1:
                dv = np.abs(np.diff(v)); i = int(np.argmax(dv))
                if dv[i] >= 0.1: jumps.append((j, float(v[i]), float(v[i + 1])))
    for j in range(a, b + 1):
        rows.append(dict(test=k if empty_end else f"extra_before_{k}", seg=j, role=role.get(j, "rest" if s.sign[j] == 0 else
                         ("op_1C_dis" if s.I_med[j] < -200 else "op_1C_ch" if s.I_med[j] > 200 else "other")),
                         **{c: s.loc[j, c] for c in ["sign", "t0", "dur_h", "Ah", "I_med", "I_end", "V0", "V1", "Vmax", "Vmin", "Tm"]}))
    rc, ro = r - 2, r + 2
    summ.append(dict(test=k if empty_end else f"extra_before_{k}", ref_dis_seg=r, empty_end=bool(empty_end),
                     ref_ch_present=role.get(rc) == "ref_ch_0.1C_CCCV", op_first_present=role.get(ro) == "op_ch_first_1C_CCCV",
                     order="ref_ch -> rest -> ref_dis -> rest -> op_ch_first" if empty_end else "full -> 0.1C dis truncated",
                     ref_ch_start_V=s.V0[rc] if empty_end else np.nan, rest_before_ref_ch_h=s.dur_h[rc - 1] if empty_end else np.nan,
                     ref_ch_I_end=s.I_end[rc] if empty_end else np.nan,
                     op_ch_start_V=s.V0[ro] if empty_end else np.nan, rest_before_op_ch_h=s.dur_h[ro - 1] if empty_end else np.nan,
                     op_ch_I_end=s.I_end[ro] if empty_end else np.nan, Tm_ref=s.Tm[r], Tm_op_ch=s.Tm[ro] if empty_end else np.nan,
                     unrecorded_jumps=";".join(f"seg{j}:{v0:.3f}->{v1:.3f}V" for j, v0, v1 in jumps)))
    if empty_end:
        k += 1
pd.DataFrame(rows).to_csv(sys.argv[3], index=False)
S = pd.DataFrame(summ); S.to_csv(sys.argv[4], index=False)
pd.set_option("display.width", 250)
print(S.round(3).to_string(index=False))
