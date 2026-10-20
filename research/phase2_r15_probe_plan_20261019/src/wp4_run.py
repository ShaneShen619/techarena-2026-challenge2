"""WP4 driver: read inputs/leaderboard_log.csv and apply the registered rules (src/grid15.py) to new rows.

- no new row since the last run -> status "waiting for leaderboard" (allowed end state);
- otherwise: hash check against wp3/packages.csv / wp0/existing_packages.csv, surviving set (G_main, G_r11) from
  wp2/predicted_scores.csv, the registered reading rule when both a SUB and a probe observation exist, and the
  end-state action.  If the reading adopts a probe, the final package and disclosure text are WP4 step 3 (built the
  same way as WP3 in the WP4 session; never uploaded).
metrics_verbatim is parsed as "label=value; label=value" (a bare number is read as label "score").
Run: python3 -B src/wp4_run.py   (writes wp4/run_<date>.json and updates wp4/processed_rows.json)
"""
import datetime
import hashlib
import json
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import grid15 as G  # noqa: E402

ST = G.ST
OUT = os.path.join(ST, "wp4")
PROCESSED = os.path.join(OUT, "processed_rows.json")
SUB_TEMPLATE_SHA = "3bd26ed8bbb5890fec5efa53606a03c39b55f52b04a0cf1e5f92ae0e36a2fbd5"


def row_id(r):
    return hashlib.sha256("|".join(str(r[c]) for c in G_COLS).encode()).hexdigest()[:16]


G_COLS = ["board_date", "package_file", "package_sha256", "model_commit", "metrics_verbatim", "rank", "notes"]


def parse_metrics(text):
    text = str(text).strip()
    if not text:
        return {}
    if re.fullmatch(r"[-+]?\d+(\.\d+)?", text):
        return {"score": text}
    out = {}
    for part in re.split(r"[;\n]", text):
        if "=" in part:
            k, v = part.split("=", 1)
            m = re.search(r"[-+]?\d+(\.\d+)?", v)
            if m:
                out[k.strip()] = m.group(0)
    return out


def known_packages():
    """{zip sha256: (model name in predicted_scores.csv, is SUB, is probe)}"""
    k = {}
    inv = pd.read_csv(os.path.join(ST, "wp0", "existing_packages.csv"))
    for _, r in inv.iterrows():
        k[r["sha256"]] = (f"zip:{r['name']}", r["model_template_sha256"] == SUB_TEMPLATE_SHA, False)
    pk = pd.read_csv(os.path.join(ST, "wp3", "packages.csv"))
    for _, r in pk.iterrows():
        k[r["package_sha256"]] = (r["probe"], False, True)
    return k


def main():
    os.makedirs(OUT, exist_ok=True)
    today = datetime.date.today().isoformat()
    log = pd.read_csv(os.path.join(ST, "inputs", "leaderboard_log.csv"), dtype=str).fillna("")
    assert list(log.columns) == G_COLS, list(log.columns)
    done = json.load(open(PROCESSED)) if os.path.exists(PROCESSED) else []
    ids = [row_id(r) for _, r in log.iterrows()]
    new = [i for i in ids if i not in done]
    res = dict(date=today, log_rows=int(len(log)), new_rows=len(new))
    if not new:
        res["status"] = "waiting for leaderboard"
        res["action"] = "keep SUB as the active and last submission; log the next board evaluation, then rerun WP4"
    else:
        kp = known_packages()
        pred = pd.read_csv(os.path.join(ST, "wp2", "predicted_scores.csv"))
        obs, checks = [], []
        for (_, r), i in zip(log.iterrows(), ids):
            sha = r["package_sha256"].strip().lower()
            name, is_sub, is_probe = kp.get(sha, (None, False, False))
            vals = parse_metrics(r["metrics_verbatim"])
            checks.append(dict(row=i, board_date=r["board_date"], sha_known=name is not None, model=name,
                               is_sub=is_sub, is_probe=is_probe, values=vals, new=i in new))
            if name is not None and vals:
                obs.append(dict(model="SUB" if is_sub else name, values=vals, is_sub=is_sub, is_probe=is_probe,
                                date=r["board_date"]))
        res["rows"] = checks
        surv = {}
        for g in ("G_main", "G_r11"):
            hs, note = G.surviving(pred[pred.grid == g], [dict(model=o["model"], values=o["values"]) for o in obs], g)
            surv[g] = dict(n=len(hs), note=note, hypotheses=hs)
        res["surviving"] = surv
        subs = [o for o in obs if o["is_sub"]]
        probes = [o for o in obs if o["is_probe"]]
        if subs and probes:
            rd = G.reading(probes[-1]["values"], subs[-1]["values"])
            res["reading"] = rd
            if rd["verdict"].startswith("probe wins"):
                res["action"] = ("adopt P_A3fix's scalar as the submission candidate: build the final package with "
                                 "disclosure (WP4 step 3); wiring into the team package is the user's call")
            else:
                res["action"] = "re-upload SUB now (end-state rule); the probe budget is spent"
                if rd["verdict"].startswith("probe loses"):
                    dl = pd.read_csv(os.path.join(ST, "wp2", "delta_s_long.csv"))
                    for g in ("G_main", "G_r11"):
                        dt = dl[(dl.probe == probes[-1]["model"]) & (dl.grid == g)]
                        surv[g]["after_drop_branch"] = G.drop_branch(dt, surv[g]["hypotheses"])
        elif probes:
            res["reading"] = dict(verdict="no information", reason="SUB's own board value is not logged")
            res["action"] = "re-upload SUB now (end-state rule)"
        else:
            res["action"] = ("SUB observed: the probe may be uploaded if the next evaluation is >= 3 days before a "
                             "known deadline (wp2/PROBE_PLAN.md); otherwise keep SUB") if subs else \
                "no usable observation (unknown hash or no value): check the log row"
        res["status"] = "decision recorded"
        done = done + new
    json.dump(done, open(PROCESSED, "w"), indent=1)
    json.dump(res, open(os.path.join(OUT, f"run_{today}.json"), "w"), indent=1, default=str)
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
