# backend/core/middleware.py

import time
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

from core.models import ErrorResponse

logger = logging.getLogger("tr4ction.middleware")


async def logging_middleware(request: Request, call_next):
    start = time.time()

    try:
        response = await call_next(request)
    except Exception as e:
        duration = round(time.time() - start, 4)
        logger.exception(
            "Unhandled error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "duration": duration,
                "error": str(e),
            },
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=f"Erro interno: {str(e)}",
                code="INTERNAL_SERVER_ERROR",
            ).dict(),
        )

    duration = round(time.time() - start, 4)
    logger.info(
        "Request handled",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "duration": duration,
        },
    )
    return response
