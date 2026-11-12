import json
import subprocess
import sys

import pandas as pd

from src.train_hpo import EPOCHS, fit, git_commit


def test_hpo_fit_returns_pipeline_and_epoch_history():
    train = pd.DataFrame(
        {
            "text": [
                f"news category {label} example {index}"
                for index, label in enumerate([0, 1] * 10)
            ],
            "label": [0, 1] * 10,
        }
    )
    test = pd.DataFrame(
        {
            "text": ["news category 0 test", "news category 1 test"],
            "label": [0, 1],
        }
    )

    pipeline, history = fit(
        {"alpha": 1e-4, "max_features": 50, "ngram_max": 1}, train, test
    )

    assert hasattr(pipeline, "predict")
    assert len(history) == EPOCHS


def test_quality_gate_accepts_and_rejects_threshold(tmp_path):
    metrics = tmp_path / "metrics.json"
    metrics.write_text(json.dumps({"f1_macro": 0.9}), encoding="utf-8")
    command = [
        sys.executable,
        "scripts/quality_gate.py",
        "--metrics",
        str(metrics),
    ]

    passing = subprocess.run(command, check=False, capture_output=True, text=True)
    failing = subprocess.run(
        [*command, "--threshold", "0.99"], check=False, capture_output=True, text=True
    )

    assert passing.returncode == 0, passing.stdout + passing.stderr
    assert failing.returncode == 1, failing.stdout + failing.stderr


def test_git_commit_uses_build_environment(monkeypatch):
    monkeypatch.setenv("GIT_COMMIT", "abc123")
    assert git_commit() == "abc123"


def test_git_commit_without_git_is_nonfatal(monkeypatch):
    monkeypatch.delenv("GIT_COMMIT", raising=False)

    def missing_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr("src.train_hpo.subprocess.run", missing_git)
    assert git_commit() is None
