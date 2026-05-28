#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Missing virtualenv python: $VENV_PYTHON" >&2
  exit 1
fi

exec "$VENV_PYTHON" -m uvicorn essay_scorer_annotator:app --host 0.0.0.0 --port 9714
