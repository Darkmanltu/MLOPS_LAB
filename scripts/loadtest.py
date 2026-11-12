import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/predict"
N, WORKERS = 100, 5
payload = {"texts": ["Stocks rally as tech earnings beat expectations"]}

def one(_):
    t = time.perf_counter()
    r = requests.post(URL, json=payload, timeout=10)
    r.raise_for_status()
    return (time.perf_counter() - t) * 1000

t0 = time.perf_counter()
with ThreadPoolExecutor(WORKERS) as ex:
    lat = sorted(ex.map(one, range(N)))
total = time.perf_counter() - t0
res = {"requests": N, "p50_ms": statistics.median(lat),
       "p95_ms": lat[int(0.95 * N) - 1], "throughput_rps": N / total}
print(res)
json.dump(res, open("docs/loadtest.json", "w"), indent=2)