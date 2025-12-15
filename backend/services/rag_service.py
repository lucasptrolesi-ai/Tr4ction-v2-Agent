# backend/services/rag_service.py
"""
RAG Service - Retrieval-Augmented Generation com Governança FCJ
Integra busca semântica filtrada por contexto do founder com geração controlada
"""

import os
from typing import List, Dict, Optional
from services.llm_client import generate_answer

# Detecção de modo de teste
IS_TEST_MODE = (
    os.getenv("PYTEST_CURRENT_TEST") is not None or
    os.getenv("TESTING") == "1"
)


def retrieve_context(
    question: str, 
    n_results: int = 5,
    trail_id: Optional[str] = None,
    step_id: Optional[str] = None
) -> List[Dict]:
    """
    Busca contexto relevante na base de conhecimento COM FILTROS.
    
    Args:
        question: Pergunta do usuário
        n_results: Número máximo de chunks a retornar
        trail_id: Filtrar por trilha do founder
        step_id: Filtrar por etapa atual do founder
        
    Returns:
        Lista de chunks com id, text, metadata e similarity
    """
    if IS_TEST_MODE:
        return [{"id": "test", "text": "conteudo_mockado", "metadata": {}, "similarity": 0.9}]

    try:
        from services.knowledge_service import search_knowledge
        
        results = search_knowledge(
            query=question,
            n_results=n_results,
            min_similarity=0.25,
            trail_id=trail_id,
            step_id=step_id
        )
        
        return results
        
    except Exception as e:
        print(f"[RAG] Erro ao buscar contexto: {e}")
        return []


def build_context_prompt(chunks: List[Dict]) -> str:
    """
    Constrói o prompt de contexto para o LLM a partir dos chunks recuperados.
    Inclui rastreabilidade completa (fonte, trilha, etapa).
    
    Args:
        chunks: Lista de chunks da busca semântica
        
    Returns:
        String formatada com o contexto para o LLM
    """
    if not chunks:
        return ""
    
    context_parts = []
    
    for i, chunk in enumerate(chunks, 1):
        text = chunk.get("text", "")
        metadata = chunk.get("metadata", {})
        filename = metadata.get("filename", "Material FCJ")
        origin = metadata.get("origin_type", "").upper().replace(".", "")
        trail = metadata.get("trail_id", "")
        step = metadata.get("step_id", "")
        similarity = chunk.get("similarity", 0)
        
        # Monta source com rastreabilidade
        source_info = filename
        if origin:
            source_info += f" ({origin})"
        if trail and trail != "geral":
            source_info += f" - Trilha: {trail}"
        if step and step != "geral":
            source_info += f" - Etapa: {step}"
        
        chunk_str = f"[Fonte {i}: {source_info} | Relevância: {similarity:.0%}]\n{text}"
        context_parts.append(chunk_str)
    
    return "\n\n---\n\n".join(context_parts)


def get_rag_system_prompt(context: str, has_context: bool = True) -> str:
    """
    Gera o system prompt completo para RAG com LINGUAGEM INSTITUCIONAL FCJ.
    
    Args:
        context: Contexto recuperado da base de conhecimento
        has_context: Se há contexto disponível
        
    Returns:
        System prompt formatado com tom FCJ
    """
    base_prompt = """Você é o Assistente Virtual da FCJ Venture Builder, especializado em apoiar founders no programa de aceleração TR4CTION.

## IDENTIDADE
- Você representa a FCJ Consultoria e Venture Builder
- Sua função é orientar founders com base nos materiais oficiais do programa
- Mantenha sempre um tom profissional, acolhedor e motivador

## CONHECIMENTO
Você tem acesso aos materiais oficiais da FCJ, incluindo:
- Metodologias de validação de startups
- Definições de ICP (Ideal Customer Profile)
- Frameworks de Persona
- Análises SWOT
- Processos de aceleração TR4CTION
- Guias e apresentações das trilhas

## DIRETRIZES DE RESPOSTA

1. **Sempre cite a fonte**: Quando usar informações do contexto, mencione de onde veio
   - Exemplo: "De acordo com os materiais da FCJ sobre ICP..."
   - Exemplo: "Conforme a metodologia TR4CTION..."

2. **Seja específico**: Use exemplos práticos dos materiais quando possível

3. **Limitação explícita**: Se a pergunta não puder ser respondida com o contexto:
   - Diga claramente: "Não encontrei essa informação específica nos materiais da FCJ"
   - Ofereça orientação geral apenas se for seguro

4. **Foco no founder**: Sempre direcione a resposta para ajudar o founder no processo de aceleração

5. **Linguagem**: Use português brasileiro, profissional mas acessível"""
    
    if context and has_context:
        return f"""{base_prompt}

=== MATERIAIS OFICIAIS DA FCJ (CONTEXTO RECUPERADO) ===

{context}

=== FIM DOS MATERIAIS ===

INSTRUÇÃO: Responda à pergunta do founder usando PREFERENCIALMENTE as informações acima. 
Cite a fonte quando usar informações dos materiais. 
Se a resposta não estiver no contexto, indique que é uma orientação geral."""
    
    return f"""{base_prompt}

ATENÇÃO: Não foram encontrados materiais específicos da FCJ para esta pergunta.
Você pode fornecer orientação geral sobre startups e aceleração, mas deixe claro que:
- Não é informação oficial dos materiais TR4CTION
- O founder deve consultar a equipe FCJ para confirmação"""


