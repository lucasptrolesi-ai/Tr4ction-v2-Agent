"""
Cognitive Memory API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.auth import get_current_user_required
from backend.db.models import User
from backend.enterprise.config import get_or_create_enterprise_config
from .models import CognitiveMemoryService

router = APIRouter(
    prefix="/enterprise/memory",
    tags=["Enterprise - Cognitive Memory"],
)


@router.get(
    "/context/{startup_id}",
    summary="Get Strategic Context",
    description="Retorna contexto estratégico completo de uma startup.",
)
async def get_strategic_context(
    startup_id: str,
    templates: Optional[str] = None,  # CSV list
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna memória estratégica de uma startup.
    
    Query params:
    - templates: Template keys separadas por vírgula (opcional)
    
    Retorna:
    - Contexto completo organizado por template
    - Inferências
    - Implicações de cada decisão
    """
    
    config = get_or_create_enterprise_config()
    if not config.cognitive_memory:
        return {"status": "disabled"}
    
    template_list = templates.split(",") if templates else None
    
    service = CognitiveMemoryService(db)
    context = service.get_strategic_context(startup_id, template_list)
    
    return {
        "startup_id": startup_id,
        "context": context,
    }


@router.get(
    "/related/{startup_id}/{template_key}/{field_key}",
    summary="Find Related Decisions",
    description="Encontra decisões relacionadas por implicações.",
)
async def get_related_decisions(
    startup_id: str,
    template_key: str,
    field_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna decisões relacionadas.
    
    Útil para entender chain de causas/efeitos.
    """
    
    config = get_or_create_enterprise_config()
    if not config.cognitive_memory:
        return {"status": "disabled"}
    
    service = CognitiveMemoryService(db)
    related = service.find_related_decisions(startup_id, template_key, field_key)
    
    return related
