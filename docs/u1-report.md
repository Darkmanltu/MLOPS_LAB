# U1 report

> Update this report with measured results and the final repository/image
> references before submission. Do not report a check as passed until it has
> been run on the target machine and cluster.

## Summary

AG News text classification is implemented as a three-stage DVC pipeline:
`prepare → train → evaluate`. The training script can send metrics, parameters,
and the model artifact to the MLflow Tracking Server selected by
`MLFLOW_TRACKING_URI`. Kubernetes manifests define the `mlops` namespace,
PostgreSQL, MLflow, and persistent volumes.

## Results to record

| Check | Measured result |
|---|---|
| DVC reproduction time with cached dataset | 58.96 seconds; `dvc repro` reported all stages up to date. |
| MLflow runs on the cluster | 5 finished runs; three distinct parameter sets were verified. |
| Selected run (`C=1.0`, `max_features=5000`, `ngram_max=2`) | Accuracy 0.87125; macro-F1 0.87010; MLflow run duration 21.9 seconds. |
| MLflow run and artifact persistence after Pod restart | Passed: run metadata and the 347,772-byte `model.joblib` were accessible after replacing the MLflow Pod. |
| Local GHCR-ready trainer image | `agnews-trainer:local`; GHCR publication still pending. |
| Local trainer image size | 896,480,153 bytes (Docker image metadata). |
| Trivy version and scan summary | Trivy 0.76.0: 0 CRITICAL, 46 HIGH, 63 MEDIUM, 62 LOW, and 3 UNKNOWN findings in the local trainer image; one HIGH Python-package finding has a fix available. Review before public publishing. |

## Issues and time spent

- The default 20,000-feature model took 3 minutes 31 seconds for its MLflow run. Reducing the vocabulary to 5,000 features kept accuracy at 0.87125 and macro-F1 at 0.87010, with measured MLflow training duration around 20 seconds.
- MLflow 3 rejected client requests with a non-local `Host` header until an explicit host:port allowlist was configured. The README uses local port 5001 because port 5000 was unavailable on this machine.
- A full DVC run in this WSL workspace took about 3 minutes even though the MLflow training run itself took about 20 seconds; the cached no-change reproduction completed in under 60 seconds.
- The container image built and successfully logged a run to the cluster MLflow server. Its local size is about 896 MB; GHCR publication remains pending because no Git remote or registry credentials are configured in this workspace.
- Time spent: record actual time before submission.

## Final references

- Repository and `u1-final` tag: pending
- GHCR image: pending
