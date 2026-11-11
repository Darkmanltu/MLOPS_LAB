import json, subprocess
import mlflow, mlflow.data, mlflow.sklearn, optuna
import numpy as np
import pandas as pd
from mlflow import MlflowClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

SEED = 42
MODEL_NAME = "agnews-clf"
EXPERIMENT = "u2-agnews-hpo"
N_TRIALS = 6          # reikalavimas: >= 5
EPOCHS = 8


def load_data():
    # TODO: pajunk prie savo prepare išvesties. Reikia stulpelių: text, label
    train = pd.read_csv("data/prepared/train.csv")
    test = pd.read_csv("data/prepared/test.csv")
    return train, test


def git_commit():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def fit(params, train, test):
    """Moko su partial_fit, kad turėtume metrikas per step. Grąžina (pipeline, history)."""
    vec = TfidfVectorizer(max_features=params["max_features"],
                          ngram_range=(1, params["ngram_max"]))
    Xtr = vec.fit_transform(train["text"])
    Xte = vec.transform(test["text"])
    clf = SGDClassifier(loss="log_loss", alpha=params["alpha"], random_state=SEED)
    classes = np.unique(train["label"])
    history = []
    for epoch in range(EPOCHS):
        clf.partial_fit(Xtr, train["label"], classes=classes)
        pred = clf.predict(Xte)
        history.append((epoch,
                        accuracy_score(test["label"], pred),
                        f1_score(test["label"], pred, average="macro")))
    return Pipeline([("tfidf", vec), ("clf", clf)]), history


def main():
    train, test = load_data()
    mlflow.set_experiment(EXPERIMENT)
    mlflow.set_system_metrics_sampling_interval(1)
    commit = git_commit()

    def log_common(history, params):
        mlflow.log_params(params)
        mlflow.log_param("seed", SEED)
        mlflow.set_tag("git_commit", commit)
        mlflow.log_input(mlflow.data.from_pandas(train, name="ag_news_train"), context="training")
        mlflow.log_input(mlflow.data.from_pandas(test, name="ag_news_test"), context="testing")
        for step, acc, f1 in history:
            mlflow.log_metric("accuracy", acc, step=step)
            mlflow.log_metric("f1_macro", f1, step=step)

    with mlflow.start_run(run_name="hpo-parent", log_system_metrics=True) as parent:
        def objective(trial):
            params = {
                "alpha": trial.suggest_float("alpha", 1e-6, 1e-3, log=True),
                "max_features": trial.suggest_categorical("max_features", [5000, 10000, 20000]),
                "ngram_max": trial.suggest_int("ngram_max", 1, 2),
            }
            with mlflow.start_run(run_name=f"trial-{trial.number}", nested=True):
                _, history = fit(params, train, test)
                log_common(history, params)
                return history[-1][2]

        study = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=SEED))
        study.optimize(objective, n_trials=N_TRIALS)

        best = study.best_params
        pipe, history = fit(best, train, test)
        log_common(history, best)
        f1 = history[-1][2]
        mlflow.log_metric("best_f1_macro", f1)

        info = mlflow.sklearn.log_model(pipe, name="model", registered_model_name=MODEL_NAME)
        version = info.registered_model_version

        # alias tik jei geresnis už esamą champion
        client = MlflowClient()
        promote = True
        try:
            champ = client.get_model_version_by_alias(MODEL_NAME, "champion")
            champ_f1 = client.get_run(champ.run_id).data.metrics.get("best_f1_macro", 0.0)
            promote = f1 > champ_f1
        except Exception:
            pass  # champion dar nėra
        if promote:
            client.set_registered_model_alias(MODEL_NAME, "champion", version)

        with open("metrics.json", "w") as f:
            json.dump({"f1_macro": f1, "accuracy": history[-1][1]}, f)
        print(f"best={best} f1={f1:.4f} version={version} promoted={promote}")


if __name__ == "__main__":
    main()