"""
Governance API Routes
====================

Endpoints para validação pré-save usando governance engine.

Nota: Não altera dados existentes. Apenas retorna warnings.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.auth import get_current_user_required
from backend.db.models import User
from backend.enterprise.config import get_or_create_enterprise_config
from .engine import GovernanceEngine, GovernanceViolation

router = APIRouter(
    prefix="/enterprise/governance",
    tags=["Enterprise - Method Governance"],
)

# Instância global do engine
_governance_engine = GovernanceEngine()


class ValidateTemplateDataRequest(BaseModel):
    """Request para validação de template."""
    template_key: str
    data: Dict[str, Any]
    previous_data: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Resultado da validação."""
    template_key: str
    is_valid: bool
    violations: List[Dict[str, Any]]
    by_risk_level: Dict[str, int]
    critical_count: int
    medium_count: int
    low_count: int


@router.post(
    "/validate",
    response_model=ValidationResult,
    summary="Validate Template Data Against Governance Rules",
    description="Valida dados ANTES de salvar.",
)
async def validate_template_data(
    request: ValidateTemplateDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Valida dados de um template contra as regras de governança.
    
    NÃO altera nem salva nada. Apenas retorna warnings.
    
    Response:
    - violations: Lista de violações encontradas
    - by_risk_level: Contagem por nível
    - critical_count: Número de violações críticas
    """
    
    config = get_or_create_enterprise_config()
    if not config.method_governance:
        # Se desligado, retorna tudo OK
        return ValidationResult(
            template_key=request.template_key,
            is_valid=True,
            violations=[],
            by_risk_level={"low": 0, "medium": 0, "high": 0, "critical": 0},
            critical_count=0,
            medium_count=0,
            low_count=0,
        )
    
    # Valida
    violations = _governance_engine.validate_template_data(
        template_key=request.template_key,
        data=request.data,
        previous_data=request.previous_data,
    )
    
    # Agrupa por nível
    by_level = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for v in violations:
        by_level[v.risk_level.value] += 1
    
    return ValidationResult(
        template_key=request.template_key,
        is_valid=len(violations) == 0,
        violations=[v.to_dict() for v in violations],
        by_risk_level=by_level,
        critical_count=by_level.get("critical", 0),
        medium_count=by_level.get("medium", 0),
        low_count=by_level.get("low", 0),
    )


@router.get(
    "/rules/summary",
    summary="Get Governance Rules Summary",
    description="Retorna estatísticas das regras carregadas.",
)
async def get_rules_summary(
    current_user: User = Depends(get_current_user_required),
):
    """Retorna informações sobre as regras de governança."""
    
    config = get_or_create_enterprise_config()
    if not config.method_governance:
        return {"status": "disabled", "message": "Method Governance está desligado"}
    
    return {
        "enabled": True,
        "stats": _governance_engine.get_stats(),
        "rules_count": len(_governance_engine.rules),
    }
