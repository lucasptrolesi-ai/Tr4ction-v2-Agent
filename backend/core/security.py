# backend/core/security.py
"""
Módulo de Segurança - Rate Limiting, CORS, Validações
"""

import os
import time
from collections import defaultdict
from typing import Dict, List, Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

# ======================================================
# Configurações via ENV
# ======================================================
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = os.getenv(
    "ALLOWED_EXTENSIONS", 
    ".pdf,.pptx,.docx,.txt,.xlsx"
).split(",")

def get_cors_origins() -> List[str]:
    """Retorna lista de origens CORS permitidas com fallbacks."""
    origins_str = os.getenv("CORS_ORIGINS", "")
    
    if not origins_str or origins_str == "*":
        # Em desenvolvimento: permite qualquer origem
        if os.getenv("ENVIRONMENT") == "development":
            return ["*"]
        # Em produção: lista padrão segura
        return [
            "https://tr4ction-v2-agent.vercel.app",
            "https://www.tr4ction-v2-agent.vercel.app",
            "https://54.144.92.71.sslip.io",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    
    # Parse customizado
    origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    return origins if origins else ["*"]


# ======================================================
# Rate Limiter em Memória
# ======================================================
class RateLimiter:
    """
    Rate limiter simples em memória.
    Para produção em escala, use Redis.
    """
    
    def __init__(self, requests: int = 100, window: int = 60):
        self.requests = requests
        self.window = window
        self.clients: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, client_id: str) -> bool:
        """Verifica se o cliente pode fazer a requisição."""
        async with self._lock:
            now = time.time()
            
            # Remove requisições antigas (fora da janela)
            self.clients[client_id] = [
                ts for ts in self.clients[client_id] 
                if now - ts < self.window
            ]
            
            # Verifica limite
            if len(self.clients[client_id]) >= self.requests:
                return False
            
            # Registra nova requisição
            self.clients[client_id].append(now)
            return True
    
    def get_remaining(self, client_id: str) -> int:
        """Retorna quantas requisições restam."""
        now = time.time()
        recent = [
            ts for ts in self.clients[client_id] 
            if now - ts < self.window
        ]
        return max(0, self.requests - len(recent))
    
    def get_reset_time(self, client_id: str) -> int:
        """Retorna segundos até reset do limite."""
        if not self.clients[client_id]:
            return 0
        oldest = min(self.clients[client_id])
        return max(0, int(self.window - (time.time() - oldest)))


# Instância global do rate limiter
rate_limiter = RateLimiter(
    requests=RATE_LIMIT_REQUESTS,
    window=RATE_LIMIT_WINDOW
)


# ======================================================
# Middleware de Rate Limiting
# ======================================================
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para aplicar rate limiting."""
    
    def __init__(self, app, limiter: RateLimiter = None, exclude_paths: List[str] = None):
        super().__init__(app)
        self.limiter = limiter or rate_limiter
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next):
        # Ignora paths excluídos
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)
        
        # Identifica cliente (IP ou user_id do token)
        client_id = self._get_client_id(request)
        
        # Verifica rate limit
        if not await self.limiter.is_allowed(client_id):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit excedido. Tente novamente mais tarde.",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": self.limiter.get_reset_time(client_id)
                },
                headers={
                    "Retry-After": str(self.limiter.get_reset_time(client_id)),
                    "X-RateLimit-Limit": str(self.limiter.requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(self.limiter.get_reset_time(client_id))
                }
            )
        
        # Adiciona headers de rate limit na resposta
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests)
        response.headers["X-RateLimit-Remaining"] = str(self.limiter.get_remaining(client_id))
        response.headers["X-RateLimit-Reset"] = str(self.limiter.get_reset_time(client_id))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Extrai identificador do cliente."""
        # Tenta pegar do header X-Forwarded-For (proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Fallback para IP direto
        return request.client.host if request.client else "unknown"


# ======================================================
# Validações de Upload
# ======================================================
def validate_file_extension(filename: str) -> bool:
    """Valida se a extensão do arquivo é permitida."""
    if not filename:
        return False
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in [e.strip().lower() for e in ALLOWED_EXTENSIONS]


def validate_file_size(size_bytes: int) -> bool:
    """Valida se o tamanho do arquivo está dentro do limite."""
    return size_bytes <= MAX_UPLOAD_SIZE_BYTES


def get_upload_limits() -> dict:
    """Retorna os limites de upload configurados."""
    return {
        "max_size_mb": MAX_UPLOAD_SIZE_MB,
        "max_size_bytes": MAX_UPLOAD_SIZE_BYTES,
        "allowed_extensions": ALLOWED_EXTENSIONS
    }


# ======================================================
# Security Headers Middleware
# ======================================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adiciona headers de segurança nas respostas."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Headers de segurança
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Remove header que expõe tecnologia
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


# ======================================================
# Request Size Limiter
# ======================================================
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limita tamanho das requisições."""
    
    def __init__(self, app, max_size: int = None):
        super().__init__(app)
        self.max_size = max_size or MAX_UPLOAD_SIZE_BYTES
    
    async def dispatch(self, request: Request, call_next):
        # Verifica Content-Length se disponível
        content_length = request.headers.get("content-length")
        
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "detail": f"Arquivo muito grande. Máximo: {MAX_UPLOAD_SIZE_MB}MB",
                    "code": "FILE_TOO_LARGE",
                    "max_size_mb": MAX_UPLOAD_SIZE_MB
                }
            )
        
        return await call_next(request)
