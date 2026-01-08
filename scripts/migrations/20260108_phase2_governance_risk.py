"""
Migration helper for Enterprise Phase 2 (governance + risk observability).
- Creates governance_gates and risk_signals tables
- Adds governance_result and risk_result columns to decision_events
"""
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from backend.db.database import engine
from backend.enterprise.governance.models import GovernanceGate
from backend.enterprise.risk_engine.models import RiskSignal


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    try:
        columns = inspector.get_columns(table_name)
    except Exception:
        return False
    return any(col["name"] == column_name for col in columns)


def add_column_if_missing(table: str, column_sql: str) -> None:
    column_name = column_sql.split(" ")[0]
    if column_exists(table, column_name):
        return
    try:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_sql}"))
            print(f"[migrate] Added column {column_sql} to {table}")
    except OperationalError as exc:
        print(f"[migrate] Skipped adding {column_sql} to {table}: {exc}")


def migrate_decision_events() -> None:
    add_column_if_missing("decision_events", "governance_result JSON")
    add_column_if_missing("decision_events", "risk_result JSON")


def migrate_governance_gates() -> None:
    GovernanceGate.__table__.create(bind=engine, checkfirst=True)


def migrate_risk_signals() -> None:
    RiskSignal.__table__.create(bind=engine, checkfirst=True)


def run() -> None:
    migrate_governance_gates()
    migrate_risk_signals()
    migrate_decision_events()
    print("✅ Phase 2 migration executed")


if __name__ == "__main__":
    run()
