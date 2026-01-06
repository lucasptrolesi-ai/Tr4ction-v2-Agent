# backend/routers/__init__.py

from .chat import router as chat_router
from .admin import router as admin_router
from .diagnostics import router as diagnostics_router
from .files import router as files_router
from .test import router as test_router
from .founder import router as founder_router
from .auth import router as auth_router
from .template_discovery import router as template_discovery_router
from .templates import router as templates_router

__all__ = [
    "chat_router",
    "admin_router",
    "diagnostics_router",
    "files_router",
    "test_router",
    "founder_router",
    "auth_router",
    "template_discovery_router",
    "templates_router",
]

