"""Predictor factories for round 5C (harness ctx -> (Q, info))."""
from common17 import H
from smodel import StressFit

_TAB = {}
_MEMO = {}
_CFG = {}


def _cfg_hash(cls, cfg):
    return repr((cls.__name__, sorted((k, repr(v)) for k, v in cfg.items())))


def s_pred(name, cls=StressFit, cfg=None, uses_steps=False):
    cfg = cfg or {}
    h = _cfg_hash(cls, cfg)
    # memo keys do not include the config: a name must never map to two configs
    assert _CFG.setdefault(name, h) == h, f"predictor name {name!r} reused with a different config"

    def f(ctx):
        key = (ctx["key"], name, ctx["delta"]) + ((ctx["step"], ctx["a4s"]) if uses_steps else ())
        if key not in _MEMO:
            m = cls(cfg)
            if uses_steps:
                _MEMO[key] = m.run(ctx["op"], ctx["fc"], ctx["ck"], ctx["at_date"], ctx["eps"], tab_cache=_TAB,
                                   key=ctx["key"], steps=ctx["steps"][ctx["step"]], a4=ctx["a4"][ctx["a4s"]])
            else:
                _MEMO[key] = m.run(ctx["op"], ctx["fc"], ctx["ck"], ctx["at_date"], ctx["eps"], tab_cache=_TAB,
                                   key=ctx["key"])
        return _MEMO[key]
    return f


def ens(f, w):
    def g(ctx):
        qs = f(ctx)[0]
        qv, iv = H.v2_pred(ctx)
        return w * qs + (1 - w) * qv, {"branch": iv["branch"]}
    return g


def hybrid_v2_at(f, ks=(1,)):
    def g(ctx):
        if ctx["k"] in ks and ctx["scenario"] == "real":
            return H.v2_pred(ctx)
        return f(ctx)
    return g
