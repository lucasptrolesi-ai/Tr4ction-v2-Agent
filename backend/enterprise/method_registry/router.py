"""
Method Registry API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.auth import get_current_user_required
from backend.db.models import User
from backend.enterprise.config import get_or_create_enterprise_config
from .models import MethodRegistry, VerticalType

router = APIRouter(
    prefix="/enterprise/method",
    tags=["Enterprise - Method Registry"],
)

_registry = MethodRegistry()


@router.get(
    "/versions",
    summary="List Method Versions",
    description="Retorna todas as versões do método FCJ disponíveis.",
)
async def list_versions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna versões do método.
    
    Cada versão tem:
    - Version string (v1.0, v1.5, v2.0)
    - Verticais suportadas
    - Breaking changes (se houver)
    - Status (deprecated ou não)
    """
    
    config = get_or_create_enterprise_config()
    if not config.verticalization:
        return {"status": "disabled"}
    
    versions = _registry.get_available_versions()
    
    return {
        "versions": [v.to_dict() for v in versions],
        "latest": _registry.get_latest_version().version,
    }


@router.get(
    "/versions/{version}",
    summary="Get Method Version Details",
    description="Retorna detalhes de uma versão específica.",
)
async def get_version_details(
    version: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Retorna detalhes de uma versão."""
    
    config = get_or_create_enterprise_config()
    if not config.verticalization:
        return {"status": "disabled"}
    
    v = _registry.get_version(version)
    if not v:
        raise HTTPException(status_code=404, detail="Versão não encontrada")
    
    return v.to_dict()


@router.get(
    "/verticals",
    summary="List Supported Verticals",
    description="Retorna verticais suportadas.",
)
async def list_verticals(
    version: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna verticais suportadas.
    
    Query params:
    - version: Filtrar por versão (opcional)
    """
    
    config = get_or_create_enterprise_config()
    if not config.verticalization:
        return {"status": "disabled"}
    
    if version:
        v = _registry.get_version(version)
        if not v:
            raise HTTPException(status_code=404, detail="Versão não encontrada")
        verticals = [vert.value for vert in v.supported_verticals]
    else:
        verticals = [v.value for v in VerticalType]
    
    return {
        "verticals": verticals,
        "count": len(verticals),
    }


@router.get(
    "/verticals/{vertical}/templates",
    summary="Get Templates for Vertical",
    description="Retorna templates específicos de uma vertical.",
)
async def get_vertical_templates(
    vertical: str,
    version: str = Query("v2.0"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna templates específicos de uma vertical.
    
    Query params:
    - version: Versão do método (default: v2.0)
    """
    
    config = get_or_create_enterprise_config()
    if not config.verticalization:
        return {"status": "disabled"}
    
    try:
        v = VerticalType(vertical)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Vertical inválido: {vertical}")
    
    templates = _registry.get_templates_for_vertical(v, version)
    rules = _registry.get_vertical_specific_rules(v, version)
    
    return {
        "vertical": vertical,
        "version": version,
        "templates": templates,
        "rules": rules,
    }


@router.get(
    "/migration-path",
    summary="Suggest Migration Path",
    description="Sugere caminho de upgrade se necessário.",
)
async def suggest_migration(
    current_version: str = Query(...),
    target_vertical: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Sugere upgrade de versão se necessário.
    
    Query params:
    - current_version: Versão atual (ex: v1.0)
    - target_vertical: Vertical desejada (ex: marketplace)
    """
    
    config = get_or_create_enterprise_config()
    if not config.verticalization:
        return {"status": "disabled"}
    
    try:
        vertical = VerticalType(target_vertical)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Vertical inválido: {target_vertical}")
    
    migration = _registry.suggest_migration_path(current_version, vertical)
    
    if not migration:
        raise HTTPException(status_code=404, detail="Combinação inválida")
    
    return {
        "current_version": current_version,
        "target_vertical": target_vertical,
        **migration,
    }
