#!/usr/bin/env bash
set -euo pipefail

echo "Forwarding MLflow to http://127.0.0.1:5001 (Ctrl-C to stop)."
exec kubectl port-forward --namespace mlops service/mlflow 5001:5000
