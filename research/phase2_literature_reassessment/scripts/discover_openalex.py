"""Reproducible bibliographic discovery; titles/abstracts do not count as full-text review."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
RAW = TASK / "runs" / "L1_openalex_20260929"
QUERIES = [
    ("F01_partial", "LiFePO4 partial charge capacity state of health unknown initial SOC"),
    ("F02_ICA", "LFP incremental capacity degradation mode partial charge battery"),
    ("F03_pulse", "LiFePO4 battery pulse relaxation impedance capacity health"),
    ("F04_temperature", "LFP battery capacity estimation temperature hysteresis health"),
    ("F05_joint_state", "LiFePO4 joint SOC SOH estimation identifiability"),
    ("F06_series_pack", "LFP series connected pack capacity imbalance estimation"),
    ("F07_low_label", "battery capacity health sparse labels Gaussian process hierarchical"),
    ("F08_knee", "LFP capacity degradation knee late life prediction"),
    ("F09_transfer", "lithium iron phosphate battery self supervised transfer health capacity"),
    ("F10_physics", "LFP physics informed model partial charge capacity degradation"),
    ("F11_uncertainty", "battery capacity health uncertainty calibration conformal prediction"),
    ("F12_dataset", "LFP field battery dataset pack capacity label benchmark"),
]
PER_PAGE = 12


def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def abstract_from_index(idx):
    if not idx:
        return ""
    words = {}
    for w, positions in idx.items():
        for p in positions:
            words[p] = w
    return " ".join(words[i] for i in sorted(words))


def fetch(qid, q):
    params = urllib.parse.urlencode({"search": q, "per-page": PER_PAGE,
                                     "filter": "to_publication_date:2026-09-29",
                                     "select": "id,title,doi,publication_year,publication_date,type,primary_location,authorships,abstract_inverted_index,cited_by_count"})
    url = "https://api.openalex.org/works?" + params
    err = ""
    data = None
    for attempt in range(2):
        try:
            p = subprocess.run(["curl", "-sS", "-L", "--fail", "--connect-timeout", "10",
                                "--max-time", "25", url], capture_output=True, text=True, timeout=30, check=True)
            data = json.loads(p.stdout)
            break
        except Exception as e:
            err = repr(e)
            time.sleep(1 + attempt)
    (RAW / f"{qid}.json").write_text(json.dumps({"url": url, "error": err if data is None else "", "data": data}, ensure_ascii=False), encoding="utf-8")
    return url, data, err


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    query_rows = []
    works = {}
    now = datetime.now(timezone.utc).isoformat()
    for qid, q in QUERIES:
        url, data, err = fetch(qid, q)
        items = data.get("results", []) if data else []
        query_rows.append({"query_id": qid, "date_utc": now, "entry": "OpenAlex works API",
                           "query": q, "url": url, "result_count_reported": data.get("meta", {}).get("count", "") if data else "",
                           "range_read": f"first {len(items)} sorted by API relevance", "records_exported": len(items),
                           "error": err if not data else "", "raw_path": str(RAW / f"{qid}.json")})
        for rank, w in enumerate(items, 1):
            title = w.get("title") or ""
            doi = (w.get("doi") or "").lower().replace("https://doi.org/", "")
            key = doi or normalize(title)
            if not key:
                continue
            entry = works.setdefault(key, {"paper_id": "OA_" + hashlib.sha1(key.encode()).hexdigest()[:10],
                "doi": doi, "title": title, "year": w.get("publication_year") or "",
                "publication_date": w.get("publication_date") or "", "type": w.get("type") or "",
                "authors": "; ".join(a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:5]),
                "source_url": w.get("id") or "", "landing_url": ((w.get("primary_location") or {}).get("landing_page_url") or ""),
                "abstract": abstract_from_index(w.get("abstract_inverted_index")),
                "query_ids": [], "ranks": [], "screening_stage": "discovered_metadata_only",
                "decision": "pending", "reason": "title/abstract screening pending; no full text evaluated", "fulltext_status": "not_checked"})
            entry["query_ids"].append(qid)
            entry["ranks"].append(rank)
        time.sleep(.2)
    with (TASK / "search_queries.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(query_rows[0])); writer.writeheader(); writer.writerows(query_rows)
    rows = []
    for w in works.values():
        w["query_ids"] = ";".join(w["query_ids"])
        w["ranks"] = ";".join(map(str, w["ranks"]))
        rows.append(w)
    with (TASK / "screening.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    flow = {"run_id": "L1_openalex_20260929", "date_utc": now, "queries": len(QUERIES),
            "raw_api_hits_first_pages": sum(r["records_exported"] for r in query_rows),
            "deduplicated_metadata_candidates": len(rows),
            "fulltext_evaluated_from_this_run": 0,
            "limitations": "OpenAlex indexed result pages only; not exhaustive database search. Metadata-only candidates are not full-text evidence."}
    (TASK / "search_flow.json").write_text(json.dumps(flow, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(flow, ensure_ascii=False))


if __name__ == "__main__":
    main()
