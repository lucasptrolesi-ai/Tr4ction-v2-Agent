# backend/services/vector_store.py
"""
Vector Store - Gerenciamento de embeddings com ChromaDB
Suporta indexação e busca semântica para RAG
"""

import os
import chromadb
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime


# ============================================================
# 🔹 CONFIGURAÇÃO DO CHROMA
# ============================================================

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", "./chroma_data")

# Se True, usa persistência local em vez de HTTP client
USE_LOCAL_PERSISTENCE = os.getenv("CHROMA_LOCAL", "true").lower() == "true"

# ============================================================
# 🔹 LAZY INITIALIZATION
# ============================================================

_client = None
_collection = None

COLLECTION_NAME = "tr4ction_knowledge"


def get_client():
    """Inicializa cliente ChromaDB apenas quando necessário."""
    global _client
    if _client is None:
        try:
            if USE_LOCAL_PERSISTENCE:
                # Modo local com persistência em disco
                os.makedirs(CHROMA_PERSIST_PATH, exist_ok=True)
                _client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
                print(f"✅ [ChromaDB] Conectado (persistência local: {CHROMA_PERSIST_PATH})")
            else:
                # Modo Docker/HTTP
                _client = chromadb.HttpClient(
                    host=CHROMA_HOST,
                    port=CHROMA_PORT
                )
                _client.heartbeat()
                print(f"✅ [ChromaDB] Conectado via HTTP ({CHROMA_HOST}:{CHROMA_PORT})")
                
        except Exception as e:
            print(f"⚠️ [ChromaDB] Erro ao conectar: {e}")
            # Fallback para ephemeral (memória)
            _client = chromadb.Client()
            print("⚠️ [ChromaDB] Usando modo ephemeral (sem persistência)")
            
    return _client


def get_collection():
    """Retorna collection, criando se necessário."""
    global _collection
    if _collection is None:
        client = get_client()
        if client is None:
            print("⚠️ [ChromaDB] Cliente não disponível")
            return None
        try:
            _collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✅ [ChromaDB] Collection '{COLLECTION_NAME}' pronta")
        except Exception as e:
            print(f"⚠️ [ChromaDB] Erro ao criar collection: {e}")
            _collection = None
    return _collection


# ============================================================
# 🔹 ADICIONAR DOCUMENTOS
# ============================================================

