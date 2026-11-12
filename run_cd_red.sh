#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

ref="${REF:-$(git branch --show-current)}"
if [[ -z "$ref" ]]; then
  echo "Detached HEAD: set REF to a GitHub branch containing the cd workflow." >&2
  exit 2
fi

gh workflow run cd.yml --ref "$ref" --field min_f1=0.99
echo "Started cd workflow on '$ref' with min_f1=0.99."
echo "Confirm Quality gate fails and later build/manifest steps are skipped."
echo "Save the failed run URL and screenshot as evidence."
