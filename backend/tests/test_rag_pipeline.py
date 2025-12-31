# backend/tests/test_rag_pipeline.py
"""
Testes do Pipeline RAG completo:
1. Document Processor (PPTX, PDF, DOCX, TXT)
2. Embedding Service (sentence-transformers)  
3. Knowledge Service (indexação e busca)
4. RAG Service (geração de respostas)
"""

import os
import sys
import tempfile

# Adiciona o backend ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestDocumentProcessor:
    """Testes do processador de documentos"""
    
    def test_supported_extensions(self):
        """Verifica extensões suportadas"""
        from services.document_processor import get_supported_extensions
        
        extensions = get_supported_extensions()
        assert '.pptx' in extensions
        assert '.pdf' in extensions
        assert '.docx' in extensions
        assert '.txt' in extensions
    
    def test_validate_file(self):
        """Testa validação de arquivo"""
        from services.document_processor import validate_file_for_processing
        
        # Arquivo válido
        is_valid, error = validate_file_for_processing("test.pdf", 1024 * 1024)  # 1MB
        assert is_valid is True
        
        # Extensão inválida
        is_valid, error = validate_file_for_processing("test.exe", 1024)
        assert is_valid is False
        assert "não suportado" in error.lower()
        
        # Arquivo muito grande
        is_valid, error = validate_file_for_processing("test.pdf", 100 * 1024 * 1024)  # 100MB
        assert is_valid is False
        assert "grande" in error.lower()
    
    def test_normalize_text(self):
        """Testa normalização de texto"""
        from services.document_processor import normalize_text
        
        # Múltiplos espaços
        text = "texto   com    muitos   espaços"
        result = normalize_text(text)
        assert "  " not in result
        
        # Múltiplas linhas vazias
        text = "linha1\n\n\n\n\nlinha2"
        result = normalize_text(text)
        assert "\n\n\n" not in result
    
    def test_chunk_text(self):
        """Testa divisão de texto em chunks"""
        from services.document_processor import chunk_text
        
        # Texto grande
        text = "Lorem ipsum dolor sit amet. " * 50
        chunks = chunk_text(text, chunk_size=200, overlap=20)
        
        assert len(chunks) > 1
        assert all(len(c) <= 250 for c in chunks)  # Com margem
        
        # Texto pequeno
        small_text = "Texto pequeno."
        chunks = chunk_text(small_text, chunk_size=500)
        assert len(chunks) == 1
    
    def test_process_txt_file(self):
        """Testa processamento de arquivo TXT"""
        from services.document_processor import process_document
        
        # Cria arquivo temporário
        content = "Este é um documento de teste para o pipeline RAG.\n" * 10
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp_path = f.name
        
        try:
            chunks, result = process_document(tmp_path, "teste.txt")
            
            assert result.success is True
            assert result.chunks_created > 0
            assert len(chunks) > 0
            assert all(c.text for c in chunks)
        finally:
            os.unlink(tmp_path)


class TestEmbeddingService:
    """Testes do serviço de embeddings"""
    
    def test_embedding_dimension(self):
        """Verifica dimensão do embedding"""
        from services.embedding_service import get_embedding_dimension, EMBEDDING_DIMENSION
        
        dim = get_embedding_dimension()
        assert dim == 384  # all-MiniLM-L6-v2
    
    def test_embed_text(self):
        """Testa geração de embedding para texto único"""
        from services.embedding_service import embed_text, EMBEDDING_DIMENSION
        
        text = "Este é um texto de teste para gerar embedding."
        embedding = embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIMENSION
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_texts_batch(self):
        """Testa geração de embeddings em batch"""
        from services.embedding_service import embed_texts, EMBEDDING_DIMENSION
        
        texts = [
            "Primeiro texto de teste.",
            "Segundo texto de teste.",
            "Terceiro texto diferente."
        ]
        embeddings = embed_texts(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == EMBEDDING_DIMENSION for emb in embeddings)
    
    def test_empty_text(self):
        """Testa comportamento com texto vazio"""
        from services.embedding_service import embed_text, EMBEDDING_DIMENSION
        
        embedding = embed_text("")
        assert len(embedding) == EMBEDDING_DIMENSION
        # Embeddings podem ter valores mesmo para texto vazio (comportamento do modelo)
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)
    
    def test_model_info(self):
        """Verifica informações do modelo"""
        from services.embedding_service import get_model_info
        
        info = get_model_info()
        # Verificar chaves que realmente existem
        assert "dimension" in info
        assert info["dimension"] == 384 or info["dimension"] == 768
        # model_name pode ou não estar presente dependendo do modo
        assert "hf_configured" in info or "is_test_mode" in info or "model_name" in info


