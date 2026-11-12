#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

ref="${REF:-$(git branch --show-current)}"
if [[ -z "$ref" ]]; then
  echo "Detached HEAD: set REF to a GitHub branch containing the cd workflow." >&2
  exit 2
fi

gh workflow run cd.yml --ref "$ref"
echo "Started cd workflow on '$ref' with min_f1 empty (uses params.yaml)."
echo "Check Actions and save the successful run URL and screenshot as evidence."
