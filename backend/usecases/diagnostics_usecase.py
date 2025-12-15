# backend/usecases/diagnostics_usecase.py

import os
from typing import Dict, Any
from config import (
    LLM_PROVIDER,
    ACTIVE_MODEL,
    KNOWLEDGE_DIR,
    UPLOADS_DIR,
    CHROMA_DB_DIR,
)


def get_status() -> Dict[str, Any]:
    return {
        "provider": LLM_PROVIDER,
        "model": ACTIVE_MODEL,
        "knowledge_dir": os.path.exists(KNOWLEDGE_DIR),
        "uploads_dir": os.path.exists(UPLOADS_DIR),
        "vector_db": os.path.exists(CHROMA_DB_DIR),
    }
