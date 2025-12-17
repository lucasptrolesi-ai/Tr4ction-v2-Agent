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
)

# Database
from db.database import init_db
from services.auth import seed_default_users
from db.database import SessionLocal


def create_app():
    setup_logging()
    
    # Inicializa o banco de dados (cria tabelas)
    init_db()

    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        debug=DEBUG_MODE,
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
    print(f"✅ [CORS] Origens permitidas: {cors_origins}")
    
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
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=f"Erro interno: {str(exc)}",
                code="UNHANDLED_EXCEPTION",
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
        return {"status": "ok"}

    return app


# Instância final
app = create_app()


# Execução direta
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
