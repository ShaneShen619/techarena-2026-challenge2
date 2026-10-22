"""Run the submitted MyModel on Challenge 1 events.

``TransferModel`` changes only where events come from (``diagnose``). Every branch decision,
the phase-matched difference, beta, the sqrt(t) gap rule and the fallback are the submitted
code. The overrides below only record what the model did, or switch one part off for an
ablation.
"""
import numpy as np

from .common import PROTOCOL, mt, patched
from .view import make_dataset


class TransferModel(mt.MyModel):
    """The submitted model, fed with events instead of pack rows."""

    def __init__(self, beta_mode="v2", beta_value=None, phase=True):
        super().__init__()
        self.beta_mode = beta_mode
        self.beta_value = beta_value
        self.phase = phase
        self.trace = {}

    @staticmethod
    def diagnose(dataset):
        return (sorted(dataset.charges, key=lambda c: c["t_end"]),
                sorted(dataset.steps, key=lambda s: s[0]))

    def _phase_diff(self, steps, anc, ck, k):
        x = super()._phase_diff(steps, anc, ck, k) if self.phase else None
        self.trace["x"] = x
        return x

    def _beta(self, anc, k):
        b = mt.MyModel._beta(anc, k)
        self.trace["beta_v2"] = b
        if self.beta_mode == "one":
            b = 1.0
        elif self.beta_mode == "value":
            b = float(self.beta_value)
        self.trace["beta"] = b
        return b

    def _sqrt_extrapolation(self, anc, ck, k, eps, op):
        self.trace["sqrt"] = True
        return super()._sqrt_extrapolation(anc, ck, k, eps, op)


def predict(view, k, scenario="main", key="robust", beta_mode="v2", beta_value=None,
            phase=True, gap_rule=True, depth_override=None):
    """Capacity (Ah) at boundary B_k from the events visible before it, plus a trace.

    phase=False switches the phase-matched branch off; gap_rule=False switches the sqrt(t)
    coverage-gap branch off (GAP_DAYS = inf). Both are ablations of the submitted logic.
    """
    ds = make_dataset(view, k, scenario, key, depth_override)
    model = TransferModel(beta_mode, beta_value, phase)
    model.fit(ds)
    consts = {"EPS_EXTRA_AH": PROTOCOL["model"]["EPS_EXTRA_AH"]}
    if not gap_rule:
        consts["GAP_DAYS"] = np.inf
    with patched(mt, **consts):
        q = float(model.estimate_capacity_ah(ds, view.boundaries[k]))
    tr = model.trace
    last_end = max((c["t_end"] for c in ds.charges), default=None)
    after = [s for s in ds.steps if last_end is not None and s[0] >= last_end]
    if tr.get("sqrt"):
        branch = "sqrt_gap"
    elif "beta" in tr:
        branch = "phase"
    elif after:
        branch = "fallback"
    else:
        branch = "anchor"
    return {"q": q, "branch": branch, "x": tr.get("x"), "beta": tr.get("beta"),
            "beta_v2": tr.get("beta_v2"), "n_steps": len(ds.steps), "n_anchors": len(ds.charges)}


def oracle_beta(view, k, xs):
    """Truth-based beta from the cell's other phase targets (leave-one-window-out; not causal).

    xs: {target j: phase step change x_j}. Least squares through the origin of
    r_j = truth_j - (anchor_{j-1} + eps0) on x_j, j != k.
    """
    anchors = {a["m"]: a for a in view.anchors}
    num = den = 0.0
    for j, x in xs.items():
        if j == k or x is None or j not in view.truth or (j - 1) not in anchors:
            continue
        base = view.label0 if j - 1 == 0 else anchors[j - 1]["q"] + view.eps0
        num += x * (view.truth[j] - base)
        den += x * x
    return num / den if den > 0 else np.nan
