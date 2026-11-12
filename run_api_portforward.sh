#!/usr/bin/env bash
set -euo pipefail

echo "Forwarding the API to http://127.0.0.1:8000 (Ctrl-C to stop)."
exec kubectl port-forward --namespace mlops service/agnews-api 8000:8000
    