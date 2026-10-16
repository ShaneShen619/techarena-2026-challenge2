#!/bin/sh
# WP2 G_impl part 2: archived 21a7a55 package copy with the T_main candidate class, Python 3.11 venv
# (numpy/pandas only), validate_submission.py and a full run_model.py run with timing.
set -e
STUDY=$(cd "$(dirname "$0")/.." && pwd)
C="$STUDY/cache"
[ -x "$C/venv311/bin/python" ] || { python3.11 -m venv "$C/venv311"; "$C/venv311/bin/pip" -q install -r "$C/submitted_package/TechArena_Challenge2_Team_Package/requirements.txt"; }
rm -rf "$C/package_copy_tmain"; mkdir -p "$C/package_copy_tmain"
cp -R "$C/submitted_package/TechArena_Challenge2_Team_Package" "$C/package_copy_tmain/"
P="$C/package_copy_tmain/TechArena_Challenge2_Team_Package"
cp "$STUDY/wp2/candidate_model/model_template.py" "$P/my_model/model_template.py"
cd "$P"
"$C/venv311/bin/python" --version
"$C/venv311/bin/python" -c "import numpy, pandas; print('numpy', numpy.__version__, 'pandas', pandas.__version__)"
"$C/venv311/bin/python" -B validate_submission.py
START=$(date +%s)
OUTD="$C/package_copy_tmain/out"
"$C/venv311/bin/python" -B run_model.py --model train --input data --output-dir "$OUTD" 2>&1 | tail -5
"$C/venv311/bin/python" -B run_model.py --model test --input data --state-dir "$OUTD" --output-dir "$OUTD" --eval-point all 2>&1 | tail -5
cat "$OUTD"/*.csv
END=$(date +%s)
echo "full run seconds: $((END-START))"
