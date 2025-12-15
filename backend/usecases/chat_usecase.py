# backend/usecases/chat_usecase.py

from typing import Optional
from services.rag_service import answer_with_rag

def handle_chat_question(
    question: str, 
    trail_id: Optional[str] = None,
    step_id: Optional[str] = None
) -> dict:
    """
    Aplica validação e delega para o RAG com filtros de contexto.
    
    Args:
        question: Pergunta do founder
        trail_id: Trilha atual do founder (para filtrar materiais)
        step_id: Etapa atual do founder (para filtrar materiais)
        
    Returns:
        Dicionário com a resposta
    """
    if not question or len(question.strip()) < 2:
        raise ValueError("Pergunta inválida.")

    answer = answer_with_rag(
        question, 
        trail_id=trail_id, 
        step_id=step_id
    )
    return {"answer": answer}
