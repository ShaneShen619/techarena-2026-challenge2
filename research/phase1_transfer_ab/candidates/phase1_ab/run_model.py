#!/usr/bin/env python3
# FRAMEWORK - DO NOT EDIT
"""Entry point used by both you and the evaluation.

  train:  python run_model.py --model train --input data --output-dir out
  test:   python run_model.py --model test  --input data --state-dir out --output-dir out --eval-point CK3
          (--eval-point all  evaluates every checkup in evaluation_points.csv, each one causally)

For every evaluation point the model only receives data recorded up to that checkup's date."""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework.data import load_dataset, load_eval_points
from framework.io import write_output
from framework.persistence import save_model, load_model
from my_model import ActiveModel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["train", "test"], required=True)
    ap.add_argument("--input", required=True, help="data directory")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--state-dir", default=None, help="where train stored the model (default: output-dir)")
    ap.add_argument("--eval-point", default="all", help="checkup id (e.g. CK3) or 'all'")
    args = ap.parse_args()
    state_dir = args.state_dir or args.output_dir
    t0 = time.time()
    if args.model == "train":
        model = ActiveModel()
        model.fit(load_dataset(args.input))
        save_model(model, state_dir)
        print(f"train ok -> {state_dir} ({time.time()-t0:.0f} s)")
        return
    model = load_model(state_dir)
    ev = load_eval_points(args.input)
    points = ev if args.eval_point == "all" else ev[ev["checkup"] == args.eval_point]
    if points.empty:
        sys.exit(f"unknown evaluation point {args.eval_point}")
    rows = []
    for p in points.itertuples():
        ds = load_dataset(args.input, until=p.date)
        soh = float(model.estimate_soh(ds, p.date))
        rows.append({"checkup": p.checkup, "date": p.date.strftime("%Y-%m-%d"), "SOH_est": round(soh, 3)})
        print(f"  {p.checkup} ({p.date.date()}): SOH_est = {soh:.2f} %")
    path = write_output(rows, args.output_dir)
    print(f"test ok -> {path} ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
