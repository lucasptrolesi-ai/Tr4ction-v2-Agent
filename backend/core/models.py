from pydantic import BaseModel
from typing import Any, Optional


class ErrorResponse(BaseModel):
    status: str = "error"
    detail: str
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    status: str = "success"
    data: Any
