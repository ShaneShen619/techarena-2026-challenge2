"""Stage A: piecewise-linear registration of anchor charge curves (stage_A/protocol.json)."""
import numpy as np

import harness as H
from events import CELLS, segment_arrays
from v2 import anchors_by_checkup, shrink

GRID = 0.25
_REG_CACHE = {}


def anchor_curve(op, row):
    """Per-cell V on a 0.25 Ah grid over the CC part of one anchor charge."""
    g = op[op["segment"] == row["segment"]].reset_index(drop=True)
    s, e = row["_seg_index"]
    _, cur, ah = segment_arrays(g)
    q = ah[s:e + 1] - ah[max(s - 1, 0)]
    cc = cur[s:e + 1] > 20.0
    qq, keep = np.unique(q[cc], return_index=True)
    grid = np.arange(0.0, qq.max(), GRID)
    v = np.stack([np.interp(grid, qq, g[c].to_numpy(float)[s:e + 1][cc][keep]) for c in CELLS], axis=1)
    return grid, v, float(qq.max())


def _dvdq(grid, v, smooth=2.0):
    k = max(1, int(round(smooth / GRID)))
    vs = np.convolve(v, np.ones(k) / k, mode="same")
    return np.gradient(vs, grid)


def _loss(ref_q, ref_v, tgt_q, tgt_v, q_cc_t, p1, sb, st, mode):
    """Mean squared residual for arrays of (sb, st); returns array of losses."""
    sb = np.asarray(sb)[:, None]
    st = np.asarray(st)[:, None]
    q = ref_q[None, :]
    m = np.where(q <= p1, sb * q, sb * p1 + st * (q - p1))
    ok = m <= q_cc_t - 0.5
    if mode == "V":
        vt = np.interp(m, tgt_q, tgt_v)
        r = vt - ref_v[None, :]
        r = np.where(ok, r, np.nan)
        r = r - np.nanmean(r, axis=1, keepdims=True)  # closed-form voltage offset
    else:
        dt = np.interp(m, tgt_q, tgt_v)  # tgt_v holds dV/dQ here
        slope = np.where(q <= p1, sb, st)
        r = np.where(ok, dt * slope - ref_v[None, :], np.nan)
    return np.nanmean(r ** 2, axis=1)


def register(ref, tgt, p1, mode="V", fit_range=None):
    """Grid-search (s_b, s_t); returns estimate, profile spans and loss."""
    rq, rv, rcc = ref
    tq, tv, tcc = tgt
    lo, hi = fit_range if fit_range else (3.0, rcc - 1.0)
    sel = (rq >= lo) & (rq <= hi)
    rq_s, rv_s = rq[sel], rv[sel]
    if mode != "V":
        rv_s = _dvdq(rq, rv)[sel]
        tv = _dvdq(tq, tv)
    cb = np.arange(0.94, 1.04 + 1e-9, 0.002)
    ct = np.arange(0.80, 1.05 + 1e-9, 0.005)
    SB, ST = np.meshgrid(cb, ct, indexing="ij")
    L = _loss(rq_s, rv_s, tq, tv, tcc, p1, SB.ravel(), ST.ravel(), mode).reshape(SB.shape)
    i, j = np.unravel_index(np.nanargmin(L), L.shape)
    fb = np.arange(cb[i] - 0.004, cb[i] + 0.004 + 1e-9, 0.0002)
    ft = np.arange(ct[j] - 0.010, ct[j] + 0.010 + 1e-9, 0.0005)
    FB, FT = np.meshgrid(fb, ft, indexing="ij")
    LF = _loss(rq_s, rv_s, tq, tv, tcc, p1, FB.ravel(), FT.ravel(), mode).reshape(FB.shape)
    a, b = np.unravel_index(np.nanargmin(LF), LF.shape)
    sb_hat, st_hat, lmin = float(fb[a]), float(ft[b]), float(LF[a, b])
    lmin_all = min(lmin, float(np.nanmin(L)))
    # profiles on the coarse grid (wide range)
    pb = np.nanmin(L, axis=1)
    pt = np.nanmin(L, axis=0)
    span_b = float(np.ptp(cb[pb <= 1.05 * lmin_all])) if (pb <= 1.05 * lmin_all).any() else 0.0
    span_t = float(np.ptp(ct[pt <= 1.05 * lmin_all])) if (pt <= 1.05 * lmin_all).any() else 0.0
    ident_b = span_b <= 0.5 * abs(sb_hat - 1.0) if abs(sb_hat - 1.0) > 0 else False
    ident_t = span_t <= 0.5 * abs(st_hat - 1.0) if abs(st_hat - 1.0) > 0 else False
    return dict(s_b=sb_hat, s_t=st_hat, loss=lmin, span_b=span_b, span_t=span_t,
                ident_b=bool(ident_b), ident_t=bool(ident_t))


