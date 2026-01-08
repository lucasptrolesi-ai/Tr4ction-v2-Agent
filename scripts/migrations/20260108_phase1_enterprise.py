"""
Migration helper for Enterprise Phase 1 (observability-only).
- Creates client_premises table
- Adds observability columns to decision_events and ai_audit_logs

Idempotent and safe for SQLite/PostgreSQL (adds columns if missing).
"""
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from backend.db.database import engine
from backend.enterprise.client_premises import ClientPremise
from backend.enterprise.decision_ledger.models import DecisionEvent
from backend.enterprise.ai_audit.models import AIAuditLog


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    try:
        columns = inspector.get_columns(table_name)
    except Exception:
        return False
    return any(col["name"] == column_name for col in columns)


def add_column_if_missing(table: str, column_sql: str) -> None:
    if column_exists(table, column_sql.split(" ")[0]):
        return
    try:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_sql}"))
            print(f"[migrate] Added column {column_sql} to {table}")
    except OperationalError as exc:
        print(f"[migrate] Skipped adding {column_sql} to {table}: {exc}")


def migrate_decision_events() -> None:
    add_column_if_missing("decision_events", "premises_used JSON")
    add_column_if_missing("decision_events", "ai_recommendation TEXT")
    add_column_if_missing("decision_events", "risk_level VARCHAR(50)")
    add_column_if_missing("decision_events", "human_confirmation BOOLEAN")
    add_column_if_missing("decision_events", "method_version VARCHAR(50)")
    add_column_if_missing("decision_events", "vertical VARCHAR(100)")


def migrate_ai_audit_logs() -> None:
    add_column_if_missing("ai_audit_logs", "response_id VARCHAR(100)")
    add_column_if_missing("ai_audit_logs", "prompt_hash VARCHAR(100)")
    add_column_if_missing("ai_audit_logs", "prompt_version VARCHAR(50)")
    add_column_if_missing("ai_audit_logs", "context_snapshot JSON")
    add_column_if_missing("ai_audit_logs", "governance_rules_active JSON")


def migrate_client_premises() -> None:
    ClientPremise.__table__.create(bind=engine, checkfirst=True)


def run() -> None:
    migrate_client_premises()
    migrate_decision_events()
    migrate_ai_audit_logs()
    print("✅ Phase 1 migration executed")


if __name__ == "__main__":
    run()
