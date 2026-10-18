"""Summarise a Basytec result file into steps (consecutive rows with the same Line/Command).
Usage: python3 -I -B basytec_steps.py <file.txt> [<out.csv>]"""
import sys
import pandas as pd

f = sys.argv[1]
d = pd.read_csv(f, sep="\t", comment="~", encoding="latin-1", header=None, skiprows=0)
hdr = None
with open(f, encoding="latin-1") as fh:
    for line in fh:
        if line.startswith("~Time"):
            hdr = line[1:].rstrip("\n").split("\t")
            break
d.columns = hdr[: d.shape[1]]
d = d.rename(columns={hdr[0]: "t_h", "U[V]": "U", "I[A]": "I", "Ah-Step": "AhS"})
tcol = [c for c in d.columns if c.startswith("T1")][0]
key = (d["Line"].ne(d["Line"].shift()) | d["Command"].ne(d["Command"].shift())).cumsum()
g = d.groupby(key)
s = pd.DataFrame({"line": g["Line"].first(), "cmd": g["Command"].first(), "t0_h": g["t_h"].first(),
                  "dur_h": g["t_h"].last() - g["t_h"].first(), "Ah_step_end": g["AhS"].last(),
                  "I_med": g["I"].median(), "I_end": g["I"].last(), "U0": g["U"].first(), "U1": g["U"].last(),
                  "T_med": g[tcol].median(), "cyc": g["Cyc-Count"].first()})
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 400)
print(s.round(3).to_string(index=False))
if len(sys.argv) > 2:
    s.to_csv(sys.argv[2], index=False)
