"""Synthetic cells in the Challenge 1 file format, with a planted graphite step.

Self-test only (WP1): the truth of every quantity the study estimates is known here, so the
pipeline can be checked end to end without the real files. Nothing here is fitted to data.

Planted physics (Ah, per cycle at day t):
* capacity C(t) = C0 - L(t), L(t) = A_b (1 - exp(-t / tau_b)) + r_lin t;
* discharge-direction step at s_dis(t) = s_dis0 - b_dis L(t) below full;
* charge-direction step at s_chg(t) = s_chg0 - b_chg L(t) below the top of charge;
* charge content Q_chg(t) = C(t) + q_extra + eps_drift L(t).
The true discharge-side beta is therefore 1 / b_dis and the charge-side beta 1 / b_chg.
"""
import os

import numpy as np
import pandas as pd

COLUMNS = ["cycle_number", "step_type", "time_in_cycle_s", "voltage_V", "current_A",
           "temperature_C", "step_capacity_Ah", "absolute_time"]
V_CV = 3.65
V_CUT = 2.5
REST_S = 600.0


def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def fade(day, a_b=3.0, tau_b=20.0, r_lin=0.035):
    """Planted capacity loss (Ah) after ``day`` days."""
    return a_b * (1.0 - np.exp(-day / tau_b)) + r_lin * day


def v_dis(q, cap, s_dis, i_a, r_ohm):
    """Discharge voltage at q Ah below full."""
    return (3.30 + 0.030 * _sig((s_dis - q) / 0.7) - 0.0003 * q + 0.06 * np.exp(-q / 1.5)
            - 0.9 * np.exp((q - cap) / 1.0) - i_a * r_ohm)


def v_chg(x, q_top, s_chg, i_a, r_ohm):
    """Charge voltage after x Ah charged from empty."""
    return (3.31 + 0.030 * _sig((x - (q_top - s_chg)) / 0.7) + 0.0003 * x
            - 0.5 * np.exp(-x / 1.0) + 0.4 * np.exp((x - q_top) / 0.6) + i_a * r_ohm)


def _cycle_steps(day, c_rate, b_dis, b_chg, eps_drift, c0, s_dis0, s_chg0, q_extra, dt_s, r_ohm):
    """The four steps of one cycle as (kind, t, v, i, q) arrays, plus the planted truth."""
    i_a = c_rate * 102.0
    dq = i_a * dt_s / 3600.0
    loss = fade(day)
    cap = c0 - loss
    s_d = s_dis0 - b_dis * loss
    s_c = s_chg0 - b_chg * loss
    q_top = cap + q_extra + eps_drift * loss
    out, tc = [], 0.0

    x = np.arange(dq, q_top, dq)
    v = v_chg(x, q_top, s_c, i_a, r_ohm)
    n_cc = int(np.argmax(v >= V_CV)) if (v >= V_CV).any() else len(x)
    x_cv = float(x[n_cc - 1]) if n_cc else 0.0
    tau = max(q_top - x_cv, 1e-3) * 3600.0 / (0.95 * i_a)
    t_cv = np.arange(dt_s, -tau * np.log(0.05) + dt_s, dt_s)
    ch_q = np.r_[x[:n_cc], x_cv + i_a * tau * (1 - np.exp(-t_cv / tau)) / 3600.0]
    ch_i = np.r_[np.full(n_cc, i_a), i_a * np.exp(-t_cv / tau)]
    ch_v = np.r_[v[:n_cc], np.full(len(t_cv), V_CV)]
    ch_t = np.arange(1, len(ch_q) + 1) * dt_s
    out.append(("cccv_charge", ch_t, ch_v, ch_i, ch_q))
    tc = ch_t[-1]

    rt = tc + np.arange(dt_s, REST_S + dt_s, dt_s)
    out.append(("rest", rt, np.full(len(rt), 3.40), np.zeros(len(rt)), np.zeros(len(rt))))
    tc = rt[-1]

    qg = np.arange(dq, cap + 3.0, dq)
    vg = v_dis(qg, cap, s_d, i_a, r_ohm)
    cut = int(np.argmax(vg <= V_CUT))
    fine = np.linspace(qg[cut - 1], qg[cut], 400)
    q_cut = float(fine[np.argmax(v_dis(fine, cap, s_d, i_a, r_ohm) <= V_CUT)])
    d_q = np.r_[qg[:cut], q_cut]
    d_v = np.r_[vg[:cut], V_CUT]
    d_t = tc + np.r_[np.arange(1, cut + 1) * dt_s, q_cut * 3600.0 / i_a]
    out.append(("cc_discharge", d_t, d_v, np.full(len(d_q), -i_a), d_q))
    tc = d_t[-1]

    rt = tc + np.arange(dt_s, REST_S + dt_s, dt_s)
    out.append(("rest", rt, np.full(len(rt), 3.00), np.zeros(len(rt)), np.zeros(len(rt))))
    truth = {"day": day, "capacity": q_cut, "loss": loss, "s_dis": s_d, "s_chg": s_c,
             "q_top": float(ch_q[-1])}
    return out, rt[-1] + dt_s, truth


def make_cell(out_dir, cell_id, days=150.0, c_rate=0.5, b_dis=0.75, b_chg=0.75,
              eps_drift=0.0, c0=103.0, s_dis0=33.0, s_chg0=31.0, q_extra=0.3,
              dt_s=30.0, r_ohm=0.0006, temp_c=25.0, pause=(60.0, 3.0), seed=0,
              start="2024-01-01 00:00:00"):
    """Write <out_dir>/<cell_id>/<cell_id>_time_series_part01.csv; return the planted truth."""
    rng = np.random.default_rng(seed)
    frames, truth = [], []
    t_s, cycle = 0.0, 1
    while t_s < days * 86400.0:
        day = t_s / 86400.0
        if pause and pause[0] <= day < pause[0] + pause[1]:
            t_s = (pause[0] + pause[1]) * 86400.0
            continue
        steps, duration, tr = _cycle_steps(day, c_rate, b_dis, b_chg, eps_drift, c0, s_dis0,
                                           s_chg0, q_extra, dt_s, r_ohm)
        for kind, t, v, i, q in steps:
            n = len(t)
            frames.append(pd.DataFrame({
                "cycle_number": cycle, "step_type": kind, "time_in_cycle_s": t,
                "voltage_V": np.round(v + rng.normal(0.0, 0.0005, n), 3), "current_A": i,
                "temperature_C": temp_c + rng.normal(0.0, 0.3, n), "step_capacity_Ah": q,
                "abs_s": t_s + t}))
        truth.append({"cycle_number": cycle, **tr})
        t_s += duration
        cycle += 1
    frame = pd.concat(frames, ignore_index=True)
    stamps = pd.Timestamp(start) + pd.to_timedelta(frame.pop("abs_s").round(), unit="s")
    frame["absolute_time"] = stamps.dt.strftime("%Y-%m-%d %H:%M:%S")
    folder = os.path.join(out_dir, cell_id)
    os.makedirs(folder, exist_ok=True)
    frame[COLUMNS].to_csv(os.path.join(folder, f"{cell_id}_time_series_part01.csv"), index=False)
    return pd.DataFrame(truth)
