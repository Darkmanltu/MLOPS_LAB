# AG News text classification — U1 mini MLOps project

Train a TF-IDF + logistic-regression text classifier on a deterministic subset
of the Hugging Face AG News dataset. DVC manages the `prepare → train → evaluate`
pipeline, MLflow tracks training runs, and the Kubernetes manifests deploy an
MLflow Tracking Server backed by PostgreSQL and persistent artifact storage.
This project does not use the course fraud-detection sample.

## Prerequisites

- Git, Python 3.12, Docker, `kind`, `kubectl`
- At least 4 GB RAM available to Docker for the local cluster
- Internet access for Python packages and the first Hugging Face dataset download

## 1. Install and prepare the project

Run commands from the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
mkdir -p ../dvc-storage
```

The DVC remote is a local directory at `../dvc-storage`. On another machine,
create that directory next to the repository and configure the local remote:

```bash
python -m dvc remote modify localremote url ../../dvc-storage
```

## 2. Start the local Kubernetes cluster and MLflow

```bash
kind create cluster --config k8s/kind-config.yaml
docker build -f docker/mlflow.Dockerfile -t mlflow-u1:local .
kind load docker-image mlflow-u1:local --name mlops
kubectl apply -f k8s/00-namespace.yaml -f k8s/10-postgres.yaml -f k8s/20-mlfow.yaml
kubectl rollout status deployment/postgres -n mlops --timeout=180s
kubectl rollout status deployment/mlflow -n mlops --timeout=180s
```

In a **separate terminal**, forward the MLflow service port and leave this
command running:

```bash
kubectl port-forward -n mlops svc/mlflow 5001:5000
```

Open <http://127.0.0.1:5001>. Configure training in the terminal where the
virtual environment is active:

```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5001
```

The Kubernetes MLflow server stores run metadata in PostgreSQL and artifacts
under `/mlflow/artifacts` on the `mlflow-artifacts-pvc`. Port-forwarding makes
the server available on the host; training runs use the forwarded server URL,
not a local `mlruns/` directory.

## 3. Run and reproduce the DVC pipeline

```bash
python -m dvc repro
python -m dvc push
cat metrics.json
```

`dvc repro` runs data preparation, model training, and evaluation in order.
The first run downloads and prepares the dataset; subsequent unchanged runs
should be up to date. The checked-in `dvc.lock` records the parameters and
content hashes used by the pipeline.

Run three experiments with different model settings; each training run is
logged to the MLflow server specified above:

```bash
python -m dvc exp run --set-param train.C=0.5
python -m dvc exp run --set-param train.C=1.0
python -m dvc exp run --set-param train.C=2.0
```

Visit <http://127.0.0.1:5001> and select the `u1-text-classification`
experiment. Confirm that the runs have distinct `C` values. Restore committed
pipeline parameters and outputs with:

```bash
git restore params.yaml dvc.lock metrics.json
```

If DVC reports that outputs are already up to date and no new run is created,
force a run after choosing the desired parameter set:

```bash
python -m dvc repro --force
```

For a clean reproducibility check, use a separate DVC experiment or restore
the committed `params.yaml` and `dvc.lock`, then measure `time python -m dvc repro`.
The target is under two minutes on the same machine after the dataset is
available locally.

## 4. Build and run the training container

The root `Dockerfile` creates a CPU training image that uses the same
`MLFLOW_TRACKING_URI` environment variable as local training:

```bash
docker build -t agnews-trainer:local .
docker run --rm \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5001 \
  --add-host=host.docker.internal:host-gateway \
  agnews-trainer:local
```

The `--add-host` option maps `host.docker.internal` to the host gateway on
Linux. Make sure the MLflow port-forward is running first.

To publish a commit-specific GHCR image, authenticate with GitHub Container
Registry with a token that has package write permission. Set `GHCR_TOKEN`
securely in your shell; do not paste or commit the token. Run these commands
after committing the source:

```bash
GHCR_USER=your-github-username
GHCR_REPOSITORY=your-repository-name
IMAGE="ghcr.io/${GHCR_USER}/${GHCR_REPOSITORY}"
TAG="sha-$(git rev-parse HEAD)"
echo "$GHCR_TOKEN" | docker login ghcr.io --username "$GHCR_USER" --password-stdin
docker build -t "$IMAGE:$TAG" .
docker push "$IMAGE:$TAG"
docker image inspect "$IMAGE:$TAG" --format '{{.Size}} bytes'
trivy image "$IMAGE:$TAG"
```

Record the exact image reference, measured size, scan date, and Trivy summary
in `docs/u1-report.md`. Do not publish a `latest` tag as the deliverable.
Never commit a GHCR token.

## Useful Kubernetes commands

```bash
kubectl get all -n mlops
kubectl get pvc -n mlops
kubectl logs deployment/mlflow -n mlops
kubectl delete -f k8s/20-mlfow.yaml -f k8s/10-postgres.yaml
kubectl delete -f k8s/00-namespace.yaml
kind delete cluster --name mlops
```

Deleting the cluster also deletes its local persistent volumes. Export or
otherwise preserve any run data you need before destroying the cluster.

## Project files

- `src/`: data preparation, training, and evaluation
- `dvc.yaml`, `params.yaml`, `dvc.lock`: pipeline, parameters, and locked state
- `k8s/`: kind, namespace, PostgreSQL, and MLflow configuration
- `docker/`: MLflow image and its Python database driver
- `docs/requirements.md`: project requirements and measurable acceptance KPIs
- `docs/u1-report.md`: U1 completion report (update measured results before submission)
