import csv
import random
import statistics

import requests

BASE = "http://127.0.0.1:8000"


def fetch(account_id: int, strategy: str) -> dict:
    resp = requests.get(f"{BASE}/transactions/{account_id}", params={"strategy": strategy})
    resp.raise_for_status()
    return resp.json()


requests.post(f"{BASE}/cache/flush").raise_for_status()

random.seed(7)
accounts = random.sample(range(1, 2001), 10)
warmup = random.sample([i for i in range(1, 2001) if i not in set(accounts)], 3)

results = []
by_strategy = {"direct": [], "index": [], "cache": []}

for strategy in ("direct", "index", "cache"):
    for wa in warmup:
        fetch(wa, strategy)

    if strategy == "cache":
        for a in accounts:
            fetch(a, "cache")

    for a in accounts:
        body = fetch(a, strategy)
        if strategy == "cache" and body.get("cache_hit") is not True:
            print(f"AVISO: cache_hit no es true para account_id={a} ({body.get('cache_hit')})")
        ms = body["elapsed_ms"]
        by_strategy[strategy].append(ms)
        results.append((strategy, a, ms))

print(f"A (direct): {by_strategy['direct']}")
print(f"B (index): {by_strategy['index']}")
print(f"C (cache): {by_strategy['cache']}")

for name, values in by_strategy.items():
    print(f"media {name}: {round(statistics.mean(values), 3)} ms")

with open("resultados.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["strategy", "account_id", "elapsed_ms"])
    w.writerows(results)
