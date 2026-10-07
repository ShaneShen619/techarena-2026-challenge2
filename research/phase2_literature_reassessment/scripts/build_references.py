"""Build a deduplicated BibTeX bibliography from reviewed registry rows."""
import csv
import re
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((TASK / "outputs" / "paper_registry.csv").open(encoding="utf-8")))


def safe(x):
    return (x or "").replace("\\", "\\textbackslash ").replace("&", "\\&").replace("%", "\\%")


out = []
for r in rows:
    if r["version_duplicate_of"]:
        continue
    pid = re.sub(r"[^A-Za-z0-9_:]", "_", r["paper_id"])
    year = r["year"] or re.search(r"20\d{2}", r["paper_id"]).group(0)
    kind = "article" if r["doi"] else "misc"
    fields = [("title", r["title"]), ("year", year)]
    if r["authors"]:
        fields.append(("author", r["authors"].replace("; ", " and ")))
    if r["doi"]:
        fields.extend([("journal", r["journal_or_status"]), ("doi", r["doi"]),
                       ("url", "https://doi.org/" + r["doi"])])
    else:
        arxiv_id = r["identity"].replace("arxiv:", "")
        fields.extend([("eprint", arxiv_id), ("archivePrefix", "arXiv"),
                       ("url", "https://arxiv.org/abs/" + arxiv_id)])
    out.append("@" + kind + "{" + pid + ",\n" + ",\n".join(f"  {k}={{{safe(v)}}}" for k, v in fields) + "\n}\n")
(TASK / "outputs" / "references.bib").write_text("\n".join(out), encoding="utf-8")
print(len(out), "unique bibliography entries")
