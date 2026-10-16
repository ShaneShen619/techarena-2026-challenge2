"""WP4: build the Yagci 2025 table for fit_prior3.py from the downloaded Data.zip (read-only, never executed).
Usage: python3 -I build_yagci_table.py <study_dir>
capacity = max_CCCV_DIS of 'Capacities in checkups - all cells.xlsx' (Checkup #1500 sheet excluded: identical to #1000);
day 0 = the Checkup_0 IR test date (end of the initial checkup, start of ageing; from the file name);
later days = 'Start of Test' in the header of each cell's standard capacity-check file (not the 18A variant);
cycles = the checkup's nominal cycle count for cyclic cells (0 for storage cells)."""
import os
import re
import sys
import zipfile

import pandas as pd

STUDY = sys.argv[1]
Y = os.path.join(STUDY, "cache", "downloads", "yagci")
X = os.path.join(Y, "unzipped", "Data")
lab = pd.read_excel(os.path.join(X, "Cell labels paper vs. raw data.xlsx"))
lab.columns = ["paper", "lab", "cond"]
meta = {}
for _, r in lab.iterrows():
    c = f"CA-181103-{int(r['lab'])}"
    m = re.search(r"(\d+)\s*°C", r["cond"])
    soc = re.search(r"(\d+)\s*%", r["cond"])
    meta[c] = dict(paper=int(r["paper"]), kind="cyclic" if "cycling" in r["cond"] else "calendar", T_C=float(m.group(1)),
                   soc=float(soc.group(1)) if soc else float("nan"))
zf = zipfile.ZipFile(os.path.join(Y, "Data.zip"))
names = zf.namelist()
dates = {}
for c in meta:
    ir = [n for n in names if re.search(rf"Checkup_0/IR/{c}_(\d{{8}})_", n)]
    dates[(c, 0)] = pd.Timestamp(re.search(r"_(\d{8})_", ir[0].split("/")[-1]).group(1))
    for k in (100, 500, 1000):
        f = [n for n in names if re.search(rf"Checkup_{k}/Capacity/{c}_\d+_", n) and "18A" not in n and n.endswith(".txt")]
        with zf.open(f[0]) as fh:
            head = fh.read(3000).decode("latin-1")
        s = re.search(r"Start of Test:\s*([\d.]+ [\d:]+)", head).group(1)
        dates[(c, k)] = pd.to_datetime(s, format="%d.%m.%Y %H:%M:%S")
cap = pd.read_excel(os.path.join(X, "Capacities in checkups - all cells.xlsx"), sheet_name=None, header=None)
rows = []
for sh, k in (("Checkup_#0", 0), ("Checkup_#100", 100), ("Checkup_#500", 500), ("Checkup_#1000", 1000)):
    t = cap[sh]
    hr = int(t.index[t.apply(lambda r: (r == "Cell").any(), axis=1)][0])
    t = t.iloc[hr + 1:]
    t.columns = cap[sh].iloc[hr]
    t = t.loc[:, t.columns.notna()].dropna(subset=["Cell"])
    for _, r in t.iterrows():
        c = r["Cell"]
        m = meta[c]
        rows.append(dict(cell=c, paper=m["paper"], kind=m["kind"], T_C=m["T_C"], soc=m["soc"], checkup=k,
                         date=dates[(c, k)], day=(dates[(c, k)] - dates[(c, 0)]).total_seconds() / 86400,
                         capacity_Ah=float(r["max_CCCV_DIS"]), cycles=k if m["kind"] == "cyclic" else 0))
df = pd.DataFrame(rows).sort_values(["cell", "day"])
assert (cap["Checkup_#1500"].iloc[2:, 2:].values == cap["Checkup_#1000"].iloc[2:, 2:].values).all()
df.to_csv(os.path.join(STUDY, "wp4", "outputs", "wp4_yagci_table.csv"), index=False)
pd.set_option("display.width", 200)
print(df.to_string(index=False))
