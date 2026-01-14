from typing import Generator
from sqlalchemy.orm import Session

# Re-export project-wide DB session and Base
from backend.db.database import SessionLocal, Base, engine, get_db as _get_db


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session.
    Uses the project's global SessionLocal to keep consistency.
    """
    yield from _get_db()

__all__ = ["SessionLocal", "Base", "engine", "get_db"]
