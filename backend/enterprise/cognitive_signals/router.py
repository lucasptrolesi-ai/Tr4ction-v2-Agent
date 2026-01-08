"""
Cognitive Signals API Routes
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.auth import get_current_user_required
from backend.db.models import User
from backend.enterprise.config import get_or_create_enterprise_config
from .generator import CognitiveSignalGenerator

router = APIRouter(
    prefix="/enterprise/signals",
    tags=["Enterprise - Cognitive Signals"],
)

_signal_generator = CognitiveSignalGenerator()


class GenerateSignalsRequest(BaseModel):
    """Request para gerar sinais."""
    template_key: str
    field_key: str
    value: str
    risk_assessment: Optional[Dict[str, Any]] = None
    governance_violations: Optional[List[Dict[str, Any]]] = None
    coherence_issues: Optional[List[str]] = None


class GenerateTemplateSignalsRequest(BaseModel):
    """Request para gerar sinais de um template completo."""
    template_key: str
    completed_fields: Dict[str, Any]
    risk_assessment: Optional[Dict[str, Any]] = None
    governance_violations: Optional[List[Dict[str, Any]]] = None


@router.post(
    "/field",
    summary="Generate Signals for Field Response",
    description="Gera sinais cognitivos para uma resposta de campo.",
)
async def generate_field_signals(
    request: GenerateSignalsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Gera sinais para uma resposta de campo.
    
    Retorna campos opcionais para adicionar ao payload:
    - risk_level
    - alert_message
    - next_step_hint
    - reasoning_summary
    - confidence_score
    - coherence_issues
    """
    
    config = get_or_create_enterprise_config()
    if not config.cognitive_signals:
        return {"status": "disabled"}
    
    signals = _signal_generator.generate_signals_for_response(
        template_key=request.template_key,
        field_key=request.field_key,
        value=request.value,
        risk_assessment=request.risk_assessment,
        governance_violations=request.governance_violations,
        coherence_issues=request.coherence_issues,
    )
    
    return signals.to_dict()


@router.post(
    "/template",
    summary="Generate Signals for Template",
    description="Gera sinais cognitivos para um template completo.",
)
async def generate_template_signals(
    request: GenerateTemplateSignalsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Gera sinais para um template completo.
    
    Useful para dashboard que precisa mostrar progress indicators.
    """
    
    config = get_or_create_enterprise_config()
    if not config.cognitive_signals:
        return {"status": "disabled"}
    
    signals = _signal_generator.generate_signals_for_template(
        template_key=request.template_key,
        completed_fields=request.completed_fields,
        risk_assessment=request.risk_assessment,
        governance_violations=request.governance_violations,
    )
    
    return signals.to_dict()
