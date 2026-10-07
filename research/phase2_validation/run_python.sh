#!/bin/bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$TASK_ROOT/../.." && pwd)"
export MPLCONFIGDIR="$TASK_ROOT/.cache/matplotlib"
export XDG_CACHE_HOME="$TASK_ROOT/.cache"
export FONTCONFIG_FILE="$TASK_ROOT/fonts.conf"
export MPLBACKEND=Agg
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export PIP_CACHE_DIR="$TASK_ROOT/.cache/pip"
mkdir -p "$MPLCONFIGDIR" "$XDG_CACHE_HOME/fontconfig" "$PIP_CACHE_DIR"
cd "$PROJECT_ROOT"
exec "$TASK_ROOT/.venv/bin/python" "$@"
