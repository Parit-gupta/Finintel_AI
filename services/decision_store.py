"""Local and optional PostgreSQL persistence for manual decisions."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HISTORY_PATH = PROJECT_ROOT / "datasets" / "processed" / "manual_decision_history.csv"


@lru_cache(maxsize=1)
def _engine():
    """Build an engine only when database settings are present."""
    load_dotenv(PROJECT_ROOT / ".env")
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return create_engine(explicit_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})

    required = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    values = {name: os.getenv(name) for name in required}
    if not all(values.values()):
        return None
    url = URL.create(
        "postgresql+psycopg2",
        username=values["DB_USER"],
        password=values["DB_PASSWORD"],
        host=values["DB_HOST"],
        port=int(values["DB_PORT"]),
        database=values["DB_NAME"],
    )
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


def _ensure_table(engine):
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS manual_decision_history (
                decision_id BIGSERIAL PRIMARY KEY,
                timestamp_utc TIMESTAMPTZ NOT NULL,
                decision_type TEXT NOT NULL,
                outcome TEXT NOT NULL,
                details TEXT NOT NULL
            )
        """))


def save_decision(decision_type: str, outcome: str, details: str) -> tuple[bool, str | None]:
    """Save locally and to PostgreSQL if configured; return database status."""
    timestamp = datetime.now(timezone.utc).isoformat()
    row = {"timestamp_utc": timestamp, "decision_type": decision_type, "outcome": outcome, "details": details}
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([row]).to_csv(HISTORY_PATH, mode="a", header=not HISTORY_PATH.exists(), index=False)

    try:
        engine = _engine()
        if engine is None:
            return False, "PostgreSQL is not configured; saved to the local CSV."
        _ensure_table(engine)
        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO manual_decision_history
                    (timestamp_utc, decision_type, outcome, details)
                VALUES (:timestamp_utc, :decision_type, :outcome, :details)
            """), row)
        return True, None
    except Exception as error:
        return False, f"PostgreSQL save failed ({type(error).__name__}); saved to the local CSV."


def load_history() -> tuple[pd.DataFrame, str]:
    """Load DB history when reachable and merge local-only records without duplicates."""
    local = pd.read_csv(HISTORY_PATH) if HISTORY_PATH.exists() else pd.DataFrame(
        columns=["timestamp_utc", "decision_type", "outcome", "details"]
    )
    try:
        engine = _engine()
        if engine is None:
            return local, "Local CSV"
        _ensure_table(engine)
        database = pd.read_sql_query(
            text("SELECT timestamp_utc, decision_type, outcome, details FROM manual_decision_history ORDER BY timestamp_utc DESC"),
            engine,
        )
        combined = pd.concat([database, local], ignore_index=True)
        combined["timestamp_utc"] = pd.to_datetime(combined["timestamp_utc"], utc=True, errors="coerce")
        combined["_timestamp_key"] = combined["timestamp_utc"].astype(str)
        combined = combined.drop_duplicates(subset=["_timestamp_key", "decision_type", "outcome", "details"])
        combined = combined.drop(columns="_timestamp_key")
        return combined.sort_values("timestamp_utc", ascending=False), "PostgreSQL + local CSV"
    except Exception:
        return local, "Local CSV (PostgreSQL unavailable)"
