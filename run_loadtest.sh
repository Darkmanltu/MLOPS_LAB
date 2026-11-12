#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

curl --fail --silent --show-error http://127.0.0.1:8000/health
printf '\n'
curl --fail --silent --show-error \
  --header 'Content-Type: application/json' \
  --data '{"texts":["Stocks rally as tech earnings beat expectations"]}' \
  http://127.0.0.1:8000/predict
printf '\n'

if [[ -x .venv/bin/python ]]; then
  PYTHON=.venv/bin/python
else
  PYTHON="${PYTHON:-python3}"
fi

"$PYTHON" scripts/loadtest.py