def answer_with_rag(
    question: str, 
    max_context_chunks: int = 3,
    trail_id: Optional[str] = None,
    step_id: Optional[str] = None
) -> str:
    """
    Responde uma pergunta usando RAG com GOVERNANÇA.
    
    Pipeline:
    1. Busca chunks relevantes FILTRADOS por trilha/etapa do founder
    2. Constrói prompt com contexto e rastreabilidade
    3. Gera resposta via LLM com linguagem FCJ
    
    Args:
        question: Pergunta do usuário
        max_context_chunks: Máximo de chunks de contexto
        trail_id: Trilha atual do founder (para filtrar)
        step_id: Etapa atual do founder (para filtrar)
        
    Returns:
        Resposta gerada pelo LLM
    """
    import time
    start_time = time.time()
    
    # 1. Recupera contexto FILTRADO
    context_chunks = retrieve_context(
        question, 
        n_results=max_context_chunks,
        trail_id=trail_id,
        step_id=step_id
    )
    
    # 2. Constrói prompt de contexto
    context_str = build_context_prompt(context_chunks)
    
    # 3. Gera system prompt completo com tom FCJ
    has_context = len(context_chunks) > 0
    system_prompt = get_rag_system_prompt(context_str, has_context)
    
    # 4. Gera resposta
    response = generate_answer(question, system_prompt)
    
    # 5. Registra métricas
    elapsed_ms = int((time.time() - start_time) * 1000)
    _record_metrics(
        question=question,
        context_chunks=context_chunks,
        response_time_ms=elapsed_ms,
        trail_id=trail_id,
        step_id=step_id
    )
    
    return response


def _record_metrics(
    question: str,
    context_chunks: List[Dict],
    response_time_ms: int,
    trail_id: Optional[str] = None,
    step_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Registra métricas de uso do RAG"""
    if IS_TEST_MODE:
        return
    
    try:
        from services.rag_metrics import record_rag_query
        
        # Calcula similaridade média
        similarities = [c.get("similarity", 0) for c in context_chunks]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        # Extrai fontes usadas
        sources = [
            c.get("metadata", {}).get("filename", "unknown")
            for c in context_chunks
        ]
        
        record_rag_query(
            question=question,
            chunks_retrieved=len(context_chunks),
            avg_similarity=avg_similarity,
            response_time_ms=response_time_ms,
            trail_id=trail_id,
            step_id=step_id,
            user_id=user_id,
            sources=sources
        )
    except Exception as e:
        # Não falha se métricas falharem
        print(f"⚠️ Erro ao registrar métricas: {e}")


def answer_with_context(
    question: str, 
    additional_context: Optional[str] = None,
    trail_id: Optional[str] = None,
    step_id: Optional[str] = None
) -> str:
    """
    Versão estendida que permite adicionar contexto extra (ex: dados do founder).
    
    Args:
        question: Pergunta do usuário
        additional_context: Contexto adicional (dados do formulário, etc.)
        trail_id: Trilha do founder
        step_id: Etapa do founder
        
    Returns:
        Resposta gerada
    """
    import time
    start_time = time.time()
    
    # Recupera contexto da KB filtrado
    context_chunks = retrieve_context(
        question, 
        n_results=3,
        trail_id=trail_id,
        step_id=step_id
    )
    kb_context = build_context_prompt(context_chunks)
    
    # Combina contextos
    full_context = kb_context
    if additional_context:
        full_context = f"{kb_context}\n\n=== DADOS DA STARTUP DO FOUNDER ===\n{additional_context}"
    
    has_context = len(context_chunks) > 0 or bool(additional_context)
    system_prompt = get_rag_system_prompt(full_context, has_context)
    
    response = generate_answer(question, system_prompt)
    
    # Registra métricas
    elapsed_ms = int((time.time() - start_time) * 1000)
    _record_metrics(
        question=question,
        context_chunks=context_chunks,
        response_time_ms=elapsed_ms,
        trail_id=trail_id,
        step_id=step_id
    )
    
    return response
