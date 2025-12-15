# backend/services/groq_client.py
from __future__ import annotations

from typing import List, Dict

from services.llm_client import get_llm_client


def chat_completion(messages: List[Dict[str, str]]) -> str:
    """
    Wrapper de compatibilidade para código legado.
    """
    client = get_llm_client()
    return client.chat(messages)
