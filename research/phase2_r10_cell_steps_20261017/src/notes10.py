"""Append bilingual entries to notes/DECISIONS.md and set rows of notes/STATUS.md (bookkeeping only)."""
import os
import re
import sys

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def add_decision(en, zh):
    p = os.path.join(STUDY, "notes", "DECISIONS.md")
    a, b = open(p, encoding="utf-8").read().split("\n---\n")
    open(p, "w", encoding="utf-8").write(a.rstrip("\n") + "\n" + en.rstrip("\n") + "\n\n---\n" + b.rstrip("\n") + "\n" + zh.rstrip("\n") + "\n")


def set_status(wp, state_en, result_en, state_zh, result_zh, next_en, next_zh):
    p = os.path.join(STUDY, "notes", "STATUS.md")
    s = open(p, encoding="utf-8").read()
    en, zh = s.split("\n---\n")
    en = re.sub(rf"^\| {wp} \|.*$", f"| {wp} | {state_en} | {result_en} |", en, flags=re.M)
    en = re.sub(r"^Next:.*$", f"Next: {next_en}", en, flags=re.M)
    if re.search(rf"^\| {wp} \|", zh, flags=re.M):
        zh = re.sub(rf"^\| {wp} \|.*$", f"| {wp} | {state_zh} | {result_zh} |", zh, flags=re.M)
    else:
        zh = zh.rstrip("\n") + f"\n| {wp} | {state_zh} | {result_zh} |\n"
    zh = re.sub(r"^下一步：.*$", "", zh, flags=re.M).rstrip("\n") + f"\n\n下一步：{next_zh}\n"
    open(p, "w", encoding="utf-8").write(en + "\n---\n" + zh)


if __name__ == "__main__":
    set_status(*sys.argv[1:8])
