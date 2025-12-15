# backend/services/knowledge_service.py
"""
Knowledge Service - Orquestra o pipeline completo de RAG
Upload → Extração → Chunking → Embedding → Indexação
"""

import os
import shutil
import uuid
import json
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from services.document_processor import (
    process_document,
    validate_file_for_processing,
    get_supported_extensions,
    DocumentChunk,
    ProcessingResult
)
from services.embedding_service import embed_texts, embed_text, get_embedding_dimension
from services.vector_store import (
    add_documents_batch,
    search_similar,
    delete_by_metadata,
    get_collection_stats,
    list_all_documents
)

# Import para compatibilidade com código antigo
try:
    from config import KNOWLEDGE_DIR
except ImportError:
    KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge")


# ============================================================
# 📁 CONFIGURAÇÃO DE STORAGE
# ============================================================

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "knowledge")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

# Arquivo de índice de documentos
DOCUMENTS_INDEX_FILE = os.path.join(KNOWLEDGE_DIR, "_documents_index.json")


# ============================================================
# 📊 ESTRUTURAS DE DADOS
# ============================================================

@dataclass
class IndexingResult:
    """Resultado da indexação de um documento"""
    success: bool
    document_id: str
    filename: str
    chunks_indexed: int
    processing_time_ms: int
    trail_id: Optional[str] = None
    step_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class KnowledgeDocument:
    """Representa um documento na base de conhecimento - Metadata corporativa FCJ"""
    document_id: str
    filename: str
    file_type: str
    chunks_count: int
    indexed_at: str
    file_path: str
    # Metadata corporativa obrigatória
    trail_id: Optional[str] = None      # Trilha associada (ex: Q1_Marketing)
    step_id: Optional[str] = None       # Etapa específica (ICP, Persona) ou "geral"
    uploaded_by: Optional[str] = None   # Admin que fez upload
    version: str = "1.0"               # Versão do documento
    description: Optional[str] = None   # Descrição opcional


# ============================================================
# 📝 REGISTRO DE DOCUMENTOS (persistente em JSON)
# ============================================================

