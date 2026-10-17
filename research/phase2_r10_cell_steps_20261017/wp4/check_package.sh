#!/bin/sh
# WP4 package check: archived 5cd305c package copy with the A3 candidate class, Python 3.11 venv (numpy/pandas only),
# validate_submission.py and a full run_model.py run with timing. The submission package itself is never touched.
set -e
STUDY=$(cd "$(dirname "$0")/.." && pwd)
C="$STUDY/cache"
[ -x "$C/venv311/bin/python" ] || { python3.11 -m venv "$C/venv311"; "$C/venv311/bin/pip" -q install -r "$C/submitted_package/TechArena_Challenge2_Team_Package/requirements.txt"; }
rm -rf "$C/package_copy_a3"; mkdir -p "$C/package_copy_a3"
cp -R "$C/submitted_package/TechArena_Challenge2_Team_Package" "$C/package_copy_a3/"
P="$C/package_copy_a3/TechArena_Challenge2_Team_Package"
cp "$STUDY/wp4/candidate_model/model_template.py" "$P/my_model/model_template.py"
cd "$P"
"$C/venv311/bin/python" --version
"$C/venv311/bin/python" -c "import numpy, pandas; print('numpy', numpy.__version__, 'pandas', pandas.__version__)"
"$C/venv311/bin/python" -B validate_submission.py
START=$(date +%s)
OUTD="$C/package_copy_a3/out"
"$C/venv311/bin/python" -B run_model.py --model train --input data --output-dir "$OUTD" 2>&1 | tail -3
"$C/venv311/bin/python" -B run_model.py --model test --input data --state-dir "$OUTD" --output-dir "$OUTD" --eval-point all 2>&1 | tail -3
cat "$OUTD"/*.csv
END=$(date +%s)
echo "full run seconds: $((END-START))"
