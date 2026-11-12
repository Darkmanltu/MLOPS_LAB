#!/usr/bin/env bash
set -euo pipefail

kubectl rollout history deployment/agnews-api --namespace mlops

if [[ "${CONFIRM_ROLLBACK:-}" != "yes" ]]; then
  read -r -p "Roll back agnews-api to the previous revision? [y/N] " answer
  case "$answer" in
    y|Y|yes|YES) ;;
    *)
      echo "Rollback cancelled."
      exit 0
      ;;
  esac
fi

kubectl rollout undo deployment/agnews-api --namespace mlops
kubectl rollout status deployment/agnews-api --namespace mlops --timeout=5m
kubectl get deployment agnews-api --namespace mlops
