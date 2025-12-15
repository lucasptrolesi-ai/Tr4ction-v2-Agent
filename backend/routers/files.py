from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from usecases.files_usecase import save_uploaded_file, ask_about_file
from core.models import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/files")


class FileQuery(BaseModel):
    question: str
    filename: str


@router.post("/upload", response_model=SuccessResponse)
async def upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        data = save_uploaded_file(file.filename, content)
        return SuccessResponse(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/ask",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}},
)
async def ask_file(payload: FileQuery):
    try:
        data = ask_about_file(payload.filename, payload.question)
        return SuccessResponse(data=data)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
