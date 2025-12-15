from fastapi import APIRouter
from core.models import SuccessResponse
from config import LLM_PROVIDER, ACTIVE_MODEL, KNOWLEDGE_DIR, UPLOADS_DIR, CHROMA_DB_DIR
import os
import time

router = APIRouter(prefix="/diagnostics")


def check_dir(path):
    return {
        "path": path,
        "exists": os.path.exists(path),
        "writable": os.access(path, os.W_OK),
    }


@router.get("/status", response_model=SuccessResponse)
async def status():
    """
    Endpoint exigido pelos testes.
    """
    diagnostics = {
        "status": "operational",
        "provider": LLM_PROVIDER,
        "model": ACTIVE_MODEL,
        "directories": {
            "knowledge_dir": check_dir(KNOWLEDGE_DIR),
            "uploads_dir": check_dir(UPLOADS_DIR),
            "chroma_db_dir": check_dir(CHROMA_DB_DIR),
        },
    }

    return SuccessResponse(data=diagnostics)


@router.get("/embedding", response_model=SuccessResponse)
async def test_embedding():
    """
    Testa o serviço de embedding.
    Verifica se Hugging Face API está funcionando.
    """
    try:
        from services.embedding_service import test_embedding_service, get_model_info
        
        info = get_model_info()
        test_result = test_embedding_service()
        
        return SuccessResponse(data={
            "config": info,
            "test": test_result
        })
    except Exception as e:
        return SuccessResponse(data={
            "error": str(e),
            "success": False
        })
