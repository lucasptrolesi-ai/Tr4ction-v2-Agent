"""
AI Audit API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.auth import get_current_user_required
from backend.db.models import User
from backend.enterprise.config import get_or_create_enterprise_config
from .models import AIAuditService

router = APIRouter(
    prefix="/enterprise/ai-audit",
    tags=["Enterprise - AI Audit"],
)


@router.get(
    "/trail/{startup_id}",
    summary="Get AI Audit Trail",
    description="Retorna trail de auditoria de interações com IA.",
)
async def get_audit_trail(
    startup_id: str,
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna trail de auditoria (read-only).
    
    Query params:
    - event_type: Filtrar por tipo (mentor_response, risk_assessment, etc)
    - limit: Máximo de registros (1-1000)
    """
    
    config = get_or_create_enterprise_config()
    if not config.ai_audit:
        return {"status": "disabled"}
    
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    service = AIAuditService(db)
    logs = service.get_audit_trail(startup_id, event_type, limit)
    
    return {
        "startup_id": startup_id,
        "event_count": len(logs),
        "events": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "model": log.model,
                "success": log.success == 1,
                "latency_ms": log.latency_ms,
                "tokens_used": log.tokens_used,
                "template_key": log.template_key,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }


@router.get(
    "/stats/{startup_id}",
    summary="Get AI Performance Statistics",
    description="Retorna estatísticas de performance da IA.",
)
async def get_ai_stats(
    startup_id: str,
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """
    Retorna performance stats da IA.
    
    Inclui:
    - Success rate
    - Average latency
    - Total tokens used
    - Models used
    """
    
    config = get_or_create_enterprise_config()
    if not config.ai_audit:
        return {"status": "disabled"}
    
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    service = AIAuditService(db)
    stats = service.get_ai_performance_stats(startup_id, event_type)
    
    return {
        "startup_id": startup_id,
        **stats
    }