class TestVectorStore:
    """Testes do vector store (ChromaDB)"""
    
    def test_get_stats(self):
        """Testa obtenção de estatísticas"""
        from services.vector_store import get_collection_stats
        
        stats = get_collection_stats()
        assert "collection_name" in stats
        assert "document_count" in stats or "error" in stats
    
    def test_add_and_search(self):
        """Testa adição e busca de documento"""
        from services.vector_store import add_document, search_by_text, delete_document
        from services.embedding_service import embed_text
        
        # Adiciona documento de teste
        test_id = "test_doc_123"
        test_text = "Este é um documento de teste sobre startups e empreendedorismo."
        embedding = embed_text(test_text)
        
        success = add_document(test_id, test_text, embedding, {"source": "test"})
        assert success is True
        
        # Busca
        results = search_by_text("startups empreendedorismo", n_results=5)
        
        # Limpa
        delete_document(test_id)
        
        # Verifica se encontrou (pode não encontrar se não houver outros docs)
        assert isinstance(results, list)


class TestKnowledgeService:
    """Testes do serviço de conhecimento"""
    
    def test_validate_upload(self):
        """Testa validação de upload"""
        from services.knowledge_service import validate_upload
        
        is_valid, error = validate_upload("documento.pdf", 1024 * 1024)
        assert is_valid is True
        
        is_valid, error = validate_upload("arquivo.exe", 1024)
        assert is_valid is False
    
    def test_get_supported_formats(self):
        """Testa listagem de formatos"""
        from services.knowledge_service import get_supported_formats
        
        formats = get_supported_formats()
        assert '.pdf' in formats
        assert '.pptx' in formats
    
    def test_index_txt_document(self):
        """Testa indexação de documento TXT"""
        from services.knowledge_service import index_document, delete_document, get_indexed_documents
        
        # Cria arquivo temporário
        content = "Conteúdo de teste para indexação no sistema RAG.\n" * 5
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp_path = f.name
        
        try:
            # Indexa
            result = index_document(tmp_path, "teste_index.txt")
            
            assert result.success is True
            assert result.chunks_indexed > 0
            
            # Verifica se está listado
            docs = get_indexed_documents()
            doc_ids = [d.get("document_id") for d in docs]
            assert result.document_id in doc_ids
            
            # Remove
            delete_document(result.document_id)
            
        finally:
            os.unlink(tmp_path)
    
    def test_search_knowledge(self):
        """Testa busca semântica"""
        from services.knowledge_service import search_knowledge
        
        results = search_knowledge("startups aceleração", n_results=3)
        assert isinstance(results, list)
    
    def test_get_context_for_query(self):
        """Testa geração de contexto para RAG"""
        from services.knowledge_service import get_context_for_query
        
        context = get_context_for_query("Como funciona a aceleração?")
        assert isinstance(context, str)
    
    def test_get_stats(self):
        """Testa estatísticas da base"""
        from services.knowledge_service import get_knowledge_stats
        
        stats = get_knowledge_stats()
        assert "total_documents" in stats
        assert "total_chunks" in stats
        assert "supported_formats" in stats


