"""Route B: constrained low-order SOC/capacity estimator with information gate.

The released CK0 C/20 discharge curve supplies only a *quasi*-OCV shape. Each
complete charge episode fits initial SOC and log-capacity from the shape of its
voltage trajectory after a fixed RC polarization correction. A free constant
voltage offset is profiled out. Q changes only when the normalized two-parameter
Jacobian has adequate rank and the event covers an informative SOC interval.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from .event_core import extract_charge_events


class RouteB:
    def __init__(self, gated: bool = True, fixed_q: bool = False, single_cell: bool = False,
                 bias_control: bool = True, reset_on_gap: bool = True,
                 quasi_ocv_sigma_V: float = 0.03):
        self.q0 = 100.41
        self.nominal = 102.0
        self.gated = gated
        self.fixed_q = fixed_q
        self.single_cell = single_cell
        self.bias_control = bias_control
        self.reset_on_gap = reset_on_gap
        self.quasi_ocv_sigma_V = quasi_ocv_sigma_V
        self.z_grid = None
        self.v_grid = None
        self.last_diagnostics = {}

    def fit(self, dataset):
        self.q0 = float(dataset.bol_capacity_Ah)
        ref = dataset.reference_discharge
        if ref.empty:
            self.z_grid = None
            return
        q = ref["discharged_Ah"].to_numpy(float)
        z = np.clip(1.0 - q / self.q0, 0.0, 1.0)
        vcols = ["voltage_V"] if self.single_cell else ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]
        v = ref[vcols].to_numpy(float)
        ix = np.argsort(z, kind="stable")
        z, v = z[ix], np.nanmedian(v[ix], axis=1)
        finite = np.isfinite(z) & np.isfinite(v)
        z, v = z[finite], v[finite]
        # Interpolate a monotone approximation; duplicates are collapsed and
        # weakly non-monotone discharge noise cannot invent negative dOCV/dz.
        uz, inv = np.unique(z, return_inverse=True)
        vv = np.bincount(inv, weights=v) / np.bincount(inv)
        # The raw curve is quantized to millivolts at ~70k time samples.
        # Differentiating it directly gives a spurious zero slope across most
        # of the plateau and huge impulses at each quantization step.
        self.z_grid = np.linspace(0.0,1.0,201)
        self.v_grid = np.interp(self.z_grid,uz,np.maximum.accumulate(vv))

    def _ocv(self, z):
        return np.interp(z, self.z_grid, self.v_grid)

    def _slope(self, z):
        grid = np.gradient(self.v_grid, self.z_grid, edge_order=1)
        return np.interp(z, self.z_grid, grid)

    def _event_fit(self, ev, q_prior, z_expected=None):
        if ev.ah < 5.0 or ev.voltages.shape[1] < 1:
            return None, "insufficient_Ah"
        # Resample a finished event uniformly by sample number, capping the
        # correlation-induced pseudo-replication of a 10-second stream.
        ix = np.unique(np.linspace(0, len(ev.q_ah)-1, min(45, len(ev.q_ah))).astype(int))
        q = ev.q_ah[ix]
        obs = np.nanmedian(ev.voltages[ix], axis=1)
        if not np.isfinite(obs).all():
            return None, "invalid_voltage"
        # Low-order first-order polarization driven by charging current.
        # The sign convention is V = OCV(z) + R0 I + vp, z += I dt/(3600 Q).
        t = ev.times_s[ix].astype(float)
        i = np.gradient(ev.q_ah, ev.times_s.astype(float), edge_order=1)[ix] * 3600.0
        vp = np.empty(len(ix)); vp[0] = 0.002 * i[0]
        for k in range(1, len(ix)):
            decay = np.exp(-(t[k]-t[k-1])/300.0)
            vp[k] = decay*vp[k-1] + (1-decay)*0.002*i[k]
        corrected = obs - 0.0015*i - vp
        # Differencing removes the unknown approximately constant charge-
        # discharge hysteresis/voltage offset. It cannot remove evolving bias.
        target = corrected - corrected[0] if self.bias_control else corrected
        def residual(x):
            z = x[0] + q / np.exp(x[1])
            predicted=self._ocv(np.clip(z,0,1))
            if self.bias_control:predicted=predicted-predicted[0]
            r=(predicted-target)/self.quasi_ocv_sigma_V
            if z_expected is not None:
                r=np.r_[r,(x[0]-z_expected)/0.02]
            return r
        best = None
        for z_init in ((z_expected,) if z_expected is not None else (0.03,0.2,0.45,0.65)):
            fit = least_squares(residual, [z_init,np.log(q_prior)],
                bounds=([0,np.log(40)],[0.96,np.log(125)]), max_nfev=65)
            score = np.mean(fit.fun**2) + 0.1*(fit.x[1]-np.log(q_prior))**2
            if best is None or score < best[0]:
                best = (score, fit)
        fit = best[1]
        z = fit.x[0] + q/np.exp(fit.x[1])
        slope = self._slope(np.clip(z,0,1))
        # Jacobian columns are normalized by voltage noise and dimensionless
        # parameter scales (SOC and log Ah); /sqrt(n) prevents oversampling
        # from manufacturing apparent observability.
        jz = (slope-slope[0] if self.bias_control else slope) / (self.quasi_ocv_sigma_V*np.sqrt(len(q)))
        jq = -slope*(q/np.exp(fit.x[1])) / (self.quasi_ocv_sigma_V*np.sqrt(len(q)))
        sigma_min = float(np.linalg.svd(np.stack([jz,jq],axis=1),compute_uv=False)[-1])
        median_slope = float(np.median(np.abs(slope)))
        result = dict(q_fit=float(np.exp(fit.x[1])), z0=float(fit.x[0]),
            voltage_rmse_V=float(np.sqrt(np.mean(fit.fun[:len(q)]**2))*self.quasi_ocv_sigma_V),
            sigma_min=sigma_min, median_slope_V_per_SOC=median_slope,
            q_span_Ah=float(q[-1]-q[0]))
        if self.gated and (result["q_fit"] < 42.0 or result["q_fit"] > 123.0):
            return result, "capacity_at_bound"
        if self.gated and abs(result["q_fit"]-q_prior) > 0.10*q_prior:
            return result, "implausible_episode_jump"
        if self.gated and (median_slope < 0.4 or sigma_min < 0.05):
            return result, "unidentifiable"
        if self.gated and result["voltage_rmse_V"] > 0.08:
            return result, "model_mismatch"
        return result, "accepted"

    def estimate_soh(self, dataset, at_date) -> float:
        if self.z_grid is None:
            self.last_diagnostics = {"fallback":True,"reason":"no_CK0_curve","updates":0}
            return float(100*self.q0/self.nominal)
        options = dict(voltage_cols=("voltage_V",), time_col="absolute_time",
                       temp_col="temperature_C", segment_col="cycle_number",
                       counter_col=None) if self.single_cell else {}
        events = extract_charge_events(dataset.operation, until=pd.Timestamp(at_date), **options)
        q_est = self.q0
        accepted = []; rejected = {}
        first_temp = None
        last_end = None
        z_carry = None
        for ev in events:
            if ev.ah < 5.0:
                continue
            if first_temp is None and np.isfinite(ev.median_temp):
                first_temp = ev.median_temp
            if self.gated and (not np.isfinite(ev.median_temp) or abs(ev.median_temp-first_temp)>5):
                rejected["temperature_mismatch"] = rejected.get("temperature_mismatch",0)+1
                continue
            if last_end is not None and (ev.start-last_end).total_seconds()>7*86400:
                rejected["gap_reinitialization"] = rejected.get("gap_reinitialization",0)+1
                # Each event separately profiles initial SOC; no SOC is carried
                # across the unknown monthly checkup throughput.
            last_end = ev.end
            result, reason = self._event_fit(ev,q_est,z_carry if not self.reset_on_gap else None)
            if reason == "accepted" and not self.fixed_q:
                # A conservative update, accounting for the quasi-OCV bias.
                q_est = 0.8*q_est + 0.2*result["q_fit"]
                accepted.append((str(ev.end),result))
                z_carry = min(0.96,result['z0']+ev.ah/result['q_fit'])
            else:
                rejected[reason if not self.fixed_q else "fixed_Q"] = rejected.get(reason if not self.fixed_q else "fixed_Q",0)+1
        self.last_diagnostics = {"fallback":not bool(accepted),"updates":len(accepted),
            "charge_runs":len(events),"rejections":rejected,"capacity_Ah_raw":q_est,
            "last_update":accepted[-1][0] if accepted else "",
            "last_information":accepted[-1][1] if accepted else None,
            "quasi_ocv_uncertainty_V":self.quasi_ocv_sigma_V}
        return float(100*q_est/self.nominal)
