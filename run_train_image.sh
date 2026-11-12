#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

IMAGE="${TRAIN_IMAGE:-agnews-train:local}"
kind_cluster="${KIND_CLUSTER:-mlops}"
GIT_COMMIT="$(git rev-parse HEAD)"

docker build \
  --build-arg "GIT_COMMIT=$GIT_COMMIT" \
  -f docker/train.Dockerfile \
  -t "$IMAGE" .
kind load docker-image "$IMAGE" --name "$kind_cluster"
