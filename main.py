import json
import sqlite3
import time

import redis
from fastapi import FastAPI, HTTPException

DB = "transactions.db"
SQL_INDEX = """
SELECT id, account_id, amount, type, status, created_at
FROM transactions
WHERE account_id = ?
ORDER BY created_at DESC
LIMIT 50
"""
SQL_DIRECT = """
SELECT id, account_id, amount, type, status, created_at
FROM transactions NOT INDEXED
WHERE account_id = ?
ORDER BY created_at DESC
LIMIT 50
"""

app = FastAPI()
r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)


def query_rows(sql: str, account_id: int) -> list[dict]:
    conn = sqlite3.connect(DB)
    try:
        cur = conn.execute(sql, (account_id,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


@app.get("/transactions/{account_id}")
def get_transactions(account_id: int, strategy: str = "direct"):
    if strategy not in ("direct", "index", "cache"):
        raise HTTPException(status_code=400, detail="strategy debe ser direct|index|cache")

    start = time.perf_counter()
    cache_hit = None

    if strategy == "direct":
        data = query_rows(SQL_DIRECT, account_id)
    elif strategy == "index":
        data = query_rows(SQL_INDEX, account_id)
    else:
        key = f"tx:{account_id}"
        cached = r.get(key)
        if cached is not None:
            data = json.loads(cached)
            cache_hit = True
        else:
            data = query_rows(SQL_INDEX, account_id)
            r.setex(key, 300, json.dumps(data))
            cache_hit = False

    elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
    return {
        "strategy": strategy,
        "account_id": account_id,
        "rows": len(data),
        "elapsed_ms": elapsed_ms,
        "cache_hit": cache_hit,
        "data": data,
    }


@app.post("/cache/flush")
def flush_cache():
    r.flushdb()
    return {"ok": True}
