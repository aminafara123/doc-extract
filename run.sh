#!/usr/bin/env bash
# Extract a file or a folder of documents. Defaults to sample/.
# Usage: ./run.sh [path] [--out DIR] [--ocr]
set -euo pipefail
cd "$(dirname "$0")"
PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"
exec "$PY" -m doc_extract "${1:-sample/}" "${@:2}"
