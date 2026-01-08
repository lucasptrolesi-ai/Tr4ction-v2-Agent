"""
Decision Ledger API Routes
==========================

Endpoints READ-ONLY para auditoria de decisões.

POST endpoints são apenas para registro interno (via DecisionLedgerService).
Nunca para API pública.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.auth import get_current_user_required
from backend.db.models import User
from backend.enterprise.config import get_or_create_enterprise_config
from .models import DecisionLedgerService, DecisionEvent

router = APIRouter(
    prefix="/enterprise/decisions",
    tags=["Enterprise - Decision Ledger"],
)


class DecisionEventResponse(BaseModel):
    """Response model para DecisionEvent."""
    id: str
    user_email: str
    template_key: str
    field_key: str
    field_label: Optional[str]
    previous_value: Optional[dict]
    new_value: dict
    value_type: str
    reasoning: Optional[str]
    source: str
    created_at: str
    expected_outcome: Optional[str]
    actual_outcome: Optional[str]
    outcome_success: Optional[int]


@router.get(
    "/history/{startup_id}",
    response_model=List[DecisionEventResponse],
    summary="Get Decision History for Startup",
    description="Retorna histórico de todas as decisões (read-only). Apenas admin/mentor.",
)
async def get_decision_history(
    startup_id: str,
    template_key: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna decisões ordenadas por data (mais recentes primeiro).
    
    Query params:
    - template_key: Filtrar por template (opcional)
    - limit: Máximo de registros (1-1000)
    """
    
    config = get_or_create_enterprise_config()
    if not config.decision_ledger:
        raise HTTPException(
            status_code=403,
            detail="Decision Ledger não está habilitado"
        )
    
    # Valida autorização (apenas admin ou mentor da startup)
    if current_user.role not in ["admin"] and startup_id != current_user.id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    service = DecisionLedgerService(db)
    events = service.get_decision_history(startup_id, template_key, limit=limit)
    
    return [DecisionEventResponse(
        id=e.id,
        user_email=e.user_email,
        template_key=e.template_key,
        field_key=e.field_key,
        field_label=e.field_label,
        previous_value=e.previous_value,
        new_value=e.new_value,
        value_type=e.value_type,
        reasoning=e.reasoning,
        source=e.source,
        created_at=e.created_at.isoformat() if e.created_at else None,
        expected_outcome=e.expected_outcome,
        actual_outcome=e.actual_outcome,
        outcome_success=e.outcome_success,
    ) for e in events]


@router.get(
    "/{startup_id}/{template_key}/{field_key}",
    response_model=List[DecisionEventResponse],
    summary="Get Decision History for Specific Field",
    description="Retorna todas as mudanças de um campo.",
)
async def get_field_history(
    startup_id: str,
    template_key: str,
    field_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Retorna histórico completo de mudanças em um campo específico."""
    
    config = get_or_create_enterprise_config()
    if not config.decision_ledger:
        raise HTTPException(status_code=403, detail="Decision Ledger desligado")
    
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    service = DecisionLedgerService(db)
    events = service.get_decision_by_field(startup_id, template_key, field_key)
    
    return [DecisionEventResponse(
        id=e.id,
        user_email=e.user_email,
        template_key=e.template_key,
        field_key=e.field_key,
        field_label=e.field_label,
        previous_value=e.previous_value,
        new_value=e.new_value,
        value_type=e.value_type,
        reasoning=e.reasoning,
        source=e.source,
        created_at=e.created_at.isoformat() if e.created_at else None,
        expected_outcome=e.expected_outcome,
        actual_outcome=e.actual_outcome,
        outcome_success=e.outcome_success,
    ) for e in events]


@router.get(
    "/audit/summary/{startup_id}",
    summary="Get Decision Summary",
    description="Retorna estatísticas de decisões.",
)
async def get_decision_summary(
    startup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna resumo de decisões:
    - Total de decisões
    - Por fonte (founder, ai_mentor, etc)
    - Por template
    - Taxa de mudanças
    """
    
    config = get_or_create_enterprise_config()
    if not config.decision_ledger:
        raise HTTPException(status_code=403, detail="Decision Ledger desligado")
    
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    service = DecisionLedgerService(db)
    events = service.get_decision_history(startup_id, limit=10000)
    
    # Agrupa estatísticas
    by_source = {}
    by_template = {}
    by_user = {}
    
    for event in events:
        by_source[event.source] = by_source.get(event.source, 0) + 1
        by_template[event.template_key] = by_template.get(event.template_key, 0) + 1
        by_user[event.user_email] = by_user.get(event.user_email, 0) + 1
    
    return {
        "startup_id": startup_id,
        "total_decisions": len(events),
        "by_source": by_source,
        "by_template": by_template,
        "by_user": by_user,
        "first_decision": events[-1].created_at.isoformat() if events else None,
        "last_decision": events[0].created_at.isoformat() if events else None,
    }
