# backend/tests/conftest.py

import os

# ====================================================================
# CRÍTICO: Define TESTING=1 ANTES de qualquer import que use ChromaDB
# ====================================================================
os.environ["TESTING"] = "1"

import pytest
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
from main import create_app


@pytest.fixture(scope="session")
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock do SQLAlchemy database session"""
    db = MagicMock()
    db.query = MagicMock(return_value=db)
    db.filter = MagicMock(return_value=db)
    db.filter_by = MagicMock(return_value=db)
    db.order_by = MagicMock(return_value=db)
    db.first = MagicMock(return_value=None)
    db.all = MagicMock(return_value=[])
    db.count = MagicMock(return_value=0)
    db.add = MagicMock()
    db.delete = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.flush = MagicMock()
    return db
