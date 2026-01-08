# backend/main.py
from core.logging_config import setup_logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import APP_NAME, APP_VERSION, DEBUG_MODE
from core.middleware import logging_middleware
from core.models import ErrorResponse
from core.security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    get_cors_origins,
    rate_limiter
)

# Importa corretamente os routers expostos em routers/__init__.py
from routers import (
    chat_router,
    admin_router,
    diagnostics_router,
    files_router,
    test_router,
    founder_router,
    auth_router,
    template_discovery_router,
)

# Database
from db.database import init_db
from services.auth import seed_default_users
from db.database import SessionLocal


def create_app():
    setup_logging()
    
    # Inicializa o banco de dados (cria tabelas)
    init_db()

    # Desabilita documentação em produção
    docs_url = "/docs" if DEBUG_MODE else None
    redoc_url = "/redoc" if DEBUG_MODE else None

    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        debug=DEBUG_MODE,
        docs_url=docs_url,
        redoc_url=redoc_url,
    )

    # ======================================================
    # Middlewares de Segurança (ordem importa!)
    # ======================================================
    
    # 1. Security Headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 2. Rate Limiting
    app.add_middleware(
        RateLimitMiddleware,
        limiter=rate_limiter,
        exclude_paths=["/health", "/docs", "/openapi.json", "/redoc"]
    )
    
    # 3. Request Size Limit
    app.add_middleware(RequestSizeLimitMiddleware)
    
    # 4. CORS - Configurado via ENV com fallbacks
    cors_origins = get_cors_origins()
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"CORS allowed origins: {cors_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
        expose_headers=[
            "X-RateLimit-Limit", 
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset",
            "Content-Type",
            "X-Total-Count"
        ],
        max_age=3600,  # Preflight cache duration
    )

    app.middleware("http")(logging_middleware)

    # ======================================================
    # Tratador global de exceções
    # ======================================================
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Tratador global de exceções com proteção de sensitive data.
        
        Em development: Mostra detalhes completos para debugging
        Em production: Sanitiza erros para evitar information disclosure
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Log completo para análise interna
        logger.error(
            f"Unhandled exception at {request.url.path}: {str(exc)}", 
            exc_info=True,
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_host": request.client.host if request.client else None
            }
        )
        
        # Resposta sanitizada baseada no ambiente
        if DEBUG_MODE:
            # Development: Mostra detalhes para debugging
            detail = f"Error: {str(exc)}"
        else:
            # Production: Resposta genérica (evita information disclosure)
            detail = "An internal error occurred. Please contact support if the issue persists."
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=detail,
                code="INTERNAL_ERROR",
            ).dict(),
        )

    # ======================================================
    # Registro correto dos routers
    # ======================================================
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(admin_router)
    app.include_router(founder_router)
    app.include_router(files_router)
    app.include_router(diagnostics_router)
    app.include_router(test_router)
    app.include_router(template_discovery_router)  # Template discovery (generic)
    
    # Seed usuários padrão
    try:
        db = SessionLocal()
        seed_default_users(db)
        db.close()
    except Exception as e:
        print(f"Aviso: Não foi possível criar usuários padrão: {e}")

    # ======================================================
    # Health Check e Rota Raiz
    # ======================================================
    @app.get("/")
    async def root():
        return {
            "status": "ok",
            "message": "TR4CTION API rodando",
            "version": APP_VERSION,
            "docs": "/docs"
        }

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


# Instância final
app = create_app()


# Execução direta
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
