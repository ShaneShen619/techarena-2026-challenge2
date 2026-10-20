"""WP3: record each built probe zip (SHA256, size, contained model_template.py / pptx hashes, validation result)
in wp3/packages.csv.  Run after src/package_submission.py:  python3 -B src/wp3_packages.py"""
import datetime
import hashlib
import json
import os
import zipfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.dirname(HERE)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    rows = []
    for probe in json.load(open(os.path.join(ST, "wp2", "selection.json")))["chosen"]:
        z = os.path.join(ST, "cache", "packages", probe, "Current State_Challenge2.zip")
        log = open(os.path.join(ST, "cache", "packages", probe, "build_log.txt")).read()
        with zipfile.ZipFile(z) as f:
            mt = sha(f.read("my_model/model_template.py"))
            pp = sha(f.read("Current State_Final_Presentation.pptx"))
            init = f.read("my_model/__init__.py").decode()
            n = len(f.namelist())
        soh = json.load(open(os.path.join(ST, "wp3", "staging.json")))[0]["soh"]
        rows.append(dict(probe=probe, package_file="Current State_Challenge2.zip",
                         path=os.path.relpath(z, ST), size_bytes=os.path.getsize(z), n_files=n,
                         package_sha256=sha(open(z, "rb").read()), model_template_sha256=mt, pptx_sha256=pp,
                         pptx_is_template=pp.startswith("8bcd38a1"),
                         active_model_is_mymodel="\nfrom .model_template import MyModel as ActiveModel" in init,
                         validate_passed="validate_submission.py: PASSED" in log,
                         output_equals_expected="full-data output equals expected: True" in log,
                         built=datetime.datetime.fromtimestamp(os.path.getmtime(z)).strftime("%Y-%m-%d %H:%M"),
                         **soh))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(ST, "wp3", "packages.csv"), index=False)
    print(df.T.to_string())


if __name__ == "__main__":
    main()
