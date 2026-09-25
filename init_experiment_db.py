#!/usr/bin/env python3
"""Apply experiment tracking schema to PostgreSQL."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "infra" / "db" / "experiment_schema.sql"


def _dsn() -> str:
    raw = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/vector_drift_db",
    )
    return raw.replace("postgresql+asyncpg://", "postgresql://").replace(
        "@vector-drift-postgres:", "@localhost:"
    )


def main() -> int:
    ddl = SCHEMA_PATH.read_text()
    dsn = _dsn()
    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(ddl)
            tables = conn.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('experiment_runs', 'vector_drift_results', 'llm_eval_results')
                ORDER BY table_name
                """
            ).fetchall()
        print(f"Experiment schema applied: {dsn.split('@')[-1]}")
        print("Tables:", ", ".join(row[0] for row in tables))
        return 0 if len(tables) == 3 else 1
    except Exception as exc:
        print(f"init_experiment_db failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
