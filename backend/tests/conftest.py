# backend/tests/conftest.py

import os

# ====================================================================
# CRÍTICO: Define TESTING=1 ANTES de qualquer import que use ChromaDB
# ====================================================================
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from main import create_app


@pytest.fixture(scope="session")
def client():
    app = create_app()
    return TestClient(app)
