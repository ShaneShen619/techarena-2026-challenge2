"""Merge verified card inventory by DOI/arXiv identity and fetch bibliographic metadata.

Cards remain separate for audit; duplicate_of prevents counting two versions as independent studies.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

TASK = Path(__file__).resolve().parents[1]
WS = TASK / "notes" / "workstreams"
CARDS = (list((WS / "A_partial_temperature").glob("A_*.md")) +
         list(WS.glob("B_card_*.md")) + list((WS / "C_evidence").glob("C_*.md")) +
         list((TASK / "notes" / "papers").glob("*.md")) +
         [WS / "D_old_refs" / name for name in ("Zhu2022.md", "Zhou2026_dynamic_ICA.md", "Cheng2024.md", "BatteryGPT2025.md")] +
         [WS / "E_forward_pack" / "Bilfinger2024.md", WS / "F_forward_limited" / "F_Deng2024_RapidPackDA.md"])
OVERRIDE = {
    "A_Cornejo2026": ("arxiv:2609.04487", "Estimating the Health and State of Charge of Each Cell in a Second-Life Battery System from Field Data"),
    "A_Wang2025": ("arxiv:2511.06989", "Capacity Estimation of Lithium-ion Batteries Using Invariance Property in Open Circuit Voltage Relationship"),
    "A_Figgener2024": ("arxiv:2411.08025", "Degradation mode estimation using reconstructed open circuit voltage curves from multi-year home storage field data"),
    "B_card_Yi2024": ("arxiv:2401.08136", "Bias-Compensated State of Charge and State of Health Joint Estimation for Lithium Iron Phosphate Batteries"),
    "B_card_Cornejo2026": ("arxiv:2609.04487", "Estimating the Health and State of Charge of Each Cell in a Second-Life Battery System from Field Data"),
    "C_Silva2026_Conformal": ("arxiv:2603.24475", "Conformalized Transfer Learning for Li-ion Battery State of Health Forecasting under Manufacturing and Usage Variability"),
    "C_Ispizua2026_PINN": ("arxiv:2608.14764", "Real-Time State-of-Health Estimation and Online Degradation Prognosis from Partial Battery Discharge Using Physics-Informed Neural Networks"),
    "C_Wen2023_PINN": ("arxiv:2301.00776", "Physics-Informed Neural Networks for Prognostics and Health Management of Lithium-Ion Batteries"),
}
DUPLICATE = {
    "B_card_Krupp2021": "A_Krupp2021",
    "B_card_ZhouAitioHowey2025": "A_Zhou2025",
    "B_card_Cornejo2026": "A_Cornejo2026",
    "C_Schaeffer2024_BattGP": "B_card_Schaeffer2024",
    "B_card_Yi2024": "A_Yi2025",
}


def first_doi(text):
    m = re.search(r"10\.\d{4,9}/[^\s)\]}>，；。]+", text[:1800])
    return m.group(0).rstrip(".,;*") if m else ""


def crossref(doi):
    p = TASK / "runs" / "L1_crossref_20260929" / (re.sub(r"[^a-zA-Z0-9]+", "_", doi) + ".json")
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        return json.loads(p.read_text())
    url = "https://api.crossref.org/works/" + quote(doi, safe="")
    try:
        cp = subprocess.run(["curl", "-sS", "-L", "--fail", "--connect-timeout", "10", "--max-time", "18", url],
                            capture_output=True, text=True, timeout=22, check=True)
        d = json.loads(cp.stdout).get("message", {})
    except Exception as e:
        d = {"lookup_error": repr(e)}
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    time.sleep(.1)
    return d


def main():
    rows = []
    for card in sorted(CARDS):
        s = card.read_text(encoding="utf-8", errors="replace")
        pid = card.stem
        doi = first_doi(s)
        identity, fallback_title = OVERRIDE.get(pid, ("", ""))
        if doi.startswith("10.5281/") and pid == "B_card_Cornejo2026":
            doi = ""  # code archive is not a paper DOI
        if not doi and not identity:
            ar = re.search(r"arxiv\.(?:org)/(?:abs|html|pdf)/(\d{4}\.\d{4,5})", s[:1800], re.I)
            identity = "arxiv:" + ar.group(1) if ar else ""
        meta = crossref(doi) if doi else {}
        title = (meta.get("title") or [fallback_title or s.splitlines()[0].lstrip("# ")])[0]
        year = ""
        for field in ("published", "issued", "created"):
            parts = (meta.get(field) or {}).get("date-parts")
            if parts:
                year = parts[0][0]; break
        authors = "; ".join(" ".join(x for x in [a.get("given", ""), a.get("family", "")] if x)
                            for a in meta.get("author", []))
        rows.append({"paper_id": pid, "identity": doi or identity,
                     "doi": doi, "title": title, "authors": authors,
                     "year": year, "journal_or_status": (meta.get("container-title") or ["preprint / see card"])[0],
                     "version_duplicate_of": DUPLICATE.get(pid, ""),
                     "fulltext_status": "read_fulltext_card",
                     "card_path": str(card.relative_to(TASK)),
                     "source_locator": "see card", "methods_results_limitations_read": True,
                     "source_metadata_status": "Crossref" if meta.get("title") else "card_only_or_pending"})
    with (TASK / "outputs" / "paper_registry.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"card rows={len(rows)}, canonical unique={len(rows)-len(DUPLICATE)}, DOI rows={sum(bool(x['doi']) for x in rows)}")


if __name__ == "__main__":
    main()
