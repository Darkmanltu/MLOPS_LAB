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
content hashes used by the pipeline. Training logs the sklearn model to MLflow's
Model Registry and assigns the `champion` alias to the newly registered
`agnews-clf` version, which is the model loaded by the serving API.

To register a model after starting MLflow and setting
`MLFLOW_TRACKING_URI`, rerun training against the prepared data:

```bash
python src/train.py
```

This is also useful if you trained before model registration was added. Once
the run completes, check the `agnews-clf` model in the MLflow UI and confirm it
has the `champion` alias before starting the API.

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

### Run HPO training as a Kubernetes Job

The DVC prepare stage in this repository writes to `data/processed/`; the HPO
trainer and its image use that same output. Reproduce the pipeline first so the
training data is present, then build and load the trainer image:

```bash
python -m dvc repro
docker build -f docker/train.Dockerfile -t agnews-train:local .
kind load docker-image agnews-train:local --name mlops
```

Create the credentials Secret in the `mlops` namespace. Supply the actual
credentials if MLflow authentication is enabled; otherwise use non-empty
placeholder values. Do not commit credentials or put them in a manifest:

```bash
kubectl create secret generic mlflow-credentials -n mlops \
  --from-literal=MLFLOW_TRACKING_USERNAME='<username-or-placeholder>' \
  --from-literal=MLFLOW_TRACKING_PASSWORD='<password-or-placeholder>'
```

The HPO settings and tracking URI are supplied by `train-config` in
`k8s/50-train.yaml`. Apply the Job and follow its logs:

```bash
kubectl apply -f k8s/50-train.yaml
kubectl logs -n mlops job/agnews-train -f
kubectl get job -n mlops
```

Confirm the Job has `COMPLETIONS 1/1` and that the MLflow UI shows a new
`u2-agnews-hpo` parent run. After training, restart the API so it resolves the
current `champion` model alias:

```bash
kubectl rollout restart deployment/agnews-api -n mlops
```

To run the Job again, delete the completed Job before applying the manifest:

```bash
kubectl delete job agnews-train -n mlops
kubectl apply -f k8s/50-train.yaml
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

## To reproduce a run 

Reproduce a run scenario using MLFOW runId (its a git commit)

and runing the following from the root directory.

<run_id> -> from Mlflow displayed Run Id

```bash
python src/reproduce.py  <run_id>
```
