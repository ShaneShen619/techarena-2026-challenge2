"""Round-5A pack stress model S (stage 3). numpy/pandas only, so the candidate class can reuse it.

L(t) = A_cal * (tau_eff(t) + tau0)^z + A_cyc * ah_eff(t)   [Ah]
Fit (MAP) on consecutive visible anchor pairs; predict CK_k from the latest anchor.
"""
import numpy as np
import pandas as pd

from r5c_stress import cumulative, horizon_lag_days, stress_table

Q_CK0 = 100.41
R_GAS = 8.314462618
TREF = 298.15

MAIN = dict(z=0.2, Ea_kJ=37.3, sigma=0.20, logA_cal_mu=0.8302140193463242, logA_cyc_mu=-11.754453247878848,
            logA_sd=float(np.log(3.0)), o45_sd=0.3, z_free=False, z_sd=0.2529733798295173,
            use_cal=True, use_cyc=True, prior_A=True, tau0=0.0, checkup_Ah=0.0)


def yagci_logA_cal(z, Ea_kJ):
    """Yagci-derived calendar scale at a given z (same rule as stage 2 fallback)."""
    aT = lambda T: np.exp(-Ea_kJ * 1e3 / R_GAS * (1 / (T + 273.15) - 1 / TREF))
    cal = {35: (7.5 + 7.8) / 2 / 100, 50: (13.3 + 14.0) / 2 / 100}
    vals = [102.0 * cal[T] / (aT(T) * 848.0) ** z for T in (35, 50)]
    return float(np.mean(np.log(vals)))


def anchors(fc, ck):
    """Anchor j -> (t_start, Q_Ah, setpoint): first full charge after CK_j."""
    out = {}
    if fc is None or len(fc) == 0:
        return out
    for _, r in fc.sort_values("t_end").iterrows():
        j = int((ck < r["t_end"]).sum()) - 1
        if j >= 0 and j not in out:
            out[j] = (pd.Timestamp(r["t_start"]), float(r["Q_Ah"]), int(r["setpoint_C"]))
    return out


def _lm(fun, x0, n_iter=200, tol=1e-12):
    """Damped Gauss-Newton (Levenberg-Marquardt) with a forward-difference Jacobian. Deterministic."""
    x = np.asarray(x0, float).copy()
    r = fun(x)
    cost = float(r @ r)
    lam = 1e-3
    for _ in range(n_iter):
        J = np.empty((len(r), len(x)))
        for i in range(len(x)):
            h = 1e-6 * max(1.0, abs(x[i]))
            xp = x.copy()
            xp[i] += h
            J[:, i] = (fun(xp) - r) / h
        g = J.T @ r
        A = J.T @ J
        improved = False
        for _ in range(30):
            step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-12), -g)
            xn = x + step
            rn = fun(xn)
            cn = float(rn @ rn)
            if cn < cost:
                improved = True
                x, r, done = xn, rn, cost - cn < tol * max(1.0, cost)
                cost = cn
                lam = max(lam / 10, 1e-12)
                break
            lam *= 10
        if not improved or done:
            break
    return x, cost


