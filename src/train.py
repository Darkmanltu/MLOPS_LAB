import os
import yaml
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score
import subprocess

p = yaml.safe_load(open("params.yaml"))["train"]
train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")

model_name = os.environ.get("MODEL_NAME", "agnews-clf")
model_alias = os.environ.get("MODEL_ALIAS", "champion")
tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
mlflow.set_tracking_uri(tracking_uri)
mlflow.set_experiment("u1-text-classification")
client = MlflowClient()
with mlflow.start_run(run_name=f"tfidf-logreg-C{p['C']}"):
    mlflow.log_params(p)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    mlflow.set_tag("git commit", commit)
    model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=p["max_features"], ngram_range=(1, p["ngram_max"]))),
        ("clf", LogisticRegression(C=p["C"], max_iter=1000)),
    ])
    model.fit(train["text"], train["label"])
    pred = model.predict(test["text"])
    mlflow.log_metric("accuracy", accuracy_score(test["label"], pred))
    mlflow.log_metric("f1_macro", f1_score(test["label"], pred, average="macro"))
    Path("models").mkdir(exist_ok=True)
    joblib.dump(model, "models/model.joblib")
    mlflow.log_artifact("models/model.joblib")
    model_info = mlflow.sklearn.log_model(
        model,
        name="model",
        registered_model_name=model_name,
        await_registration_for=300,
    )
    client.set_registered_model_alias(
        model_name, model_alias, model_info.registered_model_version
    )