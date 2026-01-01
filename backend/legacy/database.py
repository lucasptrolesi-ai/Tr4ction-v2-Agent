import json
import os
from typing import Dict, Any, List

from config import KNOWLEDGE_DIR

DB_FILE = os.path.join(KNOWLEDGE_DIR, "knowledge.json")


def _init_db_if_needed() -> None:
    """
    Se o arquivo de 'banco de dados' não existir, cria com estrutura básica.
    """
    if not os.path.exists(DB_FILE):
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({"items": []}, f, ensure_ascii=False, indent=4)


def load_db() -> Dict[str, Any]:
    _init_db_if_needed()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(data: Dict[str, Any]) -> None:
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def next_id(items: List[Dict[str, Any]]) -> int:
    """
    Gera um ID incremental simples.
    """
    if not items:
        return 1
    return max(i.get("id", 0) for i in items) + 1
# --- IGNORE ---        