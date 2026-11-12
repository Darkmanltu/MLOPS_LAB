#!/usr/bin/env bash
set -euo pipefail

kubectl get namespace mlops >/dev/null

read -r -p "MLflow username (leave blank if auth is disabled): " username
read -r -s -p "MLflow password (leave blank if auth is disabled): " password
printf '\n'

username="${username:-not-configured}"
password="${password:-not-configured}"

umask 077
secret_file="$(mktemp)"
trap 'rm -f -- "$secret_file"; unset username password' EXIT

printf 'MLFLOW_TRACKING_USERNAME=%s\nMLFLOW_TRACKING_PASSWORD=%s\n' \
  "$username" "$password" >"$secret_file"

kubectl create secret generic mlflow-credentials \
  --namespace mlops \
  --from-env-file="$secret_file" \
  --dry-run=client \
  --output=yaml |
  kubectl apply -f -
