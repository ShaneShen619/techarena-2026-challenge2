"""WP1: self-tests that must pass before any Challenge 1 file is read.

* tests/test_pack_faithfulness.py: on the pack's own data, the step adapter is bit-identical to
  the submitted ``_robust_step``, keeps the same discharges and gives the same charge-side top.
* tests/test_synthetic.py: on synthetic cells with planted physics, the emulated information
  structure, causality (future rows replaced by noise), no use of hidden rows, the branches,
  beta recovery and the decision rules.

Writes outputs/wp1_selftest.json and exits non-zero on any failure.

    python3 -B run_wp1_selftest.py [--work DIR]
"""
import json
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from src import store  # noqa: E402


def main():
    args = store.parser(__doc__).parse_args()
    _, out = store.dirs(args.work)
    t0 = time.time()
    suite = unittest.defaultTestLoader.discover(str(HERE / "tests"), top_level_dir=str(HERE))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"tests_run": result.testsRun, "failures": len(result.failures),
              "errors": len(result.errors), "skipped": len(result.skipped),
              "skipped_reasons": [str(r) for _, r in result.skipped],
              "seconds": round(time.time() - t0, 1), "passed": result.wasSuccessful()}
    (out / "wp1_selftest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)


if __name__ == "__main__":
    main()