def _load_documents_index() -> Dict[str, Dict]:
    """Carrega índice de documentos do disco"""
    if os.path.exists(DOCUMENTS_INDEX_FILE):
        try:
            with open(DOCUMENTS_INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_documents_index(index: Dict[str, Dict]):
    """Salva índice de documentos no disco"""
    try:
        with open(DOCUMENTS_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erro ao salvar índice: {e}")


def _register_document(doc: KnowledgeDocument):
    """Registra documento indexado"""
    index = _load_documents_index()
    index[doc.document_id] = asdict(doc)
    _save_documents_index(index)


def _unregister_document(document_id: str):
    """Remove registro de documento"""
    index = _load_documents_index()
    if document_id in index:
        del index[document_id]
        _save_documents_index(index)


def get_indexed_documents() -> List[Dict]:
    """Retorna lista de documentos indexados"""
    index = _load_documents_index()
    return list(index.values())


# ============================================================
# 🚀 PIPELINE PRINCIPAL
# ============================================================

def index_document(
    file_path: str,
    filename: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    # Metadata corporativa FCJ
    trail_id: Optional[str] = None,
    step_id: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    version: str = "1.0",
    description: Optional[str] = None
) -> IndexingResult:
    """
    Pipeline completo para indexar um documento com governança corporativa.
    
    1. Processa documento (extrai texto, normaliza, chunka)
    2. Adiciona metadata corporativa obrigatória
    3. Gera embeddings para cada chunk
    4. Indexa no ChromaDB com filtros por trilha/etapa
    
    Args:
        file_path: Caminho do arquivo temporário
        filename: Nome original do arquivo
        chunk_size: Tamanho dos chunks
        chunk_overlap: Sobreposição entre chunks
        trail_id: ID da trilha associada (ex: Q1_Marketing)
        step_id: ID da etapa (ICP, Persona) ou "geral"
        uploaded_by: Email/ID do admin que fez upload
        version: Versão do documento
        description: Descrição opcional
        
    Returns:
        IndexingResult com status da operação
    """
    start_time = datetime.now()
    
    # Normaliza IDs
    trail_id = trail_id or "geral"
    step_id = step_id or "geral"
    
    # 1. Processa documento
    chunks, processing_result = process_document(
        file_path=file_path,
        filename=filename,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    if not processing_result.success:
        return IndexingResult(
            success=False,
            document_id=processing_result.document_id,
            filename=filename,
            chunks_indexed=0,
            processing_time_ms=processing_result.processing_time_ms,
            error_message=processing_result.error_message
        )
    
    if not chunks:
        return IndexingResult(
            success=False,
            document_id=processing_result.document_id,
            filename=filename,
            chunks_indexed=0,
            processing_time_ms=processing_result.processing_time_ms,
            error_message="Nenhum chunk gerado - documento pode estar vazio"
        )
    
    # 2. Gera embeddings em batch
    texts = [chunk.text for chunk in chunks]
    embeddings = embed_texts(texts)
    
    # 3. Prepara dados para indexação com metadata corporativa
    doc_ids = [chunk.chunk_id for chunk in chunks]
    document_id = processing_result.document_id
    
    # Enriquece metadata de cada chunk com governança corporativa
    enriched_metadatas = []
    for chunk in chunks:
        enriched_meta = {
            **chunk.metadata,
            # Metadata corporativa obrigatória
            "document_id": document_id,
            "trail_id": trail_id,
            "step_id": step_id,
            "uploaded_by": uploaded_by or "admin",
            "version": version,
            "description": description or "",
            # Rastreabilidade
            "origin_type": processing_result.file_type,
            "chunk_index": chunk.chunk_index,
            "total_chunks": chunk.total_chunks,
            "indexed_at": datetime.utcnow().isoformat()
        }
        enriched_metadatas.append(enriched_meta)
    
    # 4. Indexa no ChromaDB
    indexed_count = add_documents_batch(
        doc_ids=doc_ids,
        texts=texts,
        embeddings=embeddings,
        metadatas=enriched_metadatas
    )
    
    # 5. Move arquivo para storage permanente
    permanent_path = os.path.join(UPLOAD_DIR, f"{document_id}_{filename}")
    
    try:
        shutil.copy2(file_path, permanent_path)
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível salvar arquivo permanente: {e}")
        permanent_path = ""
    
    # 6. Registra documento com metadata corporativa
    _register_document(KnowledgeDocument(
        document_id=document_id,
        filename=filename,
        file_type=processing_result.file_type,
        chunks_count=indexed_count,
        indexed_at=datetime.utcnow().isoformat(),
        file_path=permanent_path,
        trail_id=trail_id,
        step_id=step_id,
        uploaded_by=uploaded_by,
        version=version,
        description=description
    ))
    
    # Calcula tempo total
    total_time = int((datetime.now() - start_time).total_seconds() * 1000)
    
    return IndexingResult(
        success=indexed_count > 0,
        document_id=document_id,
        filename=filename,
        chunks_indexed=indexed_count,
        processing_time_ms=total_time,
        trail_id=trail_id,
        step_id=step_id
    )


# ============================================================
# 🔍 BUSCA SEMÂNTICA (RAG)
# ============================================================

def search_knowledge(
    query: str,
    n_results: int = 5,
    min_similarity: float = 0.3,
    # Filtros de contexto do founder
    trail_id: Optional[str] = None,
    step_id: Optional[str] = None
) -> List[Dict]:
    """
    Busca documentos relevantes para uma query COM GOVERNANÇA.
    Filtra por trilha/etapa do founder para retornar apenas conteúdo relevante.
    
    Args:
        query: Texto da pergunta/busca
        n_results: Número máximo de resultados
        min_similarity: Similaridade mínima (0-1)
        trail_id: Filtrar por trilha do founder (opcional)
        step_id: Filtrar por etapa atual (opcional)
        
    Returns:
        Lista de documentos relevantes com metadata
    """
    # Gera embedding da query
    query_embedding = embed_text(query)
    
    # Constrói filtro de metadata para ChromaDB
    where_filter = None
    if trail_id or step_id:
        conditions = []
        if trail_id and trail_id != "geral":
            # Busca na trilha específica OU em "geral"
            conditions.append({"$or": [{"trail_id": trail_id}, {"trail_id": "geral"}]})
        if step_id and step_id != "geral":
            # Busca na etapa específica OU em "geral"
            conditions.append({"$or": [{"step_id": step_id}, {"step_id": "geral"}]})
        
        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}
    
    # Busca no ChromaDB com filtro
    results = search_similar(query_embedding, n_results=n_results, where_filter=where_filter)
    
    # Filtra por similaridade mínima
    filtered = [r for r in results if r.get("similarity", 0) >= min_similarity]
    
    return filtered


def get_context_for_query(
    query: str,
    max_chunks: int = 3,
    max_context_length: int = 2000,
    trail_id: Optional[str] = None,
    step_id: Optional[str] = None
) -> str:
    """
    Monta contexto RAG para uma query COM GOVERNANÇA.
    Filtra por trilha/etapa do founder.
    
    Args:
        query: Pergunta do usuário
        max_chunks: Máximo de chunks a incluir
        max_context_length: Tamanho máximo do contexto
        trail_id: Trilha do founder para filtrar
        step_id: Etapa atual do founder para filtrar
        
    Returns:
        Texto formatado com contexto relevante
    """
    results = search_knowledge(
        query, 
        n_results=max_chunks,
        trail_id=trail_id,
        step_id=step_id
    )
    
    if not results:
        return ""
    
    context_parts = []
    total_length = 0
    
    for i, result in enumerate(results, 1):
        text = result.get("text", "")
        metadata = result.get("metadata", {})
        filename = metadata.get("filename", "Material FCJ")
        origin = metadata.get("origin_type", "").upper().replace(".", "")
        trail = metadata.get("trail_id", "")
        step = metadata.get("step_id", "")
        similarity = result.get("similarity", 0)
        
        # Header do chunk com rastreabilidade completa
        source_info = f"{filename}"
        if origin:
            source_info += f" ({origin})"
        if trail and trail != "geral":
            source_info += f" | Trilha: {trail}"
        if step and step != "geral":
            source_info += f" | Etapa: {step}"
        
        chunk_header = f"[Fonte: {source_info} | Relevância: {similarity:.0%}]"
        chunk_content = f"{chunk_header}\n{text}\n"
        
        # Verifica limite de tamanho
        if total_length + len(chunk_content) > max_context_length:
            break
            
        context_parts.append(chunk_content)
        total_length += len(chunk_content)
    
    if not context_parts:
        return ""
    
    return "---\n📚 MATERIAIS DA FCJ CONSULTORIA:\n\n" + "\n---\n".join(context_parts) + "\n---"


# ============================================================
# 🗑️ GERENCIAMENTO DE DOCUMENTOS
# ============================================================

def delete_document(doc_id: str) -> bool:
    """
    Remove documento da base de conhecimento.
    
    Args:
        doc_id: ID do documento a remover
        
    Returns:
        True se removido com sucesso
    """
    index = _load_documents_index()
    doc_data = index.get(doc_id)
    
    # Remove do ChromaDB
    delete_by_metadata({"document_id": doc_id})
    
    # Remove arquivo físico
    if doc_data and doc_data.get("file_path") and os.path.exists(doc_data["file_path"]):
        try:
            os.remove(doc_data["file_path"])
        except Exception:
            pass
    
    # Remove registro
    _unregister_document(doc_id)
    
    # Compatibilidade: remove JSON antigo se existir
    old_json_path = os.path.join(KNOWLEDGE_DIR, f"{doc_id}.json")
    if os.path.exists(old_json_path):
        try:
            os.remove(old_json_path)
        except Exception:
            pass
    
    return True


def get_knowledge_stats() -> Dict:
    """Retorna estatísticas da base de conhecimento"""
    chroma_stats = get_collection_stats()
    index = _load_documents_index()
    
    return {
        "total_documents": len(index),
        "total_chunks": chroma_stats.get("document_count", 0),
        "supported_formats": get_supported_extensions(),
        "embedding_dimension": get_embedding_dimension(),
        "storage": chroma_stats
    }


# ============================================================
# 🔧 UTILITÁRIOS E COMPATIBILIDADE
# ============================================================

def validate_upload(filename: str, file_size: int) -> Tuple[bool, str]:
    """Valida arquivo antes do upload"""
    return validate_file_for_processing(filename, file_size, max_size_mb=50)


def get_supported_formats() -> List[str]:
    """Retorna formatos suportados"""
    return get_supported_extensions()


# ============================================================
# 🔄 REINDEXAÇÃO E VERSIONAMENTO
# ============================================================

def reindex_document(document_id: str) -> IndexingResult:
    """
    Reindexa um documento existente.
    
    1. Busca metadata do documento
    2. Remove chunks antigos do ChromaDB
    3. Reprocessa o arquivo original
    4. Reindexa com os mesmos metadados
    
    Args:
        document_id: ID do documento a reindexar
        
    Returns:
        IndexingResult com status da operação
    """
    start_time = datetime.now()
    
    # 1. Busca documento no índice
    index = _load_documents_index()
    if document_id not in index:
        return IndexingResult(
            success=False,
            document_id=document_id,
            filename="",
            chunks_indexed=0,
            processing_time_ms=0,
            error_message="Documento não encontrado no índice"
        )
    
    doc_info = index[document_id]
    filename = doc_info.get("filename", "")
    file_path = doc_info.get("file_path", "")
    
    # 2. Verifica se arquivo existe
    if not file_path or not os.path.exists(file_path):
        # Tenta encontrar no diretório de uploads
        possible_path = os.path.join(UPLOAD_DIR, f"{document_id}_{filename}")
        if os.path.exists(possible_path):
            file_path = possible_path
        else:
            return IndexingResult(
                success=False,
                document_id=document_id,
                filename=filename,
                chunks_indexed=0,
                processing_time_ms=0,
                error_message=f"Arquivo original não encontrado: {file_path}"
            )
    
    # 3. Remove chunks antigos do ChromaDB
    try:
        delete_by_metadata("document_id", document_id)
    except Exception as e:
        print(f"⚠️ Erro ao remover chunks antigos: {e}")
    
    # 4. Reindexa com metadados preservados
    result = index_document(
        file_path=file_path,
        filename=filename,
        trail_id=doc_info.get("trail_id", "geral"),
        step_id=doc_info.get("step_id", "geral"),
        uploaded_by=doc_info.get("uploaded_by", "admin"),
        version=doc_info.get("version", "1.0"),
        description=doc_info.get("description", "")
    )
    
    # Atualiza tempo de processamento
    elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    result.processing_time_ms = elapsed_ms
    
    return result


def reindex_all_documents() -> Dict[str, Any]:
    """
    Reindexa todos os documentos da base de conhecimento.
    
    Returns:
        Dicionário com estatísticas da reindexação
    """
    start_time = datetime.now()
    
    index = _load_documents_index()
    total = len(index)
    success_count = 0
    error_count = 0
    errors = []
    
    for doc_id, doc_info in index.items():
        try:
            result = reindex_document(doc_id)
            if result.success:
                success_count += 1
            else:
                error_count += 1
                errors.append({
                    "document_id": doc_id,
                    "filename": doc_info.get("filename", ""),
                    "error": result.error_message
                })
        except Exception as e:
            error_count += 1
            errors.append({
                "document_id": doc_id,
                "filename": doc_info.get("filename", ""),
                "error": str(e)
            })
    
    elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    
    return {
        "total_documents": total,
        "success_count": success_count,
        "error_count": error_count,
        "errors": errors[:10],  # Limita a 10 erros
        "total_time_ms": elapsed_ms
    }


def update_document_version(
    document_id: str,
    new_version: str,
    description: Optional[str] = None
) -> bool:
    """
    Atualiza a versão de um documento.
    
    Args:
        document_id: ID do documento
        new_version: Nova versão (ex: "2.0")
        description: Nova descrição (opcional)
        
    Returns:
        True se atualizado com sucesso
    """
    index = _load_documents_index()
    
    if document_id not in index:
        return False
    
    index[document_id]["version"] = new_version
    index[document_id]["updated_at"] = datetime.utcnow().isoformat()
    
    if description is not None:
        index[document_id]["description"] = description
    
    _save_documents_index(index)
    return True


# ============================================================
# 🔄 FUNÇÕES DE COMPATIBILIDADE (API antiga)
# ============================================================

def _ensure_storage():
    """Garante que diretórios existem"""
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def list_documents() -> List[Dict[str, Any]]:
    """
    Lista os documentos armazenados na Knowledge Base.
    Compatível com API antiga + nova.
    """
    _ensure_storage()
    
    # Documentos indexados (novo sistema)
    indexed = get_indexed_documents()
    
    # Documentos JSON legados
    legacy_docs = []
    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.endswith(".json") and filename != "_documents_index.json":
            path = os.path.join(KNOWLEDGE_DIR, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["id"] = filename.replace(".json", "")
                    data["legacy"] = True
                    legacy_docs.append(data)
            except:
                continue
    
    return indexed + legacy_docs


def save_document(doc_id: str, content: Dict[str, Any]) -> None:
    """
    Salva um documento JSON com ID específico.
    Mantido para compatibilidade.
    """
    _ensure_storage()
    path = os.path.join(KNOWLEDGE_DIR, f"{doc_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)


def load_document(doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Carrega um documento pelo ID.
    """
    _ensure_storage()
    
    # Tenta carregar do índice novo
    index = _load_documents_index()
    if doc_id in index:
        return index[doc_id]
    
    # Tenta carregar JSON legado
    path = os.path.join(KNOWLEDGE_DIR, f"{doc_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return None