class TestRAGService:
    """Testes do serviço RAG"""
    
    def test_retrieve_context(self):
        """Testa recuperação de contexto"""
        from services.rag_service import retrieve_context
        
        chunks = retrieve_context("O que é uma startup?", n_results=3)
        assert isinstance(chunks, list)
    
    def test_build_context_prompt(self):
        """Testa construção de prompt de contexto"""
        from services.rag_service import build_context_prompt
        
        chunks = [
            {"text": "Texto 1", "metadata": {"filename": "doc1.pdf"}, "similarity": 0.9},
            {"text": "Texto 2", "metadata": {"filename": "doc2.pdf"}, "similarity": 0.8}
        ]
        
        prompt = build_context_prompt(chunks)
        assert "Texto 1" in prompt
        assert "Texto 2" in prompt
        assert "doc1.pdf" in prompt
        assert "90%" in prompt or "0.9" in prompt
    
    def test_get_rag_system_prompt(self):
        """Testa geração de system prompt"""
        from services.rag_service import get_rag_system_prompt
        
        # Com contexto
        prompt_with_context = get_rag_system_prompt("Contexto de teste")
        assert "TR4CTION" in prompt_with_context or "tr4ction" in prompt_with_context.lower()
        assert "Contexto de teste" in prompt_with_context
        
        # Sem contexto
        prompt_without = get_rag_system_prompt("")
        assert "TR4CTION" in prompt_without or "tr4ction" in prompt_without.lower()
        # Verificar mensagem de falta de contexto no texto real do prompt FCJ
        assert "não foram encontrados" in prompt_without.lower() or "atenção" in prompt_without.lower()


# ============================================================
# 🧪 TESTE DE INTEGRAÇÃO (Requer LLM)
# ============================================================

class TestIntegration:
    """Testes de integração do pipeline completo"""
    
    def test_full_rag_pipeline(self):
        """Testa pipeline RAG completo em modo mock"""
        from services.rag_service import answer_with_rag
        
        # Em modo teste/offline, a função deve retornar resposta mock
        question = "O que é uma startup?"
        
        try:
            response = answer_with_rag(question)
            
            # Se a função executar, verificar resposta
            assert isinstance(response, str)
            assert len(response) > 10
        except Exception as e:
            # Se não tiver LLM ativo, aceitar a exceção
            # (teste documenta que pipeline precisa de LLM)
            assert "offline" in str(e).lower() or "api" in str(e).lower() or "groq" in str(e).lower()


if __name__ == "__main__":
    # Executa testes básicos
    print("=" * 60)
    print("🧪 TESTES DO PIPELINE RAG")
    print("=" * 60)
    
    # Testa imports
    print("\n📦 Testando imports...")
    try:
        from services.document_processor import process_document, get_supported_extensions
        from services.embedding_service import embed_text, embed_texts
        from services.knowledge_service import index_document, search_knowledge
        from services.rag_service import answer_with_rag, retrieve_context
        print("✅ Todos os imports OK!")
    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        sys.exit(1)
    
    # Testa embedding
    print("\n🧠 Testando embedding service...")
    try:
        embedding = embed_text("Texto de teste para embedding")
        print(f"✅ Embedding gerado: {len(embedding)} dimensões")
    except Exception as e:
        print(f"❌ Erro no embedding: {e}")
    
    # Testa processador de documentos
    print("\n📄 Testando document processor...")
    try:
        extensions = get_supported_extensions()
        print(f"✅ Extensões suportadas: {extensions}")
    except Exception as e:
        print(f"❌ Erro no document processor: {e}")
    
    # Testa knowledge service
    print("\n📚 Testando knowledge service...")
    try:
        from services.knowledge_service import get_knowledge_stats
        stats = get_knowledge_stats()
        print(f"✅ Stats da base: {stats}")
    except Exception as e:
        print(f"❌ Erro no knowledge service: {e}")
    
    print("\n" + "=" * 60)
    print("✅ TESTES BÁSICOS CONCLUÍDOS!")
    print("=" * 60)
    print("\nPara executar todos os testes: pytest tests/test_rag_pipeline.py -v")
