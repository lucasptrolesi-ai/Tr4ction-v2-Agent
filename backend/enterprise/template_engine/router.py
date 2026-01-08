"""
Template Engine API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.auth import get_current_user_required
from backend.db.models import User
from backend.enterprise.config import get_or_create_enterprise_config
from .orchestrator import DynamicTemplateEngine, VerticalType

router = APIRouter(
    prefix="/enterprise/templates",
    tags=["Enterprise - Template Engine"],
)

# Instância global
_template_engine = DynamicTemplateEngine()


@router.get(
    "/routes",
    summary="List Available Template Routes",
    description="Retorna rotas de templates disponíveis.",
)
async def list_routes(
    vertical: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna rotas de templates disponíveis.
    
    Query params:
    - vertical: Filtrar por vertical (saas, marketplace, etc)
    """
    
    config = get_or_create_enterprise_config()
    if not config.template_engine:
        return {"status": "disabled"}
    
    v = VerticalType(vertical) if vertical else None
    routes = _template_engine.get_available_routes(v)
    
    return {
        "routes": [
            {
                "route_id": r.route_id,
                "name": r.name,
                "description": r.description,
                "vertical": r.vertical.value,
                "template_count": len(r.templates),
                "is_default": r.is_default,
            }
            for r in routes
        ]
    }


@router.get(
    "/routes/{route_id}/progress",
    summary="Get Route Progress",
    description="Retorna progresso em uma rota para um founder.",
)
async def get_route_progress(
    route_id: str,
    startup_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna progresso de um founder em uma rota.
    
    Query params:
    - startup_id: ID da startup (obrigatório)
    """
    
    config = get_or_create_enterprise_config()
    if not config.template_engine:
        return {"status": "disabled"}
    
    # TODO: Buscar completed_templates de DecisionLedger
    completed = []  # Placeholder
    
    progress = _template_engine.get_route_progress(route_id, completed)
    
    return {
        "startup_id": startup_id,
        **progress,
    }


@router.get(
    "/routes/{route_id}/next",
    summary="Get Next Template in Route",
    description="Retorna próximo template baseado em branch logic.",
)
async def get_next_template(
    route_id: str,
    current_template_id: str = Query(...),
    startup_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna próximo template com base em branch logic.
    
    Query params:
    - current_template_id: Template atual
    - startup_id: ID da startup
    """
    
    config = get_or_create_enterprise_config()
    if not config.template_engine:
        return {"status": "disabled"}
    
    # TODO: Buscar completed_fields de DecisionLedger
    completed_fields = {}  # Placeholder
    
    next_node = _template_engine.get_next_template(
        route_id, current_template_id, completed_fields
    )
    
    if not next_node:
        return {"message": "Fim da rota"}
    
    return {
        "next_template": next_node.to_dict(),
        "route_id": route_id,
    }