def add_document(
    doc_id: str, 
    text: str, 
    embedding: List[float],
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Adiciona documento único ao ChromaDB.
    
    Args:
        doc_id: ID único do documento/chunk
        text: Texto do documento
        embedding: Vetor de embedding
        metadata: Metadados opcionais
    """
    collection = get_collection()
    if collection is None:
        print("⚠️ [ChromaDB] Collection não disponível")
        return False
    
    try:
        # Garante que metadata seja serializável
        if metadata:
            clean_metadata = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v 
                           for k, v in metadata.items()}
        else:
            clean_metadata = {}
        
        # Adiciona timestamp
        clean_metadata["indexed_at"] = datetime.utcnow().isoformat()
        
        collection.add(
            ids=[doc_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[clean_metadata]
        )
        return True
        
    except Exception as e:
        print(f"⚠️ [ChromaDB] Erro ao adicionar: {e}")
        return False


def add_documents_batch(
    doc_ids: List[str],
    texts: List[str],
    embeddings: List[List[float]],
    metadatas: Optional[List[Dict[str, Any]]] = None
) -> int:
    """
    Adiciona múltiplos documentos de uma vez (mais eficiente).
    
    Returns:
        Número de documentos adicionados com sucesso
    """
    collection = get_collection()
    if collection is None:
        return 0
    
    try:
        # Prepara metadatas
        if metadatas:
            clean_metadatas = []
            for meta in metadatas:
                clean_meta = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v 
                            for k, v in meta.items()}
                clean_meta["indexed_at"] = datetime.utcnow().isoformat()
                clean_metadatas.append(clean_meta)
        else:
            clean_metadatas = [{"indexed_at": datetime.utcnow().isoformat()} for _ in doc_ids]
        
        collection.add(
            ids=doc_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=clean_metadatas
        )
        return len(doc_ids)
        
    except Exception as e:
        print(f"⚠️ [ChromaDB] Erro ao adicionar batch: {e}")
        return 0


# ============================================================
# 🔹 BUSCAR DOCUMENTOS
# ============================================================

def search_similar(
    query_embedding: List[float], 
    n_results: int = 5,
    where_filter: Optional[Dict] = None
) -> List[Dict]:
    """
    Busca documentos similares ao embedding fornecido.
    
    Args:
        query_embedding: Embedding da query
        n_results: Número de resultados
        where_filter: Filtro opcional de metadados
        
    Returns:
        Lista de dicts com id, text, metadata, distance
    """
    collection = get_collection()
    if collection is None:
        return []
    
    try:
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"]
        }
        
        if where_filter:
            query_params["where"] = where_filter
        
        results = collection.query(**query_params)

        # Formata resultados
        formatted = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            formatted.append({
                "id": doc_id,
                "text": docs[i] if i < len(docs) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else 1.0,
                "similarity": 1 - (distances[i] if i < len(distances) else 1.0)
            })

        return formatted
        
    except Exception as e:
        print(f"⚠️ [ChromaDB] Erro ao buscar: {e}")
        return []


def search_by_text(
    query_text: str,
    n_results: int = 5
) -> List[Dict]:
    """
    Busca por texto gerando embedding automaticamente.
    
    Args:
        query_text: Texto da busca
        n_results: Número de resultados
        
    Returns:
        Lista de documentos similares
    """
    from services.embedding_service import embed_text
    
    query_embedding = embed_text(query_text)
    return search_similar(query_embedding, n_results)


# ============================================================
# 🔹 GERENCIAMENTO
# ============================================================

def delete_document(doc_id: str) -> bool:
    """Remove documento pelo ID."""
    collection = get_collection()
    if collection is None:
        return False
    
    try:
        collection.delete(ids=[doc_id])
        return True
    except Exception as e:
        print(f"⚠️ [ChromaDB] Erro ao deletar: {e}")
        return False


def delete_by_metadata(where_filter: Dict) -> int:
    """
    Remove documentos que correspondem ao filtro.
    
    Args:
        where_filter: Filtro de metadados (ex: {"document_id": "abc123"})
        
    Returns:
        Número estimado de documentos removidos
    """
    collection = get_collection()
    if collection is None:
        return 0
    
    try:
        # ChromaDB não retorna count de deletados, então só executa
        collection.delete(where=where_filter)
        return -1  # Indica que algo foi deletado mas não sabemos quantos
    except Exception as e:
        print(f"⚠️ [ChromaDB] Erro ao deletar por filtro: {e}")
        return 0


def get_collection_stats() -> Dict:
    """Retorna estatísticas da collection."""
    collection = get_collection()
    if collection is None:
        return {"error": "Collection não disponível"}
    
    try:
        count = collection.count()
        return {
            "collection_name": COLLECTION_NAME,
            "document_count": count,
            "storage_mode": "local" if USE_LOCAL_PERSISTENCE else "http",
            "storage_path": CHROMA_PERSIST_PATH if USE_LOCAL_PERSISTENCE else f"{CHROMA_HOST}:{CHROMA_PORT}"
        }
    except Exception as e:
        return {"error": str(e)}


def reset_collection():
    """Remove e recria a collection."""
    global _client, _collection
    
    client = get_client()
    if client is None:
        return False
        
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"🗑️ [ChromaDB] Collection '{COLLECTION_NAME}' deletada")
    except Exception:
        pass

    _collection = None
    get_collection()
    print(f"✅ [ChromaDB] Collection '{COLLECTION_NAME}' recriada")
    return True


def list_all_documents(limit: int = 100) -> List[Dict]:
    """Lista todos os documentos na collection (debug)."""
    collection = get_collection()
    if collection is None:
        return []
    
    try:
        results = collection.get(
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        formatted = []
        ids = results.get("ids", [])
        docs = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        
        for i, doc_id in enumerate(ids):
            formatted.append({
                "id": doc_id,
                "text": docs[i][:200] + "..." if len(docs[i]) > 200 else docs[i],
                "metadata": metadatas[i] if i < len(metadatas) else {}
            })
        
        return formatted
        
    except Exception as e:
        print(f"⚠️ [ChromaDB] Erro ao listar: {e}")
        return []


