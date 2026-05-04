"""
python .\verify_sql.py > out.txt 2>&1
notepad out.txt
"""

import sqlite3
from pathlib import Path
import sys

db_path = Path("../reports_streamlit/build4_football_analytics.sqlite")
if not db_path.exists():
    print("ERROR: file not found:", db_path)
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

# 1) PRAGMA integrity_check
cur.execute("PRAGMA integrity_check;")
res = cur.fetchall()
print("PRAGMA integrity_check:", res)

# 2) Check foreign key integrity (if DB uses FKs)
cur.execute("PRAGMA foreign_key_check;")
fk_issues = cur.fetchall()
print("PRAGMA foreign_key_check:", fk_issues or "no foreign key issues or no foreign keys defined")

# 3) List tables and views
cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name;")
for row in cur.fetchall():
    print("schema object:", row)

# 4) Show CREATE statement for each table
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
for name, sql in cur.fetchall():
    print(f"TABLE: {name}\n{sql}\n")

# 5) Basic row counts (helpful to detect truncated data)
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM \"{t}\";")
        print(f"{t} rows:", cur.fetchone()[0])
    except Exception as e:
        print(f"Error counting rows in {t}: {e}")

# 6) Sample rows from important tables (change names as needed)
for t in tables:
    cur.execute(f"PRAGMA table_info('{t}');")
    cols = [c[1] for c in cur.fetchall()]
    if not cols:
        continue
    cur.execute(f"SELECT * FROM \"{t}\" LIMIT 5;")
    print(f"Sample from {t}:")
    for r in cur.fetchall():
        print(dict(zip(cols, r)))
    print()

conn.close()
