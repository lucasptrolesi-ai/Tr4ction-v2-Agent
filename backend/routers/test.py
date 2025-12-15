# backend/routers/test.py

from fastapi import APIRouter
from core.models import SuccessResponse
from services.llm_client import generate_answer

router = APIRouter(prefix="/test")


@router.get("/ping", response_model=SuccessResponse)
async def ping():
    return SuccessResponse(data="ok")


@router.get("/llm", response_model=SuccessResponse)
async def test_llm():
    answer = generate_answer("Responda apenas 'ok'.")
    return SuccessResponse(data={"llm_response": answer})
