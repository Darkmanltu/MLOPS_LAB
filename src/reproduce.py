import sys, json, shutil, subprocess, tempfile
import yaml, mlflow
from mlflow.tracking import MlflowClient

run_id = sys.argv[1]
client = MlflowClient()  # naudoja MLFLOW_TRACKING_URI
run = client.get_run(run_id)

with tempfile.TemporaryDirectory() as tmp:
    try:
        path = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="params.yaml", dst_path=tmp)
        shutil.copy(path, "params.yaml")
    except Exception:
        # fallback: senas run'as be params.yaml artefakto, atkuriame tik train dalį
        params = yaml.safe_load(open("params.yaml"))
        params["train"] = {k: yaml.safe_load(v) for k, v in run.data.params.items()}
        yaml.safe_dump(params, open("params.yaml", "w"))

subprocess.run(["dvc", "repro", "--force"], check=True)

expected = run.data.metrics
actual = json.load(open("metrics.json"))
for k, v in actual.items():
    print(f"{k}: originalus={expected.get(k):.4f}  atkurtas={v:.4f}")