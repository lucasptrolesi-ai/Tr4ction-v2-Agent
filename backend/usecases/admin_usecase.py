# backend/usecases/admin_usecase.py

from typing import Dict, Any
from services.knowledge_service import list_documents, delete_document
from services.vector_store import reset_collection


def list_knowledge_docs() -> Dict[str, Any]:
    docs = list_documents()
    return {"documents": docs, "count": len(docs)}


def remove_knowledge_doc(doc_id: str) -> Dict[str, Any]:
    ok = delete_document(doc_id)
    if not ok:
        raise ValueError("Documento não encontrado.")
    return {"deleted": doc_id}


def reset_vector_db() -> Dict[str, Any]:
    reset_collection()
    return {"message": "Vector DB resetado com sucesso."}