class StressFit:
    """Fit/predict for one cutoff. ``cfg`` overrides MAIN."""

    def __init__(self, cfg=None):
        self.cfg = dict(MAIN, **(cfg or {}))

    def _terms(self, tau, ah, z):
        c = self.cfg
        cal = np.power(np.clip(tau + c["tau0"], 0, None), z) if c["use_cal"] else np.zeros_like(tau)
        cyc = ah if c["use_cyc"] else np.zeros_like(ah)
        return cal, cyc

    def run(self, op, fc, ck, at_date, eps, tab_cache=None, key=None):
        c = self.cfg
        ck = pd.DatetimeIndex(ck)
        k = int((ck <= pd.Timestamp(at_date)).sum()) - 1
        anc = anchors(fc, ck)
        vis = sorted(j for j in anc if j <= k - 1)
        L = horizon_lag_days(fc, ck, pd.Timestamp(at_date))
        hz = ck[k] + pd.Timedelta(days=L)
        ckey = (key, c["checkup_Ah"], str(hz))
        if tab_cache is not None and key is not None and ckey in tab_cache:
            tab = tab_cache[ckey]
        else:
            tab = stress_table(op, ck[k], ck, horizon=hz, checkup_Ah=c["checkup_Ah"])
            if tab_cache is not None and key is not None:
                tab_cache[ckey] = tab
        times = [anc[j][0] for j in vis] + [hz]
        tau, ah = cumulative(tab, c["Ea_kJ"] * 1e3, t_eval=times)
        pairs = [(i - 1, i) for i in range(1, len(vis)) if vis[i] == vis[i - 1] + 1]
        if c.get("prior_only"):
            pairs = []

        # parameter vector: [logA_cal, logA_cyc, o45, (z)]
        mu = np.array([c["logA_cal_mu"], c["logA_cyc_mu"], 0.0] + ([c["z"]] if c["z_free"] else []))
        sd = np.array([c["logA_sd"], c["logA_sd"], c["o45_sd"]] + ([c["z_sd"]] if c["z_free"] else []))

        def unpack(x):
            z = x[3] if c["z_free"] else c["z"]
            return x[0], x[1], x[2], min(max(z, 0.02), 1.5)

        def resid(x):
            lac, lay, o45, z = unpack(x)
            cal, cyc = self._terms(tau, ah, z)
            M = np.exp(lac) * cal + np.exp(lay) * cyc
            res = []
            for a, b in pairs:
                dq_obs = anc[vis[b]][1] - anc[vis[a]][1]
                dq_mod = -(M[b] - M[a]) - (o45 if vis[a] == 0 else 0.0)
                res.append((dq_obs - dq_mod) / c["sigma"])
            pri = (x - mu) / sd
            if not c["prior_A"]:
                pri = pri.copy()
                pri[0] = pri[1] = 0.0
            if not c["use_cal"]:
                pri[0] = x[0] - mu[0]
            if not c["use_cyc"]:
                pri[1] = x[1] - mu[1]
            return np.r_[np.array(res, float), pri]

        if pairs:
            x, cost = _lm(resid, mu)
            if not c["prior_A"]:
                x[0] = min(max(x[0], np.log(1e-6)), np.log(1e3))
                x[1] = min(max(x[1], np.log(1e-12)), np.log(1e-1))
        else:
            x, cost = mu.copy(), 0.0
        # Laplace posterior SDs (residuals are already scaled)
        psd = np.full(len(x), np.nan)
        if pairs:
            r0 = resid(x)
            J = np.empty((len(r0), len(x)))
            for i in range(len(x)):
                h = 1e-6 * max(1.0, abs(x[i]))
                xp = x.copy()
                xp[i] += h
                J[:, i] = (resid(xp) - r0) / h
            try:
                psd = np.sqrt(np.clip(np.diag(np.linalg.pinv(J.T @ J)), 0, None))
            except np.linalg.LinAlgError:
                pass
        lac, lay, o45, z = unpack(x)
        cal, cyc = self._terms(tau, ah, z)
        M = np.exp(lac) * cal + np.exp(lay) * cyc
        last = vis[-1] if vis else None
        if last is None:
            base, i_last = Q_CK0, None
        elif last == 0:
            base, i_last = Q_CK0, len(vis) - 1     # mirrors M4/V2: CK0 label at the 45 C anchor
        else:
            base, i_last = anc[last][1] + eps, len(vis) - 1
        dM = M[-1] - (M[i_last] if i_last is not None else 0.0)
        q = base - dM
        info = dict(A_cal=float(np.exp(lac) if c["use_cal"] else 0.0),
                    A_cyc=float(np.exp(lay) if c["use_cyc"] else 0.0),
                    o45=float(o45), z=float(z), n_pairs=len(pairs), horizon_lag_d=L,
                    loss_cal=float(np.exp(lac) * (cal[-1] - (cal[i_last] if i_last is not None else 0.0))),
                    loss_cyc=float(np.exp(lay) * (cyc[-1] - (cyc[i_last] if i_last is not None else 0.0))),
                    last_anchor=-1 if last is None else int(last),
                    sd_logA_cal=float(psd[0]), sd_logA_cyc=float(psd[1]), sd_o45=float(psd[2]))
        return float(q), info
