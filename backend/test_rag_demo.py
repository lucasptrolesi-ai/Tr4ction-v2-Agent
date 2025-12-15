# backend/test_rag_demo.py
"""
Demonstração do Pipeline RAG completo
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.knowledge_service import (
    index_document, 
    search_knowledge, 
    get_knowledge_stats, 
    get_context_for_query
)

def main():
    print("=" * 60)
    print("🚀 DEMONSTRAÇÃO DO PIPELINE RAG - TR4CTION")
    print("=" * 60)
    
    # 1. Indexa documento de exemplo
    print("\n📄 Indexando documento de exemplo...")
    result = index_document('data/sample_knowledge.txt', 'tr4ction_programa.txt')
    
    print(f"   Documento: {result.filename}")
    print(f"   Sucesso: {result.success}")
    print(f"   Chunks criados: {result.chunks_indexed}")
    print(f"   Tempo: {result.processing_time_ms}ms")
    
    if not result.success:
        print(f"   ❌ Erro: {result.error_message}")
        return
    
    # 2. Testa buscas semânticas
    print("\n🔍 Testando buscas semânticas...")
    
    queries = [
        "quanto custa o investimento da TR4CTION?",
        "quais setores são aceitos no programa?",
        "como funciona o processo de seleção?",
        "o que é a fase de validação?"
    ]
    
    for query in queries:
        print(f"\n   Query: '{query}'")
        results = search_knowledge(query, n_results=2)
        
        if results:
            for i, r in enumerate(results, 1):
                sim = r.get("similarity", 0)
                text = r.get("text", "")[:80]
                print(f"   {i}. [{sim:.0%}] {text}...")
        else:
            print("   Nenhum resultado encontrado")
    
    # 3. Mostra contexto para RAG
    print("\n📚 Contexto gerado para LLM:")
    print("-" * 40)
    context = get_context_for_query("Qual o valor do investimento?", max_chunks=2)
    print(context[:500] + "..." if len(context) > 500 else context)
    print("-" * 40)
    
    # 4. Stats finais
    print("\n📊 Estatísticas da Base de Conhecimento:")
    stats = get_knowledge_stats()
    print(f"   Total documentos: {stats['total_documents']}")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Formatos suportados: {', '.join(stats['supported_formats'])}")
    print(f"   Dimensão embedding: {stats['embedding_dimension']}")
    
    print("\n" + "=" * 60)
    print("✅ DEMONSTRAÇÃO CONCLUÍDA!")
    print("=" * 60)


if __name__ == "__main__":
    main()
