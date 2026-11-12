import argparse
import json
import sys

import yaml

p = argparse.ArgumentParser()
p.add_argument("--metrics", default="metrics.json")
p.add_argument("--key", default="f1_macro")     # pakeisk pagal savo metrics.json raktą
p.add_argument("--threshold", type=float)
a = p.parse_args()

thr = a.threshold if a.threshold is not None else yaml.safe_load(open("params.yaml"))["gate"]["min_f1"]
val = json.load(open(a.metrics))[a.key]
print(f"{a.key}={val:.4f} threshold={thr}")
sys.exit(0 if val >= thr else 1)