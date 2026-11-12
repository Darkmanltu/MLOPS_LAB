from pathlib import Path

import yaml
from datasets import load_dataset
from sklearn.model_selection import train_test_split

p = yaml.safe_load(open("params.yaml"))["prepare"]
ds = load_dataset(p["dataset"], split="train").shuffle(seed=p["seed"]).select(range(p["n_samples"]))
df = ds.to_pandas()[["text", "label"]]
train, test = train_test_split(df, test_size=p["test_size"], random_state=p["seed"], stratify=df["label"])
out = Path("data/processed")
out.mkdir(parents=True, exist_ok=True)
train.to_csv(out / "train.csv", index=False)
test.to_csv(out / "test.csv", index=False)