#!/bin/bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE_PYTHON=/Users/shane/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
if [[ ! -x "$TASK_ROOT/.venv/bin/python" ]]; then
  "$BASE_PYTHON" -m venv "$TASK_ROOT/.venv"
fi
bash "$TASK_ROOT/run_python.sh" -m pip install --disable-pip-version-check --no-index --find-links "$TASK_ROOT/wheelhouse" -r "$TASK_ROOT/requirements.lock.txt"
bash "$TASK_ROOT/run_python.sh" -m pip check
bash "$TASK_ROOT/run_python.sh" "$TASK_ROOT/scripts/preflight.py"
bash "$TASK_ROOT/run_python.sh" "$TASK_ROOT/scripts/audit_downloaded_data.py"
