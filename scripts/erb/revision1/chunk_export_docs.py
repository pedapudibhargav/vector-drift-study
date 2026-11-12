#!/usr/bin/env python3
"""Export the ladder documents (scale_rank < 100000) as JSONL for the chunking control."""
import json, os, psycopg2
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
out = ROOT / "data" / "chunk_study" / "docs.jsonl"
conn = psycopg2.connect(host="localhost", port=int(os.environ.get("PGPORT", 5433)), user=os.environ["PGUSER"],
                        password=os.environ["PGPASSWORD"], dbname=os.environ["PGDATABASE"])
cur = conn.cursor(name="x"); cur.itersize = 2000
cur.execute("SELECT doc_id, scale_rank, source_type, title, chunk_text FROM document_chunks WHERE scale_rank < 100000 ORDER BY scale_rank, doc_id")
n = 0
with out.open("w") as f:
    for d, r, st, t, c in cur:
        f.write(json.dumps({"doc_id": d, "scale_rank": r, "source_type": st, "title": t or "", "text": c or ""}) + "\n"); n += 1
print("docs", n)