def anchor_registrations(op, fc, a4_ref, ck, mode="V", fit="full"):
    """Registration of every visible 25 C anchor j>=2 against anchor 1, per cell.

    Cached by (segment, mode, fit): an anchor charge is complete in every cut that
    contains it, so its registration does not depend on the cutoff."""
    anc = anchors_by_checkup(fc, ck)
    if 1 not in anc:
        return anc, {}
    r1 = anc[1]
    seg1 = int(r1["segment"])
    p1_row = a4_ref[a4_ref["segment"] == seg1]
    if p1_row.empty:
        return anc, {}
    p1 = [float(p1_row[f"bottom_to_step_{c}"].iloc[0]) for c in CELLS]
    ref = anchor_curve(op, r1)
    out = {}
    for j, r in anc.items():
        if j < 2 or r["setpoint_C"] != 25:
            continue
        key = (int(r["segment"]), mode, fit)
        if key not in _REG_CACHE:
            tgt = anchor_curve(op, r)
            cells = []
            for c in range(4):
                fr = (3.0, p1[c] + 15.0) if fit == "bottom" else None
                rr = register((ref[0], ref[1][:, c], ref[2]), (tgt[0], tgt[1][:, c], tgt[2]), p1[c], mode, fr)
                rr["bottom"] = rr["s_b"] * p1[c]
                rr["p1"] = p1[c]
                cells.append(rr)
            _REG_CACHE[key] = cells
        out[j] = _REG_CACHE[key]
    return anc, out


def beta_reg(ctx, mode="V", fit="full", beta0=1.0, tau=1.0):
    fc, ck, k = ctx["fc"], ctx["ck"], ctx["k"]
    anc, reg = anchor_registrations(ctx["op"], fc, ctx["a4"][2.0], ck, mode, fit)
    js = [j for j in range(2, k) if j in reg]
    if 1 not in anc or not js:
        return beta0, {}
    q1 = anc[1]["Q_Ah"]
    bottom1 = np.mean([c["p1"] for c in reg[js[0]]])
    pairs, info = [], {}
    for j in js:
        bottom_j = float(np.mean([c["bottom"] for c in reg[j]]))
        dq = anc[j]["Q_Ah"] - q1
        dtop = dq - (bottom_j - bottom1)
        pairs.append((dtop, dq))
        info[j] = dict(dQ=dq, dbottom=bottom_j - bottom1, dtop=dtop)
    return shrink(pairs, beta0, tau), info


def v2_reg(ctx, mode="V", fit="full"):
    """V2 with beta from registration on the phase branch."""
    from v2 import phase_diff
    q, info = H.v2_pred(ctx)
    if info["branch"] != "phase":
        return q, dict(info, beta_reg=np.nan)
    b, _ = beta_reg(ctx, mode, fit)
    anc = anchors_by_checkup(ctx["fc"], ctx["ck"])
    x = phase_diff(ctx["steps"][ctx["step"]], anc, ctx["ck"], ctx["k"], 10.0, True)
    q_new = anc[ctx["k"] - 1]["Q_Ah"] + ctx["eps"] + b * x
    return float(q_new), dict(info, beta_reg=b)
