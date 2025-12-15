# backend/routers/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from usecases.chat_usecase import handle_chat_question
from core.models import SuccessResponse, ErrorResponse

# ============================================================
# Router
# ============================================================
router = APIRouter(
    prefix="/chat",
    tags=["Chat / RAG"]
)

# ============================================================
# Request model
# ============================================================
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    trail_id: Optional[str] = Field(None, description="ID da trilha atual do founder")
    step_id: Optional[str] = Field(None, description="ID da etapa atual do founder")

# ============================================================
# Endpoint principal
# ============================================================
@router.post(
    "/",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def chat_with_agent(payload: ChatRequest):
    """
    Endpoint principal de interação com RAG filtrado por contexto.
    
    O contexto do founder (trail_id, step_id) é usado para filtrar
    os materiais relevantes antes de gerar a resposta.
    """
    try:
        result = handle_chat_question(
            payload.question,
            trail_id=payload.trail_id,
            step_id=payload.step_id
        )
        return SuccessResponse(data=result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
