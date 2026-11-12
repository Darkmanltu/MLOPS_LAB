#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -n "${SERVE_IMAGE:-}" ]]; then
  image="$SERVE_IMAGE"
else
  image="ghcr.io/darkmanltu/agnews-serve:$(git rev-parse HEAD)"
fi

if [[ ! "$image" =~ ^ghcr\.io/darkmanltu/agnews-serve:[A-Za-z0-9._-]+$ ]]; then
  echo "Expected SERVE_IMAGE in ghcr.io/darkmanltu/agnews-serve:<tag> format." >&2
  exit 2
fi

kubectl get configmap train-config --namespace mlops >/dev/null
kubectl get secret mlflow-credentials --namespace mlops >/dev/null

sed "s|image: ghcr.io/darkmanltu/agnews-serve:.*|image: $image|" \
  k8s/40-serve.yaml |
  kubectl apply -f -

kubectl rollout status deployment/agnews-api --namespace mlops --timeout=5m
kubectl get deployment agnews-api --namespace mlops
