import json, joblib, pandas as pd
from sklearn.metrics import accuracy_score, f1_score

model = joblib.load("models/model.joblib")
test = pd.read_csv("data/processed/test.csv")
pred = model.predict(test["text"])
json.dump({"accuracy": accuracy_score(test["label"], pred),
           "f1_macro": f1_score(test["label"], pred, average="macro")},
          open("metrics.json", "w"), indent=2)