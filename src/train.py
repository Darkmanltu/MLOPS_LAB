import yaml, joblib, pandas as pd, mlflow
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score

p = yaml.safe_load(open("params.yaml"))["train"]
train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")

mlflow.set_experiment("u1-text-classification")
with mlflow.start_run():
    mlflow.log_params(p)
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