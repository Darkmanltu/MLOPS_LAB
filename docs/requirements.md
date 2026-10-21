# Project requirements — v1.1

## Purpose and scope

This project demonstrates a reproducible MLOps workflow for classifying AG
News text into its four news categories. It uses a small, deterministic
Hugging Face dataset subset and a CPU-friendly TF-IDF + logistic-regression
model. The course fraud-detection sample is not part of this project.

The U1 scope is dataset preparation, model training and evaluation, DVC
reproduction, MLflow experiment tracking in a local Kubernetes cluster, and a
versioned Docker training image. Model serving and CI/CD are out of scope.

## Functional requirements

| ID | Requirement | Acceptance check |
|---|---|---|
| FR-1 | Prepare a deterministic train/test split from the configured Hugging Face AG News dataset. | `dvc repro prepare` creates train and test CSV files with the configured seed and test ratio. |
| FR-2 | Train a TF-IDF + logistic-regression classifier using values from `params.yaml`. | `dvc repro train` creates `models/model.joblib` and logs the parameters and metrics to the configured MLflow Tracking Server. |
| FR-3 | Evaluate the trained model on the held-out test set. | `dvc repro evaluate` writes accuracy and macro-F1 to `metrics.json`. |
| FR-4 | Track and reproduce preparation, training, and evaluation with DVC. | `dvc repro` completes all three stages as needed; `dvc.lock` records stage parameters and dependency/output hashes. |
| FR-5 | Persist experiments in the Kubernetes-hosted MLflow service. | The MLflow UI shows at least three runs with different training parameters after setting `MLFLOW_TRACKING_URI` to the forwarded cluster service. |
| FR-6 | Package the training program as a Docker image. | `docker build -t agnews-trainer:local .` succeeds and the container can log a run to the reachable MLflow service. |

## Non-functional requirements

| ID | Requirement | KPI / verification |
|---|---|---|
| NFR-1 | Reproducibility: the same committed code, parameters, and DVC-tracked inputs produce the same split and evaluation metrics. | Run `dvc repro` twice with unchanged inputs; the second run reports up to date, and the recorded metrics match exactly. |
| NFR-2 | Reproduction time: rerun the pipeline using an already available dataset and DVC cache. | `time dvc repro` finishes in less than 120 seconds on the project machine. |
| NFR-3 | Tracking persistence: MLflow run metadata and model artifacts survive an MLflow Pod restart. | Create a run, delete the MLflow Pod, wait for its replacement, and verify the run and artifact remain accessible. |
| NFR-4 | Traceability: every run identifies the model settings and evaluation metrics. | Each MLflow run includes `C`, `max_features`, `ngram_max`, accuracy, and macro-F1. |
| NFR-5 | Resource-conscious training: the model trains on CPU without GPU dependencies. | Complete training on the configured 8,000-example subset in under 120 seconds on the project machine. |
| NFR-6 | Container traceability and security evidence. | Publish an immutable `sha-<commit>` GHCR tag; record its measured size and Trivy scan summary in `docs/u1-report.md`. |
| NFR-7 | Usability: a new setup can follow the repository instructions without relying on the fraud-detection sample. | A clean setup can install prerequisites, deploy MLflow, run `dvc repro`, and open the MLflow UI using only `README.md`. |

NFR-2, NFR-3, NFR-5, and NFR-6 are measured operationally and must be filled
with actual results in the U1 report; the targets above are not claims that
the measurements have already passed.

## Assumptions and constraints

- Python 3.12, Docker, kind, and kubectl are available.
- The first dataset preparation requires internet access.
- The DVC local remote is a directory adjacent to the repository (`../dvc-storage`); each machine must create or configure its own local path.
- PostgreSQL data and MLflow artifacts use persistent volume claims in the kind cluster.
- The demo PostgreSQL password in the local Kubernetes manifest is for local coursework only; do not reuse it in a shared or public deployment.
