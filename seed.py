import random
import sqlite3
from datetime import datetime, timedelta

DB = "transactions.db"
N = 1_000_000
BATCH = 50_000
TYPES = ["deposit", "withdrawal", "transfer"]
STATUSES = ["approved", "pending", "rejected"]
END = datetime(2026, 10, 27)
SPAN_SECONDS = 2 * 365 * 24 * 3600

random.seed(42)

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode = OFF")
conn.execute("PRAGMA synchronous = OFF")
conn.execute("DROP TABLE IF EXISTS transactions")
conn.execute(
    """
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY,
        account_id INTEGER,
        amount REAL,
        type TEXT,
        status TEXT,
        created_at TEXT
    )
    """
)

sql = "INSERT INTO transactions (account_id, amount, type, status, created_at) VALUES (?, ?, ?, ?, ?)"
conn.execute("BEGIN")
for offset in range(0, N, BATCH):
    batch = []
    for _ in range(BATCH):
        created = END - timedelta(seconds=random.randint(0, SPAN_SECONDS))
        batch.append(
            (
                random.randint(1, 2000),
                round(random.uniform(1, 10_000), 2),
                random.choice(TYPES),
                random.choice(STATUSES),
                created.isoformat(timespec="seconds"),
            )
        )
    conn.executemany(sql, batch)
    print(f"insertadas {offset + BATCH} / {N}")
conn.commit()

conn.execute("CREATE INDEX idx_account_date ON transactions(account_id, created_at DESC)")
conn.commit()
conn.close()
print("listo: transactions.db")
