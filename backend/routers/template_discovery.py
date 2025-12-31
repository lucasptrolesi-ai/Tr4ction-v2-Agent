"""
Template Discovery Router - Endpoints públicos para descobrir templates dinamicamente

100% genérico - sem hardcode de cycles (Q1, Q2, Q3...)
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from core.models import SuccessResponse
from db.database import get_db
from services.template_registry import get_registry

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/cycles", response_model=SuccessResponse)
async def list_cycles(db: Session = Depends(get_db)):
    """
    Lista todos os cycles disponíveis
    
    Returns:
        Lista de cycles (Q1, Q2, Q3, etc.)
    """
    try:
        registry = get_registry(db)
        cycles = registry.list_available_cycles()
        
        return SuccessResponse(data={
            "cycles": cycles,
            "total": len(cycles)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=SuccessResponse)
async def list_all_templates(
    cycle: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista templates disponíveis
    
    Args:
        cycle: Filtrar por cycle específico (opcional)
    
    Returns:
        Lista de templates com metadados
    """
    try:
        registry = get_registry(db)
        
        if cycle:
            templates = registry.list_templates_by_cycle(cycle)
        else:
            templates = registry.list_all_templates()
        
        return SuccessResponse(data={
            "templates": templates,
            "total": len(templates),
            "cycle": cycle
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cycle}", response_model=SuccessResponse)
async def list_templates_by_cycle_path(
    cycle: str,
    db: Session = Depends(get_db)
):
    """
    Lista templates de um cycle específico
    
    Args:
        cycle: Identificador do cycle (Q1, Q2, Q3...)
    
    Returns:
        Lista de templates do cycle
    """
    try:
        registry = get_registry(db)
        templates = registry.list_templates_by_cycle(cycle)
        
        if not templates:
            raise HTTPException(
                status_code=404,
                detail=f"No templates found for cycle '{cycle}'"
            )
        
        return SuccessResponse(data={
            "cycle": cycle,
            "templates": templates,
            "total": len(templates)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cycle}/{template_key}", response_model=SuccessResponse)
async def get_template_with_schema(
    cycle: str,
    template_key: str,
    db: Session = Depends(get_db)
):
    """
    Busca template específico com schema completo
    
    Args:
        cycle: Cycle do template
        template_key: Chave do template
    
    Returns:
        Metadados + schema JSON completo
    """
    try:
        registry = get_registry(db)
        template = registry.get_template(cycle, template_key)
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_key}' not found in cycle '{cycle}'"
            )
        
        return SuccessResponse(data=template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cycle}/{template_key}/schema", response_model=SuccessResponse)
async def get_only_schema(
    cycle: str,
    template_key: str,
    db: Session = Depends(get_db)
):
    """
    Carrega apenas o schema JSON de um template
    
    Args:
        cycle: Cycle do template
        template_key: Chave do template
    
    Returns:
        Schema JSON completo
    """
    try:
        registry = get_registry(db)
        schema = registry.get_template_schema(cycle, template_key)
        
        if not schema:
            raise HTTPException(
                status_code=404,
                detail=f"Schema not found for template '{template_key}' in cycle '{cycle}'"
            )
        
        return SuccessResponse(data=schema)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
