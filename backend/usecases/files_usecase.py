# backend/usecases/files_usecase.py

import os
from typing import Dict, Any

from config import UPLOADS_DIR
from services.llm_client import generate_answer


def save_uploaded_file(filename: str, content: bytes) -> Dict[str, Any]:
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    path = os.path.join(UPLOADS_DIR, filename)

    with open(path, "wb") as f:
        f.write(content)

    return {"filename": filename}


def ask_about_file(filename: str, question: str) -> Dict[str, Any]:
    path = os.path.join(UPLOADS_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError("Arquivo não encontrado.")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    prompt = f"""
Você é o TR4CTION Agent.

Arquivo analisado:
{content}

Pergunta do usuário:
{question}
"""
    answer = generate_answer(prompt)
    return {"answer": answer}
