"""WP3 driver: stage a full package copy for each chosen probe under cache/pkg_<probe>/ and check it.

- my_model/model_template.py = the registered research copy (src/variants.py) plus one docstring line;
- README.md gets one short section describing the variant;
- the staged copy must reproduce the probe's WP2 SOH vector through the CLI.
The base package is never modified.  Run: python3 -B src/wp3_stage.py
"""
import difflib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import variants as V  # noqa: E402

ST = os.path.dirname(HERE)
OUT = os.path.join(ST, "wp3")
DOC_ANCHOR = "multi-variant cell-median step, active model).\n"
DOC_LINE = {
    "P_A3fix": "Leaderboard probe variant P_A3fix: anchor 3 (segment 6) charge minus a_3^rel = 0.3047 Ah (round 12).\n",
}
README_ANCHOR = "\n## Method\n"
README_SECTION = {"P_A3fix": """
## Leaderboard probe variant (P_A3fix)

This zip is a **one-constant variant** of our main model. It is submitted once to test a single physical
hypothesis on the leaderboard, and it is disclosed here and in our report.

- **What differs.** Anchor 3, the first from-empty full charge after CK3 (segment 6), is reduced by
  a_3^rel = 0.3047 Ah after its step-to-top distance is computed. Nothing else changes.
- **Why.** That charge started from an unrelaxed state (+53 mV/h at its start, after a 3.1-day window), so its
  charged Ah overstate the capacity. The offset was measured from the operating data (bottom locators, 4 of 5 agree
  in sign), not tuned to the leaderboard.
- **Effect.** CK4 −0.36 pp, CK5–CK7 −0.02 pp; CK1–CK3 unchanged. Estimates of this variant:
  98.441, 95.984, 94.507, 93.600, **92.461**, 91.987, 91.410, 90.750 (CK0–CK7). The *Estimates* table below is the
  main model's.
- **Decision rule.** The variant is kept only if it scores better than the main model on the leaderboard;
  otherwise the main model is resubmitted. No checkup-specific value is used.
"""}


def stage(probe):
    dst = os.path.join(ST, "cache", f"pkg_{probe}")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(V.PKG, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    research, hook_diff, _ = V.build(probe, root=os.path.join(ST, "cache", "variants_wp3"))
    src = open(os.path.join(research, "my_model", "model_template.py")).read()
    assert src.count(DOC_ANCHOR) == 1
    new = src.replace(DOC_ANCHOR, DOC_ANCHOR + DOC_LINE[probe])
    open(os.path.join(dst, "my_model", "model_template.py"), "w").write(new)
    base = open(os.path.join(V.PKG, "my_model", "model_template.py")).read()
    diff = [ln for ln in difflib.unified_diff(base.splitlines(), new.splitlines(), lineterm="", n=0)
            if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
    expected = sorted(hook_diff + ["+" + DOC_LINE[probe].rstrip("\n")])
    assert sorted(diff) == expected, diff
    rd = os.path.join(dst, "README.md")
    txt = open(rd, encoding="utf-8").read()
    assert txt.count(README_ANCHOR) == 1
    open(rd, "w", encoding="utf-8").write(txt.replace(README_ANCHOR, README_SECTION[probe] + README_ANCHOR))
    soh = V.run_cli(dst, os.path.join(ST, "cache", "out_wp3", probe))
    soh = {c: float(soh[c]) for c in soh.index}
    want = json.load(open(os.path.join(ST, "wp2", "selection.json")))["SOH"][probe]
    assert soh == want, (soh, want)
    return dict(probe=probe, staged=os.path.relpath(dst, ST), model_template_diff=diff, soh=soh,
                reproduces_wp2=soh == want)


def main():
    chosen = json.load(open(os.path.join(ST, "wp2", "selection.json")))["chosen"]
    os.makedirs(OUT, exist_ok=True)
    res = [stage(p) for p in chosen]
    json.dump(res, open(os.path.join(OUT, "staging.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
