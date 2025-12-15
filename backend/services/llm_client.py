# backend/services/llm_client.py

import os
from config import LLM_PROVIDER, ACTIVE_MODEL, DEBUG_MODE


# Detecta Pytest via múltiplas formas
IS_TEST_MODE = (
    os.getenv("PYTEST_CURRENT_TEST") is not None or
    os.getenv("TESTING") == "1" or
    "pytest" in os.getenv("_", "").lower()
)


# ============================================================
# LAZY INITIALIZATION - NÃO inicializa no import!
# ============================================================
_client = None

def get_client():
    """Inicializa cliente LLM apenas quando necessário."""
    global _client
    
    if IS_TEST_MODE:
        return None
    
    if _client is None:
        if LLM_PROVIDER == "groq":
            from groq import Groq
            _client = Groq()
        elif LLM_PROVIDER == "openai":
            from openai import OpenAI
            _client = OpenAI()
        else:
            _client = None  # modo offline
    
    return _client

def generate_answer(question: str, system_prompt: str = "") -> str:
    """
    Gera resposta do LLM.
    - Em MODO TESTE: retorna resposta MOCK e nunca chama API externa.
    - Em modo normal: usa Groq / OpenAI.
    """

    # ============================================================
    # MODO TESTE → NÃO CHAMA API EXTERNA!
    # ============================================================
    if IS_TEST_MODE:
        return f"[RESPOSTA MOCK] {question}"

    # ============================================================
    # Obtém cliente (lazy)
    # ============================================================
    client = get_client()
    
    # ============================================================
    # MODO OFFLINE
    # ============================================================
    if client is None:
        return "Agente executando em modo offline."

    # ============================================================
    # MODO GROQ
    # ============================================================
    if LLM_PROVIDER == "groq":
        try:
            response = client.chat.completions.create(
                model=ACTIVE_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Invalid API Key" in error_msg:
                return f"⚠️ **Modo de demonstração ativo** (API key inválida)\n\nSua pergunta: *{question}*\n\nO TR4CTION Agent te ajudaria com:\n- Definição de ICP (Ideal Customer Profile)\n- Criação de Personas detalhadas\n- Análise SWOT da sua startup\n- Estratégias de marketing e go-to-market\n\n💡 Configure uma chave GROQ_API_KEY válida no arquivo .env para ativar o modo completo."
            raise

    # ============================================================
    # MODO OPENAI
    # ============================================================
    if LLM_PROVIDER == "openai":
        response = client.chat.completions.create(
            model=ACTIVE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ]
        )
        return response.choices[0].message.content

    raise RuntimeError("Nenhum provider válido configurado.")
    # Segurança: se cair aqui algo está errado