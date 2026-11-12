#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

kubectl get secret mlflow-credentials --namespace mlops >/dev/null

if kubectl get job agnews-train --namespace mlops >/dev/null 2>&1; then
  conditions="$(kubectl get job agnews-train --namespace mlops \
    -o jsonpath='{.status.conditions[*].type}')"
  if [[ " $conditions " == *" Complete "* || " $conditions " == *" Failed "* ]]; then
    kubectl delete job agnews-train --namespace mlops
  else
    active="$(kubectl get job agnews-train --namespace mlops \
      -o jsonpath='{.status.active}')"
    if [[ "$active" =~ ^[1-9][0-9]*$ ]]; then
      read -r -p "An active agnews-train Job exists. Delete and replace it? [y/N] " answer
      case "$answer" in
        y|Y|yes|YES) kubectl delete job agnews-train --namespace mlops ;;
        *)
          echo "Existing Job was left unchanged."
          exit 1
          ;;
      esac
    else
      echo "Existing Job is not complete or failed; inspect it before retrying." >&2
      exit 1
    fi
  fi
fi

kubectl apply -f k8s/50-train.yaml

if ! kubectl wait --namespace mlops \
  --for=condition=complete job/agnews-train \
  --timeout="${JOB_TIMEOUT:-30m}"; then
  kubectl describe job agnews-train --namespace mlops || true
  kubectl logs --namespace mlops job/agnews-train \
    --all-containers=true --tail=100 || true
  exit 1
fi

kubectl get job agnews-train --namespace mlops
kubectl logs --namespace mlops job/agnews-train --all-containers=true
