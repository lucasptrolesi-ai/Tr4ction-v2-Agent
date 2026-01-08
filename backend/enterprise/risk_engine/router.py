"""
Risk Detection API Routes
========================

Endpoints para análise de risco pré-save.

Não altera dados. Apenas retorna assessment com red flags.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.auth import get_current_user_required
from backend.db.models import User
from backend.enterprise.config import get_or_create_enterprise_config
from .detector import RiskDetectionEngine, RiskClassification

router = APIRouter(
    prefix="/enterprise/risk",
    tags=["Enterprise - Risk Detection"],
)

# Instância global
_risk_engine = RiskDetectionEngine()


class AssessFieldRequest(BaseModel):
    """Request para assessment de um campo."""
    template_key: str
    field_key: str
    value: str
    related_templates: Optional[Dict[str, Dict[str, Any]]] = None


class AssessTemplateRequest(BaseModel):
    """Request para assessment de um template completo."""
    template_key: str
    data: Dict[str, Any]
    previous_versions: Optional[List[Dict[str, Any]]] = None
    related_templates: Optional[Dict[str, Dict[str, Any]]] = None


@router.post(
    "/assess-field",
    summary="Assess Risk for Single Field Response",
    description="Avalia nível de risco de uma resposta em um campo.",
)
async def assess_field_risk(
    request: AssessFieldRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Avalia risco de uma resposta de campo.
    
    Retorna:
    - overall_risk: low, medium, high, critical
    - red_flags: Lista de issues detectadas
    - trust_score: 0.0-1.0
    - data_quality: 0.0-1.0
    """
    
    config = get_or_create_enterprise_config()
    if not config.risk_engine:
        return {
            "status": "disabled",
            "message": "Risk Engine não está habilitado"
        }
    
    assessment = _risk_engine.assess_field_response(
        template_key=request.template_key,
        field_key=request.field_key,
        value=request.value,
        related_templates=request.related_templates,
    )
    
    return assessment.to_dict()


@router.post(
    "/assess-template",
    summary="Assess Risk for Complete Template",
    description="Avalia nível de risco de um template completo.",
)
async def assess_template_risk(
    request: AssessTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Avalia risco completo de um template preenchido.
    
    Retorna:
    - overall_risk: low, medium, high, critical
    - red_flags: Lista completa de issues
    - decision_maturity: reactive, considered, strategic
    - coherence_score: Alinhamento com templates relacionados
    """
    
    config = get_or_create_enterprise_config()
    if not config.risk_engine:
        return {
            "status": "disabled",
            "message": "Risk Engine não está habilitado"
        }
    
    assessment = _risk_engine.assess_template_response(
        template_key=request.template_key,
        data=request.data,
        previous_versions=request.previous_versions,
        related_templates=request.related_templates,
    )
    
    # Retorna assessment + focus para AI Mentor
    return {
        **assessment.to_dict(),
        "mentoring_focus": _risk_engine.get_mentoring_focus(assessment),
    }


@router.get(
    "/red-flags/{startup_id}/{template_key}",
    summary="Get Recent Red Flags",
    description="Retorna red flags recentes de um template.",
)
async def get_recent_red_flags(
    startup_id: str,
    template_key: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna padrão de red flags detectadas nos últimos X preenchimentos.
    
    Útil para mentores identificarem padrões de risco.
    """
    
    config = get_or_create_enterprise_config()
    if not config.risk_engine:
        return {"status": "disabled"}
    
    # TODO: Implementar query no histórico de decisões
    # Por enquanto, retorna stub
    return {
        "startup_id": startup_id,
        "template_key": template_key,
        "message": "Feature em desenvolvimento"
    }
